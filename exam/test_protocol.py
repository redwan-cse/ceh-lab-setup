import unittest
from types import SimpleNamespace
from exam_runtime import ProviderBlocked, complete, request_messages


class Message:
    def __init__(self, value): self.value = value
    def model_dump(self, **kwargs): return self.value.copy()


class ProtocolTests(unittest.TestCase):
    def test_machine_observations_are_data_not_system_instructions(self):
        messages=[{'role':'system','content':'Base role'},{'role':'user','content':'hello'}]
        original=[dict(m) for m in messages]
        result=request_messages(messages,'Keep authorization and approval rules.','Observed address: 10.0.0.2')
        self.assertIn('Keep authorization and approval rules.',result[0]['content'])
        self.assertNotIn('10.0.0.2',result[0]['content'])
        self.assertEqual(result[1]['role'],'user')
        self.assertIn('Observed address: 10.0.0.2',result[1]['content'])
        self.assertEqual(result[-1],original[-1])
        self.assertEqual(messages,original)

    def test_request_context_does_not_accumulate_in_chat_history(self):
        messages=[{'role':'system','content':'Base role\n\n<ceh_exam_workflow>\nlegacy observation\n</ceh_exam_workflow>'},
                  {'role':'user','content':'task'},{'role':'assistant','content':'answer'},{'role':'user','content':'next task'}]
        first=request_messages(messages,'Current rules','current observation')
        second=request_messages(messages,'Current rules','new observation')
        self.assertNotIn('legacy observation',str(first))
        self.assertNotIn('current observation',str(second))
        self.assertEqual(second[-3:],messages[-3:])
        self.assertEqual(sum(m['content'].count('Current rules') for m in second),1)

    def test_real_tool_history_survives_without_transient_context(self):
        history=[{'role':'system','content':'Base role'},{'role':'user','content':'pwd'}]
        prepared=request_messages(history,'Approval rules','Transient observation')
        assistant={'role':'assistant','tool_calls':[{'id':'one','type':'function',
            'function':{'name':'execute_shell_command','arguments':'{"shell_command":"pwd"}'},
            'extra_content':{'google':{'thought_signature':'test-signature'}}}]}
        values=iter([assistant,{'role':'assistant','content':'Done'}])
        def create(**kwargs):return SimpleNamespace(choices=[SimpleNamespace(message=Message(next(values)))])
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        list(complete(client,prepared,'gemini-4-carbon',[{}],lambda command:'actual output',history=history))
        self.assertEqual(history[-2],assistant)
        self.assertEqual(history[-1],{'role':'tool','tool_call_id':'one','content':'actual output'})
        self.assertNotIn('Transient observation',str(history))

    def test_metadata_and_multiple_tool_results_survive(self):
        assistant = {'role':'assistant','content':None,'tool_calls':[
            {'id':'one','type':'function','function':{'name':'execute_shell_command','arguments':'{"shell_command":"pwd"}'},'extra_content':{'google':{'thought_signature':'dummy-signature'}}},
            {'id':'two','type':'function','function':{'name':'execute_shell_command','arguments':'{"shell_command":"id"}'}}]}
        calls=[]
        def create(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=Message(assistant if len(calls)==1 else {'role':'assistant','content':'OK'}))])
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        messages=[]
        output=''.join(complete(client,messages,'gemini-4-carbon',[{}],lambda x:'result:'+x))
        self.assertTrue(output.endswith('OK'))
        self.assertIn('result:pwd',output)
        self.assertIn('result:id',output)
        self.assertEqual(messages[0],assistant)
        self.assertEqual([x['tool_call_id'] for x in messages[1:]],['one','two'])
        self.assertEqual(calls[0]['reasoning_effort'],'high')

    def test_unknown_tool_never_executes(self):
        value={'role':'assistant','tool_calls':[{'id':'x','function':{'name':'other','arguments':'{}'}}]}
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw:SimpleNamespace(choices=[SimpleNamespace(message=Message(value))]))))
        with self.assertRaises(RuntimeError):
            list(complete(client,[],'gemini-4-carbon',[{}],lambda x:self.fail('executed unknown tool')))

    def test_repeated_calls_have_a_limit(self):
        value={'role':'assistant','tool_calls':[{'id':'x','function':{'name':'execute_shell_command','arguments':'{"shell_command":"pwd"}'}}]}
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw:SimpleNamespace(choices=[SimpleNamespace(message=Message(value))]))))
        with self.assertRaises(RuntimeError):list(complete(client,[],'gemini-4-carbon',[{}],lambda x:'OK',limit=2))

    def test_provider_filter_without_message_stops_without_execution(self):
        calls=[]
        def create(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=None,finish_reason='content_filter: OTHER')])
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        with self.assertRaises(ProviderBlocked) as raised:list(complete(client,[],'gemini-4-carbon',[{}],lambda x:self.fail('executed after provider block')))
        self.assertIn('content_filter: OTHER',str(raised.exception))
        self.assertIn('unspecified',str(raised.exception))
        self.assertNotIn('Provider blocked this response',str(raised.exception))
        self.assertEqual(len(calls),1)

    def test_provider_finish_details_are_not_echoed(self):
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw:SimpleNamespace(choices=[SimpleNamespace(message=None,finish_reason='content_filter: private-provider-data')]))))
        with self.assertRaises(ProviderBlocked) as raised:list(complete(client,[],'gemini-4-carbon',[{}],lambda x:self.fail('executed after provider stop')))
        self.assertNotIn('private-provider-data',str(raised.exception))

if __name__=='__main__':unittest.main()
