"""Concept 2 appearance experiment, with a lossless public-spelling syntax tape.

The tape check is deliberately NOT called visible decoding. SVGs contain only
ink primitives. This module has no dependency on the old placement search.
"""
from copy import deepcopy
from collections import Counter
import math
import xml.etree.ElementTree as ET

U = 10.0
S, M, L, F = U, (1+math.sqrt(2))*U, (1+2*math.sqrt(2))*U, (1+3*math.sqrt(2))*U
P = (2+math.sqrt(2))*U
PEN = 1.65
EPS = 1e-5


def circle(r, x=0., y=0.):
    return dict(kind='arc', x=x, y=y, r=r, a=0., b=360.)


def arc(r, a, b, x=0., y=0.):
    return dict(kind='arc', x=x, y=y, r=r, a=float(a), b=float(b))


def line(a, b):
    return dict(kind='line', x1=a[0], y1=a[1], x2=b[0], y2=b[1])


def move(shapes, dx=0., dy=0.):
    out = deepcopy(shapes)
    for s in out:
        for key in ('x', 'x1', 'x2'):
            if key in s: s[key] += dx
        for key in ('y', 'y1', 'y2'):
            if key in s: s[key] += dy
    return out


def on_arc(s, angle):
    return any(s['a']-EPS <= angle+360*k <= s['b']+EPS for k in range(-3, 4))


def point(s, angle):
    t = math.radians(angle)
    return s['x']+s['r']*math.cos(t), s['y']+s['r']*math.sin(t)


def bounds(shapes):
    points = []
    for s in shapes:
        if s['kind'] == 'line':
            points.extend(((s['x1'],s['y1']), (s['x2'],s['y2'])))
        else:
            points.extend(point(s,a) for a in (s['a'],s['b'],0,90,180,270) if a in (s['a'],s['b']) or on_arc(s,a))
    return min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)


def support_bounds(shapes):
    return bounds([circle(s['r'],s['x'],s['y']) if s['kind']=='arc' else s for s in shapes])


def orthogonal_pair(big, small, mode='cross', side=-1):
    """Both centers are on the middle rail; actual arcs implement clipping."""
    d = math.hypot(big, small)
    beta = math.degrees(math.atan2(small, big))
    phi = 180 if side < 0 else 0
    if mode == 'cross': outer = circle(big)
    elif mode == 'cut': outer = arc(big, phi+beta, phi+360-beta)
    elif mode == 'eclipse': outer = arc(big, phi-beta, phi+beta)
    else: raise ValueError(mode)
    return [outer, circle(small, side*d)]


# Public root outlines. These are explicit spelling choices, never generated
# from a declaration number, a source sentence, a hash or random values.
ROOT_FORMS = {
    'aki': [circle(S)],
    'nao': [circle(S), arc(M,180,360)],
    'home': [arc(M,45,315), circle(S)],
    'book': [arc(M,-45,45),arc(M,135,225)],
    'above': [arc(M,180,360)],
    'round': [circle(M)],
    'inside': [circle(M),circle(S)],
    'give': [arc(L,45,315),arc(M,-90,90)],
    'fruit': [arc(M,0,270),circle(S)],
    'treeone': [circle(M),arc(L,225,315)],
    'birdone': [circle(M),arc(L,45,135)],
    'bird': [arc(M,0,180),arc(M,225,270)],
    'rain': [arc(M,180,360),arc(L,45,135)],
    'town': [circle(L),arc(M,90,270)],
    'red': [arc(M,90,270),circle(S)],
    'fly': [arc(M,-90,90),circle(S)],
    'candidatepossible': [arc(L,90,270),arc(M,-90,90),circle(S)],
    'candidatenecessary': [circle(L),arc(M,0,180)],
    'candidateexcluded': [arc(L,135,405),circle(S)],
    'candidatecontingent': [arc(L,-45,225),circle(S)],
    'candidateexists': [arc(L,90,270),circle(M)],
    'candidateempty': [arc(L,-90,90),circle(M)],
    'necessaryactual': [circle(L),arc(M,180,360)],
    'assessmentdecisive': [arc(M,-45,225),arc(L,225,315)],
    'assessmentvalid': [arc(M,135,405),arc(L,45,135)],
    'methodpossible': [arc(L,-45,45),arc(L,135,225),circle(S)],
    'methodguaranteed': [circle(L),arc(M,45,135),arc(M,225,315)],
    'assessedability': orthogonal_pair(M,S,'cut',1),
    'assessedinability': orthogonal_pair(M,S,'cut',-1),
    'methodsassessable': [arc(M,-45,45),arc(M,135,225),circle(S)],
}

