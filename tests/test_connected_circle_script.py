from copy import deepcopy
from itertools import product
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw
import pytest

from noema.constructed import parse, format_graph
from noema.constructed_semantics import evaluate_document
from scripts.connected_circle_script import compile_document, geometry_check, svg
from scripts.proof_connected_circle_script import result, SOURCE, PROFILE


TEXT = Path(SOURCE).read_text(encoding='utf-8')
READING = json.loads(Path(PROFILE).read_text(encoding='utf-8'))
HEADER = TEXT[:TEXT.index('s[')]
A = 'k ax[k ac[] k ad[]]'
B = 'k ay[k ac[] k ad[]]'


def visible(sentence):
    return json.dumps(sentence['shapes'], sort_keys=True)


def test_every_sample_is_one_connected_ink_component_and_obeys_geometry():
    # Independent raster flood-fill, not merely checking the intended graph.
    for sentence in result()['sentences']:
        assert geometry_check(sentence['shapes'])
        image = Image.new('L', (int(sentence['width'] * 3), 176 * 3))
        draw = ImageDraw.Draw(image)
        for shape in sentence['shapes']:
            if shape['kind'] == 'line':
                draw.line([(round(shape['x1']*3), round((shape['y1']+48)*3)),
                           (round(shape['x2']*3), round((shape['y2']+48)*3))], fill=1, width=5)
            else:
                x, y, r = shape['x']*3, (shape['y']+48)*3, shape['r']*3
                draw.ellipse(tuple(round(v) for v in (x-r,y-r,x+r,y+r)), outline=1,
                             fill=1 if shape['kind'] == 'dot' else None, width=5)
        first = next((x, y) for y in range(image.height) for x in range(image.width) if image.getpixel((x, y)))
        ImageDraw.floodfill(image, first, 2)
        assert image.histogram()[1] == 0, 'Detached ink remains'


def test_identifier_and_parameter_spelling_does_not_determine_shape():
    renamed = TEXT
    profile = deepcopy(READING)
    for old, new in [('ax','perception'), ('ay','reliance'), ('ae','help'), ('ac','someone'), ('ad','another'), ('ab','trust'), ('af','complex')]:
        renamed = renamed.replace(old, new)
        for section in ('references', 'relations'):
            if old in profile[section]:
                profile[section][new] = profile[section].pop(old)
    changed = compile_document(renamed, profile)
    assert [visible(s) for s in changed['sentences']] == [visible(s) for s in result()['sentences']]


def test_shared_participants_and_joints_are_fused_before_layout():
    plain, _, _, extended = result()['sentences'][:4]
    assert plain['bundles'][0]['relations'] == 2
    assert extended['bundles'][0]['relations'] == 3
    assert sum(n['type'] == 'reference' for n in extended['nodes']) == 2
    assert len(extended['bundles'][0]['shared_joints']) == 2
    # Extending the compound changes the pre-existing dependence nucleus and
    # its exit direction, rather than appending an independently drawn word.
    before = next(n for n in plain['nodes'] if n.get('feature') == 'dependence')
    after = next(n for n in extended['nodes'] if n.get('feature') == 'dependence')
    assert before['radii'] != after['radii']
    outgoing = lambda s, n: next(e for e in s['edges'] if e['left'] == s['nodes'].index(n))
    assert outgoing(plain, before)['path'] != outgoing(extended, after)['path']


def test_reversing_roles_changes_the_internal_contour_not_only_name_marks():
    a, b = result()['sentences'][:2]
    rails = lambda s: [n['y'] for n in s['nodes'] if n['type'] == 'feature']
    assert rails(a) != rails(b)
    assert [e['departure_port'] for e in a['edges']] != [e['departure_port'] for e in b['edges']]


def test_definition_change_changes_shape_without_a_glyph_registry_entry():
    changed = TEXT.replace('c[w[k ax[v x v y]][k ay[v x v y]]]', 'c[x[k ax[v x v y]][k ay[v x v y]]]')
    assert visible(compile_document(changed, READING)['sentences'][0]) != visible(result()['sentences'][0])
    explicit = HEADER + f's[w[{A}][{B}]].'
    assert visible(compile_document(explicit, READING)['sentences'][0]) == visible(result()['sentences'][0])


def test_repeated_definitions_share_semantic_structure():
    # Repeated conjunctions can otherwise double the expansion at every level.
    declarations = HEADER
    previous = 'ab'
    for i in range(15):
        name = 'word' + chr(ord('a')+i)
        declarations += f'd {name}[x a y a] c[w[k {previous}[v x v y]][k {previous}[v x v y]]].\n'
        previous = name
    compiled = compile_document(declarations+f's[k {previous}[k ac[] k ad[]]].', READING)
    assert visible(compiled['sentences'][0]) == visible(result()['sentences'][0])
    assert len(compiled['sentences'][0]['expanded_dag']['nodes']) < 50
    assert len(json.dumps(compiled)) < 25000


