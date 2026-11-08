from pathlib import Path
import sys
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').exists())
SRC=ROOT/'mods/Project Roc Unicorns/source-assets/GGA1401'
OUT=ROOT/'outputs/UyaIava_Optimization'
sys.path.insert(0,str(SRC))
from reactor_geometry import render_scm,load_sca_pose
from PIL import Image
for folder,lod in [('original',0),('runtime',0),('runtime',1)]:
 for name,az,el in [('front',0,16),('game',35,38)]:
  render_scm(OUT/f'{folder}/GGA1401_lod{lod}.scm',SRC,OUT/f'checked_{folder}_{lod}_{name}.png',az,el,(.13,.78,.42),720)
  print(folder,lod,name,flush=True)
frames=[]
for sec in [0,8,16,24]:
 p=OUT/f'pose_{sec}.png'
 frames.append(render_scm(OUT/'runtime/GGA1401_lod0.scm',SRC,p,35,38,(.13,.78,.42),440,pose=load_sca_pose(OUT/'original/GGA1401_idle.sca',sec)))
sheet=Image.new('RGB',(1760,440))
for i,im in enumerate(frames):sheet.paste(im,(440*i,0))
sheet.save(OUT/'animation_phases.png')