# Reusable spelling ligatures, not new words or new source meanings. Each has
# an explicit expansion into the already published roots, in the same order.
LIGATURES = {
    ('book','home','round'): orthogonal_pair(L,M,'cut',-1),
    ('book','home','above'): orthogonal_pair(L,M,'eclipse',-1),
    ('book','home'): orthogonal_pair(L,S,'cut',-1),
    ('home','book'): [arc(L,-90,90),arc(M,90,270),circle(S)],
    ('book','aki'): [arc(M,-45,45),arc(M,135,225),circle(S,P,P),
        line((M/math.sqrt(2),M/math.sqrt(2)),(P-S/math.sqrt(2),P-S/math.sqrt(2)))],
    ('above','book'): [arc(M,180,360),arc(L,0,180)],
    ('give','book'): orthogonal_pair(L,M,'cross',1),
    ('book','inside'): [arc(L,135,405),arc(M,-45,225)],
    ('book','methodpossible'): [arc(L,-45,225),arc(M,135,405)],
    ('book','fruit'): orthogonal_pair(M,S,'cross',1),
    ('aki','round'): [circle(M),circle(S,P,-P),
        line((M/math.sqrt(2),-M/math.sqrt(2)),(P-S/math.sqrt(2),-P+S/math.sqrt(2)))],
    ('above','round','treeone'): [circle(M),circle(M,P,-P),circle(S,2*P,P),
        line((M/math.sqrt(2),M/math.sqrt(2)),(P,P)),line((P,P),(2*P-S,P))],
}

# Empty inner small circle is a real unfilled role. It is not a dot or an
# accidental eccentric inner circle. Binding use is separately identified.
OPERATORS = {
    'not': [arc(M,45,315),arc(L,90,270)],
    'and': [circle(S,0,-P),circle(M)],
    'or': [circle(M),circle(S,0,P)],
    'equal': [circle(S,0,-P),circle(S,0,P),line((0,-P+S),(0,P-S))],
    'implies': [arc(M,90,270),circle(S),arc(L,-45,45)],
    'quote-open': [arc(F,135,225),arc(M,135,225),circle(S)],
    'quote-close': [arc(F,-45,45),arc(M,-45,45),circle(S)],
    'group-open': [arc(F,135,225),circle(S)],
    'group-close': [arc(F,-45,45),circle(S)],
    'lambda': [arc(M,0,270),circle(S),arc(L,225,315)],
    'forall': [arc(M,90,360),circle(S),arc(L,45,135)],
    'variable': [arc(M,90,270),circle(S),arc(L,135,225)],
    'evaluate': [arc(L,90,270),arc(M,-90,90)],
    'function_ref': [arc(M,135,405),arc(L,225,315)],
    'quoted_ref': [arc(F,135,225),arc(M,180,360),circle(S)],
    'quoted_value': [arc(F,135,225),arc(M,0,180),circle(S)],
    'quotation-rank': [arc(M,0,90),arc(M,180,270),arc(L,90,180),arc(L,270,360),circle(S)],
}
# Equality has middle-rail ports on a small circle; it breaks the vertical line
# into two radial segments and avoids a forbidden diameter.
OPERATORS['equal'] = [circle(S,0,-P),circle(S),circle(S,0,P),
    line((0,-P+S),(0,-S)),line((0,S),(0,P-S))]


def root_name(symbol):
    if not symbol.startswith('wr') or not symbol.endswith('zq'): raise ValueError(symbol)
    return symbol[2:-2].replace('zz','z')


def root_symbol(name): return 'wr'+name.replace('z','zz')+'zq'


