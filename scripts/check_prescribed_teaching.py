"""Check prescribed communication independently of belief, truth and permission."""
import argparse
import hashlib
from itertools import product
import json

from noema.description_templates import apply_description
from noema.finite_semantics import Content
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_closed_policies import quoted
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded, callbacks
from scripts.check_assessed_payments import description
from scripts import check_office_speech as office
from scripts.compose_prescribed_teaching import ROOT, PARENT, BUILDERS, MESSAGE, CRITERIA, CRITERION, SERVES, ADOPTED

REPORT = ROOT/'reports/prescribed-teaching-v1.json'
EXTRA = office.EXTRA + ('r zp[] a.r zq[] a.r zr[a] c.r zs[a] c.r zt[a '+MESSAGE+'] e.r zu[a '+MESSAGE+'] e.'
    'r zv[] '+SERVES+'.r zw[] '+ADOPTED+'.r zx[a '+MESSAGE+' d] c.')
DOMAIN = (*office.DOMAIN, 'institution', 'standard', 'student', 'member')


def source_setup(text, criteria=('zt', 'zu')):
    doc = candidate(text, EXTRA)
    criterion_list = description(doc, 'l['+CRITERION+']['+' '.join('p '+name for name in criteria)+']')
    message = quoted('function_ref', 'zm')
    arguments = [quoted('call', 'zp'), quoted('call', 'zc'), quoted('call', 'zq'),
        quoted('function_ref', 'zr'), quoted('function_ref', 'zs'), quoted('call', 'zi'),
        description(doc, 'r[p zm]'), criterion_list, quoted('call', 'zv'), quoted('call', 'zw')]
    teaching = apply_description(doc, quoted('function_ref', 'hzbe'), arguments)
    callnode = lambda name: quoted('call', name)['body']
    duty = [callnode(n) for n in ('za', 'zb', 'zc', 'zd')]+[teaching, callnode('zk')]
    public = [callnode(n) for n in ('ze', 'zf', 'zg', 'zh', 'zi')]+[message, callnode('zj')]
    doc['statements'] = [{'kind': 'ask', 'body': {'kind': 'call', 'symbol': name, 'arguments': args}}
        for name, args in (('hzbf', duty), ('hzbg', duty), ('hzbh', duty+public))]
    # Inspect the very same closed normative target, using a parsed template.
    probe = parse(format_graph(doc, 'compact')+'q[t[c[s[r[p zo]]][k za[] k zb[]]][k zk[]]].')
    target = probe['statements'][-1]
    def replace(node):
        if isinstance(node, dict):
            if node == quoted('function_ref', 'zo'): return teaching
            return {key: replace(value) for key, value in node.items()}
        if isinstance(node, list): return [replace(value) for value in node]
        return node
    doc['statements'].append(replace(target))
    doc = parse(format_graph(doc, 'compact'))
    return doc, teaching, criteria


