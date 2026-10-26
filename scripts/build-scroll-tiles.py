#!/usr/bin/env python3
"""Build deterministic, hash-named display tiles from the reviewed scroll assets."""
import hashlib
import io
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / 'apps/web/public/timeline-scroll'
OUTPUT = PUBLIC / 'tiles'
OUTPUT.mkdir(exist_ok=True)
scroll = json.loads((ROOT / 'apps/web/src/data/history-scroll.json').read_text())

def save(image, stem, quality):
    buffer = io.BytesIO()
    image.save(buffer, 'WEBP', quality=quality, method=6)
    data = buffer.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    name = f'{stem}-{digest[:16]}.webp'
    (OUTPUT / name).write_bytes(data)
    return dict(file='tiles/' + name, bytes=len(data), sha256=digest, width=image.width, height=image.height)

panels = []
for panel in [scroll['ancient_panel'], *scroll['panels']]:
    source = PUBLIC / panel['file']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == panel['sha256'], panel['file']
    image = Image.open(source).convert('RGB')
    c = panel['crop']
    x0, y0, width, height = (c[k] for k in ('x', 'y', 'width', 'height'))
    assert 0 <= x0 < x0 + width <= image.width and 0 <= y0 < y0 + height <= image.height
    active = image.crop((x0, y0, x0 + width, y0 + height))
    ratio = min(72 / height, 936 / width)
    preview = save(active.resize((max(1, round(width * ratio)), max(1, round(height * ratio))), Image.Resampling.LANCZOS), panel['id'] + '-preview', 48)
    tiles = []
    for left in range(x0, x0 + width, 1560):
        right = min(left + 1560, x0 + width)
        start, end = max(x0, left - 2), min(x0 + width, right + 2)
        cut = image.crop((start, y0, end, y0 + height))
        high = save(cut, panel['id'] + f'-{left-x0:05}-high', 90)
        low = save(cut.resize(((cut.width + 1) // 2, (cut.height + 1) // 2), Image.Resampling.LANCZOS), panel['id'] + f'-{left-x0:05}-low', 82)
        tiles.append(dict(x=start, y=y0, width=end-start, height=height, content_x=left, content_width=right-left, low=low, high=high))
    panels.append(dict(id=panel['id'], source=panel['file'], source_sha256=panel['sha256'], crop=c, preview=preview, tiles=tiles))
manifest = dict(version=1, tile_width=1560, bleed=2, low_scale=0.5, panels=panels)
target = ROOT / 'apps/web/src/data/history-scroll-tiles.json'
target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'panels':len(panels),'tiles':sum(len(p['tiles']) for p in panels),'all_low_bytes':sum(t['low']['bytes'] for p in panels for t in p['tiles']),'all_high_bytes':sum(t['high']['bytes'] for p in panels for t in p['tiles']),'all_previews_bytes':sum(p['preview']['bytes'] for p in panels)},indent=2))
