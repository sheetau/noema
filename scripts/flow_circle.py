"""Horizontal circle writing with reversible grammar ligatures, not AST trees.

Word spellings and native meanings are unchanged. A grammar ligature combines
the existing family ray and a shorter operation ray. External branches are
local sequential pairs; scope is carried by the public prefix grammar.
"""
from copy import deepcopy
import math

from scripts.visible_syntax import END_GLYPH,KEYWORD_ALIAS
from scripts.visible_syntax_vocabulary import Vocabulary,KEYWORDS,FAMILIES,family_glyph,modifier_glyph
from scripts.visible_sharing import SHARING
from scripts.visible_public_page import PublicWriter,PublicLayoutReader
from scripts.visible_word_forms import _marker,_lexical_tree
from scripts.visible_lexical_script import _glyph,_shape_set,_translate,require
from scripts.visible_syntax_geometry import moved,clean,to_svg,from_svg
from scripts.visible_page import vertical_bounds
from scripts.balanced_circle_script import SMALL,MEDIUM,LARGE,PITCH,MIN_RUN,circle,line,nucleus
from scripts.structural_circle import circle_key,TOL,close
from collections import defaultdict

OPERATIONS=KEYWORDS|SHARING
VERSION='flow-circle-draft-1'


def segment_key(s):
    a,b=(s['x1'],s['y1']),(s['x2'],s['y2'])
    require(math.dist(a,b)>1e-7,'Zero length ink')
    if abs(a[1]-b[1])<1e-7:key=('h',round(a[1],7));ends=(a[0],b[0])
    elif abs(a[0]-b[0])<1e-7:key=('v',round(a[0],7));ends=(a[1],b[1])
    else:
        require(abs(abs(b[0]-a[0])-abs(b[1]-a[1]))<1e-6,'Unknown stroke angle')
        slope=1 if (b[0]-a[0])*(b[1]-a[1])>0 else -1
        key=(slope,round(a[1]-slope*a[0],7));ends=(a[0],b[0])
    return key,tuple(sorted(round(x,7) for x in ends))


class Ink:
    """Union of visible lines at finer precision than the rim tolerance."""
    def __init__(self,shapes):
        self.rows=defaultdict(list)
        for s in shapes:
            if s['kind']=='line':
                key,extent=segment_key(s);self.rows[key].append(extent)
        for key,spans in self.rows.items():
            merged=[]
            for a,b in sorted(spans):
                if merged and a<=merged[-1][1]+1e-7:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
                else:merged.append((a,b))
            self.rows[key]=merged
    def locate(self,s):
        key,(a,b)=segment_key(s)
        keys=[k for k in self.rows if k[0]==key[0] and abs(k[1]-key[1])<2e-7]
        matches=[(k,j,lo,hi,a,b) for k in keys for j,(lo,hi) in enumerate(self.rows[k]) if lo-2e-7<=a and b<=hi+2e-7]
        require(len(matches)<=1,'Ambiguous coincident ink')
        return matches[0] if matches else None
    def contains(self,s):return self.locate(s) is not None
    def remove(self,s):
        found=self.locate(s);require(found is not None,'Missing letter stroke')
        key,j,lo,hi,a,b=found
        self.rows[key][j:j+1]=([(lo,a)] if a-lo>2e-7 else [])+([(b,hi)] if hi-b>2e-7 else [])
    def shapes(self):
        for (direction,intercept),spans in self.rows.items():
            for a,b in spans:
                if direction=='h':yield line((a,intercept),(b,intercept))
                elif direction=='v':yield line((intercept,a),(intercept,b))
                else:yield line((a,direction*a+intercept),(b,direction*b+intercept))


def ligature(key):
    family,direction=OPERATIONS[KEYWORD_ALIAS.get(key,key)]
    g=deepcopy(family_glyph(family))
    if direction is None:
        g['shapes'].append(circle(0.,PITCH,SMALL))
    elif direction!=FAMILIES[family][1]:
        angle=direction*math.pi/4
        p=[(0.,PITCH),(MEDIUM*math.cos(angle),PITCH+MEDIUM*math.sin(angle))]
        g['paths'].append(p);g['shapes'].append(line(*p))
    return g


def margin_glyph(kind,value=0):
    g=nucleus(0.,PITCH,SMALL,None,mode='none')
    directions=[value] if kind=='digit' else [0,2 if kind=='continue' else 6]
    for d in directions:
        p=[(0.,PITCH),(SMALL*math.cos(d*math.pi/4),PITCH+SMALL*math.sin(d*math.pi/4))]
        g['paths'].append(p);g['shapes'].append(line(*p))
    return g


