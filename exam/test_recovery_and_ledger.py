"""Tests for bounded API retries, command execution ledger, and incremental mid-turn chat persistence."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from exam_runtime import complete
from exam_workflow import Workflow
from providers import ProviderCalls, select_profile


class TransientAPIError(RuntimeError):
    def __init__(self, status_code, message='temporary failure', retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        headers = {'Retry-After': str(retry_after)} if retry_after is not None else {}
        self.response = SimpleNamespace(headers=headers)


class Message:
    def __init__(self, value):
        self.value = value

    def model_dump(self, **kwargs):
        return self.value.copy()


class RecoveryAndLedgerTests(unittest.TestCase):
    def test_provider_calls_retries_429_and_503_with_retry_after_then_succeeds(self):
        attempts = []
        sleeps = []

        def raw_create(**kwargs):
            attempts.append(kwargs)
            if len(attempts) == 1:
                raise TransientAPIError(429, 'rate limited', retry_after='1.5')
            if len(attempts) == 2:
                raise TransientAPIError(503, 'upstream unavailable')
            return SimpleNamespace(
                choices=[SimpleNamespace(finish_reason='stop', message=SimpleNamespace(content='RECOVERED_OK'))],
                usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5),
            )

        raw = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=raw_create)))
        logs = []
        active = select_profile({}, 'openrouter-deepseek', {'openrouter': 'key'})
        calls = ProviderCalls(active, logs.append, raw, max_retries=2, sleep=sleeps.append)
        response = calls.chat.completions.create(model=active['DEFAULT_MODEL'], messages=[])
        self.assertEqual(response.choices[0].message.content, 'RECOVERED_OK')
        self.assertEqual(len(attempts), 3)
        self.assertEqual(sleeps[0], 1.5)
        self.assertEqual(len(sleeps), 2)
        self.assertTrue(attempts[0]['extra_body']['provider']['allow_fallbacks'])
        api_record = json.loads(logs[-1].removeprefix('[API] '))
        self.assertEqual(api_record['attempts'], 3)
        self.assertEqual(api_record['status'], 'returned')

    def test_provider_calls_does_not_retry_auth_or_bad_request_401_400(self):
        attempts = []
        sleeps = []

        def raw_create(**kwargs):
            attempts.append(kwargs)
            raise TransientAPIError(401, 'unauthorized')

        raw = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=raw_create)))
        active = select_profile({}, 'openrouter-deepseek', {'openrouter': 'key'})
        calls = ProviderCalls(active, lambda _: None, raw, max_retries=2, sleep=sleeps.append)
        with self.assertRaises(TransientAPIError):
            calls.chat.completions.create(model=active['DEFAULT_MODEL'], messages=[])
        self.assertEqual(len(attempts), 1)
        self.assertEqual(sleeps, [])

    def test_command_ledger_records_started_and_completed_or_interrupted(self):
        with tempfile.TemporaryDirectory() as folder:
            w = Workflow(Path(folder))
            w.execute('echo hello', lambda _: 'Exit code: 0\nhello')
            with self.assertRaises(RuntimeError):
                w.execute('failing_cmd', lambda _: (_ for _ in ()).throw(RuntimeError('boom')))
            ledger_file = w.state / 'command-ledger.jsonl'
            self.assertTrue(ledger_file.exists())
            entries = [json.loads(line) for line in ledger_file.read_text(encoding='utf-8').splitlines()]
            statuses = [(e['command'], e['status']) for e in entries]
            self.assertEqual(
                statuses,
                [
                    ('echo hello', 'started'),
                    ('echo hello', 'completed'),
                    ('failing_cmd', 'started'),
                    ('failing_cmd', 'interrupted'),
                ],
            )
            summary = w.command_ledger()
            self.assertEqual(len(summary), 2)
            self.assertEqual(summary[0]['status'], 'completed')
            self.assertEqual(summary[1]['status'], 'interrupted')

    def test_incremental_checkpoint_saves_completed_tool_turns_before_later_api_failure(self):
        round_count = 0

        def create(**kwargs):
            nonlocal round_count
            round_count += 1
            if round_count == 1:
                tool_msg = {
                    'role': 'assistant',
                    'tool_calls': [
                        {
                            'id': 'call-1',
                            'type': 'function',
                            'function': {'name': 'execute_shell_command', 'arguments': '{"shell_command":"whoami"}'},
                        }
                    ],
                }
                return SimpleNamespace(choices=[SimpleNamespace(finish_reason='tool_calls', message=Message(tool_msg))])
            raise TransientAPIError(503, 'upstream outage on round 2')

        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        history = [{'role': 'system', 'content': 'sys'}, {'role': 'user', 'content': 'check user'}]
        prepared = [dict(m) for m in history]
        checkpoints = []

        with self.assertRaises(TransientAPIError):
            list(
                complete(
                    client,
                    prepared,
                    'model',
                    [{}],
                    lambda cmd: 'Exit code: 0\nattacker',
                    history=history,
                    on_checkpoint=lambda h: checkpoints.append([dict(m) for m in h]),
                )
            )

        # Even though round 2 failed, round 1's assistant tool_call and tool result were checkpointed
        self.assertEqual(len(checkpoints), 1)
        saved = checkpoints[-1]
        self.assertEqual(saved[-2]['role'], 'assistant')
        self.assertEqual(saved[-2]['tool_calls'][0]['id'], 'call-1')
        self.assertEqual(saved[-1], {'role': 'tool', 'tool_call_id': 'call-1', 'content': 'Exit code: 0\nattacker'})


if __name__ == '__main__':
    unittest.main()
