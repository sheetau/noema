"""Check structural composition, purpose references and actual bodily activity separately."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_caused_conditions import source_unit
from scripts.check_confinement import sequence, paragraph_review as prior_review
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.compose_training_frame import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/training-frame-v1.json'
PARTS = ('rail', 'post', 'base')
DOMAIN = ('frame', *PARTS, 'person', 'other')


def values(doc, model, people=DOMAIN, scenes=('now',)):
    return [row['value'] for row in evaluate_document(doc, individuals=people, situations=scenes,
        primitives=model, max_steps=15_000_000, memoize_definitions=True)]


def generic_candidate():
    return parse(generic_composed()[0] + '''
r za[] a.r zb[] j[a].r zc[] d.r zd[a d] c.r ze[a a d] c.r zf[a a d] c.
r zg[a i[h[a] c] i[h[a] e] d] c.r zh[a a d] c.r zi[a d] c.r zj[a] c.r zk[a d] c.
d zl[person a] e[b scene[k zk[v person v scene]]].
q[k rai[k za[] k zb[] r[p zj] r[p zl] k zc[] p zd p ze p zf p zg p zh p zi]].
''')


def generic_model(bits=(True,)*6, parts=PARTS, edges=(('rail', 'post'), ('post', 'base'))):
    formed, structural, connected, purpose, support, movement = bits
    def forbidden(*args):
        raise ValueError('Design purpose evaluated users or successful activity')
    return {'za': lambda: 'frame', 'zb': lambda: sequence(parts), 'zc': lambda: 'now',
        'zd': lambda device, scene: formed and (device, scene) == ('frame', 'now'),
        'ze': lambda device, part, scene: structural and device == 'frame' and part in parts and scene == 'now',
        'zf': lambda a, b, scene: connected and (a, b) in edges and scene == 'now',
        'zg': lambda device, users, activity, scene: purpose and (device, symbol(users), symbol(activity), scene) == ('frame', 'zj', 'zl', 'now'),
        'zh': lambda device, part, scene: support and (device, part, scene) == ('frame', 'rail', 'now'),
        'zi': lambda device, scene: movement and (device, scene) == ('frame', 'now'), 'zj': forbidden, 'zk': forbidden}


def generic_checks():
    doc = generic_candidate()
    rows = []
    for bits in product((False, True), repeat=6):
        actual = values(doc, generic_model(bits))[0]
        if actual != all(bits):
            raise ValueError('Structure, support arrangement and training purpose differ')
        rows.append({'formed': bits[0], 'structural': bits[1], 'connected': bits[2], 'purpose': bits[3],
                     'support': bits[4], 'movement': bits[5], 'accepted': actual})
    return rows


def assembly_checks():
    doc = generic_candidate()
    pairs = (('rail', 'post'), ('post', 'base'), ('rail', 'base'))
    graphs = []
    for bits in product((False, True), repeat=3):
        edges = {edge for edge, bit in zip(pairs, bits) if bit}
        # On three vertices, at least two different undirected edges connect all vertices.
        actual = values(doc, generic_model(edges=edges))[0]
        if actual != (sum(bits) >= 2):
            raise ValueError('Structural members are not connected')
        graphs.append({'edges': list(bits), 'accepted': actual})
    rows = {}
    normal = (('rail', 'post'), ('post', 'base'))
    for variant, parts, edges in (
        ('permuted', tuple(reversed(PARTS)), normal),
        ('reversed_connections', PARTS, tuple((b, a) for a, b in normal)),
        ('duplicate_member', (*PARTS, 'post'), normal),
        ('empty', (), ()), ('singleton', ('rail',), (('rail', 'rail'),)),
        ('repeated_singleton', ('rail', 'rail'), (('rail', 'rail'),)),
        ('whole_as_part', ('rail', 'frame'), (('rail', 'frame'),)),
        ('unlisted_bridge', PARTS, (('rail', 'other'), ('other', 'post'), ('post', 'base')))):
        actual = values(doc, generic_model(parts=parts, edges=edges))[0]
        if actual != (variant in ('permuted', 'reversed_connections', 'duplicate_member')):
            raise ValueError('Assembly membership or proper-part condition differs: ' + variant)
        rows[variant] = actual
    return {'graphs': graphs, 'scope': rows}


def source_model(doc, variant='baseline'):
    def forbidden(*args):
        raise ValueError('Frame purpose asserted a child or bodily activity')
    model = {d['name']: forbidden for d in doc['declarations'] if d['kind'] == 'primitive'}
    model.update(za=lambda: 'frame', zb=lambda: 'now',
        zaa=lambda device, context: sequence(PARTS if (device, context) == ('frame', 'now') else ()),
        zad=lambda device, context: variant != 'not_formed' and (device, context) == ('frame', 'now'),
        zab=lambda device, part, context: (device, context) == ('frame', 'now') and part in PARTS
            and not (variant == 'foreign_member' and part == 'base'),
        zac=lambda a, b, context: context == 'now' and ((a, b) == ('rail', 'post') or
            variant != 'disconnected' and (a, b) == ('post', 'base')),
        zae=lambda device, users, activity, context: variant != 'no_training_purpose' and
            (device, symbol(users), symbol(activity), context) == (
                'other' if variant == 'wrong_purpose_device' else 'frame',
                'aa' if variant == 'wrong_user_class' else 'zah',
                'bb' if variant == 'intellectual_instead_of_bodily' else 'zal',
                'other' if variant == 'wrong_purpose_context' else 'now'),
        zaf=lambda device, part, context: variant != 'no_body_support' and (device, part, context) == (
            'other' if variant == 'wrong_support_device' else 'frame',
            'other' if variant == 'unlisted_support' else 'rail', 'now'),
        zag=lambda device, context: variant != 'no_leg_space' and (device, context) == ('frame', 'now'))
    if variant in ('children_and_activity_false', 'children_and_activity_true'):
        model['zah'] = lambda *args: variant == 'children_and_activity_true'
        model['zai'] = lambda *args: variant == 'children_and_activity_true'
        model['zaj'] = lambda *args: False
    required = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {name: callback for name, callback in model.items() if name in required}


def source_checks():
    doc = candidate(source_composed()[0], 'r za[] a.r zb[] d.q[t[k zam[k za[]]][k zb[]]].')
    rows = {}
    for variant in ('baseline', 'children_and_activity_false', 'children_and_activity_true', 'not_formed',
                    'foreign_member', 'disconnected', 'no_training_purpose', 'wrong_purpose_device',
                    'wrong_user_class', 'intellectual_instead_of_bodily', 'wrong_purpose_context',
                    'no_body_support', 'wrong_support_device', 'unlisted_support', 'no_leg_space'):
        actual = values(doc, source_model(doc, variant))[0]
        if actual != (variant in ('baseline', 'children_and_activity_false', 'children_and_activity_true')):
            raise ValueError('Source device configuration or intended use differs: ' + variant)
        rows[variant] = actual
    return rows


def bodily_checks():
    doc = candidate(source_composed()[0], 'r za[] a.r zb[] d.q[t[k zal[k za[]]][k zb[]]].')
    rows = {}
    for variant in ('baseline', 'supported', 'no_movement', 'other_act_supported', 'other_person_supported'):
        model = source_model(doc)
        model.update(za=lambda: 'person',
            zai=lambda person, act, context: variant != 'no_movement' and (person, act, context) == ('person', 'frame', 'now'),
            zaj=lambda person, act, context: variant != 'baseline' and (person, act, context) == (
                'other' if variant == 'other_person_supported' else 'person',
                'other' if variant == 'other_act_supported' else 'frame', 'now'))
        actual = values(doc, model)[0]
        if actual != (variant in ('baseline', 'other_act_supported', 'other_person_supported')):
            raise ValueError('Bodily motion and support act differ: ' + variant)
        rows[variant] = actual
    return rows


def depiction_checks():
    from scripts.check_confinement import source_model as enclosure_model, NODES
    from scripts.check_husbandry_depiction import source_model as husbandry_model
    doc = candidate(source_composed()[0], 'r za[] a.r zb[] d.q[t[k zan[k za[]]][k zb[]]].')
    domain = ('lock', 'person', 'guardone', 'guardtwo', 'guards', 'frame', 'closing', *NODES, *PARTS, 'other')
    rows = {}
    for variant in ('baseline', 'unowned', 'bypass', 'wrong_device', 'no_training_purpose'):
        model = husbandry_model(doc, 'unowned' if variant == 'unowned' else 'baseline')
        enclosure = enclosure_model(doc, 'bypass' if variant == 'bypass' else 'baseline')
        substitutions = {'person': 'being', 'guardone': 'guard', 'actual': 'now'}
        for name in ('qt', 'qu', 'qv', 'qw', 'qx', 'qy', 'qz', 'q7', 'df', 'dg'):
            callback = enclosure[name]
            model[name] = lambda *args, callback=callback: callback(*(substitutions.get(arg, arg) for arg in args))
        frame = source_model(doc, 'no_training_purpose' if variant == 'no_training_purpose' else 'baseline')
        for name in ('zaa', 'zab', 'zac', 'zad', 'zae', 'zaf', 'zag', 'zah', 'zai', 'zaj'):
            callback = frame[name]
            def adapt(*args, callback=callback):
                converted = tuple('now' if arg == 'actual' else
                    'other' if arg == 'frame' and variant == 'wrong_device' else arg for arg in args)
                return callback(*converted)
            model[name] = adapt
        model['qs'] = lambda being, context: 'frame'
        actual = values(doc, model, domain, ('early', 'actual'))[0]
        if actual != (variant == 'baseline'):
            raise ValueError('Training apparatus was not bound to enclosed device: ' + variant)
        rows[variant] = actual
    return rows


def attribution_checks():
    doc = candidate(source_composed()[0], 'q[k zao[]].')
    rows = {}
    for variant in ('baseline', 'reversed', 'old_unexplained_device'):
        model = source_model(doc)
        model.update(zap=lambda: 'frame', wa=lambda: 'person', wh=lambda: 'now',
            qa=lambda node, author, target, depiction, context: (node, author, symbol(target), symbol(depiction), context) == (
                'frame', 'person', 'zan' if variant == 'reversed' else 'q3',
                'q3' if variant == 'reversed' else 'q4' if variant == 'old_unexplained_device' else 'zan', 'now'))
        actual = values(doc, model)[0]
        if actual != (variant == 'baseline'):
            raise ValueError('Apparatus depiction references differ: ' + variant)
        rows[variant] = {'framed': actual, 'bodily_activity_evaluated': False}
    return rows


def alignment():
    unit = source_unit()
    phrase = 'Gängelwagen, darin sie sie einsperreten'
    if unit['text'].count(phrase) != 1:
        raise ValueError('Pinned apparatus phrase differs')
    start = unit['text'].index(phrase)
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': start+len(phrase),
        'source': phrase, 'definitions': ['rah', 'rai', 'zal', 'zam', 'zan', 'zao'],
        'status': 'partial_explicit_reading', 'full_semantic_equivalence': False,
        'remaining': ['historical configurations and physical grounding', 'walking kinematics',
                      'child classification and purpose semantics', 'temporal and metaphor interpretation', 'facsimile review']}


def paragraph_review():
    review = prior_review()
    row = next(item for item in review['current_obligations'] if item['id'] == 'walking_frame')
    row['progress_ja'] += 'さらに構造部分の接続、身体支持と脚の動作の配置、子どもによる身体移動の習得という用途を分離し、同じ装置に接続した。用途は実際の学習成果を含めない。'
    row['required_review_ja'] = '歴史的な器具の形状と物理的な基礎、歩行の運動学、子どもの分類と目的一般、移動範囲の完全性、閉じ込めの開始・時間順序、比喩対応全体。'
    return review


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored training frame differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Training frame roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    if parse(source_composed()[0])['statements'] != parse((ROOT / 'examples/v014/kant-confinement.noema').read_text(encoding='utf-8'))['statements']:
        raise ValueError('Inherited assertions changed')
    files = [*documents, 'data/training-frame-basis-v1.json', 'data/kant-training-frame-basis-v1.json',
        'data/training-frame-reading-review-v1.json', 'examples/v014/kant-confinement.noema',
        'data/kant-confinement-basis-v1.json', 'scripts/compose_training_frame.py', 'scripts/check_training_frame.py',
        'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'partial_training_structure_and_nonfactive_purpose', 'documents': documents,
        'generic': generic_checks(), 'assembly': assembly_checks(), 'source': source_checks(),
        'bodily_activity': bodily_checks(), 'depiction': depiction_checks(), 'attribution': attribution_checks(),
        'alignment': alignment(), 'paragraph_review': paragraph_review(), 'roundtrips': True,
        'inherited_statements_unchanged': True, 'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Training frame report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('64 role, 16 assembly, 15 source, 5 bodily, 5 depiction and 3 attribution cases checked')


if __name__ == '__main__':
    main()
