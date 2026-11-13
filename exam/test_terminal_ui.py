import io
import sys
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from terminal_ui import TerminalPrinter, install_terminal_printer


class TerminalUITests(unittest.TestCase):
    def test_local_key_error_does_not_blame_credentials_or_print_its_value(self):
        from exam_runtime import failure_heading
        text=failure_heading(KeyError('sensitive-value'))
        self.assertIn('failed locally: KeyError',text)
        self.assertNotIn('sensitive-value',text)
        self.assertNotIn('billing',text)
        self.assertNotIn('endpoint',text)

    def test_history_renderer_handles_tool_only_and_null_content_without_mutation(self):
        import copy
        from terminal_ui import install_chat_history_renderer
        messages=[{'role':'system','content':'You are ShellGPT'},
                  {'role':'user','content':'Inspect this machine'},
                  {'role':'assistant','tool_calls':[{'id':'call1','function':{'name':'execute_shell_command','arguments':'{"shell_command":"pwd"}'}}],
                   'reasoning_details':[{'type':'reasoning.encrypted','data':'private-metadata'}]},
                  {'role':'tool','tool_call_id':'call1','content':'ACTUAL_RESULT'},
                  {'role':'assistant','content':None,'tool_calls':[{'id':'call2','function':{'name':'init_machine','arguments':'{}'}}]},
                  {'role':'assistant','content':'Done'}]
        original=copy.deepcopy(messages)
        class Session:
            def _read(self,chat_id):return messages
            def get_messages(self,chat_id):
                return [f"{message['role']}: {message['content']}" for message in self._read(chat_id)]
        install_chat_history_renderer(Session)
        rendered=Session().get_messages('challenge5')
        self.assertEqual(rendered[0],'system: You are ShellGPT')
        self.assertIn('execute_shell_command',rendered[2])
        self.assertIn('ACTUAL_RESULT',rendered[3])
        self.assertIn('init_machine',rendered[4])
        self.assertNotIn('private-metadata','\n'.join(rendered))
        self.assertEqual(messages,original)

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
