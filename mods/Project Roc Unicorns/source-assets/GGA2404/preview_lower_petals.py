from pathlib import Path
import sys,json,math,html
import numpy as np
S=Path(__file__).resolve().parent;OUT=Path('F:/FAF-Development/outputs/VaelItha_Lower_Petals_v10');DEST=OUT
from PIL import Image,ImageDraw,ImageFont
FONT='C:/Windows/Fonts/segoeui.ttf'
def font(n):return ImageFont.truetype(FONT,n)
code=(S/'make_pattern_sheets.py').read_text();exec(code[code.index('class Sheet:'):code.index('profile=np.array')])
r=json.loads((OUT/'report.json').read_text());sheet=Sheet('lower_petal_pattern','VAEL-ITHA — НИЖНИЕ ЛЕПЕСТКИ',1600,1000);pr=projector((100,180,1400,700),(0,1,-.52,.52))
for path in r['designs']:sheet.path([pr(p) for p in path],'#723dad',4)
sheet.save()
sys.path.insert(0,str(S));from preview_scm import render_scm
for name,az,el in [('turret_three_quarter',35,28),('turret_top',35,70)]:
 render_scm(S.parents[1]/'units/GGA2404/GGA2404_lod0.scm',S,OUT/(name+'.png'),azimuth=az,elevation=el,player=(.85,.9,1),size=1100,hidden_bones=[7,8,9,10,11],runtime_textures=True)
 print('PREVIEW_COMPLETE',name,flush=True)
