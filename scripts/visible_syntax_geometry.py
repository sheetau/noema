"""Visible glyph streams, with strict geometry and plain SVG transport."""
from copy import deepcopy
import math
import xml.etree.ElementTree as ET

from scripts.visible_lexical_script import (
    _clean_shapes, _translate, _merge_segments, _connected_words, _take_marks,
    _shape_set, require, to_svg as small_svg, from_svg as small_from_svg,
)
from scripts.visible_word_forms import _lexical_tree
from scripts.balanced_circle_script import LARGE, PITCH, EPS, geometry_check, route

MAX_SHAPES = 4096
MAX_GLYPHS = 768


def clean(shapes):
    require(isinstance(shapes, list) and 0 < len(shapes) <= MAX_SHAPES,
            'Visible primitive budget exceeded')
    return [s for i in range(0, len(shapes), 256) for s in _clean_shapes(shapes[i:i+256])]


def moved(glyph, x, y):
    g = deepcopy(glyph)
    dx, dy = x-g['x'], y-g['y']
    g['shapes'] = _translate(g['shapes'], dx, dy)
    g['paths'] = [[(a+dx, b+dy) for a,b in p] for p in g['paths']]
    for port in ('entry', 'exit'):
        g[port]['x'] += dx
        g[port]['y'] += dy
    g.update(x=x, y=y, left=g['left']+dx, right=g['right']+dx)
    return g


def render(glyphs, *, first_rail=0, gap=80.):
    require(glyphs and len(glyphs) <= MAX_GLYPHS, 'Glyph budget exceeded')
    require(type(first_rail) is int and first_rail in (0,2), 'Invalid rail')
    require(type(gap) in (int,float) and math.isfinite(gap) and gap >= 64., 'Invalid spacing')
    shapes, paths, previous, moment = [], [], None, 0.
    for original in glyphs:
        preferred = 0 if moment > 0 else 2 if moment < 0 else first_rail
        rails = [1] if original['radius'] == LARGE else [preferred, 2-preferred, 1]
        found = None
        for rail in rails:
            x = 50. if previous is None else previous['right']+gap-original['left']
            g = moved(original, x, rail*PITCH)
            lines, joins = [], []
            if previous:
                # Monotone x placement makes more distant glyphs irrelevant
                # to this connection. The complete geometry is checked below.
                local = previous['shapes'] + g['shapes']
                joined = route(previous['exit'], g['entry'],
                               [s for s in local if s['kind']=='circle'], obstacles=local)
                if joined is None:
                    continue
                path, lines = joined
                joins = [path]
            try:
                geometry_check((previous['shapes'] if previous else [])+g['shapes']+lines,
                               (previous['paths'] if previous else [])+g['paths']+joins)
            except ValueError:
                continue
            found = g, lines, joins
            break
        require(found is not None, 'No legal glyph layout')
        g, lines, joins = found
        shapes += g['shapes']+lines
        paths += g['paths']+joins
        previous = g
        moment += sum(s['r']**2*(s['y']-PITCH) for s in g['shapes'] if s['kind']=='circle')
    clean(shapes)
    geometry_check(shapes, paths)
    return dict(shapes=shapes, width=previous['right']+12.)


def recognize(shapes):
    visible = clean(shapes)
    circles = [s for s in visible if s['kind']=='circle']
    require(circles, 'Missing circles')
    anchor = max(circles, key=lambda c:c['r'])
    scale = LARGE/anchor['r']
    visible = _translate(visible, -anchor['x']*scale, PITCH-anchor['y']*scale, scale)
    circles = [s for s in visible if s['kind']=='circle']
    segments = _merge_segments([s for s in visible if s['kind']=='line'])
    geometry_check(circles+segments,
                   [[(s['x1'],s['y1']),(s['x2'],s['y2'])] for s in segments])
    groups = _connected_words(circles)
    require(len(groups) <= MAX_GLYPHS, 'Glyph budget exceeded')
    tokens, remaining = [], segments
    for rings in groups:
        main = max(rings, key=lambda c:c['r'])
        marks, remaining = _take_marks(main, remaining)
        local = _translate(rings+marks, -main['x'], PITCH-main['y'])
        tokens.append((main['x'], _shape_set(local)))
    _lexical_tree(remaining, groups)
    tokens.sort()
    require(all(b[0]-a[0]>EPS for a,b in zip(tokens,tokens[1:])), 'Ambiguous glyph order')
    return [s for x,s in tokens]


def to_svg(shapes):
    visible = clean(shapes)
    chunks = [ET.fromstring(small_svg(visible[i:i+256])) for i in range(0,len(visible),256)]
    boxes = [[float(v) for v in c.get('viewBox').split()] for c in chunks]
    x,y = min(b[0] for b in boxes), min(b[1] for b in boxes)
    w,h = max(b[0]+b[2] for b in boxes)-x, max(b[1]+b[3] for b in boxes)-y
    root = chunks[0]
    root.set('viewBox', ' '.join(f'{v:.9f}' for v in (x,y,w,h)))
    for c in chunks[1:]: root.extend(list(c))
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    return ET.tostring(root, encoding='unicode')+'\n'


def from_svg(text):
    require(isinstance(text,str) and len(text)<=2000000 and '<!' not in text and '<?' not in text,
            'Invalid SVG input')
    root = ET.fromstring(text)
    children = list(root)
    require(0 < len(children) <= MAX_SHAPES, 'Invalid SVG size')
    result = []
    for i in range(0,len(children),256):
        chunk = ET.Element(root.tag, root.attrib)
        chunk.text = root.text
        chunk.extend(children[i:i+256])
        result.extend(small_from_svg(ET.tostring(chunk, encoding='unicode')))
    return clean(result)
