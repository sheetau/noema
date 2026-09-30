"""Check produced conditions without inventing a former capability level."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, evaluate_document
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_directed_presentations import SOURCE_DOMAIN, source_model as presentation_model
from scripts.compose_caused_conditions import ROOT, generic_composed, source_composed

REPORT = ROOT / 'reports/caused-conditions-v1.json'
DOMAIN = (*SOURCE_DOMAIN, 'conditioning_act', 'other_conditioning_act')
SCENES = ('initial', 'conditioning', 'prior', 'actual', 'belief', 'loss')


def values(doc, model, people=DOMAIN, scenes=SCENES):
    return [row['value'] for row in evaluate_document(doc, individuals=people, situations=scenes,
        primitives=model, max_steps=30_000_000, memoize_definitions=True)]


def generic_checks():
    doc = parse(generic_composed()[0] + '''
r za[a] c.r zb[] a.r zc[] e.r zd[] d.r ze[a d] c.r zf[a a d] c.r zg[a a i[h[a] e] d] c.
r zh[a d] c.d zi[person a] e[b point[k zh[v person v point]]].
q[k raa[p za k zb[] k zc[] r[p zi] k zd[] p ze p zf p zg]].
''')
    rows = []
    def forbidden(*args):
        raise ValueError('Result description was evaluated separately from supplied result content')
    for state, occurs, first, second, cause, prior_state in product((False, True), repeat=6):
        model = {'za': lambda agent: agent in ('one', 'two'), 'zb': lambda: 'person',
            'zc': lambda: Content(('before', 'now'), (prior_state, state)), 'zd': lambda: 'now',
            'ze': lambda act, point: occurs and (act, point) == ('act', 'now'),
            'zf': lambda agent, act, point: (act, point) == ('act', 'now') and (
                agent == 'one' and first or agent == 'two' and second),
            'zg': lambda act, person, description, point: cause and (act, person, symbol(description), point) == ('act', 'person', 'zi', 'now'),
            'zh': forbidden}
        result = values(doc, model, ('one', 'two', 'person', 'act'), ('before', 'now'))
        if result != [state and occurs and first and second and cause]:
            raise ValueError('Causative state or joint act differs')
        rows.append({'state': state, 'occurs': occurs, 'agents': [first, second], 'cause': cause,
                     'prior_state': prior_state, 'caused_condition': result[0]})
    return rows


def source_model(doc, variant='baseline'):
    model = presentation_model(doc, 'no_prior_effect' if variant == 'no_prior_effect' else
        'no_presentation_event' if variant == 'no_warning' else 'empty_senders' if variant == 'empty_agents' else 'baseline')
    base_occurs, base_participates, base_human = model['dg'], model['df'], model['aa']
    def order(a, b):
        if variant == 'reverse_prefix':
            ranks = ('initial', 'prior', 'conditioning', 'actual', 'belief', 'loss')
        else:
            ranks = SCENES
        return ranks.index(a) < ranks.index(b)
    def occurs(act, point):
        return base_occurs(act, point) or (variant != 'no_act' and
            act in ('conditioning_act', 'other_conditioning_act') and point == 'conditioning')
    def participates(agent, act, point):
        return base_participates(agent, act, point) or (agent in ('guardone', 'guardtwo') and point == 'conditioning'
            and act == ('other_conditioning_act' if variant == 'split_agents' and agent == 'guardtwo' else 'conditioning_act'))
    def understanding(person, point):
        return not (person in ('person', 'other', 'third') and (
            point == 'conditioning' and variant != 'sufficient_understanding' or
            point == 'initial' and variant == 'already_insufficient'))
    model.update(za=lambda: 'person', zb=lambda: 'conditioning', zc=lambda: 'actual', zd=lambda: 'prior',
        ze=lambda: 'initial',
        aa=lambda person: base_human(person) and not (variant == 'nonhuman_target' and person == 'person'),
        ak=understanding, dg=occurs, df=participates, dd=order,
        g3=lambda act, person, description, point: variant != 'no_causation' and act == 'conditioning_act'
            and person in ('person', 'other', 'third') and not (variant == 'different_target' and person == 'person')
            and symbol(description) == ('bf' if variant == 'dependency_instead_of_understanding' else 'bj')
            and point == ('prior' if variant == 'wrong_result_context' else 'conditioning'))
    required = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return {name: callback for name, callback in model.items() if name in required}


def source_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.r zb[] d.r zc[] d.r zd[] d.r ze[] d.
q[k g4[k db[] k za[] k zb[]]].q[t[k bj[k za[]]][k zb[]]].q[t[k bj[k za[]]][k ze[]]].
''')
    rows = {}
    for variant in ('baseline', 'already_insufficient', 'sufficient_understanding', 'no_act', 'split_agents',
                    'no_causation', 'different_target', 'dependency_instead_of_understanding', 'wrong_result_context',
                    'empty_agents', 'nonhuman_target'):
        result = values(doc, source_model(doc, variant))
        expected = [variant in ('baseline', 'already_insufficient'), variant != 'sufficient_understanding',
                    variant == 'already_insufficient']
        if result != expected:
            raise ValueError('Produced understanding condition differs: ' + variant + repr(result))
        rows[variant] = dict(zip(('caused_condition', 'result_condition', 'prior_condition'), result))
    return rows


def temporal_checks():
    doc = candidate(source_composed()[0], '''
r za[] a.r zb[] d.r zc[] d.r zd[] d.r ze[] d.
q[k g5[k db[] k zc[] k zb[] k zd[]]].q[t[k g6[k db[]]][k zc[]]].
q[g person a[k dj[v person k zb[]]]].
''')
    rows = {}
    for variant in ('baseline', 'already_insufficient', 'reverse_prefix', 'no_prior_effect', 'no_warning', 'different_target'):
        result = values(doc, source_model(doc, variant))
        expected = [variant in ('baseline', 'already_insufficient', 'no_warning'),
                    variant in ('baseline', 'already_insufficient'), False]
        if result != expected:
            raise ValueError('Temporal chain or recipient anchoring differs: ' + variant + repr(result))
        rows[variant] = dict(zip(('ordered_prefix', 'prefix_then_warning', 'earlier_selection'), result))
    return rows


def source_unit():
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units']
                if u['id'] == 'kant-1784:u0009')
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest() != 'c719db3057e3bfe00e0791532aa4a79b4126930dca80e2042e55cf4150f1dd2b':
        raise ValueError('Pinned source differs')
    return unit


def alignment():
    unit = source_unit()
    text = unit['text']
    start, end = text.index('Nachdem sie ihr Hausvieh'), text.index('und sorgfältig')
    excerpt = text[start:end].rstrip()
    return {'unit': unit['id'], 'unit_sha256': unit['text_sha256'], 'start': start, 'end': start+len(excerpt),
        'source': excerpt, 'definitions': ['bj', 'g4', 'g5', 'g6'], 'status': 'partial_explicit_reading',
        'full_semantic_equivalence': False,
        'remaining': ['understanding adequacy and causal grounding', 'livestock and ownership depiction',
            'docility walking-frame falling and walking', 'permission care focus and concession', 'facsimile review']}


def paragraph_review():
    text = source_unit()['text']
    # These are current obligations, not the historical unresolved notes copied by earlier drafts.
    obligations = [
        ('motive_meanings', 'Faulheit und Feigheit', '程度・規範的評価・例外と動機の基礎説明'),
        ('natural_release', 'die Natur längst von fremder Leitung frei gesprochen (naturaliter majorennes)', '自然・解放・ラテン語・長期性の語義と原刊照合'),
        ('preference_duration', 'dennoch gerne Zeitlebens unmündig bleiben', '好ましく受け入れる態度、期間、譲歩の範囲'),
        ('delegated_nouns', 'ein Buch', '本・宗教上の助言者・医師と、その知的役割の構成説明'),
        ('focus_payment', 'wenn ich nur bezahlen kann', 'nurの焦点、支払い・引受け・皮肉の関係'),
        ('female_aside', 'das ganze schöne Geschlecht', '分類、美的評価、歴史的な言い方と皮肉'),
        ('ironic_supervision', 'die Oberaufsicht über sie gütigst auf sich genommen haben', '監督の地位、gütigstの評価と皮肉'),
        ('livestock_possession', 'ihr Hausvieh', '家畜としての描写、所有・支配、対象者との比喩対応'),
        ('understanding_causation', 'zuerst dumm gemacht haben', '理解の十分さと結果を生じさせる関係の基礎説明、評価的意味'),
        ('care_docility_permission', 'sorgfältig verhüteten, daß diese ruhigen Geschöpfe', '慎重さ、穏順さ、妨害と許可・機会・勇気の区別'),
        ('walking_frame', 'Gängelwagen, darin sie sie einsperreten', '歩行器の構造、内外と閉じ込め、比喩の対応'),
        ('walking_falling', 'durch einigemahl Fallen wohl endlich gehen lernen', '転倒・歩行・学習の身体的描写、様相と程度'),
        ('final_contrast', 'allein ein Beispiel von der Art macht doch schüchtern', '先行する見込みとの譲歩、dochの焦点、萎縮の語義'),
        ('generic_case_scope', 'gemeiniglich von allen ferneren Versuchen', '通常性の事例の代表性と、後続する試みの範囲')]
    rows = []
    for identifier, quote, detail in obligations:
        if text.count(quote) != 1:
            raise ValueError('Review obligation source is missing or ambiguous: ' + identifier)
        start = text.index(quote)
        rows.append({'id': identifier, 'start': start, 'end': start+len(quote), 'source': quote,
                     'status': 'open', 'required_review_ja': detail})
    return {'semantic_completion': False, 'current_obligations': rows,
        'interpretation_limit': 'Bound source ranges and executable definitions do not discharge these meaning obligations.',
        'not_a_complete_obligation_inventory': True}


def build_report():
    documents = {}
    for compose in (generic_composed, source_composed):
        text, basis = compose()
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text:
            raise ValueError('Stored caused condition differs')
        doc = parse(text)
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Caused condition roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    files = [*documents, 'data/caused-conditions-basis-v1.json', 'data/kant-caused-conditions-basis-v1.json',
        'data/caused-conditions-reading-review-v1.json',
        'examples/v014/kant-example-deterrence.noema', 'data/kant-example-deterrence-basis-v1.json',
        'scripts/compose_caused_conditions.py', 'scripts/check_caused_conditions.py',
        'noema/discourse.py', 'noema/finite_semantics.py']
    return {'status': 'produced_understanding_condition_with_anchored_temporal_chain', 'documents': documents,
        'causative_conditions': generic_checks(), 'source': source_checks(), 'temporal': temporal_checks(),
        'alignment': alignment(), 'paragraph_review': paragraph_review(), 'roundtrips': True,
        'definitions_replaced_by_primitives': False,
        'inherited_statements_unchanged': parse(source_composed()[0])['statements'] == parse(
            (ROOT / 'examples/v014/kant-example-deterrence.noema').read_text(encoding='utf-8'))['statements'],
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Caused condition report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('64 causative, 11 source, 6 temporal cases; 14 open paragraph obligations recorded')


if __name__ == '__main__':
    main()
