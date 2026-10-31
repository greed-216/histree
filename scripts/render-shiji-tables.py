"""Export one standalone reading edition of the ten tables, preserving source text."""
import argparse
from collections import defaultdict
import gzip
from html import escape
import json
from pathlib import Path
from build_shiji_layout_loader import load_layout_builder

ROOT=Path(__file__).resolve().parents[1]


def render(root, data):
    builder=load_layout_builder();rawpath=root/'resources/originals/twenty-four-histories/01史记-EPUB全文.txt'
    raw=rawpath.read_bytes();assert builder.sha(raw)==data['source_sha256'];text=raw.decode('utf-8')
    with gzip.open(root/'resources/derived/history-library/shiji/paragraphs.jsonl.gz','rt',encoding='utf-8') as stream:
        paragraphs=[json.loads(line) for line in stream]
    selected=[p for p in paragraphs if p.get('volume_candidate') in range(13,23)]
    original={p['id']:text[p['locator']['char_start']:p['locator']['char_end']] for p in selected}
    def table(parts):
        tid=data['paragraphs'][parts[0]['id']]['table_id'];meta=data['tables'][tid];rows=defaultdict(list)
        for p in parts:rows[data['paragraphs'][p['id']]['row_index']].append(p)
        output=['<div class="scroll" tabindex="0"><table style="min-width:'+str(meta['columns']*160 if meta['columns']>2 else 500)+'px"><caption>'+escape(meta['caption'])+'</caption>']
        for row_index,ps in rows.items():
            cells=meta['rows'][row_index];heading=all(c[3] for c in cells);output.append('<tr>');column=0
            for ci,(at,cs,rs,header) in enumerate(cells):
                while column<at:output.append('<td></td>');column+=1
                tag='th' if header else 'td';output.append('<'+tag+' colspan="'+str(cs)+'" rowspan="'+str(rs)+'">')
                for p in ps:
                    for cell,start,end in data['paragraphs'][p['id']]['fragments']:
                        if cell==ci:output.append('<span>'+escape(original[p['id']][start:end])+'</span>')
                output.append('</'+tag+'>');column=at+cs
            while column<meta['columns']:output.append('<td></td>');column+=1
            if heading:output.append('<th>逐段原文</th>')
            else:
                output.append('<td><details><summary>原文</summary>')
                for p in ps:
                    link='https://histree.wiki/library/shiji/'+p['section_id']+'?paragraph='+p['id']
                    output.append('<pre>'+escape(original[p['id']])+'</pre><a href="'+link+'">在史料库查看 →</a>')
                output.append('</details></td>')
            output.append('</tr>')
        output.append('</table></div>');return ''.join(output)
    chapters={c['volume']:c for c in data['chapters']};output=['<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>史记 · 十表排版阅读稿</title><style>body{max-width:1200px;margin:40px auto;padding:0 20px;background:#f8f7ef;color:#344334;font:18px/2 "Songti SC",serif}nav{display:flex;flex-wrap:wrap;gap:12px}a{color:#486a40}h1,h2{scroll-margin-top:30px}h2{border-bottom:1px solid #cbd4bf;padding-top:30px}p{white-space:pre-wrap}.scroll{max-width:100%;overflow:auto;border:1px solid #cbd4bf;margin:20px 0}table{border-collapse:collapse;table-layout:fixed;background:#fffdf8;width:100%;font-size:16px}td,th{border:1px solid #d5dccb;padding:12px;vertical-align:top;overflow-wrap:anywhere;white-space:pre-wrap}th,caption{background:#e7eddd}caption{text-align:left;padding:12px;font-weight:bold}td span,th span{display:block}pre{white-space:pre-wrap;font:14px/1.8 serif}summary{cursor:pointer;color:#486a40}.note{font:14px/1.9 sans-serif;color:#737b68}</style><h1>史记 · 十表</h1><p class="note">依选定 EPUB 底本恢复表格列位、空格与合并列，保留原字与异文。原始 TXT 及既有引用不改写。表中的公元纪年为底本附带的对照编排。</p><nav>']
    for v in range(13,23):output.append('<a href="#volume-'+str(v)+'">卷'+str(v)+' · '+escape(chapters[v]['title'])+'</a>')
    output.append('</nav>');block=[];current=None
    def flush():
        if block:output.append(table(block));block.clear()
    for p in selected:
        v=p['volume_candidate']
        if v!=current:
            flush();current=v;output.append('<h2 id="volume-'+str(v)+'">卷'+str(v)+' · '+escape(chapters[v]['title'])+'</h2>')
        meta=data['paragraphs'].get(p['id'])
        if meta:
            if block and data['paragraphs'][block[-1]['id']]['table_id']!=meta['table_id']:flush()
            block.append(p);continue
        flush()
        if p['kind']=='heading' and p['id']==chapters[v]['source_heading_id'] or 'editorial_navigation_heading' in p.get('flags',[]):continue
        tag='h3' if p['kind']=='heading' else 'p';output.append('<'+tag+'>'+escape(original[p['id']])+'</'+tag+'>')
    flush();output.append('</html>');return ''.join(output)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    builder=load_layout_builder();data=builder.build(ROOT);html=render(ROOT,data);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(html,encoding='utf-8');print(args.output)


if __name__=='__main__':main()
