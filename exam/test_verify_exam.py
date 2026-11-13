"""The live verifier must accept quiet output and require real execution."""
import unittest
from pathlib import Path
import tempfile
from verify_exam import case_passed,live_cases


class LiveVerifierTests(unittest.TestCase):
    def test_show_chat_exit_patch_is_repeatable(self):
        from setup_exam import patch_show_chat_exit
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'app.py'
            path.write_text('def main():\n    if show_chat:\n        ChatHandler.show_messages(show_chat, md)\n\n    if sum((shell, code)) > 1:\n        raise ValueError()\n')
            patch_show_chat_exit(path)
            first=path.read_text()
            patch_show_chat_exit(path)
            self.assertEqual(path.read_text(),first)
            self.assertEqual(first.count('        return\n'),1)

    def test_quiet_success_requires_no_automatic_approval_banner(self):
        case=live_cases(False)[1]
        self.assertTrue(case_passed(0,'COMMAND: pwd\nOUTPUT:\nExit code: 0, Output:\n/home/fixture\n',case))

    def test_model_text_alone_does_not_prove_a_command_executed(self):
        self.assertFalse(case_passed(0,'sgpt Reply exactly EXAM_TEXT_OK\nA different answer\n',live_cases(False)[0]))
        case=live_cases(True)[2]
        self.assertFalse(case_passed(0,'EXAM_TOOL_OK\n',case))
        self.assertFalse(case_passed(0,'COMMAND: Get-Date\nOUTPUT:\nExit code: 1\nEXAM_TOOL_OK\n',case))
        self.assertTrue(case_passed(0,'COMMAND: Get-Date\nOUTPUT:\nExit code: 0\nFriday 2026\nEXAM_TOOL_OK\n',case))

    def test_failure_or_human_prompt_is_not_a_pass(self):
        case=live_cases(False)[1]
        output='COMMAND: pwd\nExit code: 0\n'
        self.assertFalse(case_passed(1,output,case))
        self.assertFalse(case_passed(0,output+'Execute this exact command? Type yes to approve:',case))


if __name__=='__main__':unittest.main()
