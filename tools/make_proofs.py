from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from render_proofs import draw_text,text_width
from samples import SAMPLES
ROOT=Path(__file__).resolve().parents[1]
import json
VERSION=json.loads((ROOT/'design/config.json').read_text())['version']
ROWS=[('English','en','Hello'),('Kannada','kn','ನಮಸ್ಕಾರ'),('Hindi','hi','नमस्ते'),('Marathi','mr','नमस्कार'),('Malayalam','ml','നമസ്കാരം'),('Tamil','ta','வணக்கம்'),('Telugu','te','నమస్కారం'),('Bengali','bn','নমস্কার')]
def label(size):return ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',size)

def proof(weight):
 p=ROOT/'desktop'/f'AT-KPN-{weight}.ttf';im=Image.new('RGB',(1600,1830),'#faf9f5');d=ImageDraw.Draw(im)
 d.text((70,48),'AT-KPN',font=label(45),fill='#17251d');d.text((70,110),f'{weight.upper()} / ACTUAL FONT PROOF / VERSION {VERSION}',font=label(19),fill='#606960')
 for i,(lang,tag,text) in enumerate(ROWS):
  y=200+i*190;d.line((70,y-20,1530,y-20),fill='#cbd0c5',width=1);d.text((70,y+40),lang.upper(),font=label(20),fill='#606960')
  size=140 if tag=='en' else 118
  while text_width(p,size,text,tag)>1100:size-=1
  draw_text(im,p,size,text,405,y+115,tag)
 d.text((70,1760),'English + seven Indian languages · OpenType shaping · SIL Open Font License 1.1',font=label(20),fill='#606960')
 (ROOT/'specimen').mkdir(exist_ok=True);im.save(ROOT/'specimen'/f'AT-KPN-{weight}-proof.png')

def repertoire(weight):
 p=ROOT/'desktop'/f'AT-KPN-{weight}.ttf';im=Image.new('RGB',(1900,2130),'white');d=ImageDraw.Draw(im)
 d.text((60,40),f'AT-KPN {weight} · alphabet and text',font=label(30),fill='black')
 for i,t in enumerate(['ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz','0123456789 ₹ $ € £ & @ % ! ?','Héllo naïve café rôle élève — office affinity']):draw_text(im,p,70,t,60,160+i*100)
 for i,s in enumerate(SAMPLES):
  y=560+i*215;d.text((60,y),s['language'],font=label(18),fill='#666666')
  draw_text(im,p,52,s['text'],60,y+85,s['lang']);draw_text(im,p,40,s['clusters'],60,y+150,s['lang'])
 im.save(ROOT/'specimen'/f'AT-KPN-{weight}-repertoire.png')
if __name__=='__main__':
 for w in ['Bold','Regular','Light']:
  if (ROOT/'desktop'/f'AT-KPN-{w}.ttf').exists():proof(w);repertoire(w)
 print('Rendered actual-font proofs')
