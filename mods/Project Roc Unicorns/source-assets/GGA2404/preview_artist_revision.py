"""Clean geometric authoring diagrams and views of the actual exported SCM."""
from pathlib import Path
import json,math,html,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
SRC=Path(__file__).resolve().parent;OUT=Path('F:/FAF-Development/outputs/VaelItha_Artist_Patterns_v9');DEST=OUT
FONT='C:/Windows/Fonts/segoeui.ttf'
def font(n):return ImageFont.truetype(FONT,n)
code=(SRC/'make_pattern_sheets.py').read_text();exec(code[code.index('class Sheet:'):code.index('profile=np.array')])
report=json.loads((OUT/'artist_revision_report.json').read_text())
s=Sheet('petal_patterns_clean','VAEL-ITHA — КОНТУР И ШТРИХОВКА ПО ЭСКИЗУ',1800,1500)
for j,design in enumerate(d for d in report['designs'] if d['type']=='petal'):
 top=240+j*600;pr=projector((100,top,1600,430),(.1,1.96,-.62,.62))
 s.text((60,top-70),'ОСНОВНОЙ ЛЕПЕСТОК' if not design['secondary'] else 'МАЛЫЙ ЛЕПЕСТОК',29)
 for path in design['existing']:s.path([pr(p) for p in path],'#292929',3)
 s.path([pr(p) for p in design['perimeter']],'#723dad',4)
 for path in design['hatches']:s.path([pr(p) for p in path],'#723dad',3)
s.text((80,1390),'Чёрным — сохранённый рисунок. Фиолетовым — новые линии цвета команды.',24,'#555555');s.save()
d=next(d for d in report['designs'] if d['type']=='gondola');cy,cz=d['center']
s=Sheet('gondola_patterns_clean','VAEL-ITHA — НОВЫЙ РИСУНОК ГОНДОЛЫ',1800,1400)
for j,key in enumerate(['outside','inside']):
 top=230+j*590;pr=projector((90,top,1620,420),(-1.65,1.33,cz-.60,cz+.60))
 s.text((60,top-60),'СНАРУЖИ — новый орнамент' if j==0 else 'ИЗНУТРИ — новый светящийся контур',29)
 for r in [.385,.575]:s.path([pr(p) for p in circle(cy,cz,r)],'#aaaaaa',2)
 for path in d[key]:s.path([pr(p) for p in path],'#723dad',3)
s.save()
sys.path.insert(0,str(SRC));from preview_scm import render_scm
UNIT=SRC.parents[1]/'units/GGA2404'
for name,az,el in [('turret_three_quarter',35,28),('turret_side',90,8)]:
 render_scm(UNIT/'GGA2404_lod0.scm',SRC,OUT/(name+'.png'),azimuth=az,elevation=el,player=(.85,.9,1.0),size=1100,hidden_bones=[7,8,9,10,11],runtime_textures=True)
 print('NATIVE_PREVIEW_DONE',name,flush=True)