def model_for(doc, teaching, criteria, bits=(True, True, False, True, True, True), variant='baseline'):
    required, allowed, forbidden, delivered, first, second = bits
    old_variant = variant if variant in ('same_activity', 'private_audience', 'speech_is_official') else 'baseline'
    model = office.model_for(doc, (required, allowed, forbidden, False, False), old_variant)
    old_norm = model['h7a']; seen = []
    def norm(source, person, role, activity, desc, sign, context):
        if json.loads(desc.syntax) == {'kind': 'function_ref', 'symbol': 'zzq'}:
            return old_norm(source, person, role, activity, desc, sign, context)
        expected = ['issuer', 'person', 'office', 'duty', 'now']
        for index, field in enumerate(('issuer', 'person', 'role', 'activity', 'context')):
            if variant == 'norm_'+field: expected[index] = 'elsewhere' if field == 'context' else 'other'
        return (required and sign and [source, person, role, activity, context] == expected
            and variant != 'norm_description' and desc.syntax == syntax(teaching))
    def match(actual, expected, category):
        expected = list(expected)
        labels = {
            'service': ('person','principal','role','context'),
            'adoption': ('principal','standard','context'),
            'presentation': ('person','activity','context'),
            'delivery': ('activity','recipient','subject','context'),
        }[category]
        for i, label in enumerate(labels):
            if variant == category+'_'+label: expected[i] = 'elsewhere' if label == 'context' else 'other'
        return list(actual) == expected
    def adopted(principal, standard, checks, context):
        seen.append(len(checks.items))
        return (variant != 'unadopted' and len(checks.items) == len(criteria)
            and match((principal, standard, context), ('institution', 'standard', 'now'), 'adoption'))
    def conveys(activity, recipient, subject, msg, context):
        if variant == 'missing_student' and recipient == 'student': return False
        if variant == 'missing_member' and recipient == 'member': return False
        return (delivered and recipient in ('student','member')
            and match((activity, recipient, subject, context), ('duty', recipient, 'topic', 'now'), 'delivery')
            and json.loads(msg.syntax) == {'kind': 'function_ref', 'symbol': 'zn' if variant == 'delivery_description' else 'zm'})
    def criterion(which, subject, msg):
        if variant == 'unknown_criterion': raise ValueError('Criterion interpretation missing')
        wanted = 'other' if variant == 'criterion_subject' else 'topic'
        described = {'kind': 'function_ref', 'symbol': 'zn' if variant == 'criterion_description' else 'zm'}
        passed = (first if which == 'zt' else second) and subject == wanted and json.loads(msg.syntax) == described
        return Content(office.SCENES, (passed, False))
    model.update(h7a=norm, zp=lambda: 'institution', zq=lambda: 'standard',
        zr=lambda person: variant not in ('empty_audiences','only_congregation') and person == 'student',
        zs=lambda person: variant != 'empty_audiences' and person == ('student' if variant == 'overlapping_audiences' else 'member'),
        zt=lambda subject, msg: criterion('zt', subject, msg), zu=lambda subject, msg: criterion('zu', subject, msg),
        dg=lambda activity, context: delivered and (activity, context) == ('duty', 'now'),
        f3=lambda person, activity, context: delivered and match((person,activity,context), ('person','duty','now'), 'presentation'),
        f2=conveys)
    callbacks(doc, model, {'zv': lambda person, principal, role, context:
        match((person, principal, role, context), ('person','institution','office','now'), 'service'), 'zw': adopted})
    if variant == 'no_entrusted_office': model['cf'] = lambda *args: False
    if variant == 'wrong_activity_role':
        old = model['cb']; model['cb'] = lambda person, activity, role, context: activity != 'duty' and old(person, activity, role, context)
    # Truth (zl), personal endorsement (zx), understanding and performance of
    # public speech remain guarded. Presenting a description must not run them.
    return model, seen


def evaluate(doc, model):
    used = {d['name'] for d in doc['declarations'] if d['kind'] == 'primitive'}
    return values(doc, {name: value for name, value in model.items() if name in used}, DOMAIN, office.SCENES)


