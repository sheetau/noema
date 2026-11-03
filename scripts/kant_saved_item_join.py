"""Join saved complete items without redrawing their circles or internal ink."""
from scripts import kant_public_fragment as writing
from scripts.kant_geometry_reader import read_geometry
from scripts.kant_flow_reader import decompose_flow
from scripts.kant_folded_flow import translate, _bounds
from scripts.balanced_circle_script import SMALL, MEDIUM, LARGE, MIN_GAP, MIN_RUN, near
from scripts.visible_syntax_geometry import clean


def endpoints(shapes):
    geometry = read_geometry(shapes)
    flow = decompose_flow(geometry, terminal_words=True, branch_seams=True,
        large_branches=True, local_continuation=True, nested_branches=True,
        multiple_branches=True)
    def port(index):
        nucleus = flow['nuclei'][index]
        x, y = nucleus['center']
        return dict(x=x, y=y, radius={'small': SMALL, 'medium': MEDIUM, 'large': LARGE}[nucleus['size']])
    first = flow['nuclei'][flow['main'][0]]
    token = writing.table()[writing.feature(geometry, first['circles'])]
    return port(flow['main'][0]), port(flow['main'][-1]), token


def join(items, *, reader):
    """Read inputs independently, then require the joined ink to read identically.

    Inputs use the same published three rails. Only horizontal translation and
    one connecting path (or a legal lexical gap) are allowed at each junction.
    Failure is explicit; it does not erase branches or regenerate old items.
    """
    if len(items) < 2:
        raise ValueError('Joining requires at least two complete items')
    parts = [clean(s) for s in items]
    expected = reader.fork()
    for shapes in parts:
        expected, records = writing.decode_run(shapes, reader=expected)
        if len(records) != 1:
            raise ValueError('Each saved input must be one complete item')
    combined = parts[0]
    preceding, _ = writing.decode_run(combined, reader=reader)
    junctions = []
    translations = [0.]
    for following in parts[1:]:
        wanted, _ = writing.decode_run(following, reader=preceding)
        _, start, _ = endpoints(combined)
        entry, _, token = endpoints(following)
        left, _ = _bounds(following)
        _, right = _bounds(combined)
        accepted = None
        for extra in (0., 32., 64., 128.):
            dx = right - left + MIN_GAP + 2 * MIN_RUN + extra
            moved = translate(following, dx)
            target = dict(entry, x=entry['x'] + dx)
            base = combined + moved
            rings = [s for s in base if s['kind'] == 'circle']
            candidates = []
            path = writing.route(start, target, rings, obstacles=base,
                detours=True, separate=True, line_detours=True)
            if path is not None:
                candidates.append(('visible', path[1]))
            # A gap remains the existing word/quotation separator, never a
            # new sentence-head symbol or arbitrary disconnected whitespace.
            if near(start['y'], target['y']) and token in {*writing.root_words(), 'quote'}:
                candidates.append(('lexical-gap', []))
            for kind, strokes in candidates:
                candidate = base + strokes
                try:
                    actual, _ = writing.decode_run(candidate, reader=reader)
                except ValueError:
                    continue
                if actual.result(True) != wanted.result(True):
                    continue
                accepted = candidate, actual, dict(kind=kind, added_lines=len(strokes), translation=dx)
                break
            if accepted is not None:
                break
        if accepted is None:
            raise ValueError('No unchanged-ink junction within the bounded route choices')
        combined, preceding, junction = accepted
        junctions.append(junction)
        translations.append(junction['translation'])
    if preceding.result(True) != expected.result(True):
        raise ValueError('Joined saved ink changed item order or scope')
    return dict(shapes=combined, junctions=junctions, translations=translations)
