import io
import sys
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from terminal_ui import TerminalPrinter, install_terminal_printer


class TerminalUITests(unittest.TestCase):
    def test_reopened_console_cannot_override_noninteractive_entry(self):
        from terminal_ui import interactive_input
        with patch('terminal_ui.sys.stdin.isatty',return_value=True),patch('builtins.input',side_effect=AssertionError('Reopened console would hang')):
            with self.assertRaises(EOFError):interactive_input('approve: ',interactive=False)

    def test_closed_stdin_never_calls_console_input_hook(self):
        from terminal_ui import interactive_input
        with patch('terminal_ui.sys.stdin.isatty',return_value=False),patch('builtins.input',side_effect=AssertionError('Console hook would hang')):
            with self.assertRaises(EOFError):interactive_input('approve: ')

    def test_approval_prompt_is_ordered_and_visible_in_both_stream_modes(self):
        for live in (True, False):
            with self.subTest(live=live):
                output = io.StringIO()
                def chunks():
                    yield 'Preparing command.\n'
                    # Tool execution advances inside the printer's generator.
                    self.assertEqual(output.getvalue(), 'Preparing command.\n')
                    self.assertIs(sys.stdout, output)
                    print('Approval required: installation')
                    print('Execute this exact command? Type yes to approve: ', end='', flush=True)
                    self.assertIn('Type yes to approve: ', output.getvalue())
                    yield '\nCommand not executed: approval was not given.\n'
                    yield 'Stopped.'
                with redirect_stdout(output):
                    result = TerminalPrinter()(chunks(), live)
                self.assertEqual(result, 'Preparing command.\n\nCommand not executed: approval was not given.\nStopped.')
                self.assertEqual(output.getvalue().count('Preparing command.'), 1)
                self.assertEqual(output.getvalue().count('Approval required:'), 1)
                self.assertTrue(output.getvalue().endswith('Stopped.\n'))

    def test_installation_overrides_shellgpt_printer_without_loading_rich(self):
        class Handler:
            @property
            def printer(self):
                raise AssertionError('Live renderer selected')
        install_terminal_printer(Handler)
        self.assertIsInstance(Handler().printer, TerminalPrinter)

    def test_interruption_does_not_repeat_already_emitted_text(self):
        def chunks():
            yield 'Before approval.\n'
            raise KeyboardInterrupt
        output = io.StringIO()
        with redirect_stdout(output), self.assertRaises(KeyboardInterrupt):
            TerminalPrinter()(chunks())
        self.assertEqual(output.getvalue(), 'Before approval.\n')


if __name__ == '__main__':
    unittest.main()
