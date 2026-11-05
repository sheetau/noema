"""Ink reader acceleration; unchanged v8 matching and rejection rules.

Memoized coverage lives only for this immutable input line list and read call.
It is neither a persistent validation cache nor a semantic judgment.
"""
from collections import defaultdict
import math
from scripts.concept2_codec_v8 import Codec,normalize_scale,merge_lines,covered_line,shape_class
from scripts import concept2_geometry_v5 as g,concept2_composition as v2


def move_ink(shapes,dx=0.,dy=0.):
    # The geometry API contains flat numeric/string primitive dictionaries.
    return [{k:(v+dx if k in ('x','x1','x2') else v+dy if k in ('y','y1','y2') else v)
             for k,v in s.items()} for s in shapes]


class FastInkMixin:
    def read_svg(self,raw,*,fragment=False):
        ink=normalize_scale(g.from_svg(raw))
        rings=[s for s in ink if s['kind']!='line'];lines=merge_lines([s for s in ink if s['kind']=='line'])
        memo={}
        def covered_ink(s):
            key=(s['x1'],s['y1'],s['x2'],s['y2'])
            if key not in memo:memo[key]=covered_line(s,lines)
            return memo[key]
        remaining=set(range(len(rings)));lookup=defaultdict(list)
        for i,s in enumerate(rings):lookup[shape_class(s)].append(i)
        matches=[]
        while remaining:
            xmin=min(rings[i]['x'] for i in remaining)
            front=[i for i in remaining if rings[i]['x']<xmin+1e-3]
            ymin=min(rings[i]['y'] for i in front)
            first=min((i for i in front if rings[i]['y']<ymin+1e-3),key=lambda i:shape_class(rings[i]))
            anchor=rings[first];candidates=[]
            for u in self.recognition[shape_class(anchor)]:
                base=u['recognition_anchor'];dx=anchor['x']-base['x'];dy=anchor['y']-base['y'];covered=set();valid=True
                translated=move_ink(u['shapes'],dx,dy)
                for s in translated:
                    if s['kind']=='line':
                        if not covered_ink(s):valid=False;break
                    else:
                        found=[i for i in lookup[shape_class(s)] if i in remaining and math.hypot(rings[i]['x']-s['x'],rings[i]['y']-s['y'])<1e-3]
                        if len(found)!=1:valid=False;break
                        covered.add(found[0])
                if not valid:continue
                # A maximal glyph cannot skip an intervening circle center.
                xmax=max(s['x'] for s in translated if s['kind']!='line')
                if any(rings[i]['x']<=xmax+1e-3 and i not in covered for i in remaining):continue
                candidates.append((len(covered),sum(s['kind']=='line' for s in translated),u,dx,dy,covered))
            if not candidates:raise ValueError(f'Unrecognized ink at {anchor}; after {[m["unit"]["token"] for m in matches[-4:]]}')
            best=max((x[0],x[1]) for x in candidates);chosen=[x for x in candidates if x[:2]==best]
            if len(chosen)!=1:raise ValueError('Ambiguous maximal glyph: '+str([x[2]['token'] for x in chosen]))
            _,_,u,dx,dy,covered=chosen[0];remaining-=covered
            matches.append(dict(unit=u,x=dx,y=dy))
        # Four lengths are a syntactic repeat operator, never word identities.
        internal=[s for m in matches for s in move_ink(m['unit']['shapes'],m['x'],m['y']) if s['kind']=='line']
        for s in lines:
            if abs(s['x2']-s['x1'])>1e-3:continue
            if covered_line(s,internal):continue
            radius=abs(s['y2']-s['y1'])/2
            n=next((n for n,r in zip(range(2,6),(g.S,g.M,g.L,g.F)) if abs(r-radius)<1e-3),None)
            if n is not None:
                matches.append(dict(unit=self.forms[('repeat',n)],x=s['x1'],y=(s['y1']+s['y2'])/2))
        matches.sort(key=lambda m:m['x']+min(s.get('x',min(s.get('x1',0),s.get('x2',0))) for s in m['unit']['shapes']))
        expected=[];previous=None;previous_right=None;breaks=[]
        for mi,m in enumerate(matches):
            u=m['unit'];x,y=m['x'],m['y'];expected.extend(move_ink(u['shapes'],x,y))
            placed={k:(u[k][0]+x,u[k][1]+y) for k in ('entry','exit','entry_anchor','exit_anchor')}
            if previous and not u.get('silent'):
                options=[]
                for candidate_x,path,_ in g.routes(previous,u,y):
                    if abs(candidate_x-x)<1e-3 and all(covered_ink(s) for s in path):options.append(path)
                if len(options)==1:expected.extend(options[0])
                elif not options and fragment and abs(x+g.bounds(u['shapes'])[0]-previous_right-2*g.M)<1e-3:
                    breaks.append(mi)
                else:raise ValueError(f'Invalid or ambiguous radius connection to {u["token"]}')
            elif previous:
                left=g.bounds(u['shapes'])[0]
                if abs(x+left-previous['exit_anchor'][0]-g.M)>1e-3:raise ValueError('Invalid silent-dot gap')
            previous=placed
            previous_right=max(previous_right or -math.inf,x+g.bounds(u['shapes'])[2])
        expected_lines=[s for s in expected if s['kind']=='line']
        leading=trailing=False;entry_rail=exit_rail=None;continuations=[]
        if fragment:
            last=matches[-1];u=last['unit'];x,y=last['x'],last['y']
            end=(u['exit_anchor'][0]+x+g.M,u['exit_anchor'][1]+y)
            stub=g.line((u['exit'][0]+x,u['exit'][1]+y),end)
            if covered_ink(stub) and not covered_line(stub,expected_lines):
                expected_lines.append(stub);trailing=True;exit_rail=end[1]
                continuations.append(end)
            first=matches[0];u=first['unit'];x,y=first['x'],first['y'];left=x+g.bounds(u['shapes'])[0]
            candidates=[]
            endpoints={(s[a],s[b]) for s in lines for a,b in (('x1','y1'),('x2','y2')) if s[a]<left-1e-3}
            for start in endpoints:
                dummy=dict(exit=start,exit_anchor=start)
                for px,path,_ in g.routes(dummy,u,y):
                    if abs(px-x)<1e-3 and all(covered_ink(s) for s in path):candidates.append((start,path))
            if candidates:
                # Intermediate bends cannot replace the incoming free end.
                xmin=min(start[0] for start,_ in candidates)
                candidates=[item for item in candidates if item[0][0]<xmin+1e-3]
            if len(candidates)>1:raise ValueError('Ambiguous incoming continuation')
            if candidates:
                start,path=candidates[0];expected_lines.extend(path);leading=True;entry_rail=start[1]
                continuations.append(start)
        if any(not covered_line(s,expected_lines) for s in lines):raise ValueError('Unexplained line ink')
        # Validate in the recovered page coordinate system.
        origin=next((m['y'] for m in matches if m['unit']['fixed']),matches[0]['y'])
        g.ink_check(move_ink(ink,dy=-origin),continuations=[(x,y-origin) for x,y in continuations])
        tokens=[m['unit']['token'] for m in matches]
        return dict(native=None if fragment else self.parse(tokens),tokens=tokens,glyphs=len(matches),unique=True,
                    breaks=breaks,leading=leading,trailing=trailing,
                    entry_rail=None if entry_rail is None else round(entry_rail-origin,3),
                    exit_rail=None if exit_rail is None else round(exit_rail-origin,3))


class FastCodec(FastInkMixin,Codec):
    pass
