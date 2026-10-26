"""Saved-geometry and finite-model evidence for visibly connected volumes."""
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
from pathlib import Path
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.visible_collection import *
from scripts.visible_syntax_geometry import to_svg, from_svg
from scripts.check_visible_senses_library import native_example, expected, scenes
from scripts.shared_modality import call, v, op
from scripts.shared_reference import I, T, definition
from scripts.shared_time import q
from scripts.shared_focus import quote, eq

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'examples/v016/visible-collection-v1.noema'
OUT = ROOT / 'output/visible-collection-v1'
LABEL = Word('proper', ('book', 'treeone', 'home'))
PAYLOAD = 768


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


@lru_cache(maxsize=1)
def vocabulary():
    return SensesVocabulary()


@lru_cache(maxsize=1)
def source():
    vocab = vocabulary(); base = native_example('senses-synonym')
    doc = vocab.encode(base)
    doc['declarations'] = [vocab.declaration(n) for n in vocab._order] + [
        d for d in doc['declarations'] if d['name'] not in vocab._by_symbol]
    plain = vocab.decode_names(doc)
    first = symbol(Word('compound', ('rain', 'book', 'home')), vocab)
    second = symbol(Word('compound', ('rain', 'book', 'town')), vocab)
    aliases = [definition(n, [], T, call('red', call('aki'))) for n in (first, second)]
    plain['declarations'].extend(aliases)
    plain['statements'].extend([
        dict(kind='ask', body=eq(quote(call(first)), quote(call(second)))),
        dict(kind='ask', body=eq(call(first), call(second))),
        dict(kind='ask', body=q('forall', 'person', I,
            q('exists', 'other', I, call('above', v('person'), v('other')))))])
    return normalize_document(plain)


def unknown(*args):
    raise ValueError('Unspecified collection interpretation')


def interpret(document, mask):
    times = scenes('senses-synonym'); pairs = [(a, b) for a in ('a', 'b') for b in ('a', 'b')]
    relation = {p for i, p in enumerate(pairs) if mask & (1 << i)}

    def address(context, index):
        if context != 'a' or index not in tuple(Fraction(i) for i in range(len(times))):
            raise ValueError('Unknown situation address')
        return times[int(index)]

    handlers = dict(aki=lambda: 'a', nao=lambda: 'b', situationslot=address,
                    red=lambda x: bool(mask & 1), above=lambda a, b: (a, b) in relation)
    primitives = {d['name']: handlers.get(d['name'], unknown)
                  for d in document['declarations'] if d['kind'] == 'primitive'}
    result = evaluate_document(document, individuals=('a', 'b'), situations=times,
                               primitives=primitives, max_steps=2000000)
    wanted = expected('senses-synonym') + [dict(kind='ask', value=x) for x in
        (False, True, all(any((a, b) in relation for b in ('a', 'b')) for a in ('a', 'b')))]
    require(result == wanted, 'Collection changed frame, quotation identity or quantifier meaning')
    return [r['value'] for r in result]


@lru_cache(maxsize=1)
def compiled():
    return compile_collection(vocabulary().encode(source()), LABEL, vocabulary(), payload=PAYLOAD)


def saved_pages():
    paths = sorted(OUT.glob('page-*.svg'))
    require(paths, 'Missing saved collection')
    return [from_svg(p.read_text(encoding='utf-8')) for p in paths]


@lru_cache(maxsize=1)
def saved():
    result = decode_collection(saved_pages(), vocabulary(), public_names=True)
    require(result['document'] == source(), 'Saved collection differs from complete source')
    require(result['volumes'] > 1 and result['pages'] > MAX_PAGES, 'Example does not cross old book capacity')
    require(nodes(result['document']) > MAX_EXPANDED_NODES, 'Example does not cross old document capacity')
    return result


def write_once(path, body):
    require(not path.exists() or path.read_text(encoding='utf-8') == body, 'Existing published artifact differs')
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(body, encoding='utf-8', newline='\n')


