from collections import Counter
import math
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops
from noema.constructed import parse
from scripts.balanced_circle_script import restore, expanded_tree, geometry_check
from scripts.proof_kant_page_script_v3 import (
    page_data, english_layout, read_json, ROOT, OUT, DOCUMENT, ASSEMBLY,
    INVENTORY, ENGLISH, UNITS, WIDTH, HEIGHT, STROKE,
)


def test_contiguous_complete_source_units_and_all_registered_assertions():
    data = page_data()
    units = read_json(INVENTORY)['units']
    start = next(i for i, u in enumerate(units) if u['id'] == UNITS[0])
    assert tuple(u['id'] for u in units[start:start+4]) == UNITS
    selection = {u['unit']: u for u in read_json(ASSEMBLY)['works']['kant-1784']['units']}
    doc = parse((ROOT/DOCUMENT).read_text(encoding='utf-8'))
    declarations = {d['name']: d for d in doc['declarations']}
    assert data['source_word_count'] == 592
    assert sum(len(p['entries']) for p in data['paragraphs']) == 40
    for p in data['paragraphs']:
        assert [e['statement'] for e in p['entries']] == selection[p['unit']]['statements']
        for e in p['entries']:
            assert e['original'] == doc['statements'][e['statement']]
            display = e['compiled']['source']
            if e['expanded_definition']:
                d = declarations[e['expanded_definition']]
                assert not d['parameters']
                assert display == dict(kind='assert', body=d['body'])
            else:
                assert display == e['original']


def test_new_corpus_inputs_preserve_every_occurrence_and_legal_geometry():
    for p in page_data()['paragraphs']:
        for e in p['entries']:
            c = e['compiled']
            assert restore(expanded_tree(c['tree'])) == c['source']
            assert geometry_check(c['shapes'], c['paths'], c['invisible'])
            expected = []
            def visit(node, path=()):
                expected.append(tuple(path))
                for i, child in enumerate(node['children']):
                    visit(child['node'], path+(i,))
            visit(c['tree'])
            if c['tree']['tag'] == 'assert':
                expected.remove(())
            actual = []
            for g in c['groups']:
                for item in [g]+g['satellites']:
                    actual.append(tuple(item['path']))
                    actual.extend(tuple(path) for path in item['fused_paths'])
            assert Counter(actual) == Counter(expected)


def test_page_wrapping_preserves_ink_and_does_not_clip():
    data = page_data()
    def line_length(shapes):
        return sum(math.hypot(s['x2']-s['x1'], s['y2']-s['y1']) for s in shapes if s['kind']=='line')
    for p in data['paragraphs']:
        raw = [s for e in p['entries'] for s in e['compiled']['shapes']]
        wrapped = [s for row in p['rows'] for s in row['shapes']]
        assert Counter(s['r'] for s in raw if s['kind']=='circle') == Counter(s['r'] for s in wrapped if s['kind']=='circle')
        assert math.isclose(line_length(raw), line_length(wrapped), abs_tol=1e-6)
        for row in p['rows']:
            for s in row['shapes']:
                points = ([(s['x']-s['r'], s['y']-s['r']), (s['x']+s['r'], s['y']+s['r'])]
                          if s['kind']=='circle' else [(s['x1'],s['y1']), (s['x2'],s['y2'])])
                for x, y in points:
                    assert STROKE < row['x']+x*data['scale'] < WIDTH-STROKE
                    assert STROKE < row['y']+y*data['scale'] < HEIGHT-STROKE


def test_noema_svg_has_only_ink_and_background_and_pngs_are_nonblank():
    svg = ET.parse(OUT/'kant-page.svg').getroot()
    assert {e.tag.split('}')[-1] for e in svg.iter()} == {'svg','rect','g','circle','path'}
    assert all(not (e.text or '').strip() for e in svg.iter())
    for name in ['kant-page.png', 'kant-page-english.png']:
        image = Image.open(OUT/name).convert('RGB')
        assert image.size == (WIDTH, HEIGHT)
        difference = ImageChops.difference(image, Image.new('RGB', image.size, image.getpixel((0,0))))
        box = difference.getbbox()
        assert box and box[0] > 20 and box[1] > 20 and box[2] < WIDTH-20 and box[3] < HEIGHT-20


