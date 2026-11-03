"""Active circle-pair interpretation after the user's eccentric-ring correction.

Keep the frozen legacy checker intact. Nonconcentric overlaps require the
SMALLER circle's center on the LARGER circle's circumference. A large center
on a small rim does not license an eccentric circle inside the larger ring.
"""
import math

from scripts.balanced_circle_script import geometry_check as legacy_geometry_check, EPS, near

VERSION = 'kant-circle-pairs-smaller-center-1'


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
    return legacy_geometry_check(shapes, paths, invisible)
