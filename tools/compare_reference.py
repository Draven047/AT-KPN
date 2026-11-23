"""Compare actual released outlines to the attached approved raster reference."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw,ImageFont
from render_proofs import draw_text
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'0.500/desktop/AT-KPN-Bold.ttf'
if not OLD.exists():OLD=ROOT/'releases/0.500/desktop/AT-KPN-Bold.ttf'
ROWS=[('English','en','Hello',(255,145,900,275)),('Kannada','kn','ನಮಸ್ಕಾರ',(255,309,900,454)),('Hindi','hi','नमस्ते',(255,481,900,615)),('Marathi','mr','नमस्कार',(255,680,900,782)),('Malayalam','ml','നമസ്കാരം',(255,827,920,947)),('Tamil','ta','வணக்கம்',(255,986,930,1104)),('Telugu','te','నమస్కారం',(255,1138,900,1278)),('Bengali','bn','নমস্কার',(255,1320,900,1437))]
LABEL=lambda n:ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',n)
def mask(im):return im.convert('L').point(lambda p:255 if p<100 else 0)
def trim(im):return im.crop(mask(im).getbbox())
def render(path,text,lang):
 im=Image.new('RGB',(11000,2600),'white');draw_text(im,path,1000,text,300,1500,lang,color='black');return trim(im)
def sameheight(im,h):return im.resize((round(im.width*h/im.height),h),Image.Resampling.LANCZOS)
if __name__=='__main__':
 source=Image.open(ROOT/'design/approved-concept.png').convert('RGB');new=ROOT/'desktop/AT-KPN-Bold.ttf';report=[];im=Image.new('RGB',(2400,2260),'#faf9f5');d=ImageDraw.Draw(im)
 d.text((60,35),'AT-KPN / OUTLINE REFINEMENT',font=LABEL(38),fill='#17251d');d.text((60,97),'Actual Bold fonts, compared at the same visible ink height. No horizontal stretching.',font=LABEL(22),fill='#526257')
 for x,t in [(60,'APPROVED IMAGE'),(860,'PREVIOUS 0.500'),(1660,'REFINED 0.600')]:d.text((x,155),t,font=LABEL(20),fill='#526257')
 out=ROOT/'qa/reference-crops';out.mkdir(exist_ok=True)
 for i,(language,lang,text,box) in enumerate(ROWS):
  ref=trim(source.crop(box));before=sameheight(render(OLD,text,lang),ref.height);after=sameheight(render(new,text,lang),ref.height);y=220+i*250
  d.line((60,y-12,2335,y-12),fill='#cbd0c5');d.text((60,y+5),language.upper(),font=LABEL(22),fill='#17251d')
  for x,img in zip([60,860,1660],[ref,before,after]):d_img=img.resize((round(img.width*1.12),round(img.height*1.12)),Image.Resampling.LANCZOS);im.paste(d_img,(x,y+55))
  for p,img in [('reference',ref),('previous',before),('refined',after)]:img.save(out/f'{lang}-{p}.png')
  report.append({'language':language,'reference_size':list(ref.size),'previous_size':list(before.size),'refined_size':list(after.size),'previous_width_delta_percent':round((before.width/ref.width-1)*100,2),'refined_width_delta_percent':round((after.width/ref.width-1)*100,2)})
 im.save(ROOT/'specimen/AT-KPN-refinement-comparison.png');(ROOT/'qa/visual-comparison.json').write_text(json.dumps({'font_sha256':hashlib.sha256(new.read_bytes()).hexdigest(),'method':'Uniform visible-ink-height normalization; silhouette measurements, not similarity scores. Native forms and fine curves require visual review.','rows':report},ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
