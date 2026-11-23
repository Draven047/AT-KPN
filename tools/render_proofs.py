"""Proof actual font glyphs using HarfBuzz shaping and FreeType rasterization."""
from pathlib import Path
from functools import lru_cache
import uharfbuzz as hb
import freetype
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]

@lru_cache(maxsize=64)
def resources(path,size):
    path=str(path);face=freetype.Face(path);face.set_pixel_sizes(0,size)
    font=hb.Font(hb.Face(Path(path).read_bytes()));hb.ot_font_set_funcs(font)
    font.scale=(size*64,size*64)
    return face,font

def shape(path,size,text,lang):
    face,font=resources(str(path),size)
    buf=hb.Buffer();buf.add_str(text);buf.guess_segment_properties();buf.language=lang
    hb.shape(font,buf)
    return face,list(zip(buf.glyph_infos,buf.glyph_positions))

def text_width(path,size,text,lang):
    _,run=shape(path,size,text,lang)
    return sum(p.x_advance for _,p in run)/64

def draw_text(image,path,size,text,x,baseline,lang='en',color='#17251d'):
    face,run=shape(path,size,text,lang)
    ox=0;oy=0
    for info,pos in run:
        face.load_glyph(info.codepoint,freetype.FT_LOAD_RENDER|freetype.FT_LOAD_NO_HINTING)
        slot=face.glyph;bitmap=slot.bitmap
        if bitmap.width and bitmap.rows:
            mask=Image.frombytes('L',(abs(bitmap.pitch),bitmap.rows),bytes(bitmap.buffer)).crop((0,0,bitmap.width,bitmap.rows))
            left=round(x+(ox+pos.x_offset)/64+slot.bitmap_left)
            top=round(baseline-(oy+pos.y_offset)/64-slot.bitmap_top)
            image.paste(color,(left,top),mask)
        ox+=pos.x_advance;oy+=pos.y_advance
    return ox/64
