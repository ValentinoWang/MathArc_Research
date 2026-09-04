import json
import os
import socket
import stat
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from matharc.demo import write_demo


FINAL = {
    "status": "progress",
    "executive_summary": "API smoke response.",
    "public_reasoning": {
        "objective": "test API",
        "premises": ["frozen run"],
        "proposed_move": "stream JSONL",
        "observation": "events arrived",
        "falsification": "malform the stream",
        "decision": "keep proposal-only",
    },
    "claim_updates": [],
    "tool_requests": [],
    "risks": [],
    "next_actions": ["continue"],
    "claim_boundary": "No claim promotion.",
}


class CodexApiTests(unittest.TestCase):
    def _port(self) -> int:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def _fake_codex(self, root: Path) -> Path:
        path = root / "fake-codex"
        path.write_text(
            "#!/usr/bin/env python3\n"
            "import json,sys\n"
            f"FINAL={json.dumps(FINAL)!r}\n"
            "args=sys.argv[1:]\n"
            "last=args[args.index('--output-last-message')+1]\n"
            "sys.stdin.read()\n"
            "print(json.dumps({'type':'thread.started','thread_id':'api-thread'}),flush=True)\n"
            "print(json.dumps({'type':'item.completed','item':{'id':'r','type':'reasoning','text':'public API reasoning'}}),flush=True)\n"
            "print(json.dumps({'type':'turn.completed','usage':{'input_tokens':2,'cached_input_tokens':0,'cache_write_input_tokens':0,'output_tokens':2,'reasoning_output_tokens':1}}),flush=True)\n"
            "open(last,'w',encoding='utf-8').write(FINAL)\n",
            encoding="utf-8",
        )
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path

    def _e2e_fake_codex(self, root: Path) -> Path:
        """Synthetic worker for the HTTP question-to-evidence acceptance chain.

        This fixture is deliberately deterministic and local.  Its events model
        the public event contract (decomposition, a tool call, and exact
        verification output); they are not production or human-acceptance proof.
        """
        path = root / "fake-codex-e2e"
        final = {
            "status": "progress",
            "executive_summary": "Synthetic decomposition and exact verification completed.",
            "public_reasoning": {
                "objective": "Decompose one bounded question.",
                "premises": ["The fixture problem is frozen for this test."],
                "proposed_move": "Split the question into a claim and a replayable check.",
                "observation": "The exact checker returned PASS for the fixture input.",
                "falsification": "A mismatch in the checker output would keep the claim open.",
                "decision": "Keep the result proposal-only pending governed promotion.",
            },
            "claim_updates": [
                {
                    "claim_id": "C-E2E",
                    "action": "keep_open",
                    "statement": "The fixture identity holds on its declared bounded input.",
                    "scope": "fixture input only",
                    "evidence_needed": ["E-E2E-EXACT"],
                }
            ],
            "tool_requests": [
                {
                    "tool": "fixture-exact-checker",
                    "purpose": "Verify the decomposed claim exactly.",
                    "command": "python -m matharc fixture-exact-check",
                    "expected_discriminator": "verified=true; evidence_id=E-E2E-EXACT",
                }
            ],
            "risks": ["Synthetic worker output is not independent human acceptance."],
            "next_actions": ["Attach E-E2E-EXACT through the verifier-controlled gate."],
            "claim_boundary": "No mathematical promotion occurred.",
        }
        script = (
            "#!/usr/bin/env python3\n"
            "import json, sys\n"
            f"FINAL = {final!r}\n"
            "args = sys.argv[1:]\n"
            "last = args[args.index('--output-last-message') + 1]\n"
            "question = sys.stdin.read()\n"
            "if 'What is the smallest exact certificate?' not in question:\n"
            "    raise SystemExit('question was not forwarded to the worker prompt')\n"
            "events = [\n"
            " {'type':'thread.started','thread_id':'e2e-thread'},\n"
            " {'type':'item.completed','item':{'id':'decompose-1','type':'reasoning','text':'Decompose: identify C-E2E, its bounded scope, and the replay obligation.'}},\n"
            " {'type':'item.completed','item':{'id':'tool-1','type':'mcp_tool_call','server':'fixture','tool':'fixture-exact-checker','arguments':{'input':'1+1=2'},'status':'completed'}},\n"
            " {'type':'item.completed','item':{'id':'verify-1','type':'command_execution','command':'python -m matharc fixture-exact-check','aggregated_output':'verified=true\\\\nevidence_id=E-E2E-EXACT\\\\n','exit_code':0,'status':'completed'}},\n"
            " {'type':'turn.completed','usage':{'input_tokens':7,'cached_input_tokens':0,'cache_write_input_tokens':0,'output_tokens':11,'reasoning_output_tokens':3}},\n"
            "]\n"
            "for event in events:\n"
            "    print(json.dumps(event, ensure_ascii=False), flush=True)\n"
            "with open(last, 'w', encoding='utf-8') as handle:\n"
            "    json.dump(FINAL, handle, ensure_ascii=False)\n"
        )
        path.write_text(script, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path

    def test_http_console_and_codex_turn(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_path = write_demo(root / "demo")["run"]
            fake = self._fake_codex(root)
            port = self._port()
            env = dict(os.environ)
            env.update(
                {
                    "MATHARC_CODEX_EXECUTABLE": str(fake),
                    "MATHARC_CODEX_WORKSPACE": str(root),
                    "MATHARC_CODEX_SESSION_DIR": str(root / "sessions"),
                }
            )
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "matharc",
                    "serve",
                    "--run",
                    str(run_path),
                    "--workspace",
                    str(root),
                    "--port",
                    str(port),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
            )
            base = f"http://127.0.0.1:{port}"
            try:
                for _ in range(60):
                    try:
                        with urllib.request.urlopen(base + "/api/health", timeout=0.5) as response:
                            if response.status == 200:
                                break
                    except (urllib.error.URLError, TimeoutError):
                        time.sleep(0.1)
                else:
                    self.fail("MathArc API did not start")

                with urllib.request.urlopen(base + "/", timeout=2) as response:
                    html = response.read().decode("utf-8")
                self.assertIn("Codex Research Agents", html)

                request = urllib.request.Request(
                    base + "/api/agent/turn",
                    data=json.dumps(
                        {"role": "strategist", "message": "api smoke", "sandbox": "read-only"}
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=10) as response:
                    result = json.loads(response.read().decode("utf-8"))
                self.assertEqual("api-thread", result["result"]["thread_id"])
                self.assertEqual("progress", result["result"]["final_response"]["status"])
                self.assertTrue(result["result"]["result_sha256"])

                stream_request = urllib.request.Request(
                    base + "/api/agent/stream",
                    data=json.dumps(
                        {"role": "verifier", "message": "stream smoke", "sandbox": "read-only"}
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(stream_request, timeout=10) as response:
                    stream = response.read().decode("utf-8")
                self.assertIn("event: thread_started", stream)
                self.assertIn("event: matharc_result", stream)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                if process.stdout is not None:
                    process.stdout.close()
                if process.stderr is not None:
                    process.stderr.close()

    def test_http_question_decomposition_tool_verification_and_evidence_output(self) -> None:
        """Exercise the complete synthetic HTTP/API demo acceptance chain."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_path = write_demo(root / "demo")["run"]
            fake = self._e2e_fake_codex(root)
            port = self._port()
            env = dict(os.environ)
            env.update(
                {
                    "MATHARC_CODEX_EXECUTABLE": str(fake),
                    "MATHARC_CODEX_WORKSPACE": str(root),
                    "MATHARC_CODEX_SESSION_DIR": str(root / "sessions"),
                }
            )
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "matharc",
                    "serve",
                    "--run",
                    str(run_path),
                    "--workspace",
                    str(root),
                    "--port",
                    str(port),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
            )
            base = f"http://127.0.0.1:{port}"
            try:
                for _ in range(60):
                    try:
                        with urllib.request.urlopen(base + "/api/health", timeout=0.5) as response:
                            if response.status == 200:
                                break
                    except (urllib.error.URLError, TimeoutError):
                        time.sleep(0.1)
                else:
                    self.fail("MathArc API did not start")

                payload = {
                    "role": "verifier",
                    "message": "What is the smallest exact certificate?",
                    "sandbox": "read-only",
                }
                request = urllib.request.Request(
                    base + "/api/agent/turn",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(request, timeout=10) as response:
                    result = json.loads(response.read().decode("utf-8"))

                self.assertEqual("e2e-thread", result["result"]["thread_id"])
                self.assertFalse(result["events"][0]["payload"]["acceptance_authority"])
                final = result["result"]["final_response"]
                self.assertEqual("keep_open", final["claim_updates"][0]["action"])
                self.assertIn("E-E2E-EXACT", final["claim_updates"][0]["evidence_needed"])
                self.assertEqual("fixture-exact-checker", final["tool_requests"][0]["tool"])
                self.assertEqual("No mathematical promotion occurred.", final["claim_boundary"])

                events = result["result"]["events"]
                event_types = [event["type"] for event in events]
                self.assertIn("thread.started", event_types)
                self.assertIn("turn.completed", event_types)
                reasoning = next(
                    event for event in events
                    if event["payload"].get("item_type") == "reasoning"
                )
                self.assertIn("Decompose", reasoning["payload"]["text"])
                tool = next(
                    event for event in events
                    if event["payload"].get("item_type") == "mcp_tool_call"
                )
                self.assertEqual("fixture-exact-checker", tool["payload"]["tool"])
                verification = next(
                    event for event in events
                    if event["payload"].get("item_type") == "command_execution"
                )
                self.assertEqual(0, verification["payload"]["exit_code"])
                self.assertIn("evidence_id=E-E2E-EXACT", verification["payload"]["output"])
                self.assertTrue(result["result"]["result_sha256"])
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                if process.stdout is not None:
                    process.stdout.close()
                if process.stderr is not None:
                    process.stderr.close()


if __name__ == "__main__":
    unittest.main()
