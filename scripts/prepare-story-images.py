#!/usr/bin/env python3
"""Build deterministic web derivatives without changing approved original sheets.

Requires Pillow and cwebp. Sources are resolved by their catalog SHA256 below
--source-dir; output and manifest stay outside Git, catalog update is explicit.
"""
import argparse
import hashlib
import json
import pathlib
import subprocess
import tempfile
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=pathlib.Path, required=True)
    parser.add_argument('--source-dir', type=pathlib.Path, required=True)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    parser.add_argument('--update-catalog', action='store_true')
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text())
    sources = {}
    for file in args.source_dir.rglob('*.png'):
        sources[hashlib.sha256(file.read_bytes()).hexdigest()] = file
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = []
    with tempfile.TemporaryDirectory(prefix='histree-panels-') as temp:
        for story in catalog['stories']:
            source = sources[story['image']['sha256']]
            with Image.open(source) as sheet:
                assert sheet.size == (story['image']['width'], story['image']['height'])
                for panel in story['panels']:
                    crop = panel['crop']
                    box = (crop['x'], crop['y'], crop['x'] + crop['width'], crop['y'] + crop['height'])
                    part = sheet.crop(box).convert('RGB')
                    variants = [('panel', part, 86)]
                    if panel['number'] == 1:
                        cover = part.copy()
                        cover.thumbnail((360, 360), Image.Resampling.LANCZOS)
                        variants.append(('cover', cover, 80))
                    for kind, picture, quality in variants:
                        png = pathlib.Path(temp) / 'crop.png'
                        webp = pathlib.Path(temp) / 'encoded.webp'
                        picture.save(png)
                        subprocess.run(['cwebp', '-quiet', '-preset', 'picture', '-q', str(quality), '-m', '6', '-sharp_yuv', '-metadata', 'none', str(png), '-o', str(webp)], check=True)
                        content = webp.read_bytes()
                        sha = hashlib.sha256(content).hexdigest()
                        target = args.output / f'{sha}.webp'
                        target.write_bytes(content)
                        asset = dict(url=f'/api/v1/media/images/{sha}.webp', width=picture.width, height=picture.height, sha256=sha, bytes=len(content))
                        if kind == 'cover':
                            story['cover'] = asset
                        else:
                            panel['image'] = asset
                        manifest.append(dict(slug=story['slug'], panel=panel['number'], kind=kind, sourceSha256=story['image']['sha256'], crop=crop, quality=quality, file=str(target.resolve()), **asset))
    (args.output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    if args.update_catalog:
        args.catalog.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(assets=len(manifest), totalBytes=sum(row['bytes'] for row in manifest), panelMin=min(row['bytes'] for row in manifest if row['kind']=='panel'), panelMax=max(row['bytes'] for row in manifest if row['kind']=='panel'))))


if __name__ == '__main__':
    main()
