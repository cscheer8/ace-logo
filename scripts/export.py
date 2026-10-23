"""Deterministic RGBA compositor and verified-codec export; no website dependencies."""
import argparse, json, math, subprocess, sys, hashlib, os
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
C=json.loads((ROOT/'src/timing.json').read_text())
def progress(t,a,b): return max(0.,min(1.,(t-a)/(b-a)))
def smooth(x): return x*x*(3-2*x)
def opacity(im,a):
    im=im.copy(); im.putalpha(im.getchannel('A').point(lambda v:round(v*a))); return im

def logo_layer(logo,t):
    p=smooth(progress(t,C['handoff_start'],C['rotation_end']))
    angle=math.radians(-88*(1-p))
    s=progress(t,C['rotation_end'],C['settle_end'])
    scale=.965+.035*smooth(s)
    h=C['logo_height']*scale; w=h*logo.width/logo.height
    # Project a textured rectangular plane with perspective; keep final art unmodified.
    local=[(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]
    dest=[]
    for x,y in local:
        z=-x*math.sin(angle); f=1700/(1700+z)
        dest.append((C['width']/2+x*math.cos(angle)*f,C['height']/2+y*f))
    source=[(0,0),(logo.width,0),(logo.width,logo.height),(0,logo.height)]
    A=[]; b=[]
    for (x,y),(u,v) in zip(dest,source):
        A.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]]); b.extend([u,v])
    coefficients=np.linalg.solve(np.array(A),np.array(b))
    if t>=C['settle_end']:
        # Identical pixel-exact stationary state for every remaining frame.
        size=(round(C['logo_height']*logo.width/logo.height),C['logo_height'])
        still=logo.resize(size,Image.Resampling.LANCZOS)
        out=Image.new('RGBA',(C['width'],C['height'])); out.alpha_composite(still,((C['width']-size[0])//2,(C['height']-size[1])//2)); return out
    return logo.transform((C['width'],C['height']),Image.Transform.PERSPECTIVE,coefficients,Image.Resampling.BICUBIC)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--logo',type=Path); parser.add_argument('--reuse-machine',action='store_true'); args=parser.parse_args()
    from placeholder import create
    create()
    logo_path=args.logo.resolve() if args.logo else ROOT/'assets/logo-placeholder.png'
    logo=Image.open(logo_path).convert('RGBA')
    if logo.width/ logo.height > .86: raise SystemExit('Expected the supplied portrait icon. Use uncropped official artwork; adjust scene framing explicitly for another aspect ratio.')
    if not args.reuse_machine:
        with (ROOT/'.build/blender.log').open('w') as log:
            subprocess.run(['blender','-b','-t','4','--python',str(ROOT/'scripts/render_machine.py')],check=True,stdout=log,stderr=subprocess.STDOUT,env={**os.environ,'XDG_CACHE_HOME':str(ROOT/'.build/cache')})
    frames=ROOT/'.build/frames'; frames.mkdir(parents=True,exist_ok=True)
    n=round(C['fps']*C['duration'])
    for i in range(n):
        t=i/C['fps']; frame=Image.new('RGBA',(C['width'],C['height']))
        blend=smooth(progress(t,C['handoff_start'],C['handoff_end']))
        if blend<1:
            machine=Image.open(ROOT/'.build/machine'/f'{i:04}.png').convert('RGBA'); frame.alpha_composite(opacity(machine,1-blend))
        if blend>0: frame.alpha_composite(opacity(logo_layer(logo,t),blend))
        frame.save(frames/f'{i:04}.png')
    out=ROOT/'exports'; out.mkdir(exist_ok=True)
    frame.save(out/'ace-hero-final-frame.png')
    common=['ffmpeg','-hide_banner','-loglevel','warning','-y','-framerate',str(C['fps']),'-i',str(frames/'%04d.png'),'-frames:v',str(n),'-an']
    subprocess.run(common+['-c:v','libvpx-vp9','-pix_fmt','yuva420p','-b:v','0','-crf','24','-auto-alt-ref','0','-metadata','title=ACE standalone brand animation'+(' — DEVELOPMENT PLACEHOLDER' if not args.logo else ''),str(out/'ace-hero-animation.webm')],check=True)
    # H.264 does not support alpha: explicitly composite over near black.
    subprocess.run(common+['-vf','split[fg][bg];[bg]lutrgb=r=10:g=12:b=16,format=rgb24[back];[back][fg]overlay=shortest=1,format=yuv420p','-c:v','libx264','-crf','18','-preset','medium','-movflags','+faststart',str(out/'ace-hero-animation.mp4')],check=True)
    report={'status':'official-artwork-supplied' if args.logo else 'DEVELOPMENT PLACEHOLDER — official artwork file required','source_logo':str(logo_path.relative_to(ROOT)) if logo_path.is_relative_to(ROOT) else logo_path.name,'source_sha256':hashlib.sha256(logo_path.read_bytes()).hexdigest(),'settings':C,'frame_count':n,'mp4_background':'#0a0c10','audio':False,'loop':False}
    (out/'render-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    # Contact sheet preserves actual output frames on a visible neutral backing.
    ids=[round(t*C['fps']) for t in [0,1.2,2.4,2.8,3.6]]+[n-1]; sheet=Image.new('RGB',(6*256,375),'#171a20'); d=ImageDraw.Draw(sheet)
    for j,i in enumerate(ids):
        im=Image.open(frames/f'{i:04}.png'); im.thumbnail((250,334)); x=j*256+(256-im.width)//2
        sheet.paste(im,(x,4),im); d.text((j*256+12,346),f'{i/C["fps"]:.2f}s',fill='white')
    sheet.save(out/'contact-sheet.jpg',quality=93)
    print(json.dumps(report,indent=2))
if __name__=='__main__':
    (ROOT/'.build').mkdir(exist_ok=True); main()
