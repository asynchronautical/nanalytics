import shapefile, csv, json, math, os
CAP=20
FIPS={'01':'AL','02':'AK','04':'AZ','05':'AR','06':'CA','08':'CO','09':'CT','10':'DE','12':'FL','13':'GA','15':'HI','16':'ID','17':'IL','18':'IN','19':'IA','20':'KS','21':'KY','22':'LA','23':'ME','24':'MD','25':'MA','26':'MI','27':'MN','28':'MS','29':'MO','30':'MT','31':'NE','32':'NV','33':'NH','34':'NJ','35':'NM','36':'NY','37':'NC','38':'ND','39':'OH','40':'OK','41':'OR','42':'PA','44':'RI','45':'SC','46':'SD','47':'TN','48':'TX','49':'UT','50':'VT','51':'VA','53':'WA','54':'WV','55':'WI','56':'WY'}
rows={r['district']:r for r in csv.DictReader(open('data/districts_2026.csv'))}
# projection: plain lon/lat, with lat scaled so hexes are regular. Measure from first polygon.
cd=shapefile.Reader('data/hex/HexCDv32/HexCDv32.shp')
pts=cd.shape(0).points
xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
# find scale factor by comparing bbox aspect of the whole map in SVG from Downballot is unknown; use cos(mean lat)
allx=[];ally=[]
for s in cd.shapes():
    allx+= [p[0] for p in s.points]; ally+=[p[1] for p in s.points]
meanlat=sum(ally)/len(ally)
K=math.cos(math.radians(meanlat))  # x compression
def proj(p): return (round((p[0]+125)*K*20,2), round((56-p[1])*20,2))
def stage(m): return 1+round(9*min(abs(m),CAP)/CAP)
def rings(shape):
    parts=list(shape.parts)+[len(shape.points)]
    return [[proj(p) for p in shape.points[parts[i]:parts[i+1]]] for i in range(len(parts)-1)]
out=[]; missing=[]
for sh,rec in zip(cd.shapes(),cd.records()):
    g=rec['GEOID']; st=rec['STATEAB']; lab=rec['CDLABEL']
    did=f"{st}-{'AL' if lab in ('0','00','AL',st) else lab.zfill(2)}"
    r=rows.get(did)
    if not r: missing.append(did); continue
    rs=rings(sh)
    # centroid of outer ring (polygon area formula)
    ring=rs[0]; A=0;cx=0;cy=0
    for i in range(len(ring)-1):
        x0,y0=ring[i]; x1,y1=ring[i+1]; c=x0*y1-x1*y0; A+=c; cx+=(x0+x1)*c; cy+=(y0+y1)*c
    A/=2; cx/=(6*A); cy/=(6*A)
    m=int(r['margin24'])
    out.append({'id':did,'geoid':g,'state':rec['STATENAME'],'inc':r['incumbent'],'party':r['party'],'margin':m,'stage':stage(m),'c':[round(cx,1),round(cy,1)],'rings':rs})
print('districts', len(out), 'missing', missing)
st=shapefile.Reader('data/hex/HexStv30/HexSTv30.shp')
states=[{'ab':rec['STATEAB'],'name':rec['STATENAME'],'rings':rings(sh)} for sh,rec in zip(st.shapes(),st.records())]
os.makedirs('public/map',exist_ok=True)
json.dump({'cap':CAP,'source':'Margins: The Downballot, 2024 presidential results on 2026 lines. Hexmap: Daniel Donner for The Downballot, CC BY 4.0 (https://the-db.co/maps).','districts':out,'states':states},open('public/map/data.json','w'),separators=(',',':'))
import collections; print(collections.Counter(d['stage'] for d in out))
bx=[p[0] for d in out for r in d['rings'] for p in r]; by=[p[1] for d in out for r in d['rings'] for p in r]
print('extent', min(bx),max(bx),min(by),max(by), 'K',K)
print(os.path.getsize('public/map/data.json'),'bytes')
