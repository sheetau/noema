"""Active circle-pair interpretation after the user's eccentric-ring correction.

Keep the frozen legacy checker intact. Nonconcentric overlaps require the
SMALLER circle's center on the LARGER circle's circumference. A large center
on a small rim does not license an eccentric circle inside the larger ring.
"""
import math
from collections import defaultdict

from scripts.balanced_circle_script import geometry_check as legacy_geometry_check, EPS, near, line

VERSION = 'kant-circle-pairs-smaller-center-2-normalized-lines'


def merged_lines(shapes):
    """Union collinear ink before both placement validation and reading."""
    rows=defaultdict(list)
    for s in shapes:
        if s['kind']!='line':continue
        ax,ay,bx,by=(s[k] for k in ('x1','y1','x2','y2'))
        if near(ay,by):key=('h',round(ay,9));span=(ax,bx)
        elif near(ax,bx):key=('v',round(ax,9));span=(ay,by)
        elif near(abs(bx-ax),abs(by-ay)):
            slope=1 if (bx-ax)*(by-ay)>0 else -1
            key=(str(slope),round(ay-slope*ax,9));span=(ax,bx)
        else:raise ValueError('Line direction')
        rows[key].append(tuple(sorted(span)))
    answer=[]
    for (direction,offset),spans in sorted(rows.items()):
        joined=[]
        for a,b in sorted(spans):
            if joined and a<=joined[-1][1]+EPS:joined[-1]=(joined[-1][0],max(b,joined[-1][1]))
            else:joined.append((a,b))
        for a,b in joined:
            if direction=='h':ends=((a,offset),(b,offset))
            elif direction=='v':ends=((offset,a),(offset,b))
            else:ends=((a,int(direction)*a+offset),(b,int(direction)*b+offset))
            answer.append(line(*ends))
    return answer


def check_circle_pairs(shapes):
    circles = [s for s in shapes if s['kind'] == 'circle']
    for i, a in enumerate(circles):
        for b in circles[:i]:
            distance = math.dist((a['x'], a['y']), (b['x'], b['y']))
            if distance > a['r']+b['r']+EPS or near(distance, a['r']+b['r']):
                continue  # Separation/tangency still obey the legacy rules.
            if near(distance, 0):
                continue
            larger = max(a['r'], b['r'])
            if near(a['r'], b['r']) or not near(distance, larger):
                raise ValueError('Nonconcentric overlap requires the smaller center on the larger rim')
    return True


def geometry_check(shapes, paths, invisible=()):
    check_circle_pairs(shapes)
    if any(s['kind'] not in ('circle','line') for s in shapes):raise ValueError('Unknown shape')
    normalized=[s for s in shapes if s['kind']=='circle']+merged_lines(shapes)
    return legacy_geometry_check(normalized, paths, invisible)