def flow_packet(payload,ordinal,final=False):
    require(type(ordinal) is int and 0<=ordinal<4096,'Flow row budget exceeded')
    head=[]
    for d in oct(ordinal)[2:]:
        g=margin_glyph('digit',int(d));g['fixed_rail']=PITCH;head.append(g)
    end=deepcopy(END_GLYPH);end['fixed_rail']=PITCH
    return head+[end]+payload+[margin_glyph('finish' if final else 'continue')]


class FlowWriter(PublicWriter):
    def __init__(self,vocabulary,*,automatic=False):
        require(automatic is False,'Flow automatic sharing is not enabled')
        super().__init__(vocabulary,automatic=False)

    def keyword(self,key):self.glyphs.append(ligature(key))

    def statement(self,s):
        if s['kind']=='assert':self.expr(s['body'])
        else:super().statement(s)


class FlowReader(PublicLayoutReader):
    def statement(self,depth=0):
        require(depth<=128,'Statement nesting limit')
        forces={tuple((_shape_set(family_glyph(OPERATIONS[k][0])['shapes']),
                       _shape_set(modifier_glyph(OPERATIONS[k][1])['shapes'])))
                for k in ('assert','ask','perform','suppose')}
        if tuple(self.tokens[self.i:self.i+2]) in forces:
            return super().statement(depth)
        if depth==0:self.top_statements.append(self.i)
        self.serial=0
        return dict(kind='assert',body=self.expr())


def alphabet(v):
    """An injective public geometric code; never indexed by document words."""
    result={}
    def add(g, expansion):
        signature=_shape_set(g['shapes'])
        require(signature not in result or result[signature][1]==expansion,'Ligature/word collision')
        result[signature]=(g,expansion)
    for k,(f,d) in OPERATIONS.items():
        add(ligature(k),[_shape_set(family_glyph(f)['shapes']),_shape_set(modifier_glyph(d)['shapes'])])
    plain=[END_GLYPH,*[_glyph(e['form']) for e in v.document()['entries'].values()],
           *[_marker(k,0.) for k in ('compound','proper')],
           modifier_glyph(None),modifier_glyph(0)]
    for g in plain:add(g,[_shape_set(g['shapes'])])
    for d in range(8):add(margin_glyph('digit',d),[('rowdigit',d)])
    for kind in ('continue','finish'):add(margin_glyph(kind),[('rowend',kind)])
    return result


def expanded(glyphs,v):
    table=alphabet(v)
    return [token for g in glyphs for token in table[_shape_set(g['shapes'])][1]]


def path_lines(points):
    return [line(a,b) for a,b in zip(points,points[1:]) if math.dist(a,b)>TOL]


def render_line(glyphs, *, branches=True):
    require(0<len(glyphs)<=64,'Flow line glyph budget exceeded')
    shapes=[];placed=[];previous=None;i=0;forks=0
    def add(g):
        shapes.extend(g['shapes']);placed.append(g)
    def plain(g):return sum(s['kind']=='circle' for s in g['shapes'])==1 and g['radius']<=MEDIUM
    def rail(g):
        if 'fixed_rail' in g:return g['fixed_rail']
        if close(g['radius'],LARGE):return PITCH
        rays=[s for s in g['shapes'] if s['kind']=='line']
        dy=sum(s['y2']-s['y1'] for s in rays)
        return PITCH if abs(dy)<TOL else (0. if dy<0 else 2*PITCH)
    while i<len(glyphs):
        # A bounded two-letter side branch. Its first letter is terminal and
        # its second continues the horizontal line; ties read top then bottom.
        pair=(branches and previous is not None and close(previous['y'],PITCH)
              and i+1<len(glyphs) and plain(glyphs[i]) and plain(glyphs[i+1])
              and 'fixed_rail' not in glyphs[i] and 'fixed_rail' not in glyphs[i+1])
        if pair:
            fork=previous['right']+MIN_RUN
            x=fork+PITCH+MIN_RUN+max(glyphs[i]['radius'],glyphs[i+1]['radius'])
            a=moved(glyphs[i],x,0.)
            b=moved(glyphs[i+1],x,2*PITCH)
            shapes+=path_lines([(previous['right'],PITCH),(fork,PITCH)])
            shapes+=path_lines([(fork,PITCH),(fork+PITCH,0.),(a['left'],0.)])
            shapes+=path_lines([(fork,PITCH),(fork+PITCH,2*PITCH),(b['left'],2*PITCH)])
            add(a);add(b);previous=b;i+=2;forks+=1
            continue
        original=glyphs[i]
        y=rail(original)
        square=previous is not None and (close(previous['radius'],SMALL) or close(original['radius'],SMALL))
        if previous is None:x=20.-original['left']
        else:
            right=max(g['right'] for g in placed[-2:])
            x=right+2*MIN_RUN+(0. if square else abs(y-previous['y']))-original['left']
        g=moved(original,x,y)
        if previous:
            bend=previous['right']+MIN_RUN
            shapes+=path_lines([(previous['right'],previous['y']),(bend,previous['y']),
                                (bend+(0. if square else abs(y-previous['y'])),y),(g['left'],y)])
        add(g);previous=g;i+=1
    return dict(shapes=clean(shapes),width=previous['right']+20.,forks=forks)