def spell(parts):
    names = tuple(map(root_name, parts)); result = []; i = 0
    while i < len(names):
        matches = [k for k in LIGATURES if names[i:i+len(k)] == k]
        key = max(matches, key=len) if matches else (names[i],)
        shape = LIGATURES[key] if key in LIGATURES else ROOT_FORMS[key[0]]
        result.append(dict(key='/'.join(key), expansion=list(map(root_symbol,key)), shapes=deepcopy(shape)))
        i += len(key)
    assert [p for r in result for p in r['expansion']] == list(parts)
    return result


PRECEDENCE = {'implies':1,'or':2,'and':3,'equal':4}


def to_tape(statement, spelling):
    if statement['kind'] != 'assert': raise ValueError('Preview supports assertions only')
    tape = []
    def emit(kind, **kw): tape.append(dict(kind=kind,**kw))
    def expression(node, level=0):
        k = node['kind']
        if k in PRECEDENCE:
            prec = PRECEDENCE[k]; grouped = prec < level
            if grouped: emit('group-open')
            expression(node['arguments'][0],prec+1);emit(k);expression(node['arguments'][1],prec)
            if grouped: emit('group-close')
        elif k in ('call','function_ref'):
            emit('word',parts=list(spelling[node['symbol']]),mode=k)
            if k == 'call':
                for a in node['arguments']: expression(a,5)
        elif k == 'quote':
            body=node['body']
            rank={} if 'rank' not in node else dict(rank=node['rank'])
            if rank: assert type(rank['rank']) is int and 1<=rank['rank']<=3
            if body['kind']=='function_ref' or body['kind']=='call' and not body['arguments']:
                emit('word',parts=list(spelling[body['symbol']]),mode='quoted_ref' if body['kind']=='function_ref' else 'quoted_value',**rank)
            else: emit('quote-open',**rank);expression(body);emit('quote-close')
        elif k == 'not': emit(k);expression(node['arguments'][0],5)
        elif k in ('lambda','forall'):
            # Explicitly bounded trial fragment; don't silently drop new types,
            # multiple binders or identifiers if a future source changes.
            assert (node['parameters']==[dict(name='va',sort='individual')] if k=='lambda'
                    else node['variable']=='va' and node['sort']=='individual')
            emit(k);emit('group-open');expression(node['body']);emit('group-close')
        elif k == 'variable':
            assert node['name']=='va';emit(k)
        elif k == 'evaluate':
            emit(k);expression(node['content'],5);expression(node['situation'],5)
        else: raise ValueError('Unimplemented syntax: '+k)
    expression(statement['body'])
    return tape


def from_tape(tape, declarations, spellings):
    i=0
    def expr(level=0):
        nonlocal i
        t=tape[i];i+=1;k=t['kind']
        if k=='word':
            symbol=spellings[tuple(t['parts'])];mode=t['mode']
            if mode in ('function_ref','quoted_ref'): node=dict(kind='function_ref',symbol=symbol)
            else:
                n=len(declarations[symbol]['parameters']); args=[expr(5) for _ in range(n)]
                node=dict(kind='call',symbol=symbol,arguments=args)
            if mode.startswith('quoted_'):
                node=dict(kind='quote',body=node)
                if 'rank' in t:node['rank']=t['rank']
        elif k in ('group-open','quote-open'):
            node=expr();assert tape[i]['kind']==('group-close' if k=='group-open' else 'quote-close');i+=1
            if k=='quote-open':
                node=dict(kind='quote',body=node)
                if 'rank' in t:node['rank']=t['rank']
        elif k=='not':node=dict(kind=k,arguments=[expr(5)])
        elif k in ('lambda','forall'):
            body=expr(5)
            node=(dict(kind=k,parameters=[dict(name='va',sort='individual')],body=body) if k=='lambda'
                  else dict(kind=k,variable='va',sort='individual',body=body))
        elif k=='variable':node=dict(kind=k,name='va')
        elif k=='evaluate':node=dict(kind=k,content=expr(5),situation=expr(5))
        else:raise ValueError('Unexpected tape token '+k)
        while i<len(tape) and PRECEDENCE.get(tape[i]['kind'],-1)>=level:
            op=tape[i]['kind'];i+=1;node=dict(kind=op,arguments=[node,expr(PRECEDENCE[op])])
        return node
    out=dict(kind='assert',body=expr());assert i==len(tape)
    return out


