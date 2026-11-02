"""Actual geometry projected to editable PNG/SVG markup sheets; no invented motifs."""
from pathlib import Path
import math,json,html,zipfile
import numpy as np
from PIL import Image,ImageDraw,ImageFont
OUT=Path('F:/FAF-Development/outputs/VaelItha_Selection_Ring_Fix_v7');DEST=OUT/'Pattern_sheets';DEST.mkdir(exist_ok=True)
data=json.loads((OUT/'pattern_geometry.json').read_text())
FONT='C:/Windows/Fonts/segoeui.ttf'
def font(n):return ImageFont.truetype(FONT,n)
class Sheet:
 def __init__(self,name,title,w=1800,h=1500):
  self.name=name;self.w=w;self.h=h;self.im=Image.new('RGB',(w,h),'white');self.d=ImageDraw.Draw(self.im);self.svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/>'];self.text((60,35),title,38);self.text((60,94),'Текущие линии модели. Серым — контур детали. Можно рисовать поверх.',24,'#555555')
 def text(self,pos,s,size=26,col='#111111'):
  self.d.text(pos,s,font=font(size),fill=col);self.svg.append(f'<text x="{pos[0]}" y="{pos[1]+size}" fill="{col}" font-family="Segoe UI,sans-serif" font-size="{size}">{html.escape(s)}</text>')
 def path(self,pts,col='#171717',width=3,closed=False):
  if len(pts)<2:return
  pts=[tuple(float(v) for v in p) for p in pts]
  if closed:pts=pts+[pts[0]]
  self.d.line(pts,fill=col,width=max(1,round(width)),joint='curve');s=' '.join(f'{x:.2f},{y:.2f}' for x,y in pts);self.svg.append(f'<polyline points="{s}" fill="none" stroke="{col}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>')
 def save(self):self.im.save(DEST/(self.name+'.png'));(DEST/(self.name+'.svg')).write_text('\n'.join(self.svg+['</svg>']),encoding='utf-8')
def projector(rect,bounds):
 x,y,w,h=rect;x0,x1,y0,y1=bounds;s=min(w/(x1-x0),h/(y1-y0));cx=x+w/2;cy=y+h/2
 return lambda p:(cx+(p[0]-(x0+x1)/2)*s,cy-((p[1]-(y0+y1)/2)*s))
