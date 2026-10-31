"""Real Node/Python publication-target boundary, without database or env-file access."""
import hashlib,json,subprocess,unittest
from pathlib import Path


class Target(unittest.TestCase):
    def invoke(self, values):
        module=Path(__file__).with_name('mysql-publication-target.mjs').resolve().as_uri()
        code="import fs from 'node:fs'; const m=await import(process.argv[1]); console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8')).map(m.mysqlPublicationTargetFingerprint)));"
        return subprocess.run(['node','--input-type=module','-e',code,module],input=json.dumps(values).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    def test_actual_node_matches_python_contract_including_default_port_and_unicode(self):
        values=[dict(MYSQL_HOST='127.0.0.1',MYSQL_DATABASE='histree_test_target'),dict(MYSQL_HOST='127.0.0.1',MYSQL_DATABASE='histree_test_target',MYSQL_PORT='3307'),dict(MYSQL_HOST='例.example',MYSQL_DATABASE='历史😀',MYSQL_PORT='03306')]
        result=self.invoke(values);self.assertEqual(result.returncode,0,result.stderr.decode())
        expected=[hashlib.sha256(json.dumps([v['MYSQL_HOST'],int(v.get('MYSQL_PORT','3306')),v['MYSQL_DATABASE']],separators=(',',':')).encode()).hexdigest() for v in values]
        self.assertEqual(json.loads(result.stdout),expected)
    def test_port_changes_target_and_account_guard_remains_separate(self):
        env=dict(MYSQL_HOST='localhost',MYSQL_DATABASE='histree_test_target',MYSQL_PORT='3306',MYSQL_USER='first')
        result=self.invoke([env,dict(env,MYSQL_USER='second'),dict(env,MYSQL_PORT='3307')]);self.assertEqual(result.returncode,0,result.stderr.decode());a,b,c=json.loads(result.stdout);self.assertEqual(a,b);self.assertNotEqual(a,c)
    def test_invalid_port_fails_instead_of_hashing_a_null_or_other_target(self):
        for port in ('',0,'bad','3306.5',65536):
            self.assertNotEqual(self.invoke([dict(MYSQL_HOST='localhost',MYSQL_DATABASE='histree_test_target',MYSQL_PORT=port)]).returncode,0)


if __name__=='__main__':unittest.main()
