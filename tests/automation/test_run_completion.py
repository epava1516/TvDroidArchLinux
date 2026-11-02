import importlib.util,json,multiprocessing,os,subprocess,tempfile,unittest,uuid
from pathlib import Path
spec=importlib.util.spec_from_file_location('completion',Path(__file__).resolve().parents[2]/'scripts/run_completion.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def attempt(manifest):
 def sender(message):
  with (Path(manifest).parent/'calls').open('a') as f:f.write(message+'\n')
  return subprocess.CompletedProcess([],0,'queued','')
 module.deliver(manifest,sender,enabled=True)
class Delivery(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.cp=Path(self.tmp.name);self.manifest=self.cp/'completion-manifest.json'
  self.manifest.write_text(json.dumps(dict(id=str(uuid.uuid4()),checkpoint=str(self.cp),unit='test',owner='test',thread='mock-thread',remote='mock',name='Markor launch')))
 def tearDown(self):self.tmp.cleanup()
 def handoff(self):
  m=json.loads(self.manifest.read_text());return module.transfer(self.manifest,'active:'+m['id'],'handoff')
 def test_success_concurrent_and_repeat(self):
  self.handoff()
  os.environ['SERVICE_RESULT']='success';(self.cp/'result.json').write_text('{"outer_exit":0}')
  ps=[multiprocessing.get_context('fork').Process(target=attempt,args=(self.manifest,)) for _ in range(8)]
  for p in ps:p.start()
  for p in ps:p.join();self.assertEqual(p.exitcode,0)
  attempt(self.manifest)
  self.assertEqual(len((self.cp/'calls').read_text().splitlines()),1)
  self.assertEqual(json.loads((self.cp/'completion-delivery.json').read_text())['continuation'],'not_observed')
 def test_failure(self):
  self.handoff()
  os.environ['SERVICE_RESULT']='exit-code'
  r=module.deliver(self.manifest,lambda m:subprocess.CompletedProcess([],0,'queued',''),enabled=True)
  self.assertIn('exit-code',r['message']);self.assertEqual(r['state'],'queued')
 def test_uncertain_not_retried(self):
  self.handoff()
  os.environ['SERVICE_RESULT']='success'
  def fail(m):raise TimeoutError('ambiguous')
  self.assertEqual(module.deliver(self.manifest,fail,enabled=True)['state'],'indeterminate')
  self.assertEqual(module.deliver(self.manifest,lambda m:self.fail('resent'))['state'],'indeterminate')
 def test_nonterminal_silent(self):
  os.environ.pop('SERVICE_RESULT',None)
  self.assertEqual(module.deliver(self.manifest,lambda m:self.fail('sent'))['state'],'not-terminal')
  self.assertFalse((self.cp/'completion-delivery.json').exists())
 def test_active_owner_persists_result_without_queue(self):
  os.environ['SERVICE_RESULT']='success'
  r=module.deliver(self.manifest,lambda m:self.fail('queued while active'),enabled=True)
  self.assertEqual(r['state'],'active_owned');self.assertTrue((self.cp/'completion-result.json').exists())
  owner='active:'+json.loads(self.manifest.read_text())['id']
  module.transfer(self.manifest,owner,'consume')
  for _ in range(3):self.assertEqual(module.deliver(self.manifest,lambda m:self.fail('already consumed'),enabled=True)['state'],'consumed')
  with self.assertRaises(AssertionError):module.transfer(self.manifest,owner,'handoff')
 def test_consume_before_callback(self):
  os.environ.pop('SERVICE_RESULT',None);(self.cp/'result.json').write_text('{"outer_exit":1}')
  owner='active:'+json.loads(self.manifest.read_text())['id']
  module.transfer(self.manifest,owner,'consume')
  self.assertEqual(module.deliver(self.manifest,lambda m:self.fail('late callback'),enabled=True)['state'],'consumed')
 def test_disabled_even_after_handoff(self):
  self.handoff();os.environ['SERVICE_RESULT']='success'
  self.assertEqual(module.deliver(self.manifest,lambda m:self.fail('disabled'),enabled=False)['state'],'notifications_disabled')
 def test_reclaim_unsent_handoff(self):
  self.handoff();owner='active:'+json.loads(self.manifest.read_text())['id']
  module.transfer(self.manifest,owner,'claim-active');os.environ['SERVICE_RESULT']='success'
  self.assertEqual(module.deliver(self.manifest,lambda m:self.fail('reclaimed'),enabled=True)['state'],'active_owned')
 def test_no_reclaim_after_uncertain_delivery(self):
  self.handoff();os.environ['SERVICE_RESULT']='success'
  module.deliver(self.manifest,lambda m:subprocess.CompletedProcess([],1,'','unknown'),enabled=True)
  owner='active:'+json.loads(self.manifest.read_text())['id']
  with self.assertRaises(RuntimeError):module.transfer(self.manifest,owner,'claim-active')
 def test_active_consume_races_callbacks(self):
  os.environ['SERVICE_RESULT']='success';(self.cp/'result.json').write_text('{"outer_exit":0}')
  owner='active:'+json.loads(self.manifest.read_text())['id']
  ps=[multiprocessing.get_context('fork').Process(target=attempt,args=(self.manifest,)) for _ in range(8)]
  ps.append(multiprocessing.get_context('fork').Process(target=module.transfer,args=(self.manifest,owner,'consume')))
  for p in ps:p.start()
  for p in ps:p.join();self.assertEqual(p.exitcode,0)
  self.assertFalse((self.cp/'calls').exists())
  self.assertEqual(json.loads((self.cp/'completion-consumer.json').read_text())['state'],'consumed')
if __name__=='__main__':unittest.main()
