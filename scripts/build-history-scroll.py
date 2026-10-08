"""Compose user-authorized overlapping generated images into a chronological strip.
No generation API is called. Requires Pillow and numpy; keeps generated originals.
"""
from pathlib import Path
import argparse, hashlib, json, shutil
import numpy as np
from PIL import Image, ImageFilter
ROOT=Path(__file__).resolve().parents[1]
PUB=ROOT/'apps/web/public/timeline-scroll'
W,H,OVERLAP,STEP=2160,720,360,1800

def join(left,right):
    """Choose a low-error path inside the overlap, discard duplicate pixels, feather 8px."""
    a=np.asarray(left.convert('RGB'),dtype=np.float32)
    b=np.asarray(right.convert('RGB'),dtype=np.float32)
    aa=np.asarray(left.filter(ImageFilter.GaussianBlur(2)),dtype=np.float32)
    bb=np.asarray(right.filter(ImageFilter.GaussianBlur(2)),dtype=np.float32)
    cost=np.mean((aa-bb)**2,axis=2)
    overlap=left.width
    edge=min(48,max(8,overlap//4))
    lo,hi=edge,overlap-edge
    cost=cost[:,lo:hi]
    trace=np.zeros_like(cost,dtype=np.int16)
    scores=cost[0].copy()
    for y in range(1,H):
        options=np.stack([np.r_[np.inf,scores[:-1]],scores,np.r_[scores[1:],np.inf]])
        pick=options.argmin(axis=0)
        trace[y]=pick-1
        scores=cost[y]+options[pick,np.arange(hi-lo)]
    path=np.empty(H,dtype=np.int16);path[-1]=scores.argmin()
    for y in range(H-1,0,-1):path[y-1]=path[y]+trace[y,path[y]]
    path=path+lo
    alpha=np.clip((np.arange(overlap)[None,:]-path[:,None]+4)/8,0,1)[...,None]
    mixed=np.clip(np.rint(a*(1-alpha)+b*alpha),0,255).astype(np.uint8)
    report={'method':'minimum-error overlap cut, 8px feather','mean_rgb_error':float(np.mean(np.abs(a-b))),
            'cut_min':int(path.min()),'cut_max':int(path.max()),'cut_mean':float(path.mean()),'cut_path':path.tolist()}
    return Image.fromarray(mixed),report

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',choices=['v5','v6'],default='v5')
    parser.add_argument('--late-ending',type=Path,help='Retain its final 1850–1912 strip only, matched without time stretching')
    parser.add_argument('--accept',nargs=2,metavar=('TILE','GENERATED_FILE'))
    args=parser.parse_args();version=args.version
    ART=ROOT/f'design/history-scroll-{version}'
    ART.mkdir(parents=True,exist_ok=True)
    if args.accept:
        number=int(args.accept[0]);assert 1<=number<=5
        src=Path(args.accept[1]);target=ART/f'generated-{number:02d}.png'
        shutil.copyfile(src,target)
        tile=Image.open(target).convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
        if number<5:
            template=Image.new('RGB',(W,H),(244,237,217))
            template.paste(tile.crop((STEP,0,W,H)),(0,0))
            template.save(ART/f'extend-{number+1:02d}.png')
        print(json.dumps({'accepted':number,'original':str(target.relative_to(ROOT))}))
        return
    if version=='v6' and not args.late_ending:
        parser.error('V6 composition requires --late-ending to retain the chronological ending')
    originals=[ART/f'generated-{i:02d}.png' for i in range(1,6)]
    tiles=[Image.open(p).convert('RGB').resize((W,H),Image.Resampling.LANCZOS) for p in originals]
    ending=None
    if args.late_ending:
        assert version=='v6'
        late=Image.open(args.late_ending).convert('RGB').resize((W,H),Image.Resampling.LANCZOS)
        # 1850 maps to global x=9109.213..., local x=1909.213... in tile five.
        start=int(np.ceil((1849+403)*9360/2314-4*STEP));overlap=64
        traditional=tiles[-1].copy()
        patch,report=join(traditional.crop((start,0,start+overlap,H)),late.crop((start,0,start+overlap,H)))
        tiles[-1].paste(patch,(start,0));tiles[-1].paste(late.crop((start+overlap,0,W,H)),(start+overlap,0))
        tiles[-1].crop((start-180,0,W,H)).save(ART/'late-ending-seam.png')
        assert np.array_equal(np.asarray(tiles[-1])[:,:start],np.asarray(traditional)[:,:start]), 'Ending changed pre-1850 pixels'
        ending={'from_year':1850,'local_start_px':start,'global_start_px':4*STEP+start,
                'file':str(args.late_ending.resolve().relative_to(ROOT)),
                'source_sha256':hashlib.sha256(args.late_ending.read_bytes()).hexdigest(),'join':report}
    canvas=Image.new('RGB',(W+4*STEP,H));canvas.paste(tiles[0],(0,0));seams=[]
    for i,tile in enumerate(tiles[1:],1):
        x=i*STEP
        patch,report=join(canvas.crop((x,0,x+OVERLAP,H)),tile.crop((0,0,OVERLAP,H)))
        canvas.paste(patch,(x,0));canvas.paste(tile.crop((OVERLAP,0,W,H)),(x+OVERLAP,0))
        report.update(tile=i+1,overlap_start_px=x,seam_year_ordinal=-403+(x+report['cut_mean'])/9360*2314)
        seams.append(report)
        canvas.crop((x-180,0,x+OVERLAP+180,H)).save(ART/f'seam-{i:02d}.png')
    PUB.mkdir(exist_ok=True)
    png=ART/f'history-scroll-{version}.png';webp=PUB/f'history-scroll-{version}.webp'
    canvas.save(png);canvas.save(webp,'WEBP',quality=95,method=6)
    preview=canvas.copy();preview.thumbnail((2340,720));preview.save(ART/'overview.png')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    audit={'from_year':-403,'to_year':1912,'elapsed_years':2314,'width':9360,'height':720,
           'pixels_per_elapsed_year':9360/2314,'overlap_px':OVERLAP,'step_px':STEP,
           'generator':'built-in imagegen','processing':'uniform 2172x724 to 2160x720 resize (0.55%), overlap cut and 8px feather; no global upscaling',
           'late_ending':ending,'seams':seams,'originals':[{'file':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in originals],
           'lossless_png_sha256':sha(png),'webp_sha256':sha(webp),'webp_bytes':webp.stat().st_size}
    (ART/'composition.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    data=json.loads((ROOT/'apps/web/src/data/history-scroll.json').read_text())
    data.update(artifact_version=version,provenance_directory=str(ART.relative_to(ROOT)),from_year=-403,to_year=1912,logical_canvas={'width':9360,'height':720},pixels_per_elapsed_year=9360/2314)
    data['panels']=[{'id':f'history-scroll-{version}','file':webp.name,'from_year':-403,'to_year':1912,'width':9360,'height':720,
                     'crop':{'x':0,'y':0,'width':9360,'height':720},'sha256':sha(webp),'bytes':webp.stat().st_size}]
    storyboard=ART/'storyboard.json'
    data['scene_notes']=json.loads(storyboard.read_text()).get('display_notes',[]) if storyboard.exists() else []
    data['artwork_note']=('AI生成的历史活动长卷；人物、动作与同框安排为艺术构图，不作为具体现场、人物容貌或政治疆域的复原。' if version=='v6' else 'AI生成的历史文化意象，按大体年代比例组织；不作疆域、建筑年代或具体场景的史实复原。')
    data['periods'][0].update(label='战国',from_year=-403)
    (ROOT/'apps/web/src/data/history-scroll.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:audit[k] for k in ['width','height','elapsed_years','pixels_per_elapsed_year','webp_bytes']}))
    for seam in seams:print({k:seam[k] for k in ['tile','mean_rgb_error','cut_mean']})

if __name__=='__main__':main()
