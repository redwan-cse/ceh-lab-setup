"""Cache limits must not separate tool results from their assistant call."""
import copy
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


if __name__=='__main__':unittest.main()
