from pathlib import Path
from PIL import Image, ImageDraw
root = Path(__file__).resolve().parent
mod = root.parent.parent
im = Image.open(root / 'source-model/preview.png').convert('RGB')
# The preview's neutral charcoal background is connected to the image edges.
mask = Image.new('L', im.size, 0)
p = im.load(); m = mask.load(); w, h = im.size
from collections import deque
q = deque()
for x in range(w): q.extend(((x, 0), (x, h - 1)))
for y in range(h): q.extend(((0, y), (w - 1, y)))
while q:
    x, y = q.popleft()
    if m[x, y]: continue
    r, g, b = p[x, y]
    if max(r, g, b) > 55 or max(r, g, b) - min(r, g, b) > 10: continue
    m[x, y] = 255
    if x: q.append((x - 1, y))
    if x + 1 < w: q.append((x + 1, y))
    if y: q.append((x, y - 1))
    if y + 1 < h: q.append((x, y + 1))
from PIL import ImageOps
im = im.convert('RGBA'); im.putalpha(ImageOps.invert(mask))
im = im.crop(im.getbbox()); im.thumbnail((60, 60), Image.Resampling.LANCZOS)
icon = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
icon.alpha_composite(im, ((64-im.width)//2, (64-im.height)//2))
icon.save(root / 'AEM2301_icon.png')
for path in (mod / 'icons/units/AEM2301_icon.dds', mod / 'textures/ui/common/icons/units/AEM2301_icon.dds'):
    icon.save(path)
