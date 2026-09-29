"""Prepare review SQL while protecting reused people in publish/rollback lists."""
import json,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(P.parents[1]/'scripts/prepare-content-import.py'),str(P/'content-batch.json'),str(P/'sql')],check=True)
ids=json.loads((P/'sql/key-map.json').read_text())
for name in ['publish.sql','unpublish.sql']:
 p=P/'sql'/name;s=p.read_text()
 for key in ['person_zhu_wen','person_朱全昱','relationship_person_朱全昱_person_zhu_wen_兄长']:
  s=s.replace("'"+ids[key]+"',",'').replace(",'"+ids[key]+"'",'')
 p.write_text(s)
# Only the guarded publication script patches Zhu Wen. Import SQL intentionally does not.
(P/'sql/README.md').write_text('SQL 仅插入草稿及切换本批新增实体状态，不更新复用人物。朱温传记更新由 ../publish.py 基于旧值条件完成；回退时按 publication.json 的 zhu_before 人工复核，不能覆盖后续编辑。\n')
