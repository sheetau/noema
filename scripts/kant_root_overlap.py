"""Overlap unchanged single-circle roots inside one lexical word."""
from copy import deepcopy
from functools import lru_cache
import math

TAG = 'root-overlap'


def pair_token(first, second):
    return (TAG, first, second)


@lru_cache(maxsize=256)
def _templates(first, second):
    from scripts import kant_public_fragment as p
    if first not in p.root_words() or second not in p.root_words():
        return ()
    a, b = p.forms(first)[0], p.forms(second)[0]
    rings = [[s for s in g['shapes'] if s['kind']=='circle'] for g in (a,b)]
    if any(len(cs)!=1 for cs in rings):
        return ()
    if {a['radius'],b['radius']} != {p.LARGE,p.MEDIUM}:
        return ()
    large_first = p.near(a['radius'],p.LARGE)
    large_token, small_token = (first,second) if large_first else (second,first)
    dx = math.sqrt(p.LARGE**2-p.PITCH**2) * (1 if large_first else -1)
    result = []
    for dy in (-p.PITCH,p.PITCH):
        large = p.forms(large_token,0.,p.PITCH)[0]
        small = p.forms(small_token,dx,p.PITCH+dy)[0]
        shapes = large['shapes']+small['shapes']
        paths = large['paths']+small['paths']
        try:
            p.geometry_check(shapes,paths)
            geometry = p.read_geometry(shapes)
        except ValueError:
            continue
        # Read the individual roots again: a neighbor must not alter either ray.
        ordered = sorted(range(len(geometry['circles'])),key=lambda i:geometry['circles'][i]['center'][0])
        recovered = tuple(p.table().get(p.feature(geometry,[i])) for i in ordered)
        if recovered != (first,second):
            continue
        if p.feature(geometry,ordered) in p.table():
            raise ValueError('Overlapping roots collide with a reserved public shape')
        glyph = deepcopy(large)
        glyph.update(shapes=shapes,paths=paths,
            left=min(c['x']-c['r'] for c in shapes if c['kind']=='circle'),
            right=max(c['x']+c['r'] for c in shapes if c['kind']=='circle'))
        result.append(glyph)
    return tuple(result)


def forms(token, x, y):
    from scripts import kant_public_fragment as p
    from scripts.visible_syntax_geometry import moved
    if not isinstance(token,tuple) or len(token)!=3 or token[0]!=TAG:
        raise ValueError('Unknown composite root token')
    if not p.near(y,p.PITCH):
        return []
    return [moved(g,x,y) for g in _templates(token[1],token[2])]


def nucleus_tokens(geometry,nucleus):
    from scripts import kant_public_fragment as p
    ids = nucleus['circles']
    known = p.table().get(p.feature(geometry,ids))
    if known is not None:
        return (known,), (ids,)
    if len(ids)!=2:
        raise ValueError('Unknown visible public word')
    circles = geometry['circles']
    a,b = sorted(ids,key=lambda i:circles[i]['center'][0])
    ca,cb = circles[a],circles[b]
    if {ca['size'],cb['size']} != {'large','medium'} or not p.near(abs(ca['center'][1]-cb['center'][1]),p.PITCH):
        raise ValueError('Unknown visible public word')
    if not p.near(math.dist(ca['center'],cb['center']),p.LARGE):
        raise ValueError('Unknown visible public word')
    tokens = tuple(p.table().get(p.feature(geometry,[i])) for i in (a,b))
    if any(t not in p.root_words() for t in tokens):
        raise ValueError('Overlap must retain two known single-circle roots')
    return tokens, ([a],[b])


def expand_flow(geometry,original):
    """Give the native parser logical root positions, not a writer's labels."""
    tokens = []
    nuclei = []
    groups = {}
    pairs = set()
    for index,nucleus in enumerate(original['nuclei']):
        parts,rings = nucleus_tokens(geometry,nucleus)
        positions = list(range(len(tokens),len(tokens)+len(parts)))
        groups[index] = positions
        tokens.extend(parts)
        if len(parts)==1:
            nuclei.append(nucleus)
        else:
            pairs.add(tuple(positions))
            for ids in rings:
                circle = geometry['circles'][ids[0]]
                nuclei.append(dict(circles=ids,center=circle['center'],size=circle['size']))
    def chain(values):
        return [i for n in values for i in groups[n]]
    flow = dict(original,nuclei=nuclei,main=chain(original['main']),
        branch_groups={groups[n][-1]:[chain(side) for side in sides] for n,sides in original['branch_groups'].items()})
    return tokens,flow,groups,pairs


def compact_events(stream):
    """Greedy disjoint pairs; never cross the emitter's complete word boundary."""
    from scripts import kant_public_fragment as p
    source = deepcopy(stream)
    for event in source:
        sides = [compact_events(side) if isinstance(side,list) else side for side in p.event_sides(event)]
        event['side'] = sides[0] if sides else None
        if len(sides)>1:event['extra_sides']=sides[1:]
    result=[];i=0
    while i<len(source):
        first=source[i]
        if not first.get('word'):
            result.append(first);i+=1;continue
        length=first.get('word_length',len(p.parts_for()[first['word']]))
        word=source[i:i+length]
        if len(word)!=length or tuple(e['token'] for e in word)!=tuple(p.parts_for()[first['word']]):
            raise ValueError('Word parts must be explicit before overlap compaction')
        compact=[];j=0
        while j<len(word):
            if j+1<len(word) and not p.event_sides(word[j]) and not word[j+1].get('lexical_seam') and _templates(word[j]['token'],word[j+1]['token']):
                event=dict(word[j],token=pair_token(word[j]['token'],word[j+1]['token']),side=word[j+1]['side'])
                if word[j+1].get('extra_sides'):event['extra_sides']=word[j+1]['extra_sides']
                compact.append(event);j+=2
            else:
                compact.append(word[j]);j+=1
        compact[0]['word_length']=len(compact)
        result+=compact;i+=length
    return result
