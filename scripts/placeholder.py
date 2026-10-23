"""Development slate only. Never substitutes for official ACE artwork."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT = Path(__file__).resolve().parents[1]
def create():
    im = Image.new('RGBA', (600, 960))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 580, 940), 64, fill='#101216', outline='#b5bcc5', width=8)
    d.rounded_rectangle((39, 39, 561, 921), 49, outline='#ed172a', width=3)
    font = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    for text,y,size,color in [('OFFICIAL',350,47,'#e7ebf0'),('ARTWORK',414,47,'#e7ebf0'),('REQUIRED',478,47,'#e7ebf0'),('DEVELOPMENT PLACEHOLDER',610,23,'#ff4052')]:
        d.text((300,y),text,font=ImageFont.truetype(font,size),fill=color,anchor='mm')
    im.save(ROOT/'assets/logo-placeholder.png')
if __name__ == '__main__': create()
