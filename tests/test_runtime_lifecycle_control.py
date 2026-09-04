import unittest

from matharc.v02.runtime.state_machine import LifecycleError, RunState, RunStateMachine


class RuntimeLifecycleTests(unittest.TestCase):
    def test_stop_drains_active_tasks_and_rejects_new_work(self):
        machine = RunStateMachine()
        machine.start(); machine.start_task("e1")
        receipt = machine.stop()
        self.assertEqual(receipt.resulting_state, RunState.DRAINING)
        with self.assertRaises(LifecycleError): machine.start_task("e2")
        machine.finish_task("e1")
        self.assertEqual(machine.status, RunState.STOPPED)

    def test_pause_resume_and_cancel_are_explicit(self):
        machine = RunStateMachine(RunState.CREATED)
        machine.start(); machine.pause()
        with self.assertRaises(LifecycleError): machine.start_task("e1")
        machine.resume(); machine.start_task("e1")
        receipt = machine.cancel()
        self.assertEqual(receipt.resulting_state, RunState.CANCELLED)
        self.assertEqual(receipt.terminated_tasks, ("e1",))


if __name__ == "__main__": unittest.main()