def horizontal_ports(shapes):
    points=[]
    for s in shapes:
        if s['kind']=='arc' and abs(s['y'])<EPS:
            for a in (0,180):
                if on_arc(s,a):points.append(point(s,a))
    if len(points)<2:raise ValueError('No horizontal ports')
    return min(points), max(points)


def mass(shapes):
    return sum(s['r']*(s['b']-s['a']) for s in shapes if s['kind']=='arc')


def units(tape):
    result=[]
    for ti,t in enumerate(tape):
        if t['kind']=='word':
            parts=spell(t['parts'])
            if t['mode']!='call':
                result.append(dict(key=t['mode'],shapes=deepcopy(OPERATORS[t['mode']]),token=ti,part=-1,word_start=True))
            for _ in range(t.get('rank',0)):
                result.append(dict(key='quotation-rank',shapes=deepcopy(OPERATORS['quotation-rank']),token=ti,part=-1,word_start=False))
            for j,part in enumerate(parts):
                result.append(dict(part,token=ti,part=j,word_start=j==0))
        else:result.append(dict(key=t['kind'],shapes=deepcopy(OPERATORS[t['kind']]),token=ti,part=0,word_start=True))
    return result


def compile_tape(tape):
    placed=[];shapes=[];links=[];moment=0.;total=0.;previous=None
    for unit in units(tape):
        local=unit['shapes'];left,top,right,bottom=support_bounds(local);entry,exit=horizontal_ports(local)
        # Large circles stay on the middle rail. Multi-rail built-in ligatures
        # are also fixed, with their unequal ink balanced by following forms.
        fixed=any(s['kind']=='arc' and (s['r']>=L-EPS or abs(s['y'])>EPS) for s in local)
        candidates=[]
        for y in ([0.] if fixed else [-P,0.,P]):
            if previous is None:
                x=-left;poly=[];cost=abs(y)*.15
            else:
                last=previous;dy=y-last['exit'][1]
                start=last['exit'];bend=last['right']+U
                x=bend+abs(dy)+U-left
                end=(x+entry[0],y)
                poly=[start,(bend,start[1]),(bend+abs(dy),y),end]
                poly=[v for j,v in enumerate(poly) if j==0 or math.dist(v,poly[j-1])>EPS]
                cost=(x+right-last['right'])*.15
                if abs(dy)>P+EPS:cost+=12
                if abs(dy)<EPS and len(placed)>1 and abs(placed[-2]['rail']-y)<EPS:cost+=14
            ink=mass(local)
            own=sum(s['r']*(s['b']-s['a'])*(s['y']+y) for s in local if s['kind']=='arc')
            imbalance=abs(moment+own)/(max(total+ink,1)*P)
            cost+=imbalance*50
            # Content with no need for a second rail prefers the middle.
            if previous is None:cost+=abs(y)*.4
            candidates.append((cost,x,y,poly,ink,own))
        _,x,y,poly,ink,own=min(candidates,key=lambda v:v[:3])
        offset=len(shapes);shapes.extend(move(local,x,y))
        newlinks=[line(a,b) for a,b in zip(poly,poly[1:])]
        shapes.extend(newlinks);links.append(poly)
        previous=dict(unit,shapes=move(local,x,y),x=x,rail=y,left=x+left,right=x+right,
                      entry=(x+entry[0],y),exit=(x+exit[0],y),shape_start=offset)
        placed.append(previous);moment+=own;total+=ink
    return dict(shapes=shapes,placed=placed,links=links,width=bounds(shapes)[2],
                balance=moment/(total*P) if total else 0.)


