"""Extract local PDF comparison caches; requires pypdf, no source mutation."""
import argparse
import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
for stem, first, last in [('14南史', 1, None), ('20宋史', 3092, 3810), ('24明史', 1, None)]:
    reader = PdfReader(ROOT / 'resources/originals/twenty-four-histories' / (stem + '.pdf'))
    with (args.output / (stem + '.jsonl')).open('w', encoding='utf-8') as out:
        for number in range(first, (last or len(reader.pages)) + 1):
            out.write(json.dumps({'pdf_page': number, 'text': reader.pages[number - 1].extract_text() or ''}, ensure_ascii=False) + '\n')
            if number % 500 == 0:
                print(stem, number, flush=True)
    print(stem, 'complete', flush=True)