def teaching_checks(texts):
    setups = [source_setup(text) for text in texts]
    def run(bits=(True, True, False, True, True, True), variant='baseline'):
        rows = [evaluate(doc, model_for(doc, target, criteria, bits, variant)[0]) for doc, target, criteria in setups]
        if rows[0] != rows[1]: raise ValueError('Extracted teaching differs')
        return rows[0]
    cases = []
    for bits in product((False, True), repeat=6):
        required, allowed, forbidden, delivered, first, second = bits
        actual = delivered and first and second
        expected = [required, required and not actual, required and allowed and not forbidden, actual]
        observed = run(bits)
        if observed != expected: raise ValueError('Teaching state differs: '+repr((bits, observed)))
        cases.append(dict(states=list(bits), results=observed))
    contrasts = {}
    for variant in (
        *['service_'+field for field in ('person','principal','role','context')],
        *['adoption_'+field for field in ('principal','standard','context')], 'unadopted',
        *['presentation_'+field for field in ('person','activity','context')],
        *['delivery_'+field for field in ('activity','recipient','subject','context')],
        'delivery_description','criterion_subject','criterion_description','missing_student','missing_member',
        'empty_audiences','no_entrusted_office','wrong_activity_role'):
        observed = run(variant=variant)
        if observed != [True, True, True, False]: raise ValueError('Teaching binding '+variant+': '+repr(observed))
        contrasts[variant] = observed
    for variant in ('norm_issuer','norm_person','norm_role','norm_activity','norm_context','norm_description'):
        observed = run(variant=variant)
        if observed != [False, False, False, True]: raise ValueError('Teaching norm target differs: '+variant)
        contrasts[variant] = observed
    for variant in ('private_audience','speech_is_official','same_activity'):
        observed = run(variant=variant)
        if observed != [True, False, False, True]: raise ValueError('Public speech distinction differs: '+variant+repr(observed))
        contrasts[variant] = observed
    for variant in ('only_congregation','overlapping_audiences'):
        observed = run(variant=variant)
        if observed != [True, False, True, True]: raise ValueError('Audience union differs')
        contrasts[variant] = observed
    independent = []
    for truth, endorsed in product((False,True), repeat=2):
        rows = []
        for doc, target, criteria in setups:
            model, _ = model_for(doc, target, criteria)
            model['zl'] = lambda *args: truth
            model['zx'] = lambda *args: endorsed
            rows.append(evaluate(doc, model))
        if rows != [[True,False,True,True]]*2: raise ValueError('Truth or endorsement inferred from teaching')
        independent.append(dict(truth=truth, endorsed=endorsed, results=rows[0]))
    lists = []
    for criteria in ((), ('zt',), ('zt','zt'), ('zt','zu','zt')):
        rows = []
        for text in texts:
            doc, target, selected = source_setup(text, criteria)
            model, _ = model_for(doc, target, selected, (True,True,False,True,True,False))
            rows.append(evaluate(doc, model))
        actual = 'zu' not in criteria
        if rows != [[True,not actual,True,actual]]*2: raise ValueError('Criterion list differs')
        lists.append(dict(criteria=list(criteria), results=rows[0]))
    for doc, target, criteria in setups:
        model, _ = model_for(doc, target, criteria, variant='unknown_criterion')
        normonly = json.loads(json.dumps(doc)); normonly['statements'] = [doc['statements'][0], doc['statements'][2]]
        if evaluate(normonly, model) != [True,True]: raise ValueError('Norm evaluated its target')
        try: evaluate(doc, model)
        except ValueError as exc:
            if 'Criterion interpretation missing' not in str(exc): raise
        else: raise ValueError('Unknown criterion supplied')
    return dict(cases=cases, contrasts=contrasts, independent_truth_and_endorsement=independent, criterion_lists=lists,
        standalone_agrees=True, unassessed_criterion_refused=True, norms_do_not_execute_target=True,
        unassessed_truth_and_endorsement_not_executed=True,
        adoption_fixture_checks_referents_and_list_length_only=True, general_criterion_function_identity_proved=False)


def alignment():
    source = json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit = next(u for u in source['units'] if u['id'] == 'kant-1784:u0012')
    excerpts = ('ein Geistlicher verbunden, seinen Katechismusschülern und seiner Gemeine nach dem Symbol der Kirche, der er dient, seinen Vortrag zu thun',
                'Aber als Gelehrter hat er volle Freiheit')
    rows = []
    for excerpt in excerpts:
        if unit['text'].count(excerpt) != 1: raise ValueError('Ambiguous teaching source range')
        start = unit['text'].index(excerpt)
        rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],text=excerpt,
            definitions=['rfu','rfv','hzbe','hzbf','hzbg','hzbh'],status='partial',
            review_ja='採用基準への適合と、同じ組織・委任役割で二群へ行う伝達を規範の対象にする明示的な部分モデル。別の公的発言の許可と併存する。教理・宗教・教会の語義、受任の因果、無制限の自由・使命、良心・本人の確信、全文意味一致は未完。'))
    return dict(segments=rows,semantic_completion=False)


def build_report():
    documents, sizes, texts = {}, {}, []
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored teaching differs')
        for notation in ('compact','full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form,'v2'))) != doc: raise ValueError('Teaching roundtrip differs')
        documents[basis['document']] = audit_basis(doc,basis)
        sizes[stem] = dict(characters=len(text),statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    paths = [*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_prescribed_teaching.py','scripts/check_prescribed_teaching.py','scripts/check_office_speech.py',
        'scripts/check_assessed_payments.py','noema/finite_semantics.py','noema/description_templates.py','noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_institutional_standards_and_teaching_requirement',documents=documents,sizes=sizes,
        teaching=teaching_checks(texts[1:]),alignment=alignment(),new_definitions=6,new_primitives=0,new_author_statements=0,
        parent_preserved=True,roundtrips=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Teaching report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Prescribed teaching, standards, truth and public permission checked separately')


if __name__=='__main__': main()
