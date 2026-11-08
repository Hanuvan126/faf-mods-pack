from pathlib import Path
import sys
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'AGENTS.md').exists())
SRC=ROOT/'mods/Project Roc Unicorns/source-assets/GGA2404'
OUT=ROOT/'outputs/VaelItha_Optimization'
sys.path.insert(0,str(SRC))
from preview_scm import render_scm
for folder,lod in [('runtime',0),('runtime',1)]:
 for view,az,el in [('perspective',35,24),('top',35,65)]:
  render_scm(OUT/f'{folder}/GGA2404_lod{lod}.scm',SRC,OUT/f'checked_{folder}_{lod}_{view}.png',az,el,(.4,.12,.85),800,runtime_textures=True)
  print(folder,lod,view,flush=True)
