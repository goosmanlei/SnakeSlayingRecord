"""Render the editable SVG master; requires Pillow and CairoSVG in a local environment."""
from pathlib import Path
from PIL import Image, ImageDraw
import cairosvg, io, struct
root=Path(__file__).resolve().parents[1]; source=root/'export/assets/lantern-home-favicon.svg'
for size in (16,32,48,64,256):
    cairosvg.svg2png(url=str(source),write_to=str(root/f'design/favicon/favicon-{size}.png'),output_width=size,output_height=size)
imgs=[(s,(root/f'design/favicon/favicon-{s}.png').read_bytes()) for s in (16,32,48,64,256)]
offset=6+16*len(imgs); ico=struct.pack('<HHH',0,1,len(imgs)); payload=b''
for size,data in imgs:
    ico+=struct.pack('<BBBBHHII',size%256,size%256,0,0,1,32,len(data),offset);payload+=data;offset+=len(data)
(root/'export/assets/lantern-home-favicon.ico').write_bytes(ico+payload)
(root/'export/assets/lantern-home-favicon.png').write_bytes((root/'design/favicon/favicon-32.png').read_bytes())
canvas=Image.new('RGB',(800,400),'#efe9dc');d=ImageDraw.Draw(canvas)
for j,bg in enumerate(('#fbfaf7','#151d24')):
    d.rectangle((j*400,0,j*400+399,399),fill=bg)
    fg='#34434a' if j==0 else '#f3eadc'
    d.text((j*400+24,18),'LIGHT' if j==0 else 'DARK',fill=fg)
    for i,size in enumerate((16,32)):
        icon=Image.open(root/f'design/favicon/favicon-{size}.png').convert('RGBA')
        x=j*400+36+i*180
        canvas.paste(icon,(x,65),icon);d.text((x,100),f'{size} px / actual',fill=fg)
        enlarged=icon.resize((128,128),Image.Resampling.NEAREST)
        canvas.paste(enlarged,(x,160),enlarged);d.text((x,306),'pixel inspection',fill=fg)
canvas.save(root/'design/favicon/preview.png')
