import importlib.util,json,multiprocessing,os,subprocess,tempfile,unittest,uuid
from pathlib import Path
spec=importlib.util.spec_from_file_location('completion',Path(__file__).resolve().parents[2]/'scripts/run_completion.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def attempt(manifest):
 def sender(message):
  with (Path(manifest).parent/'calls').open('a') as f:f.write(message+'\n')
  return subprocess.CompletedProcess([],0,'queued','')
 module.deliver(manifest,sender)
class Delivery(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.cp=Path(self.tmp.name);self.manifest=self.cp/'completion-manifest.json'
  self.manifest.write_text(json.dumps(dict(id=str(uuid.uuid4()),checkpoint=str(self.cp),unit='test',owner='test',thread='mock-thread',remote='mock',name='Markor launch')))
 def tearDown(self):self.tmp.cleanup()
 def test_success_concurrent_and_repeat(self):
  os.environ['SERVICE_RESULT']='success';(self.cp/'result.json').write_text('{"outer_exit":0}')
  ps=[multiprocessing.get_context('fork').Process(target=attempt,args=(self.manifest,)) for _ in range(8)]
  for p in ps:p.start()
  for p in ps:p.join();self.assertEqual(p.exitcode,0)
  attempt(self.manifest)
  self.assertEqual(len((self.cp/'calls').read_text().splitlines()),1)
  self.assertEqual(json.loads((self.cp/'completion-delivery.json').read_text())['continuation'],'not_observed')
 def test_failure(self):
  os.environ['SERVICE_RESULT']='exit-code'
  r=module.deliver(self.manifest,lambda m:subprocess.CompletedProcess([],0,'queued',''))
  self.assertIn('exit-code',r['message']);self.assertEqual(r['state'],'queued')
 def test_uncertain_not_retried(self):
  os.environ['SERVICE_RESULT']='success'
  def fail(m):raise TimeoutError('ambiguous')
  self.assertEqual(module.deliver(self.manifest,fail)['state'],'indeterminate')
  self.assertEqual(module.deliver(self.manifest,lambda m:self.fail('resent'))['state'],'indeterminate')
 def test_nonterminal_silent(self):
  os.environ.pop('SERVICE_RESULT',None)
  self.assertEqual(module.deliver(self.manifest,lambda m:self.fail('sent'))['state'],'not-terminal')
  self.assertFalse((self.cp/'completion-delivery.json').exists())
if __name__=='__main__':unittest.main()
