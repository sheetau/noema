"""Recover one-item rows from primitive geometry, without SVG group metadata."""
from copy import deepcopy
import json
from scripts.balanced_circle_script import PITCH,LARGE,EPS,near
from scripts.visible_syntax_geometry import clean
from scripts import kant_public_fragment as writing
from scripts.kant_incremental_dictionary import Reader

ROW_GAP=4*PITCH


def vertical_bounds(shape):
    if shape['kind']=='circle':return shape['y']-shape['r'],shape['y']+shape['r']
    return min(shape['y1'],shape['y2']),max(shape['y1'],shape['y2'])


def shifted(shapes,dy):
    result=deepcopy(shapes)
    for s in result:
        for key in ('y',) if s['kind']=='circle' else ('y1','y2'):s[key]+=dy
    return result


def pack_rows(items):
    result=[];bottom=0.
    for shapes in items:
        parts=clean(shapes)
        low=min(vertical_bounds(s)[0] for s in parts)
        high=max(vertical_bounds(s)[1] for s in parts)
        result+=shifted(parts,bottom-low)
        bottom+=high-low+ROW_GAP
    if not result:raise ValueError('Page requires at least one item row')
    return result


def split_rows(shapes):
    parts=clean(shapes)
    ordered=sorted(parts,key=lambda s:vertical_bounds(s))
    rows=[];bottom=None
    for s in ordered:
        low,high=vertical_bounds(s)
        if bottom is None or low-bottom>=ROW_GAP-EPS:
            rows.append([]);bottom=high
        else:bottom=max(bottom,high)
        rows[-1].append(s)
    return rows


def read_row(shapes,context):
    circles=[s for s in shapes if s['kind']=='circle']
    if not circles:raise ValueError('Page row has no circles')
    large=[s['y'] for s in circles if near(s['r'],LARGE)]
    if large:
        if any(not near(y,large[0]) for y in large):raise ValueError('Page row has inconsistent central rails')
        baselines=[large[0]]
    else:
        low=min(s['y'] for s in circles)
        baselines=[low-PITCH,low,low+PITCH]
    decoded={};errors=[]
    for baseline in baselines:
        try:result=writing.decode_item(shifted(shapes,PITCH-baseline),lexicon=context)
        except ValueError as error:errors.append(str(error));continue
        decoded[json.dumps(result,sort_keys=True,separators=(',',':'))]=result
    if not decoded:raise ValueError('No readable page row: '+('; '.join(errors)))
    if len(decoded)!=1:raise ValueError('Ambiguous page row reading')
    return next(iter(decoded.values()))


def decode_page(shapes,*,seed=None,include_spellings=False):
    reader=Reader(seed)
    for row in split_rows(shapes):reader.register(read_row(row,reader.context))
    return reader.result(include_spellings)