def validate_geometry(shapes):
    """Actual drawn arcs/segments: radial incidence and legal circle relations.

    This is a geometry check, not a parser. In particular it does not prove
    unique decomposition of disconnected forms or word/scope boundaries.
    """
    arcs=[s for s in shapes if s['kind']=='arc'];lines=[s for s in shapes if s['kind']=='line']
    for c in arcs:
        if min(abs(c['r']-r) for r in (S,M,L,F))>EPS:raise ValueError('Unknown radius')
        if c['r']>=L-EPS and abs(c['y'])>EPS:raise ValueError('Large circle off middle rail')
        if abs(c['r']-S)<EPS and abs(c['b']-c['a']-360)>EPS:raise ValueError('Small partial circle')
    supports={tuple(round(c[k],7) for k in ('x','y','r')):c for c in arcs}
    cc=list(supports.values())
    for i,c in enumerate(cc):
        for d in cc[:i]:
            distance=math.hypot(c['x']-d['x'],c['y']-d['y']);r,R=sorted((c['r'],d['r']))
            if distance<EPS:continue
            if distance>r+R+EPS:continue
            if distance<abs(R-r)-EPS:raise ValueError('Eccentric containment')
            if abs(distance-r-R)<EPS:
                dx=abs(c['x']-d['x']);dy=abs(c['y']-d['y'])
                if not (abs(r-S)<EPS and abs(R-M)<EPS and dx<EPS and abs(dy-P)<EPS or
                        abs(r-M)<EPS and abs(R-M)<EPS and abs(dx-P)<EPS and abs(dy-P)<EPS):
                    raise ValueError('Unapproved tangency')
            elif abs(distance*distance-r*r-R*R)>EPS*max(distance,1):raise ValueError(f'Nonorthogonal circles: {c}, {d}')
    for s in lines:
        ax,ay=s['x1'],s['y1'];dx,dy=s['x2']-ax,s['y2']-ay
        if not (abs(dx)<EPS or abs(dy)<EPS or abs(abs(dx)-abs(dy))<EPS):raise ValueError('Non-45-degree line')
        den=dx*dx+dy*dy
        if den<EPS:raise ValueError('Zero-length line')
        for c in arcs:
            vx,vy=ax-c['x'],ay-c['y'];b=2*(vx*dx+vy*dy);q=vx*vx+vy*vy-c['r']**2;disc=b*b-4*den*q
            if disc < -EPS:continue
            for t in ((-b-math.sqrt(max(0,disc)))/(2*den),(-b+math.sqrt(max(0,disc)))/(2*den)):
                if not -EPS<=t<=1+EPS:continue
                px,py=vx+t*dx,vy+t*dy
                if on_arc(c,math.degrees(math.atan2(py,px))) and abs(px*dy-py*dx)>EPS*max(den,1):
                    raise ValueError('Nonradial line/arc intersection')
    return dict(arcs=len(arcs),segments=len(lines),circle_relations='checked',radial_incidence='checked')


