import unittest
from types import SimpleNamespace
from providers import PROFILES, select_profile, ProviderCalls, review_task


class ProfileTests(unittest.TestCase):
    def test_default_requests_do_not_force_reasoning_effort(self):
        active=select_profile({'REASONING_EFFORT':'max'},'openrouter-deepseek',{})
        self.assertNotIn('REASONING_EFFORT',active)
        sent=[]
        raw=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw:sent.append(kw) or SimpleNamespace(usage=None))))
        ProviderCalls(active,lambda text:None,raw).chat.completions.create(model=active['DEFAULT_MODEL'],messages=[])
        self.assertNotIn('reasoning_effort',sent[0])
        self.assertNotIn('reasoning',sent[0]['extra_body'])

    def test_provider_keys_never_cross_endpoints(self):
        active={'API_BASE_URL':PROFILES['gemini-mix']['base'],'OPENAI_API_KEY':'google-dummy'}
        step=select_profile(active,'stepfun',{'stepfun':'step-dummy','gemini':'google-dummy'})
        self.assertEqual(step['OPENAI_API_KEY'],'step-dummy')
        self.assertEqual(step['DEFAULT_MODEL'],'step-5-preview')
        self.assertEqual(select_profile(active,'stepfun',{})['OPENAI_API_KEY'],'')
        mix=select_profile(step,'gemini-mix',{'gemini':'google-dummy'})
        self.assertEqual(mix['DEFAULT_MODEL'],'gemini-3.8-flash')
        self.assertEqual(mix['REVIEW_MODEL'],'gemini-4-carbon')

    def test_openrouter_profile_requires_its_own_key(self):
        active=select_profile({},'stepfun',{'stepfun':'step-dummy'})
        router=select_profile(active,'openrouter-deepseek',{'openrouter':'router-dummy'})
        self.assertEqual(router['OPENAI_API_KEY'],'router-dummy')
        self.assertEqual(router['API_BASE_URL'],'https://openrouter.ai/api/v1')
        self.assertEqual(router['DEFAULT_MODEL'],'deepseek/deepseek-v4.1-flash-1017')
        self.assertEqual(select_profile(active,'openrouter-deepseek',{})['OPENAI_API_KEY'],'')

    def test_openrouter_adapts_reasoning_and_preserves_tool_history(self):
        sent=[]
        raw=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw:sent.append(kw) or SimpleNamespace(usage=None))))
        client=ProviderCalls(select_profile({},'openrouter-deepseek',{}),lambda text:None,raw)
        messages=[dict(role='assistant',content=None,reasoning_details=[{'type':'reasoning.encrypted','data':'fixture'}],tool_calls=[])]
        client.chat.completions.create(model='deepseek/deepseek-v4.1-flash-1017',messages=messages,reasoning_effort='high',max_completion_tokens=4096)
        self.assertEqual(sent[0]['max_tokens'],4096)
        self.assertNotIn('reasoning_effort',sent[0])
        self.assertEqual(sent[0]['extra_body']['reasoning']['effort'],'high')
        self.assertTrue(sent[0]['extra_body']['provider']['require_parameters'])
        self.assertEqual(sent[0]['messages'],messages)

    def test_saving_another_provider_key_keeps_active_profile(self):
        import io
        from unittest.mock import patch
        import setup_exam
        active=select_profile({},'stepfun',{'stepfun':'step-dummy'})
        with patch.object(setup_exam,'read',return_value=active),patch.object(setup_exam,'load_keys',return_value={}),patch.object(setup_exam,'remember_key') as remember,patch.object(setup_exam,'save') as save,patch('sys.argv',['setup_exam.py','--key-only','--provider','openrouter-deepseek','--key-stdin']),patch('sys.stdin',io.StringIO('router-dummy')):
            setup_exam.main()
            self.assertEqual(remember.call_args.args[0]['OPENAI_API_KEY'],'router-dummy')
            self.assertEqual(remember.call_args.args[0]['API_BASE_URL'],'https://openrouter.ai/api/v1')
            save.assert_not_called()

    def test_stepfun_uses_documented_output_limit_without_changing_effort(self):
        sent=[]
        raw=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw:sent.append(kw) or SimpleNamespace(usage=None))))
        client=ProviderCalls(select_profile({},'stepfun',{}),lambda text:None,raw)
        client.chat.completions.create(model='step-5-preview',messages=[],reasoning_effort='high',max_completion_tokens=4096)
        self.assertEqual(sent[0]['max_tokens'],4096)
        self.assertNotIn('max_completion_tokens',sent[0])
        self.assertEqual(sent[0]['reasoning_effort'],'high')

    def test_carbon_review_is_one_bounded_tool_less_request(self):
        sent=[]
        def create(**kw):
            sent.append(kw)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='Verified output.'))])
        calls=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        workflow=SimpleNamespace(recent_evidence=[{'command':'pwd','output':'x'*20000}])
        text=review_task(workflow,calls,'gemini-4-carbon','Check directory','Done')
        self.assertIn('Verified',text)
        self.assertEqual(len(sent),1)
        self.assertNotIn('tools',sent[0])
        self.assertLessEqual(len(sent[0]['messages'][1]['content']),7000)
        self.assertEqual(sent[0]['max_completion_tokens'],1536)

    def test_empty_reviewer_is_a_failure(self):
        client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kw:SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=None))]))))
        with self.assertRaises(RuntimeError):review_task(SimpleNamespace(recent_evidence=[]),client,'gemini-4-carbon','Task','Answer')

    def test_interpretation_comparison_requires_real_booleans(self):
        from compare_profiles import interpretation_passed
        self.assertTrue(interpretation_passed({'offline_proven':False,'scope_authorized':False}))
        self.assertFalse(interpretation_passed({'offline_proven':0,'scope_authorized':0}))
        self.assertFalse(interpretation_passed({'offline_proven':False}))

if __name__=='__main__':unittest.main()
