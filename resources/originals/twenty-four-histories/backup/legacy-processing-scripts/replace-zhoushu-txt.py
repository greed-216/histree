"""Replace the Zhou Shu TXT with its checked supplemented reading copy.

Run only on explicit authorization to replace the original. Saves raw/decoded
backups and hash-bound aliases so older paragraph locators remain exportable.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'resources/derived/supplements/zhoushu-volume-04'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')


def main():
    manifest_file=BASE/'manifest.json'
    manifest=json.loads(manifest_file.read_text())
    target=ROOT/'resources/originals/twenty-four-histories/12周书.TXT'
    replacement_file=BASE/'replacement.json'
    if replacement_file.exists():
        replacement=json.loads(replacement_file.read_text())
        assert sha(target)==replacement['target_sha256']
        assert sha(ROOT/replacement['backup_file'])==replacement['backup_sha256']
        print('Already replaced; target and backup verified')
        return
    combined=ROOT/manifest['combined_file']
    decoded=ROOT/manifest['insert_before']['file']
    assert sha(target)==manifest['original_txt_sha256']
    assert sha(combined)==manifest['combined_sha256']
    assert sha(decoded)==manifest['insert_before']['sha256']
    assert target.read_bytes().decode('gb18030')==decoded.read_bytes().decode('utf-8')
    backup=target.parent/'archive/12周书.before-volume-04.TXT'
    frozen=BASE/'original-decoded.txt'
    backup.parent.mkdir(parents=True,exist_ok=True)
    for src,dst in [(target,backup),(decoded,frozen)]:
        if dst.exists(): assert sha(dst)==sha(src)
        else: dst.write_bytes(src.read_bytes())
    replacement={'format_version':'history-source-replacement-v1','authorization':'用户明确要求用补卷全文替换原TXT',
                 'target_file':str(target.relative_to(ROOT)),'target_sha256':sha(combined),'encoding':'utf-8',
                 'backup_file':str(backup.relative_to(ROOT)),'backup_sha256':sha(backup),
                 'decoded_backup_file':str(frozen.relative_to(ROOT)),'decoded_backup_sha256':sha(frozen),
                 'replacement_source':manifest['combined_file'],'status':'replaced_verified'}
    # Freeze provenance references before the canonical decoded file is rebuilt.
    joined_file=ROOT/manifest['combined_map_file']
    joined=json.loads(joined_file.read_text())
    for item in joined:
        if item.get('source_file')==str(decoded.relative_to(ROOT)):
            item['source_file']=str(frozen.relative_to(ROOT))
    save(joined_file,joined)
    manifest['combined_map_sha256']=sha(joined_file)
    manifest['insert_before']['file']=str(frozen.relative_to(ROOT))
    manifest['original_txt_file']=str(backup.relative_to(ROOT))
    manifest.update(canonical_txt_file=replacement['target_file'],canonical_txt_sha256=replacement['target_sha256'])
    save(manifest_file,manifest)
    aliases_file=ROOT/'resources/catalog/source-replacements.json'
    aliases=json.loads(aliases_file.read_text()) if aliases_file.exists() else {'format_version':1,'aliases':[]}
    aliases['aliases'].extend([
        {'file':str(target.relative_to(ROOT)),'sha256':sha(target),'backup_file':str(backup.relative_to(ROOT))},
        {'file':str(decoded.relative_to(ROOT)),'sha256':sha(decoded),'backup_file':str(frozen.relative_to(ROOT))}])
    save(aliases_file,aliases)
    target.write_bytes(combined.read_bytes())
    assert sha(target)==replacement['target_sha256']
    save(replacement_file,replacement)
    print(json.dumps(replacement,ensure_ascii=False))


if __name__=='__main__':main()
