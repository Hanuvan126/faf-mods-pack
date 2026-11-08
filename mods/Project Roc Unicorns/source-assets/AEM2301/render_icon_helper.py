import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path

d=Path(__file__).resolve().parent/'source-model'
out=d.parent
texture=np.asarray(Image.open(d/'Aeon_albedo.png').convert('RGB'))
def load(path):
    v=[]; uv=[]; faces=[]
    for line in path.read_text(encoding='utf-8',errors='replace').splitlines():
        s=line.split()
        if not s: continue
        if s[0]=='v': v.append(list(map(float,s[1:4])))
        if s[0]=='vt': uv.append(list(map(float,s[1:3])))
        if s[0]=='f':
            face=[x.split('/') for x in s[1:]]
            for i in range(1,len(face)-1): faces.append([face[0],face[i],face[i+1]])
    return np.array(v),np.array(uv),faces
models=[load(d/'Aeon_Missile_Turret.obj'),load(d/'Aeon_Missile_Turret_optimized.obj')]
allv=models[0][0]; center=(allv.min(0)+allv.max(0))/2
size=650
def render(model, direction):
    v,uv,faces=model
    forward=np.array(direction,dtype=float); forward/=np.linalg.norm(forward)
    right=np.cross([0,1,0],forward); right/=np.linalg.norm(right)
    up=np.cross(forward,right)
    p=v-center
    scale=32
    x=p@right*scale+size/2; y=size/2-p@up*scale; z=p@forward
    image=np.full((size,size,3),[31,38,48],dtype=np.uint8); depth=np.full((size,size),-np.inf)
    light=np.array([-.4,.8,1.]); light/=np.linalg.norm(light)
    for f in faces:
        ids=[int(a[0])-1 for a in f]; tis=[int(a[1])-1 for a in f]
        xs=x[ids]; ys=y[ids]; zs=z[ids]
        x0=max(0,int(np.floor(xs.min()))); x1=min(size-1,int(np.ceil(xs.max())))
        y0=max(0,int(np.floor(ys.min()))); y1=min(size-1,int(np.ceil(ys.max())))
        if x1<x0 or y1<y0: continue
        den=(ys[1]-ys[2])*(xs[0]-xs[2])+(xs[2]-xs[1])*(ys[0]-ys[2])
        if abs(den)<1e-8: continue
        xx,yy=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
        a=((ys[1]-ys[2])*(xx-xs[2])+(xs[2]-xs[1])*(yy-ys[2]))/den
        b=((ys[2]-ys[0])*(xx-xs[2])+(xs[0]-xs[2])*(yy-ys[2]))/den
        c=1-a-b; zz=a*zs[0]+b*zs[1]+c*zs[2]
        dep=depth[y0:y1+1,x0:x1+1]; mask=(a>=0)&(b>=0)&(c>=0)&(zz>dep)
        if not mask.any(): continue
        coords=uv[tis]; u=a*coords[0,0]+b*coords[1,0]+c*coords[2,0]; w=a*coords[0,1]+b*coords[1,1]+c*coords[2,1]
        tx=np.clip((u*(texture.shape[1]-1)).astype(int),0,texture.shape[1]-1); ty=np.clip(((1-w)*(texture.shape[0]-1)).astype(int),0,texture.shape[0]-1)
        n=np.cross(v[ids[1]]-v[ids[0]],v[ids[2]]-v[ids[0]]); norm=np.linalg.norm(n)
        shade=.60+.40*abs(np.dot(n/norm,light)) if norm else 1
        region=image[y0:y1+1,x0:x1+1]; region[mask]=(texture[ty[mask],tx[mask]]*shade).astype(np.uint8); dep[mask]=zz[mask]
    return Image.fromarray(image)
canvas=Image.new('RGB',(1300,1380),(20,26,34)); draw=ImageDraw.Draw(canvas)
for row,direction in enumerate(([1,.75,1],[-1,.75,-1])):
    for col,model in enumerate(models): canvas.paste(render(model,direction),(col*650,40+row*670))
draw.text((20,12),'Original: 4480 triangles',fill='white'); draw.text((670,12),'Optimized: 3000 triangles',fill='white')
draw.text((20,1360),'Same camera, scale and lighting; albedo texture only',fill='white')
canvas.save(out/'AEM2301_comparison.png')
print(out/'AEM2301_comparison.png')