def centerline(o):
 v=np.array(o['vertices']);n=2 if o['engraved'] else 4
 return v[:len(v)//n*n].reshape(-1,n,3).mean(1)
def drawparts(sheet,objects,transform,project):
 for o in objects:
  pts=centerline(o)
  if len(pts)<2:continue
  ds=np.linalg.norm(np.diff(pts,axis=0),axis=1);limit=max(.06,float(np.median(ds))*3.5);start=0
  for i,d in enumerate(ds):
   if d>limit:sheet.path([project(transform(p)) for p in pts[start:i+1]],width=3);start=i+1
  sheet.path([project(transform(p)) for p in pts[start:]],width=3)
def circle(cx,cy,r,n=128):return [(cx+r*math.cos(i*2*math.pi/n),cy+r*math.sin(i*2*math.pi/n)) for i in range(n+1)]
profile=np.array([(.22,.91,.14),(.42,1,.26),(.65,.83,.41),(.91,.56,.55),(1.18,.31,.56),(1.49,.135,.38),(1.76,.055,.18),(1.94,.025,.004)])
def prof(t):
 t=min(6.999999,max(0,t));j=int(t);u=t-j;a,b,c,d=profile[max(0,j-1)],profile[j],profile[j+1],profile[min(7,j+2)]
 return .5*(2*b+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u**3)
s=Sheet('01_foundation_petals','VAEL-ITHA — УЗОРЫ ЛЕПЕСТКОВ ОСНОВАНИЯ')
for idx,angle,secondary,top in [(1,-150,False,230),(4,-90,True,850)]:
 a=math.radians(angle);rad=np.array([math.cos(a),math.sin(a),0]);side=np.array([-math.sin(a),math.cos(a),0]);rs=.94 if secondary else 1;ws=.88 if secondary else 1
 s.text((60,top-60),'ОСНОВНОЙ ЛЕПЕСТОК — повторяется 3 раза' if not secondary else 'МАЛЫЙ ЛЕПЕСТОК — повторяется 3 раза',30)
 pr=projector((80,top,1640,450),(-.05,1.9,-.65,.65));outline=[]
 for sign,ts in [(1,np.linspace(0,7,160)),(-1,np.linspace(7,0,160))]:
  for t in ts:r,z,w=prof(t);outline.append(pr((1.94-r*rs,sign*w*ws)))
 s.path(outline,'#999999',2,True)
 objs=[o for o in data if any(o['name'].startswith(x) for x in [f'Crop circle petal {idx}/',f'Orbital node petal {idx}/',f'Petal circle link {idx}/',f'Living energy vein {idx} /'])]
 drawparts(s,objs,lambda p:(1.94-float(p@rad),float(p@side)),pr)
 s.text((100,top+460),'КОНЧИК',22,'#666666');s.text((1470,top+460),'К ЦЕНТРУ',22,'#666666')
s.save()
s=Sheet('02_gondola','VAEL-ITHA — ГОНДОЛА: СНАРУЖИ И ИЗНУТРИ',1800,1450)
for outside,top in [(True,230),(False,860)]:
 s.text((60,top-60),'ВНЕШНЯЯ СТОРОНА — повтор для второй гондолы зеркальный' if outside else 'ВНУТРЕННЯЯ СТОРОНА — светящаяся панель и продольные линии',29)
 pr=projector((80,top,1640,430),(-1.65,1.33,2.3,3.5));outline=[]
 for sign,ts in [(1,np.linspace(0,1,150)),(-1,np.linspace(1,0,150))]:
  for t in ts:outline.append(pr((-1.56+2.8*t,2.9+sign*(.003+.345*math.sin(math.pi*t)**.72))))
 s.path(outline,'#999999',2,True)
 for r in [.575,.385]:s.path([pr(p) for p in circle(-.16,2.9,r)],'#999999',2)
 if outside:
  objects=[o for o in data if o['bone']=='GondolaL' and any(o['name'].startswith(x) for x in ['Hull nested orbital seal','Hull satellite','Team long hull circuit'])]
  drawparts(s,objects,lambda p:(p[1],p[2]),pr)
 else:
  objects=[o for o in data if o['bone']=='GondolaL' and 'electric inner lip' in o['name']]
  drawparts(s,objects,lambda p:(p[1],p[2]),pr)
  panel=next(o for o in data if o['bone']=='GondolaL' and 'upper recessed panel' in o['name'])
  for f in panel['faces']:s.path([pr((panel['vertices'][i][1],panel['vertices'][i][2])) for i in f],'#cccccc',1,True)
 s.text((85,top+450),'ПЕРЕД',22,'#666666');s.text((1550,top+450),'ЗАД',22,'#666666')
s.save()
s=Sheet('03_ring','VAEL-ITHA — КОЛЬЦО: ВНЕШНИЙ УЗОР И ВНУТРЕННЕЕ СВЕЧЕНИЕ',1800,1500)
pr=projector((480,180,840,840),(-.62,.62,-.62,.62))
for r in [.575,.385]:s.path([pr(p) for p in circle(0,0,r)],'#999999',2)
objects=[o for o in data if o['bone']=='GondolaL' and any(o['name'].startswith(x) for x in ['Ring orbital seal','Ring paired orbit'])]
drawparts(s,objects,lambda p:(p[1]+.16,p[2]-2.9),pr)
s.text((70,1040),'ВНУТРЕННЯЯ СТЕНКА — развёртка на полный оборот',29)
s.path([(120,1130),(1680,1130),(1680,1350),(120,1350)],'#999999',2,True)
s.text((160,1200),'Сейчас: сплошное свечение цвета команды, без отдельного рисунка.',28,'#666666')
s.text((120,1380),'0° — шов',22,'#666666');s.text((1570,1380),'360°',22,'#666666');s.save()
s=Sheet('04_crown','VAEL-ITHA — ЦЕНТРАЛЬНАЯ КОРОНА, ВИД СВЕРХУ',1600,1500)
pr=projector((140,230,1320,1100),(-.7,.7,-.7,.7))
for rr in [.4,.59]:
 pts=[]
 for i in range(241):a=2*math.pi*i/240;r=rr*(1+.14*math.cos(3*a));pts.append(pr((r*math.cos(a),r*math.sin(a))))
 s.path(pts,'#999999',2)
objs=[o for o in data if o['name'].startswith('Team crown orbital seal')]
drawparts(s,objs,lambda p:(p[0],p[1]),pr)
for r in [.365,.38]:s.path([pr(p) for p in circle(0,0,r)],'#222222',3)
s.save()
s=Sheet('05_ring_outer_band','VAEL-ITHA — НАРУЖНЫЙ ТОРЕЦ КОЛЬЦА, РАЗВЁРТКА 360°',1800,850)
s.text((65,170),'Две существующие круговые дорожки по наружной поверхности обода.',28)
pr=projector((120,290,1560,330),(0,2*math.pi,-.12,.12))
s.path([pr(p) for p in [(0,-.09),(2*math.pi,-.09),(2*math.pi,.09),(0,.09)]],'#999999',2,True)
for o in [o for o in data if o['bone']=='GondolaL' and o['name'].startswith('Outer ring track')]:
 pts=centerline(o);angles=np.unwrap(np.arctan2(pts[:,2]-2.9,pts[:,1]+.16));angles-=angles[0]
 s.path([pr((abs(float(a)),-float(v[0]+.68))) for a,v in zip(angles,pts)],width=3)
s.text((120,650),'0° — шов',23,'#666666');s.text((1550,650),'360°',23,'#666666');s.save()
# Actual shared mask is included for completeness; geometry templates are for redraw.
mod=Path(__file__).resolve().parents[2];Image.open(mod/'units/GGA2404/GGA2404_albedo.dds').convert('RGBA').getchannel('A').save(DEST/'shared_army_mask.png')
(DEST/'README.txt').write_text('Листы сняты с текущей геометрии Vael-Itha. Чёрным показаны существующие узоры, серым — контуры деталей. Это плоские проекции для правок; общий игровой атлас не содержит уникальную развёртку каждого орнамента. PNG можно разрисовать в любом редакторе, SVG сохраняет линии векторными. На листе 03 внутренняя цилиндрическая стенка кольца показана развёрнутой на 360 градусов. Новые узоры пока не применены.\n',encoding='utf-8')
with zipfile.ZipFile(OUT/'VaelItha_Pattern_Sheets.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in DEST.iterdir():z.write(p,'VaelItha_Pattern_Sheets/'+p.name)
print('PATTERN_SHEETS_READY',len(list(DEST.iterdir())))
