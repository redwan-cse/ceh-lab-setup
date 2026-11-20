"""Cache limits must not separate tool results from their assistant call."""
import copy
from contextlib import ExitStack
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from terminal_ui import install_chat_cache_guard


def cache_class():
    class Cache:
        def __init__(self,length):self.length=length;self.data=[]
        def _read(self,chat_id):return self.data
        def _write(self,messages,chat_id):
            self.data=messages[:1]+messages[1+max(0,len(messages)-self.length):]
    return Cache


class ChatRetentionTests(unittest.TestCase):
    def messages(self):
        return [dict(role='system',content='role'),dict(role='user',content='first task'),
                dict(role='assistant',tool_calls=[dict(id='one',function=dict(name='inspection',arguments='{}'))],reasoning_details=[dict(type='reasoning.encrypted',data='fixture-signature')]),
                dict(role='tool',tool_call_id='one',content='real result'),dict(role='assistant',content='done'),
                dict(role='user',content='next task'),dict(role='assistant',content='reply')]

    def test_cache_limit_keeps_whole_turns_without_orphaned_tool_results(self):
        Cache=cache_class();install_chat_cache_guard(Cache)
        cache=Cache(5);messages=self.messages();before=copy.deepcopy(messages)
        cache._write(messages,'test')
        self.assertEqual(cache.data,[messages[0],*messages[5:]])
        self.assertEqual(cache._read('test'),cache.data)
        self.assertEqual(messages,before)

    def test_latest_long_turn_and_its_metadata_stay_complete(self):
        Cache=cache_class();install_chat_cache_guard(Cache);original=Cache._write
        install_chat_cache_guard(Cache);self.assertIs(Cache._write,original)
        cache=Cache(3);messages=self.messages()[:5]
        cache._write(messages,'test')
        self.assertEqual(cache.data,messages)
        self.assertEqual(cache.length,3)
        self.assertEqual(cache._read('test')[2]['reasoning_details'],messages[2]['reasoning_details'])

    def test_old_partial_prefix_is_not_sent_but_stored_history_is_untouched(self):
        Cache=cache_class();install_chat_cache_guard(Cache);cache=Cache(100)
        messages=self.messages();cache.data=[messages[0],*messages[3:]]
        stored=copy.deepcopy(cache.data)
        self.assertEqual(cache._read('test'),[messages[0],*messages[5:]])
        self.assertEqual(cache.data,stored)

    def test_active_chat_refuses_a_second_writer_and_unlocks_on_exit(self):
        import terminal_ui

        class Context(ExitStack):
            with_resource = ExitStack.enter_context

        class Handler:
            def __init__(self, chat_id):
                starts.append(chat_id)

        starts = []
        context = None
        terminal_ui.install_chat_writer_guard(Handler, lambda **_: context)
        with TemporaryDirectory() as folder:
            Handler.chat_session = SimpleNamespace(storage_path=Path(folder)/'chats'/'provider')
            Handler.chat_session.storage_path.mkdir(parents=True)
            with Context() as first:
                context = first
                Handler('docs')
                with Context() as second:
                    context = second
                    with self.assertRaisesRegex(terminal_ui.ChatAlreadyOpen, 'another terminal'):
                        Handler('docs')
                    Handler('logs')
                self.assertEqual(starts, ['docs', 'logs'])
            with Context() as reopened:
                context = reopened
                Handler('docs')
            self.assertEqual(starts, ['docs', 'logs', 'docs'])
            self.assertEqual(list(Handler.chat_session.storage_path.iterdir()), [])


if __name__=='__main__':unittest.main()
