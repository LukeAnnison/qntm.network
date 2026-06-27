#!/usr/bin/env python3
"""Generate og.png (1200x630 social preview card) for qntm.network. Run: python3 scripts/make_og.py"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H=1200,630; bg=(10,11,10); ink=(230,235,230); dim=(138,148,138); faint=(85,92,85)
acc=(63,240,127); acc_dim=(31,122,68); PAD=96
def font(p,s,i=0):
    try: return ImageFont.truetype(p,s,index=i)
    except Exception: return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc",s)
f_head=font("/System/Library/Fonts/Supplemental/Arial Bold.ttf",104)
f_brand=font("/System/Library/Fonts/Menlo.ttc",30,1); f_lede=font("/System/Library/Fonts/Helvetica.ttc",29)
f_foot=font("/System/Library/Fonts/Menlo.ttc",23)
img=Image.new("RGB",(W,H),bg); d=ImageDraw.Draw(img)
for x in range(W):
    a=max(0.0,1-x/(W*0.6))
    if a<=0: break
    d.line([(x,0),(x,3)],fill=tuple(int(bg[i]+(acc_dim[i]-bg[i])*a) for i in range(3)))
glow=Image.new("RGBA",(W,H),(0,0,0,0)); gd=ImageDraw.Draw(glow)
dots=[(0.78,0.30,12,1),(0.86,0.46,8,0),(0.70,0.64,9,1),(0.90,0.72,7,0),(0.64,0.22,6,0),(0.82,0.18,7,1),(0.75,0.50,6,0)]
for fx,fy,r,lit in dots:
    if lit: gd.ellipse([fx*W-r*2,fy*H-r*2,fx*W+r*2,fy*H+r*2],fill=(63,240,127,150))
glow=glow.filter(ImageFilter.GaussianBlur(9))
img=Image.alpha_composite(img.convert("RGBA"),glow).convert("RGB"); d=ImageDraw.Draw(img)
for fx,fy,r,lit in dots: d.ellipse([fx*W-r,fy*H-r,fx*W+r,fy*H+r],fill=acc if lit else (120,140,120))
d.ellipse([PAD,98,PAD+15,113],fill=acc); d.text((PAD+28,92),"qntm",font=f_brand,fill=ink)
hy=176; lh=104; x=PAD; s="The path of "
d.text((x,hy),s,font=f_head,fill=ink); x+=d.textlength(s,font=f_head)
d.text((x,hy),"least",font=f_head,fill=acc); d.text((PAD,hy+lh),"resistance.",font=f_head,fill=acc)
ly=176+2*lh+34
d.text((PAD,ly),"A personal operating system. It makes the next thing",font=f_lede,fill=dim)
d.text((PAD,ly+38),"legible — and the path to it, the shortest one.",font=f_lede,fill=dim)
d.text((PAD,H-70),"qntm.network",font=f_foot,fill=acc)
t="building in the open"; d.text((W-PAD-d.textlength(t,font=f_foot),H-70),t,font=f_foot,fill=faint)
img.save("og.png","PNG"); print("wrote og.png",img.size)
