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


if __name__ == "__main__":
    unittest.main()
