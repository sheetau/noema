"""Conservative broad phase for the existing endpoint-on-line predicate."""
import math
from scripts.branch_circle_script import _on_segment
from scripts.circle_contact_script import EPS


def bounds(segment):
    coordinates=tuple(segment[k] for k in ('x1','y1','x2','y2'))
    # Outside this modest numeric range, use the exact legacy predicate only.
    # No coordinate is clamped, rounded, or accepted by this acceleration.
    if any(not math.isfinite(v) or abs(v)>1_000_000 for v in coordinates):return None
    x1,y1,x2,y2=coordinates
    length=math.hypot(x2-x1,y2-y1)
    # Legacy membership uses distance(a,p)+distance(p,b)-distance(a,b)<EPS.
    # Its region is a thin ellipse, NOT a segment expanded by EPS. In this
    # coordinate range, doubling EPS also covers floating arithmetic error.
    tolerance=2*EPS
    padding=math.sqrt(tolerance*(2*length+tolerance))/2
    return (math.nextafter(min(x1,x2)-padding,-math.inf),
            math.nextafter(min(y1,y2)-padding,-math.inf),
            math.nextafter(max(x1,x2)+padding,math.inf),
            math.nextafter(max(y1,y2)+padding,math.inf))


class JunctionIndex:
    """A per-route snapshot of old ink; never a cache of validation outcomes."""
    def __init__(self,obstacles):
        lines=[dict(s) for s in obstacles if s['kind']=='line']
        self.rows=[(s,bounds(s)) for s in lines]

    def joins(self,segments,ends):
        for segment in segments:
            box=bounds(segment)
            current_ends=((segment['x1'],segment['y1']),(segment['x2'],segment['y2']))
            for old,old_box in self.rows:
                if box is not None and old_box is not None and (
                    box[0]>old_box[2] or old_box[0]>box[2] or
                    box[1]>old_box[3] or old_box[1]>box[3]):continue
                for point in current_ends:
                    if _on_segment(point,old) and all(math.dist(point,end)>EPS for end in ends):return True
                for point in ((old['x1'],old['y1']),(old['x2'],old['y2'])):
                    if _on_segment(point,segment) and all(math.dist(point,end)>EPS for end in ends):return True
        return False
