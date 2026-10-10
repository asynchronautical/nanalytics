# Post-process public/map/data.json: scale the arrangement of states toward the center by F,
# keeping each state's shape and size, then push overlapping neighbours apart until GAP holds.
import json, math, sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter
F=float(sys.argv[1]) if len(sys.argv)>1 else 0.82
GAP=3.0; SCALE=2
d=json.load(open('public/map/data.json'))
by_state={}
for x in d['districts']: by_state.setdefault(x['id'][:2],[]).append(x)
geo={ab:[r for x in xs for r in x['rings']] for ab,xs in by_state.items()}
allpts=[p for rs in geo.values() for r in rs for p in r]
minx=min(p[0] for p in allpts)-80; miny=min(p[1] for p in allpts)-80
maxx=max(p[0] for p in allpts)+80; maxy=max(p[1] for p in allpts)+80
W=int((maxx-minx)*SCALE); H=int((maxy-miny)*SCALE)
def mask_of(rings, pad=0):
    im=Image.new('L',(W,H),0); dr=ImageDraw.Draw(im)
    for r in rings: dr.polygon([((p[0]-minx)*SCALE,(p[1]-miny)*SCALE) for p in r], fill=255, outline=255)
    if pad: im=im.filter(ImageFilter.MaxFilter(int(pad*SCALE)*2+1))
    return np.array(im)>0
cent={ab:(np.mean([p[0] for r in rs for p in r]), np.mean([p[1] for r in rs for p in r])) for ab,rs in geo.items()}
mobile=[ab for ab in geo if ab not in ('AK','HI')]
gx=np.mean([cent[a][0] for a in mobile]); gy=np.mean([cent[a][1] for a in mobile])
shift={ab:((gx-cent[ab][0])*(1-F),(gy-cent[ab][1])*(1-F)) if ab in mobile else (0,0) for ab in geo}
plain={ab:mask_of(geo[ab]) for ab in geo}; padded={ab:mask_of(geo[ab],pad=GAP/2) for ab in geo}
bb={}
for ab in geo:
    ys,xs=np.where(padded[ab]); bb[ab]=(xs.min(),xs.max(),ys.min(),ys.max())
def rolled(m,ab):
    sx=int(round(shift[ab][0]*SCALE)); sy=int(round(shift[ab][1]*SCALE)); return np.roll(np.roll(m,sy,axis=0),sx,axis=1)
def overlap(a,b):
    ax0,ax1,ay0,ay1=bb[a]; bx0,bx1,by0,by1=bb[b]
    sa=(shift[a][0]*SCALE,shift[a][1]*SCALE); sb=(shift[b][0]*SCALE,shift[b][1]*SCALE)
    if ax1+sa[0]<bx0+sb[0] or bx1+sb[0]<ax0+sa[0] or ay1+sa[1]<by0+sb[1] or by1+sb[1]<ay0+sa[1]: return 0
    return int((rolled(padded[a],a)&rolled(padded[b],b)).sum())
for it in range(200):
    moved=0
    for i,a in enumerate(mobile):
        for b in mobile[i+1:]:
            n=overlap(a,b)
            if n:
                ax,ay=cent[a][0]+shift[a][0],cent[a][1]+shift[a][1]; bx,by=cent[b][0]+shift[b][0],cent[b][1]+shift[b][1]
                vx,vy=ax-bx,ay-by; L=math.hypot(vx,vy) or 1; vx,vy=vx/L,vy/L
                shift[a]=(shift[a][0]+vx,shift[a][1]+vy); shift[b]=(shift[b][0]-vx,shift[b][1]-vy); moved+=1
    if not moved: break
print('iterations',it+1,'remaining overlaps',moved)
for x in d['districts']:
    dx,dy=shift[x['id'][:2]]
    x['rings']=[[[round(p[0]+dx,2),round(p[1]+dy,2)] for p in r] for r in x['rings']]
    x['c']=[round(x['c'][0]+dx,1),round(x['c'][1]+dy,1)]
for s in d['states']:
    dx,dy=shift[s['ab']]
    s['rings']=[[[round(p[0]+dx,2),round(p[1]+dy,2)] for p in r] for r in s['rings']]
d['compressed']={'factor':F,'gap':GAP}
json.dump(d,open('public/map/data.json','w'),separators=(',',':'))
bx=[p[0] for x in d['districts'] for r in x['rings'] for p in r]; by=[p[1] for x in d['districts'] for r in x['rings'] for p in r]
print('extent', round(min(bx)),round(max(bx)),round(min(by)),round(max(by)))