def groups_of(circles):
    # A line has at most 64 atoms. No all-document pair enumeration is used.
    groups=[];remaining=set(range(len(circles)))
    while remaining:
        component={remaining.pop()}
        while True:
            added={i for i in remaining if any(math.dist((circles[i]['x'],circles[i]['y']),
                  (circles[j]['x'],circles[j]['y']))<=circles[i]['r']+circles[j]['r']+TOL for j in component)}
            if not added:break
            component.update(added);remaining-=added
        require(len(component)<=3,'Joined unrelated circle letters')
        groups.append([circles[i] for i in component])
    return groups


def recognize_line(shapes,v):
    visible=clean(shapes);circles=[s for s in visible if s['kind']=='circle']
    require(circles,'Missing circles')
    # The page supplies uniform scale; the first visible small numeral sets
    # the local rail origin, even on a row containing no large circles.
    anchor=min(circles,key=lambda s:s['x'])
    require(close(anchor['r'],SMALL),'Missing compact row numeral')
    visible=clean(_translate(visible,-anchor['x'],PITCH-anchor['y']))
    groups=groups_of([s for s in visible if s['kind']=='circle'])
    require(len(groups)<=64,'Flow line glyph budget exceeded')
    table={}
    for signature,(g,tokens) in alphabet(v).items():
        key=circle_key([s for s in g['shapes'] if s['kind']=='circle'],g['x'],g['y'])
        table.setdefault(key,[]).append((g,tokens))
    ink=Ink(visible);read=[]
    for rings in groups:
        main=max(rings,key=lambda c:c['r']);x,y=main['x'],main['y']
        require(any(close(y,r) for r in (0,PITCH,2*PITCH)),'Unknown line rail')
        require(not close(main['r'],LARGE) or close(y,PITCH),'Large circle outside middle rail')
        matches=[]
        for g,tokens in table.get(circle_key(rings,x,y),()):
            strokes=[s for s in _translate(g['shapes'],x-g['x'],y-g['y']) if s['kind']=='line']
            if all(ink.contains(s) for s in strokes):matches.append((len(strokes),strokes,tokens))
        require(matches,'Unknown flow letter')
        count=max(m[0] for m in matches);matches=[m for m in matches if m[0]==count]
        require(len(matches)==1,'Ambiguous flow letter')
        _,strokes,tokens=matches[0]
        for s in strokes:ink.remove(s)
        read.append((x,y,main['r'],len(rings),tokens))
    segments=list(ink.shapes())
    # Reject unmarked crossings before validating the visible connected tree.
    for i,a in enumerate(segments):
        ax,ay=a['x1'],a['y1'];ux,uy=a['x2']-ax,a['y2']-ay
        for b in segments[:i]:
            bx,by=b['x1'],b['y1'];vx,vy=b['x2']-bx,b['y2']-by
            det=ux*vy-uy*vx
            if abs(det)>TOL:
                t=((bx-ax)*vy-(by-ay)*vx)/det;u=((bx-ax)*uy-(by-ay)*ux)/det
                require(not (TOL<t<1-TOL and TOL<u<1-TOL),'Unmarked crossing')
    _lexical_tree(segments,groups)
    read.sort(key=lambda item:(item[0],item[1]))
    columns=[]
    for item in read:
        if columns and close(item[0],columns[-1][0][0]):columns[-1].append(item)
        else:columns.append([item])
    ordered=[]
    for column in columns:
        column.sort(key=lambda item:item[1])
        if len(column)>1:
            require(len(column)==2 and all(item[3]==1 and item[2]<=MEDIUM+TOL for item in column)
                    and close(column[0][1],0.) and close(column[1][1],2*PITCH),
                    'Ambiguous horizontal reading order')
        ordered.extend(column)
    return [t for x,y,r,n,ts in ordered for t in ts]


def compile_page(document,vocabulary=None,*,line_atoms=16,branches=True):
    v=vocabulary or Vocabulary()
    w=FlowWriter(v,automatic=False);canonical=w.document(document)
    require(FlowReader(expanded(w.glyphs,v),v).document()==canonical,'Implicit assertion differs')
    return compile_glyphs(w.glyphs,line_atoms=line_atoms,branches=branches)


