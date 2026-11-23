from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from make_proofs import ROWS
from render_proofs import draw_text,text_width
ROOT=Path(__file__).resolve().parents[1]
im=Image.new('RGB',(2000,1710),'#faf9f5');d=ImageDraw.Draw(im)
font=lambda n:ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',n)
d.text((70,50),'AT-KPN',font=font(46),fill='#17251d');d.text((70,112),'VERSION 0.600 · ACTUAL FONT PROOFS · EIGHT LANGUAGES',font=font(19),fill='#667166')
for j,w in enumerate(['Light','Regular','Bold']):d.text((340+j*540,190),w.upper(),font=font(22),fill='#667166')
for i,(language,lang,text) in enumerate(ROWS):
 y=270+i*165;d.line((70,y-30,1930,y-30),fill='#cbd0c5');d.text((70,y+30),language.upper(),font=font(19),fill='#667166')
 for j,w in enumerate(['Light','Regular','Bold']):
  p=ROOT/'desktop'/f'AT-KPN-{w}.ttf';size=82 if lang=='en' else 69
  while text_width(p,size,text,lang)>485:size-=1
  draw_text(im,p,size,text,340+j*540,y+80,lang)
d.text((70,1640),'Light 300 · Regular 400 · Bold 700     |     Desktop TTF + Web WOFF2     |     SIL Open Font License 1.1',font=font(21),fill='#667166')
im.save(ROOT/'specimen/AT-KPN-family-overview.png')
