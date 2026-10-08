"""Compose user-authorized overlapping generated images into a chronological strip.
No generation API is called. Requires Pillow and numpy; keeps generated originals.
"""
from pathlib import Path
import hashlib, json
import numpy as np
from PIL import Image, ImageFilter
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'design/history-scroll-v5'
PUB=ROOT/'apps/web/public/timeline-scroll'
W,H,OVERLAP,STEP=2160,720,360,1800

def join(left,right):
    """Choose a low-error path inside the overlap, discard duplicate pixels, feather 8px."""
    a=np.asarray(left.convert('RGB'),dtype=np.float32)
    b=np.asarray(right.convert('RGB'),dtype=np.float32)
    aa=np.asarray(left.filter(ImageFilter.GaussianBlur(2)),dtype=np.float32)
    bb=np.asarray(right.filter(ImageFilter.GaussianBlur(2)),dtype=np.float32)
    cost=np.mean((aa-bb)**2,axis=2)
    lo,hi=48,OVERLAP-48
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
    alpha=np.clip((np.arange(OVERLAP)[None,:]-path[:,None]+4)/8,0,1)[...,None]
    mixed=np.clip(np.rint(a*(1-alpha)+b*alpha),0,255).astype(np.uint8)
    report={'method':'minimum-error overlap cut, 8px feather','mean_rgb_error':float(np.mean(np.abs(a-b))),
            'cut_min':int(path.min()),'cut_max':int(path.max()),'cut_mean':float(path.mean()),'cut_path':path.tolist()}
    return Image.fromarray(mixed),report

def main():
    originals=[ART/f'generated-{i:02d}.png' for i in range(1,6)]
    tiles=[Image.open(p).convert('RGB').resize((W,H),Image.Resampling.LANCZOS) for p in originals]
    canvas=Image.new('RGB',(W+4*STEP,H));canvas.paste(tiles[0],(0,0));seams=[]
    for i,tile in enumerate(tiles[1:],1):
        x=i*STEP
        patch,report=join(canvas.crop((x,0,x+OVERLAP,H)),tile.crop((0,0,OVERLAP,H)))
        canvas.paste(patch,(x,0));canvas.paste(tile.crop((OVERLAP,0,W,H)),(x+OVERLAP,0))
        report.update(tile=i+1,overlap_start_px=x,seam_year_ordinal=-403+(x+report['cut_mean'])/9360*2314)
        seams.append(report)
        canvas.crop((x-180,0,x+OVERLAP+180,H)).save(ART/f'seam-{i:02d}.png')
    PUB.mkdir(exist_ok=True)
    png=ART/'history-scroll-v5.png';webp=PUB/'history-scroll-v5.webp'
    canvas.save(png);canvas.save(webp,'WEBP',quality=95,method=6)
    preview=canvas.copy();preview.thumbnail((2340,720));preview.save(ART/'overview.png')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    audit={'from_year':-403,'to_year':1912,'elapsed_years':2314,'width':9360,'height':720,
           'pixels_per_elapsed_year':9360/2314,'overlap_px':OVERLAP,'step_px':STEP,
           'generator':'built-in imagegen','processing':'uniform 2172x724 to 2160x720 resize (0.55%), overlap cut and 8px feather; no global upscaling',
           'seams':seams,'originals':[{'file':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in originals],
           'lossless_png_sha256':sha(png),'webp_sha256':sha(webp),'webp_bytes':webp.stat().st_size}
    (ART/'composition.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    data=json.loads((ROOT/'apps/web/src/data/history-scroll.json').read_text())
    data.update(from_year=-403,to_year=1912,logical_canvas={'width':9360,'height':720},pixels_per_elapsed_year=9360/2314)
    data['panels']=[{'id':'history-scroll-v5','file':webp.name,'from_year':-403,'to_year':1912,'width':9360,'height':720,
                     'crop':{'x':0,'y':0,'width':9360,'height':720},'sha256':sha(webp),'bytes':webp.stat().st_size}]
    data['periods'][0].update(label='战国',from_year=-403)
    (ROOT/'apps/web/src/data/history-scroll.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:audit[k] for k in ['width','height','elapsed_years','pixels_per_elapsed_year','webp_bytes']}))
    for seam in seams:print({k:seam[k] for k in ['tile','mean_rgb_error','cut_mean']})

if __name__=='__main__':main()
