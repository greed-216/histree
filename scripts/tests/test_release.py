"""Exercise release rollback and pointer updates with isolated command doubles."""
import os,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class ReleaseTests(unittest.TestCase):
 def run_release(self,scenario):
  with tempfile.TemporaryDirectory(prefix='histree-release-') as temporary:
   d=Path(temporary);host=d/'host';new=host/'releases/new';old=host/'releases/old';new.mkdir(parents=True);old.mkdir()
   (host/'runtime.env').write_text('MYSQL_PASSWORD=fixture-private\n');(host/'current-release').write_text(str(old)+'\n')
   (old/'.image').write_text('histree-api:old\n');(old/'compose.yml').write_text('fixture')
   for name in ['image.tar.gz','image.tar.gz.sha256','compose.yml','release-manifest.json','verify.mjs']:(new/name).write_text('fixture')
   script=(ROOT/'deploy/ecs/release.sh').read_text().replace('/opt/histree',str(host));(new/'release.sh').write_text(script)
   (new/'cleanup-releases.py').write_text("import os,sys\nfrom pathlib import Path\nhost=Path(__file__).resolve().parents[2]\nassert (host/'current-release').read_text().strip()==str(Path(__file__).parent)\nwith open(os.environ['TEST_LOG'],'a') as f: f.write('retention-after-pointer\\n')\nsys.exit(1 if os.environ['SCENARIO']=='cleanup-failure' else 0)\n")
   binaries=d/'bin';binaries.mkdir();log=d/'commands';revision='a'*40
   commands={
    'flock':'exit 0',
    'nginx':'exit 0',
    'timeout':'shift; exec "$@"',
    'sha256sum':'if [[ "$1" == -c ]]; then exit 0; fi; echo "fixedhash  $1"',
    'docker':'''printf '%s|%s\\n' "$HISTREE_IMAGE" "$*" >> "$TEST_LOG"
if [[ "$1" == image && "$2" == inspect ]]; then
 if [[ "$4" == *Architecture* ]]; then echo amd64; else echo "$TEST_REVISION"; fi
fi
if [[ "$1" == compose && "$HISTREE_IMAGE" == "histree-api:$TEST_REVISION" && "$SCENARIO" == startup-failure ]]; then exit 1; fi
if [[ "$1" == exec && "$SCENARIO" == verify-failure ]]; then exit 1; fi
exit 0'''}
   for name,body in commands.items():
    p=binaries/name;p.write_text('#!/usr/bin/env bash\n'+body+'\n');p.chmod(0o755)
   env={**os.environ,'PATH':str(binaries)+os.pathsep+os.environ['PATH'],'TEST_LOG':str(log),'TEST_REVISION':revision,'SCENARIO':scenario}
   result=subprocess.run(['bash',str(new/'release.sh'),str(new),'histree-api:'+revision],env=env,text=True,capture_output=True)
   return result.returncode,(host/'current-release').read_text().strip(),str(old),str(new),log.read_text(),(host/'runtime.env').read_text()
 def test_success_updates_pointer_after_verification(self):
  status,pointer,old,new,log,secret=self.run_release('success');self.assertEqual(status,0);self.assertEqual(pointer,new);self.assertIn('exec -i',log);self.assertEqual(secret,'MYSQL_PASSWORD=fixture-private\n');self.assertIn('retention-after-pointer',log)
 def test_startup_failure_restores_previous_container_and_pointer(self):
  status,pointer,old,new,log,_=self.run_release('startup-failure');self.assertNotEqual(status,0);self.assertEqual(pointer,old);self.assertIn('histree-api:old|compose',log);self.assertNotIn('retention-after-pointer',log)
 def test_post_start_verification_failure_also_rolls_back(self):
  status,pointer,old,new,log,_=self.run_release('verify-failure');self.assertNotEqual(status,0);self.assertEqual(pointer,old);self.assertIn('exec -i',log);self.assertIn('histree-api:old|compose',log);self.assertNotIn('retention-after-pointer',log)
 def test_cleanup_failure_keeps_accepted_release_running(self):
  status,pointer,old,new,log,_=self.run_release('cleanup-failure');self.assertNotEqual(status,0);self.assertEqual(pointer,new);self.assertIn('retention-after-pointer',log);self.assertNotIn('histree-api:old|compose',log)
if __name__=='__main__':unittest.main()
