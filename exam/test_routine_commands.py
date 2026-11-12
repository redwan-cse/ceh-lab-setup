"""Routine workflows run as literal argv; scripts/installs/deletes need approval."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import Mock
import shutil
import os
import importlib.util
import functools
import http.server
import threading
from routine_commands import classify_linux,run_linux


class RoutineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        self.resolve=lambda name:'/usr/bin/'+name if name in {'curl','grep','sort','wc','cat','head','echo','printf','uniq','pwd','ls'} else None

    def classify(self,command):return classify_linux(command,self.folder,self.resolve,cwd=self.folder)

    def test_user_download_and_email_search_examples(self):
        download=self.classify('cd $CEH_EXAM_DIR && curl -sS --max-time 60 -A "Mozilla/5.0 (X11; Linux x86_64)" https://example.com/bundle.js -o bundle.js; echo "exit=$?"; wc -c bundle.js')
        self.assertIsNotNone(download)
        search=self.classify("cd $CEH_EXAM_DIR && grep -oEi '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}' bundle.js | sort -u")
        self.assertIsNotNone(search)

    def test_entire_chain_validated_before_any_execution(self):
        for command in ('cat input; rm input','curl https://example.com -o page; pip install x','cat input | bash','echo $(touch x)','cat input &','sort --compress-program=evil input','uniq input output','curl -K config https://example.com','curl -T secret https://example.com','curl file:///etc/passwd','curl https://example.com --libcurl code.c'):
            with self.subTest(command=command):self.assertIsNone(self.classify(command))

    def test_outputs_stay_inside_exam_and_preserve_existing_evidence(self):
        self.assertIsNotNone(self.classify('cat input > report.txt'))
        for command in ('cat input > ../outside','curl https://example.com -o ../outside','cat input > terminal.md'):
            self.assertIsNone(self.classify(command))
        self.assertIsNone(self.classify('curl https://example.com -o report.txt; curl https://example.com -o report.txt'))
        (self.folder/'report.txt').write_text('existing')
        self.assertIsNone(self.classify('cat input > report.txt'))
        self.assertIsNotNone(self.classify('cat input >> report.txt'))

    def test_symlink_output_is_not_followed(self):
        target=self.folder/'target.txt';target.write_text('preserve')
        link=self.folder/'link.txt'
        try:link.symlink_to(target)
        except OSError:self.skipTest('Symlink privileges unavailable')
        self.assertIsNone(self.classify('cat input >> link.txt'))
        self.assertEqual(target.read_text(),'preserve')

    def test_output_created_after_planning_is_preserved_without_crash(self):
        plan=self.classify('cat input > report.txt')
        (self.folder/'report.txt').write_text('new evidence')
        runner=Mock(side_effect=AssertionError('Should not overwrite'))
        self.assertIn('Exit code: 1',run_linux(plan,runner))
        self.assertEqual((self.folder/'report.txt').read_text(),'new evidence')

    def test_run_preserves_literal_regex_and_conditional_failures(self):
        plan=self.classify("grep -oEi 'a[0-9]{2,}$(x)' input | sort -u")
        self.assertIsNone(plan)  # command-substitution syntax stays an approval case
        plan=self.classify("grep -oEi 'a[0-9]{2,}$' input | sort -u")
        runner=Mock(return_value='Exit code: 0, Output:\nmatch')
        self.assertIn('match',run_linux(plan,runner))
        self.assertEqual(runner.call_args.args[0][0][2],'a[0-9]{2,}$')
        runner=Mock(side_effect=['Exit code: 1, Output:\nfailed','Exit code: 0, Output:\nalways'])
        run_linux(self.classify('grep x input && wc -c input; echo always'),runner)
        self.assertEqual(runner.call_count,2)

    def test_actual_download_search_and_scoped_redirection(self):
        binaries={}
        for name in ('curl','echo','wc','grep','sort','cat'):
            candidates=[Path('C:/Program Files/Git/usr/bin')/(name+'.exe'),Path('C:/Program Files/Git/mingw64/bin')/(name+'.exe')]
            binary=next((str(p) for p in candidates if p.is_file()),None) if os.name=='nt' else shutil.which(name)
            if not binary:self.skipTest('Required native tool unavailable: '+name)
            binaries[name]=binary
        source=Path(__file__).parent.parent/'universal/linux/linux_command_guard.py'
        spec=importlib.util.spec_from_file_location('fixture_linux_guard',source);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
        class Handler(http.server.SimpleHTTPRequestHandler):
            def log_message(self,*args):pass
        with tempfile.TemporaryDirectory() as directory:
            Path(directory,'bundle.js').write_text("const contact='training@example.test';\n")
            server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=directory))
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                from unittest.mock import patch
                with patch.dict(os.environ,{'NO_PROXY':'127.0.0.1','no_proxy':'127.0.0.1'}):
                    command='cd $CEH_EXAM_DIR && curl -sS --max-time 10 -A "Mozilla/5.0 (X11; Linux x86_64)" http://127.0.0.1:'+str(server.server_port)+'/bundle.js -o bundle.js; echo "exit=$?"; wc -c bundle.js'
                    result=run_linux(classify_linux(command,self.folder,binaries.get),guard.run_pipeline)
                    self.assertIn('exit=0',result)
                    self.assertIn('training@example.test',(self.folder/'bundle.js').read_text())
                    command="cd $CEH_EXAM_DIR && grep -oEi '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}' bundle.js | sort -u > contacts.txt"
                    plan=classify_linux(command,self.folder,binaries.get)
                    result=run_linux(plan,guard.run_pipeline)
                    self.assertIn('Exit code: 0',result)
                    self.assertEqual((self.folder/'contacts.txt').read_text().strip(),'training@example.test')
            finally:server.shutdown();server.server_close();thread.join(timeout=2)


if __name__=='__main__':unittest.main()