def test_modifiers_and_overlapping_nuclei_are_actual_many_to_one_forms():
    sentence = result()['sentences'][0]
    head = next(n for n in sentence['nodes'] if n.get('feature') == 'prospect')
    assert head['absorbed_features'] == ['positive']
    assert not any(n.get('feature') == 'positive' for n in sentence['nodes'])
    action = next(n for n in sentence['nodes'] if n.get('feature') == 'action')
    dependence = next(n for n in sentence['nodes'] if n.get('feature') == 'dependence')
    assert action['x'] == dependence['x']
    assert abs(action['y']-dependence['y']) < max(action['radii'])+max(dependence['radii'])
    # A repeated modifier must not silently disappear during geometric fusion.
    changed = deepcopy(READING)
    changed['relations']['ax']['features'].append('positive')
    assert visible(compile_document(TEXT, changed)['sentences'][0]) != visible(sentence)


def evaluate_plan(plan, table, feature_names):
    if plan['kind'] == 'bundle':
        pair = tuple(p['identity'] for p in plan['participants'])
        return all(table[(feature_names[tuple(r['features'])], *pair)] for r in plan['relations'])
    values = [evaluate_plan(c, table, feature_names) for c in plan['children']]
    return {'and': lambda: all(values), 'or': lambda: any(values),
            'not': lambda: not values[0], 'implies': lambda: not values[0] or values[1]}[plan['kind']]()


def test_fusion_scope_and_role_order_preserve_truth_against_native_interpreter():
    data = result()
    slots = [(r, *p) for r in ('ax', 'ay', 'ae') for p in (('aki', 'nao'), ('nao', 'aki'))]
    feature_names = {tuple(s['features']): name for name, s in READING['relations'].items()}
    for bits in product((False, True), repeat=len(slots)):
        table = dict(zip(slots, bits))
        model = {name: (lambda a,b,name=name: table.get((name,a,b), False)) for name in ('ax','ay','ae')}
        model.update(ac=lambda: 'aki', ad=lambda: 'nao')
        original = evaluate_document(data['source'], individuals=('aki','nao'), situations=('scene',), primitives=model)
        assert [r['value'] for r in original] == [evaluate_plan(s['plan'], table, feature_names) for s in data['sentences']]
    assert visible(data['sentences'][2]) != visible(data['sentences'][6])


def test_nested_scopes_and_three_logical_connectors_remain_distinguishable():
    bodies = [f'{op}[{A}][{B}]' for op in ('w', 'x', 'y')]
    bodies += [f'u[w[{A}][{B}]]', f'w[{A}][u[{B}]]', f'w[u[{A}]][{B}]']
    bodies += [f'y[y[{A}][{B}]][{A}]', f'y[{A}][y[{B}][{A}]]']
    sentences = compile_document(HEADER + ''.join(f's[{b}].' for b in bodies), READING)['sentences']
    assert len({visible(s) for s in sentences}) == len(sentences)
    for s in sentences:
        geometry_check(s['shapes'])


@pytest.mark.parametrize('change', ['unknown_relation', 'unknown_reference', 'quote', 'quantifier', 'duplicate_marks', 'unknown_feature'])
def test_unhandled_meanings_are_rejected_instead_of_visually_erased(change):
    profile = deepcopy(READING)
    text = TEXT
    if change == 'unknown_relation':
        del profile['relations']['ax']
    elif change == 'unknown_reference':
        del profile['references']['ac']
    elif change == 'quote':
        text = 'p: r ab[] c. s[s[r[k ab[]]]].'
        profile = dict(references={}, relations={})
    elif change == 'quantifier':
        text = HEADER + 's[f x a[k ax[v x k ac[]]]].'
    elif change == 'duplicate_marks':
        profile['references']['ad']['marks'] = ['dot']
    else:
        profile['relations']['ax']['features'] = ['unknown']
    with pytest.raises(ValueError):
        compile_document(text, profile)


def test_svg_preserves_checked_source_profile_and_regenerates_exact_contour():
    data = result()
    root = ET.fromstring(svg(data, 4))
    metadata = json.loads(root.find('{http://www.w3.org/2000/svg}metadata').text)
    assert parse(format_graph(metadata['source'], 'compact')) == data['source']
    recovered = compile_document(format_graph(metadata['source'], 'compact'), metadata['profile'])
    assert visible(recovered['sentences'][metadata['sentence']]) == visible(data['sentences'][4])
