from pathlib import Path
from PIL import Image
from io import BytesIO
import zipfile,numpy as np,struct
ROOT=Path('F:/FAF-Development/work/faf-upload');MOD=ROOT/'mods/Project Roc Unicorns';OUT=ROOT/'outputs/ShaVeyr_Burst_20261108'
# Reuse the independently filtered data-map DDS writer without executing its build loop.
exec(Path('texture_vael.py').read_text().split("for suffix in ['albedo'")[0].replace("OUT=Path('F:/FAF-Development/work/faf-upload/outputs/VaelItha_Optimization')",''))
with zipfile.ZipFile(OUT/'before.zip') as z:
 im=Image.open(BytesIO(z.read('projectiles/GGP2302/GGP2302_albedo.dds'))).convert('RGBA')
 a=np.asarray(im).copy();level=a[:,:,:3].mean(2);level=(level-level.min())/max(1,float(np.ptp(level)))
 # Near-white, faint cool edge; retain gentle surface variation without a pulsing light.
 for c,(lo,hi) in enumerate([(205,245),(215,250),(232,255)]):a[:,:,c]=lo+(hi-lo)*level
 dds(Image.fromarray(a),MOD/'projectiles/GGP2302/GGP2302_albedo.dds')
 spec=Image.open(BytesIO(z.read('projectiles/GGP2302/GGP2302_specteam.dds'))).convert('RGBA');s=np.asarray(spec).copy();s[:,:,2]=95
 dds(Image.fromarray(s),MOD/'projectiles/GGP2302/GGP2302_specteam.dds')
 Image.fromarray(a).save(OUT/'projectile_albedo_preview.png')
print('Near-white projectile maps saved; purple trail maps unchanged.')