def prepare():
    write_once(ROOT / SOURCE, format_graph(source()))
    result = compiled(); OUT.mkdir(parents=True, exist_ok=True)
    for i, page in enumerate(result['pages']):
        write_once(OUT / ('page-' + str(i + 1).zfill(5) + '.svg'), to_svg(page['shapes']))
    # Raster preview of six actual saved rows, preserving a common scale.
    from PIL import Image, ImageDraw
    shapes = [s for row in split_rows(saved_pages()[0])[:6] for s in row]
    lo = min(s['x']-s['r'] if s['kind']=='circle' else min(s['x1'],s['x2']) for s in shapes)
    hi = max(s['x']+s['r'] if s['kind']=='circle' else max(s['x1'],s['x2']) for s in shapes)
    bottom, top = vertical_bounds(shapes); scale = 0.4
    canvas = Image.new('RGB', (round((hi-lo)*scale)+40, round((top-bottom)*scale)+40), 'white')
    draw = ImageDraw.Draw(canvas)
    for s in shapes:
        if s['kind'] == 'circle':
            x=(s['x']-lo)*scale+20; y=(s['y']-bottom)*scale+20; r=s['r']*scale
            draw.ellipse((x-r,y-r,x+r,y+r),outline='#203438',width=2)
        else:
            draw.line(((s['x1']-lo)*scale+20,(s['y1']-bottom)*scale+20,
                       (s['x2']-lo)*scale+20,(s['y2']-bottom)*scale+20),fill='#203438',width=2)
    canvas.save(OUT / 'first-six-rows.png')


def build_report():
    result = saved(); doc = result['document']; pictures = saved_pages()
    require(parse((ROOT / SOURCE).read_text(encoding='utf-8')) == doc, 'Stored Native differs')
    rows = [dict(mask=mask, answers=interpret(doc, mask)) for mask in range(16)]
    tokens, table, bounds, _ = body_stream(vocabulary().encode(doc), vocabulary())
    trace = CollectionReader(tokens, vocabulary()); trace.document()
    volume_rows = []
    for stream, breaks, pages, count in volume_streams(pictures, vocabulary()):
        reader = HeaderReader(stream, vocabulary()); header = reader.header()
        volume_rows.append(dict(ordinal=header.ordinal, offset=header.offset, length=header.length,
                               header_glyphs=reader.i, pages=pages, rows=count))
    previous = json.loads((ROOT/'reports/visible-senses-v1.json').read_text(encoding='utf-8'))
    paths = {SOURCE, 'scripts/visible_collection.py', 'scripts/check_visible_collection.py',
             'tests/test_visible_collection.py', 'docs/visible-collection-v1.md',
             'reports/visible-senses-v1.json', *previous['source_sha256']}
    for path, stamp in previous['source_sha256'].items():
        require(digest((ROOT/path).read_bytes()) == stamp, 'Previous visible evidence changed: '+path)
    return dict(schema='noema-visible-collection-evidence-1', format=FORMAT, vocabulary_edition=12,
                declarations=len(doc['declarations']), statements=len(doc['statements']), nodes=nodes(doc),
                public_words=375, public_definitions=352, public_primitives=23,
                local_definitions=len(doc['declarations'])-375, volumes=volume_rows,
                pages=len(pictures), body_glyphs=len(tokens),
                page_glyphs=[p['glyphs'] for p in compiled()['pages']],
                page_shapes=[len(p) for p in pictures], finite_models=rows,
                source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},
                artifact_sha256={p.relative_to(ROOT).as_posix():digest(p.read_bytes()) for p in sorted(OUT.iterdir()) if p.is_file()},
                earlier_page_and_book_limits_unchanged=True, full_manuscript_decoding=False,
                independent_human_reading=False,
                limits=[
                    'Each logical declaration or top-level statement retains the 8192 expanded-node guard; each volume retains eight pages and 128 rows.',
                    'The separate collection format supports 16384 declarations, 4096 statements, 524288 expanded nodes, 4194304 body glyphs and 4096 volumes.',
                    'The volume header contains visible label, ordinal, total volumes, body extent and offset, payload length and record counts; numbers describe transport, not word meanings.',
                    'The complete typed syntax is assembled from visible geometry and published imports; no local name table or sidecar AST supplies definitions.',
                    'A label is not a cryptographic identity. A different internally valid collection with the same label cannot be authenticated without external evidence; saved artifact hashes bind this report to this exhibit.',
                    'The exhibit includes all 375 public words and 17 local definitions, not the two complete source manuscripts or all their primitive conventions.',
                    'Finite interpretations and vector geometry recovery do not establish OCR, independent human reading, minimal spelling length or universal semantic coverage.'])