def svg(shapes, *, width=None, height=None, pad=16, pen=PEN):
    left,top,right,bottom=bounds(shapes)
    if width is None:width=right-left+2*pad;height=bottom-top+2*pad;shapes=move(shapes,pad-left,pad-top)
    elements=[]
    for s in shapes:
        if s['kind']=='line':elements.append(f'<line x1="{s["x1"]:.7f}" y1="{s["y1"]:.7f}" x2="{s["x2"]:.7f}" y2="{s["y2"]:.7f}"/>')
        elif abs(s['b']-s['a']-360)<EPS:elements.append(f'<circle cx="{s["x"]:.7f}" cy="{s["y"]:.7f}" r="{s["r"]:.7f}"/>')
        else:
            a=point(s,s['a']);b=point(s,s['b']);large=int(s['b']-s['a']>180)
            elements.append(f'<path d="M {a[0]:.7f} {a[1]:.7f} A {s["r"]:.7f} {s["r"]:.7f} 0 {large} 1 {b[0]:.7f} {b[1]:.7f}"/>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.4f}" height="{height:.4f}" viewBox="0 0 {width:.4f} {height:.4f}"><g fill="none" stroke="#203438" stroke-width="{pen}" stroke-linecap="round" stroke-linejoin="round">'+''.join(elements)+'</g></svg>'


def png(shapes,path,width,height,scale=1,pen=PEN):
    from PIL import Image,ImageDraw
    ss=3;image=Image.new('RGB',(round(width*ss),round(height*ss)),'#fffffe');draw=ImageDraw.Draw(image)
    def p(x,y):return x*ss*scale,y*ss*scale
    for s in shapes:
        if s['kind']=='line':points=[p(s['x1'],s['y1']),p(s['x2'],s['y2'])]
        else:
            steps=max(8,int((s['b']-s['a'])*s['r']*scale/60))
            points=[p(*point(s,s['a']+(s['b']-s['a'])*i/steps)) for i in range(steps+1)]
        draw.line(points,fill='#203438',width=max(1,round(pen*ss*scale)),joint='curve')
    image.resize((round(width),round(height)),Image.Resampling.LANCZOS).save(path)


def from_svg(raw):
    """Read only circle/line/arc ink; no groups, IDs, titles or source metadata."""
    result=[]
    for e in ET.fromstring(raw).iter():
        tag=e.tag.split('}')[-1]
        if tag=='circle':result.append(circle(float(e.attrib['r']),float(e.attrib['cx']),float(e.attrib['cy'])))
        elif tag=='line':result.append(dict(kind='line',**{k:float(e.attrib[k]) for k in ('x1','y1','x2','y2')}))
        elif tag=='path':
            t=e.attrib['d'].split();assert t[0]=='M' and t[3]=='A' and len(t)==11
            ax,ay,r,ry,rotation,large,sweep,bx,by=map(float,[*t[1:3],*t[4:]])
            assert abs(r-ry)<EPS and rotation==0 and sweep==1
            dx,dy=bx-ax,by-ay;length=math.hypot(dx,dy)
            h=math.sqrt(max(0,r*r-length*length/4))
            for sign in (1,-1):
                cx=(ax+bx)/2-sign*dy*h/length;cy=(ay+by)/2+sign*dx*h/length
                start=math.degrees(math.atan2(ay-cy,ax-cx));end=math.degrees(math.atan2(by-cy,bx-cx))
                span=(end-start)%360
                if abs(span-180)<1e-3 or (span>180)==bool(large):
                    result.append(arc(r,start,start+span,cx,cy));break
            else:raise ValueError('Invalid SVG arc')
        elif tag not in ('svg','g'):raise ValueError('Unexpected SVG content '+tag)
    return result


def fold_paragraph(drawings, max_width=2200.):
    allshapes=[];cuts=[];offset=0.
    for si,d in enumerate(drawings):
        allshapes.extend(move(d['shapes'],offset))
        for poly in d['links']:
            if len(poly)<2:continue
            a,b=poly[-2:]
            if abs(a[1]-b[1])<EPS and b[0]-a[0]>U*.9:
                cuts.append((offset+(a[0]+b[0])/2,a[1]))
        offset+=d['width']
        if si<len(drawings)-1:
            cuts.append((offset+2*U,None));offset+=4*U
    cuts.append((offset,None));start=0.;start_rail=None;rows=[]
    while start < offset-EPS:
        valid=[c for c in cuts if start+EPS<c[0]<=start+max_width]
        if not valid:raise ValueError('An atomic form is wider than a row')
        end,end_rail=max(valid)
        row=[]
        for s in allshapes:
            a,_,b,_=bounds([s])
            if b<start-EPS or a>end+EPS:continue
            if s['kind']=='arc':
                if a<start-EPS or b>end+EPS:raise ValueError('Fold cuts a circle')
                row.extend(move([s],-start))
            else:
                if a<start-EPS or b>end+EPS:
                    if abs(s['y1']-s['y2'])>EPS:raise ValueError('Fold cuts a nonhorizontal stroke')
                    if min(b,end)-max(a,start)>EPS:row.append(line((max(a,start)-start,s['y1']),(min(b,end)-start,s['y2'])))
                else:row.extend(move([s],-start))
        # Continuation ends remain on the identical rail on the following row.
        rows.append(dict(shapes=row,width=end-start,entry_rail=start_rail,exit_rail=end_rail))
        start=end;start_rail=end_rail
    for a,b in zip(rows,rows[1:]):assert a['exit_rail']==b['entry_rail']
    return rows
