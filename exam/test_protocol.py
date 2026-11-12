import unittest
from types import SimpleNamespace
from exam_runtime import ProviderBlocked, ProviderIncomplete, complete, request_messages, profile_chat_paths


class Message:
    def __init__(self, value): self.value = value
    def model_dump(self, **kwargs): return self.value.copy()


class ProtocolTests(unittest.TestCase):
    def test_refused_script_stops_batch_and_provider_calls(self):
        from terminal_ui import ApprovalRefusal,ApprovalDeclined
        value={'role':'assistant','tool_calls':[
            {'id':'one','function':{'name':'run_lab_script','arguments':'{"script":"scripts_test_1.py"}'}},
            {'id':'two','function':{'name':'execute_shell_command','arguments':'{"shell_command":"pwd"}'}}]}
        requests=[]
        def create(**kwargs):
            requests.append(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=Message(value))])
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        messages=[]
        with self.assertRaises(ApprovalDeclined):
            list(complete(client,messages,'model',[{}],lambda command:self.fail('ran after refusal'),actions={'run_lab_script':lambda script:ApprovalRefusal('Execution declined')}))
        self.assertEqual(len(requests),1)
        self.assertEqual([m['tool_call_id'] for m in messages if m['role']=='tool'],['one','two'])

    def test_bare_sgpt_opens_chat_but_piped_input_stays_one_shot(self):
        from exam_runtime import conversation_arguments
        self.assertEqual(conversation_arguments([],True),['--repl','lab'])
        self.assertEqual(conversation_arguments([],False),[])
        self.assertEqual(conversation_arguments(['hello'],True),['hello'])

    def test_malformed_tool_batch_executes_nothing(self):
        value={'role':'assistant','tool_calls':[
            {'id':'ok','function':{'name':'execute_shell_command','arguments':'{"shell_command":"pwd"}'}},
            {'id':'bad','function':{'name':'execute_shell_command','arguments':'{"shell_command":"id"} trailing'}}]}
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw:SimpleNamespace(choices=[SimpleNamespace(message=Message(value))]))))
        with self.assertRaisesRegex(ProviderIncomplete,'Malformed tool arguments'):
            list(complete(client,[],'model',[{}],lambda cmd:self.fail('Part of invalid batch executed')))

    def test_profiles_never_share_saved_chat_paths(self):
        from pathlib import Path
        step=profile_chat_paths(Path('/config'),'stepfun')
        router=profile_chat_paths(Path('/config'),'openrouter-deepseek')
        self.assertNotEqual(step['CHAT_CACHE_PATH'],router['CHAT_CACHE_PATH'])
        self.assertTrue(step['CHAT_CACHE_PATH'].endswith('stepfun'))

    def test_output_limit_never_executes_an_incomplete_tool_call(self):
        value={'role':'assistant','tool_calls':[{'id':'x','function':{'name':'execute_shell_command','arguments':'{"shell_command":"pwd"}'}}]}
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw:SimpleNamespace(choices=[SimpleNamespace(message=Message(value),finish_reason='length')]))))
        with self.assertRaises(RuntimeError):list(complete(client,[],'model',[{}],lambda x:self.fail('executed truncated response')))

    def test_empty_assistant_is_not_success(self):
        value={'role':'assistant','content':None}
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw:SimpleNamespace(choices=[SimpleNamespace(message=Message(value),finish_reason='stop')]))))
        with self.assertRaises(RuntimeError):list(complete(client,[],'model',[{}],lambda x:self.fail('executed empty response')))
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

    def test_results_destination_is_always_in_system_rules_not_chat_history(self):
        import json
        from pathlib import Path
        folder=Path('exam evidence')/'10.10.10.22'
        messages=[{'role':'system','content':'Base role'},{'role':'user','content':'List tools'}]
        original=[dict(message) for message in messages]
        first=request_messages(messages,'Save final results in the exam folder.','',results_folder=folder)
        second=request_messages(first,'Save final results in the exam folder.','New facts',results_folder=folder)
        for request in (first,second):
            system=request[0]['content']
            self.assertIn(json.dumps(str(folder)),system)
            self.assertIn(json.dumps(str(folder/'terminal.md')),system)
            self.assertIn(json.dumps(str(folder/'findings.txt')),system)
            self.assertEqual(system.count('exam_results_folder'),1)
        self.assertEqual(messages,original)

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
        self.assertNotIn('reasoning_effort',calls[0])

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

class StdioTests(unittest.TestCase):
    def test_unicode_response_can_be_printed_over_legacy_encoded_ssh_stream(self):
        import io
        from unittest.mock import patch
        from exam_runtime import configure_stdio
        buffer=io.BytesIO()
        stream=io.TextIOWrapper(buffer,encoding='ascii',write_through=True,newline='\n')
        with patch('sys.stdout',stream),patch('sys.stderr',stream):
            configure_stdio()
            print('Review: \u2713 \u03bb')
        self.assertEqual(buffer.getvalue(),'Review: \u2713 \u03bb\n'.encode('utf-8'))


if __name__=='__main__':unittest.main()