def test_english_layout_keeps_the_transcribed_passage_and_same_selection():
    source = read_json(ENGLISH)
    assert tuple(p['unit'] for p in source['paragraphs']) == UNITS
    layout = english_layout()
    for source_p, lines in zip(source['paragraphs'], layout['paragraphs'], strict=True):
        assert ' '.join(lines) == source_p['text']
    assert source['paragraphs'][-1]['text'].endswith('the thoughtless multitude.')


def test_more_text_and_more_space_between_noema_rows():
    from scripts.proof_kant_page_script import page_data as previous_page_data
    old = previous_page_data()
    new = page_data()
    assert new['source_word_count'] == 2*old['source_word_count']
    assert new['scale'] < old['scale']
    def ink_interval(row, scale):
        lower, upper = [], []
        for s in row['shapes']:
            lo, hi = ((s['y']-s['r'], s['y']+s['r']) if s['kind']=='circle'
                      else (min(s['y1'],s['y2']), max(s['y1'],s['y2'])))
            lower.append(row['y']+lo*scale)
            upper.append(row['y']+hi*scale)
        return min(lower), max(upper)
    def gaps(data):
        result = []
        for paragraph in data['paragraphs']:
            intervals = [ink_interval(row,data['scale']) for row in paragraph['rows']]
            result.extend(b[0]-a[1] for a,b in zip(intervals,intervals[1:]))
        return result
    assert min(gaps(new)) > min(gaps(old))


def test_opening_variety_is_traceable_to_real_syntax():
    entries = [e for p in page_data()['paragraphs'] for e in p['entries']]
    families = Counter(e['compiled']['opening']['family'] for e in entries)
    assert families == {'conjunction':22, 'quoted-argument':11,
                        'function-argument':4, 'native-call':2, 'evaluation':1}
    assert sum(e['compiled']['groups'][0]['stroke_mode']=='entry' for e in entries) == 2
    for e in entries:
        c = e['compiled']
        g = c['groups'][0]
        if c['opening']['directions'] is not None:
            assert g['ray'] in c['opening']['directions']


def test_identifier_renaming_cannot_change_the_opening_or_geometry():
    from scripts.contextual_opening_script import compile_expression
    from copy import deepcopy
    entries = [e for p in page_data()['paragraphs'] for e in p['entries']]
    representatives = {}
    for e in entries:
        representatives.setdefault(e['compiled']['opening']['family'],e['compiled'])
    for c in representatives.values():
        value = deepcopy(c['source'])
        names = {name:'renamed_'+str(i) for i,name in enumerate(c['reference_order'])}
        def rename(node):
            if isinstance(node,dict):
                for key,item in node.items():
                    if key=='symbol': node[key]=names[item]
                    else: rename(item)
            elif isinstance(node,list):
                for item in node: rename(item)
        rename(value)
        renamed = compile_expression(value,reference_order={names[n]:i for n,i in c['reference_order'].items()})
        assert renamed['opening'] == c['opening']
        assert renamed['shapes'] == c['shapes']


def test_ordinary_sentences_and_equations_preserve_native_openings():
    from scripts.contextual_opening_script import compile_expression
    from scripts.balanced_circle_script import compile_expression as old_compile
    doc = parse((ROOT/'examples/v016/branch-circle-samples.noema').read_text(encoding='utf-8'))
    registry = {d['name']:i for i,d in enumerate(doc['declarations'])}
    call = lambda name: dict(kind='call',symbol=name,arguments=[])
    equation = dict(kind='assert',body=dict(kind='equal',arguments=[call('town'),call('home')]))
    for value in doc['statements']+[equation]:
        c = compile_expression(value,reference_order=registry)
        old = old_compile(value,reference_order=registry)
        assert c['shapes'] == old['shapes']
        assert restore(expanded_tree(c['tree'])) == value
        assert geometry_check(c['shapes'],c['paths'],c['invisible'])
