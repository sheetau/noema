"""Evidence for the first visible lexical-identity contrast, not all of W1."""
from copy import deepcopy
from functools import lru_cache
import hashlib
from itertools import permutations
import json
from pathlib import Path

from noema.constructed import parse
from noema.visible_lexical import (
    Lexicon, check_extension, compile_assertion, decode, to_svg, from_svg, STROKE,
)
from scripts.check_writing_freeze import build_report as check_freeze

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/visible-lexical-v1'
SOURCE = 'examples/v016/branch-circle-samples.noema'


def digest(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def specimens():
    statement = parse((ROOT/SOURCE).read_text(encoding='utf-8'))['statements'][0]
    entries = []
    for argument in ('town', 'home'):
        source = deepcopy(statement)
        source['body']['arguments'][0]['symbol'] = argument
        visible = compile_assertion(source)
        svg = to_svg(visible['shapes'])
        decoded = decode(from_svg(svg))
        if decoded != source:
            raise ValueError('The visible SVG did not recover the source statement')
        entries.append(dict(name=argument, source=source, decoded=decoded, svg=svg,
                            shapes=visible['shapes'], width=visible['width']))
    return entries


def prepare():
    from PIL import Image, ImageDraw
    OUT.mkdir(parents=True, exist_ok=True)
    for entry in specimens():
        (OUT/(entry['name']+'.svg')).write_text(entry['svg'], encoding='utf-8', newline='\n')
        # A plain raster of the same visible primitives, without text or metadata.
        scale, margin = 4, 48
        canvas = Image.new('RGB', (int(entry['width']*scale)+margin*2, 160*scale), 'white')
        draw = ImageDraw.Draw(canvas)
        for s in entry['shapes']:
            if s['kind'] == 'circle':
                x, y, r = s['x']*scale+margin, s['y']*scale+150, s['r']*scale
                draw.ellipse((x-r,y-r,x+r,y+r), outline='#203438', width=round(STROKE*scale))
            else:
                draw.line((s['x1']*scale+margin,s['y1']*scale+150,
                           s['x2']*scale+margin,s['y2']*scale+150),
                          fill='#203438', width=round(STROKE*scale))
        canvas.save(OUT/(entry['name']+'.png'))


def build_report():
    entries = specimens()
    baseline = Lexicon()
    data = baseline.document()
    rows = []
    for entry in entries:
        stable_orders = 0
        for order in permutations(data['entries']):
            variant = deepcopy(data)
            variant['entries'] = {k: variant['entries'][k] for k in order}
            lexicon = Lexicon(variant)
            if compile_assertion(entry['source'], lexicon)['shapes'] != entry['shapes']:
                raise ValueError('Lexicon order changed visible ink')
            if decode(entry['shapes'], lexicon) != entry['decoded']:
                raise ValueError('Lexicon order changed reading')
            stable_orders += 1
        layouts = 0
        for rail in (0, 1, 2):
            for distance in (140., 160., 210.):
                shapes = compile_assertion(entry['source'], argument_rail=rail, separation=distance)['shapes']
                if decode(shapes) != entry['decoded']:
                    raise ValueError('Layout changed the reading')
                layouts += 1
        rows.append(dict(name=entry['name'], source=entry['source'], decoded=entry['decoded'],
                         svg_sha256=hashlib.sha256(entry['svg'].encode()).hexdigest(),
                         visible_primitives=len(entry['shapes']),
                         stable_registry_orders=stable_orders, readable_layouts=layouts))
    added = deepcopy(data)
    new = deepcopy(added['entries']['rain'])
    new['form']['ray'] = 'north'
    new['meaning'] = '検査専用の別の一引数関係。降雨という意味は付与しない。'
    added['entries']['probe'] = new
    successor = Lexicon(added)
    check_extension(baseline, successor)
    for entry in entries:
        if (compile_assertion(entry['source'], successor)['shapes'] != entry['shapes']
                or decode(entry['shapes'], successor) != entry['decoded']):
            raise ValueError('Lexicon addition changed old ink or reading')
    old = check_freeze()
    paths = [SOURCE, 'noema/visible_lexical.py', 'noema/resources/visible-lexicon-v1.json',
             'tests/test_visible_lexical.py', 'scripts/check_visible_lexical.py',
             'docs/visible-lexical-identity-v1.md',
             *old['source_sha256'],
             'scripts/branch_circle_script.py', 'scripts/circle_contact_script.py']
    return dict(schema='noema-visible-lexical-evidence-1',
                status='first_W1_counterexample_resolved_in_explicit_fragment',
                lexical_identity_complete=False, general_syntax_decoder_complete=False,
                two_work_semantic_judgments_changed=False,
                original_visible_collision_preserved=old['collision_witnesses'][0]['visible_equal'],
                frozen_visual_assets_verified=old['visual_freeze_verified'],
                new_visible_shapes_differ=entries[0]['shapes'] != entries[1]['shapes'],
                append_only_extension_stable=True, cases=rows,
                source_sha256={p:digest(p) for p in sorted(set(paths))},
                limits=[
                    'Shared public vocabulary is allowed; no document-specific registry is decoded.',
                    'Three lexical entries and one unary-assertion fragment, not an open vocabulary.',
                    'Vector geometry is decoded; raster OCR and independent human reading are untested.',
                    'No new semantic-equivalence judgment or corpus coverage is certified.',
                    'Morphological composition, local naming, general scope and full documents remain open.',
                ])