def compile_glyphs(glyphs,*,line_atoms=16,branches=True,ordinal_start=0,final=True):
    require(type(line_atoms) is int and 4<=line_atoms<=32,'Invalid line length')
    require(0<len(glyphs)<=2048,'Flow page payload budget exceeded')
    rows=[];shapes=[];bottom=None
    for start in range(0,len(glyphs),line_atoms):
        payload=glyphs[start:start+line_atoms]
        row=render_line(flow_packet(payload,ordinal_start+len(rows),final=final and start+len(payload)==len(glyphs)),branches=branches)
        lo,hi=vertical_bounds(row['shapes']);shift=0. if bottom is None else bottom+64.-lo
        shapes.extend(_translate(row['shapes'],0.,shift));bottom=hi+shift;rows.append(row)
    return dict(shapes=clean(shapes),rows=len(rows),width=max(r['width'] for r in rows),
                atoms=len(glyphs),forks=sum(r['forks'] for r in rows),version=VERSION)


def _read_rows(shapes,vocabulary=None,*,ordinal_start=0,final=True):
    v=vocabulary or Vocabulary();visible=clean(shapes);body=[]
    circles=[s for s in visible if s['kind']=='circle'];require(circles,'Missing page circles')
    # Every row carries small margin circles, including a root-only excerpt.
    scale=SMALL/min(c['r'] for c in circles);visible=clean(_translate(visible,0.,0.,scale))
    def bounds(s):return (s['y']-s['r'],s['y']+s['r']) if s['kind']=='circle' else (min(s['y1'],s['y2']),max(s['y1'],s['y2']))
    rows=[];bottom=None
    for shape in sorted(visible,key=lambda s:bounds(s)[0]):
        lo,hi=bounds(shape)
        if bottom is None or lo>bottom+TOL:
            require(bottom is None or lo-bottom>=32.-TOL,'Insufficient row separation')
            rows.append([])
        rows[-1].append(shape);bottom=hi if bottom is None else max(bottom,hi)
    require(len(rows)<=128,'Flow row budget exceeded')
    for ordinal,row in enumerate(rows):
        tokens=recognize_line(row,v);i=0;digits=[]
        while i<len(tokens) and len(tokens[i])==2 and tokens[i][0]=='rowdigit':
            digits.append(tokens[i][1]);i+=1
        require(1<=len(digits)<=4 and (len(digits)==1 or digits[0]!=0),'Invalid row numeral')
        require(i<len(tokens) and tokens[i]==_shape_set(END_GLYPH['shapes']),'Missing row numeral end')
        number=0
        for d in digits:number=number*8+d
        require(number==ordinal_start+ordinal,'Missing/reordered flow row')
        require(tokens[-1]==('rowend','finish' if final and ordinal==len(rows)-1 else 'continue'),'Wrong flow continuation')
        part=tokens[i+1:-1]
        require(part and not any(len(t)==2 and t[0] in ('rowdigit','rowend') for t in part),'Misplaced row frame')
        body.extend(part)
    return body,len(rows)


def read_payload(shapes,vocabulary=None):return _read_rows(shapes,vocabulary)[0]


def decode_page(shapes,vocabulary=None):
    v=vocabulary or Vocabulary()
    return FlowReader(read_payload(shapes,v),v).document()


def compile_excerpt(statements,vocabulary=None,**layout):
    v=vocabulary or Vocabulary();w=FlowWriter(v)
    for s in statements:w.statement(s)
    return compile_glyphs(w.glyphs,**layout)


def decode_excerpt(shapes,vocabulary=None):
    v=vocabulary or Vocabulary();r=FlowReader(read_payload(shapes,v),v);result=[]
    while r.i<len(r.tokens):result.append(r.statement())
    return result


def compile_pages(document,vocabulary=None,*,line_atoms=32,rows_per_page=8,branches=True):
    require(type(rows_per_page) is int and 1<=rows_per_page<=8,'Invalid rows per page')
    require(type(line_atoms) is int and 4<=line_atoms<=32,'Invalid line length')
    v=vocabulary or Vocabulary();w=FlowWriter(v);canonical=w.document(document)
    require(FlowReader(expanded(w.glyphs,v),v).document()==canonical,'Implicit assertion differs')
    size=line_atoms*rows_per_page
    require(len(w.glyphs)<=min(128*size,8192),'Flow document budget exceeded')
    pages=[]
    for start in range(0,len(w.glyphs),size):
        pages.append(compile_glyphs(w.glyphs[start:start+size],line_atoms=line_atoms,branches=branches,
                     ordinal_start=start//line_atoms,final=start+size>=len(w.glyphs)))
    return pages


def decode_pages(pages,vocabulary=None):
    require(isinstance(pages,list) and 1<=len(pages)<=128,'Invalid page list')
    v=vocabulary or Vocabulary();tokens=[];ordinal=0
    for i,shapes in enumerate(pages):
        part,count=_read_rows(shapes,v,ordinal_start=ordinal,final=i==len(pages)-1)
        tokens.extend(part);ordinal+=count
        require(ordinal<=4096 and len(tokens)<=32768,'Flow document budget exceeded')
    return FlowReader(tokens,v).document()
