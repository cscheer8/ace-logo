"""Exercise real exported streams, including decoding VP9 alpha explicitly."""
import json, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageChops
import numpy as np
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'exports'
C=json.loads((ROOT/'src/timing.json').read_text()); results={}
for ext,codec in [('webm','vp9'),('mp4','h264')]:
    p=OUT/f'ace-hero-animation.{ext}'
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
    s=info['streams'][0]
    assert s['codec_name']==codec and s['width']==C['width'] and s['height']==C['height']
    assert int(s['nb_read_frames'])==round(C['duration']*C['fps'])
    assert abs(float(info['format']['duration'])-C['duration'])<.05
    subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],check=True)
    results[ext]={'codec':codec,'dimensions':[s['width'],s['height']],'duration':info['format']['duration'],'decoded_frames':s['nb_read_frames']}
with tempfile.TemporaryDirectory() as tmp:
    alpha=Path(tmp)/'alpha.png'
    subprocess.run(['ffmpeg','-v','error','-c:v','libvpx-vp9','-i',str(OUT/'ace-hero-animation.webm'),'-vf','alphaextract','-frames:v','1',str(alpha)],check=True)
    a=Image.open(alpha); lo,hi=a.getextrema(); assert lo==0 and hi==255
    results['webm']['decoded_alpha_range']=[lo,hi]
    tail=Path(tmp)/'tail.png'
    subprocess.run(['ffmpeg','-v','error','-c:v','libvpx-vp9','-sseof','-0.04','-i',str(OUT/'ace-hero-animation.webm'),'-frames:v','1',str(tail)],check=True)
    assert Image.open(tail).getchannel('A').getbbox() is not None
    reference=Image.open(OUT/'ace-hero-final-frame.png').convert('RGBA')
    def composite(im):
        return np.asarray(Image.alpha_composite(Image.new('RGBA',im.size,(10,12,16,255)),im.convert('RGBA')).convert('RGB')).astype(float)
    for ext in ['webm','mp4']:
        sample=tail
        if ext=='mp4':
            sample=Path(tmp)/'mp4-tail.png'
            subprocess.run(['ffmpeg','-v','error','-sseof','-0.04','-i',str(OUT/'ace-hero-animation.mp4'),'-frames:v','1',str(sample)],check=True)
        error=float(np.abs(composite(Image.open(sample))-composite(reference)).mean())
        assert error<5, 'Encoded final frame differs unexpectedly from still'
        results[ext]['final_frame_mean_rgb_error']=round(error,3)
frames=ROOT/'.build/frames'
last_path=frames/f'{round(C["duration"]*C["fps"])-1:04}.png'
last=Image.open(last_path).convert('RGBA')
assert ImageChops.difference(last,Image.open(OUT/'ace-hero-final-frame.png').convert('RGBA')).getbbox() is None
for i in range(round(C['settle_end']*C['fps'])+1,round(C['duration']*C['fps'])):
    assert (frames/f'{i:04}.png').read_bytes()==last_path.read_bytes(), 'Final hold must be stationary'
results['stationary_final_hold']=True
manifest=json.loads((OUT/'render-manifest.json').read_text())
results['artwork_status']=manifest['status']
if manifest['status']=='official-artwork-supplied':
    source=ROOT/manifest['source_logo']
    if source.exists():
        logo=Image.open(source).convert('RGBA'); h=C['logo_height']; w=round(h*logo.width/logo.height)
        expected=Image.new('RGBA',(C['width'],C['height'])); expected.alpha_composite(logo.resize((w,h),Image.Resampling.LANCZOS),((C['width']-w)//2,(C['height']-h)//2))
        assert expected.tobytes()==last.tobytes()
        results['final_artwork_pixels_match_resized_source']=True
(OUT/'validation.json').write_text(json.dumps(results,indent=2)+'\n'); print(json.dumps(results,indent=2))
