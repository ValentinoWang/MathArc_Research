import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from matharc.v02.runtime.recovery import build_recovery_plan
from matharc.v02.runtime.run_store import RuntimeStore


class RuntimeCrashRecoveryTests(unittest.TestCase):
    def test_cold_start_after_forced_process_termination_recovers_last_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "runtime"
            marker = Path(tmp) / "durable.marker"
            script = (
                "from pathlib import Path\n"
                "import os, time\n"
                "from matharc.v02.runtime.run_store import RuntimeStore\n"
                f"store = RuntimeStore(Path({str(root)!r}))\n"
                "store.create_run({'runtime_run_id': 'run-1', 'workspace_id': 'w', 'trace_id': 't', 'status': 'RUNNING'})\n"
                "store.record_generation_commit({'runtime_run_id': 'run-1', 'generation_id': 'g1', 'snapshot_digest': 'snap-1', 'complete': True, 'closed': True, 'status': 'COMPLETED'})\n"
                f"Path({str(marker)!r}).write_text('ready')\n"
                "time.sleep(60)\n"
            )
            process = subprocess.Popen([sys.executable, "-c", script], cwd=os.getcwd())
            try:
                deadline = time.monotonic() + 10
                while not marker.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(marker.exists(), "child did not reach durable commit")
                process.kill()
                process.wait(timeout=5)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=5)

            recovered = RuntimeStore.load(root)
            plan = build_recovery_plan(recovered, expected={"snapshot_digest": "snap-1"})
            self.assertEqual(recovered.state["commits"][0]["generation_id"], "g1")
            self.assertEqual(plan.next_generation_id, "g2")
            self.assertEqual(plan, build_recovery_plan(recovered, expected={"snapshot_digest": "snap-1"}))


if __name__ == "__main__":
    unittest.main()
