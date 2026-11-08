from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent
mod = root.parent.parent
code = (root/'render_icon_helper.py').read_text(encoding='utf8').split('canvas=')[0]
exec(code)
# Aeon uses the alpha channel of SpecTeam as its player-colour mask.
rgba = np.asarray(Image.open(root/'source-model/Aeon_albedo.png').convert('RGB')).astype(float)
mask = np.asarray(Image.open(root/'source-model/Aeon_specteam.png').convert('RGBA'))[:,:,3:4]/255.0
texture = np.uint8(np.clip(rgba*(1-mask)+np.array([22,150,65])*mask,0,255))
rendered = render(models[1], [1,.95,1]).convert('RGBA')
arr = np.asarray(rendered).copy()
arr[:,:,3] = np.where(np.any(arr[:,:,:3] != [31,38,48],axis=2),255,0).astype('uint8')
rendered = Image.fromarray(arr)
rendered = rendered.crop(rendered.getbbox())
rendered.thumbnail((60,60),Image.Resampling.LANCZOS)
icon = Image.new('RGBA',(64,64))
icon.alpha_composite(rendered,((64-rendered.width)//2,(64-rendered.height)//2))
icon.save(root/'AEM2301_icon.png')
for path in (mod/'icons/units/AEM2301_icon.dds',mod/'textures/ui/common/icons/units/AEM2301_icon.dds'):
    path.parent.mkdir(parents=True,exist_ok=True); icon.save(path)

# Unique strategic icon: square, two vertical strokes, and three T3 marks.
folder=mod/'custom-strategic-icons'; folder.mkdir(exist_ok=True)
for state in ('rest','over','selected','selectedover'):
    im=Image.new('RGBA',(12,16),(0,0,0,0)); draw=ImageDraw.Draw(im)
    face=(150,150,150,255) if state in ('over','selectedover') else (123,125,123,255)
    draw.rectangle((0,0,11,10),fill=(0,0,0,255)); draw.rectangle((1,1,10,9),fill=face)
    draw.rectangle((4,3,4,7),fill=(0,0,0,255)); draw.rectangle((7,3,7,7),fill=(0,0,0,255))
    draw.rectangle((2,11,9,15),fill=(0,0,0,255))
    for x in (3,5,7): draw.rectangle((x,12,x,14),fill=(255,255,255,255))
    im.save(folder/f'icon_aem2301_{state}.dds')
    if state=='rest': im.resize((240,320),Image.Resampling.NEAREST).save(root/'AEM2301_strategic_preview.png')
