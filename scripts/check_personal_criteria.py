"""Check non-factive, personally adopted criteria at the undertaking's point."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, FunctionValue
from noema.higher_order_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from noema.specialization import specialize_definition
from scripts import check_institutional_choices as prior
from scripts.check_described_appraisals import candidate
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.compose_limits import call as k
from scripts.compose_personal_criteria import ROOT, PARENT, BUILDERS, DESCRIPTION, APPRAISAL, KNOWLEDGE, BASED, SOURCE, POLICY

REPORT = ROOT / 'reports/personal-criteria-v1.json'
DOMAIN = (*prior.DOMAIN, 'judgealice', 'judgebob', 'claimfirst', 'claimsecond')
EXTRA = '''r jsphases[a a] d.r jsscopes[a a] h[a] c.r jscorpus[a a d] c.r jssupported[a a d] c.r jscontents[a] e.
r jsjudgments[a a d] c.r jsmatters[a a d] c.r jslinked[a i[h[j[a]] e] j[a] d] c.r jscandidates[a d d] c.
r jsadopted[a i[h[j[a]] e] d] c.r jsused[a a a d] c.r jsjudgment[] a.r jsdeclaration[] d.
r jschoose[a i[h[j[a]] e] i[h[j[a]] e]] i[h[j[a]] e].'''
REFS = {**prior.REFS, **{n: 'p js' + n for n in ('phases', 'scopes', 'corpus', 'supported', 'contents',
    'judgments', 'matters', 'linked', 'candidates', 'adopted', 'used')}, 'judgment': 'k jsjudgment[]'}


def assemble(text, mixed=False):
    data = prior.assemble(format_graph(candidate(text, EXTRA), 'compact'))
    criterion = k('rli', k('rlh', *(REFS[n] for n, _ in KNOWLEDGE)))
    doc = parse(format_graph(data['document'], 'compact') + 'd jsalias[] h[j[a]] e[' + criterion + '].')
    primary = description(doc, criterion); alias = description(doc, 'k jsalias[]')
    choice = k('jschoose', 'v who', 'r[' + criterion + ']', 'r[k jsalias[]]') if mixed else 'r[' + criterion + ']'
    standards = 'i[who a community a point d][' + choice + ']'
    return dict(data, document=doc, criterion_text=criterion, criterion=primary, criterion_syntax=syntax(primary),
        alias_syntax=syntax(alias), standards=standards, mixed=mixed)


def refs_for(data):
    return {**REFS, 'terms': 'r[' + data['terms_text'] + ']', 'standards': data['standards']}


def setup(text, source=False, mixed=False):
    data = assemble(text, mixed); refs = refs_for(data)
    old = k('hzel' if source else 'rlb', *(refs[n] for n, _ in (prior.SOURCE_CHANGE if source else prior.CHANGE)))
    new = k('hzeo' if source else 'rlj', *(refs[n] for n, _ in (SOURCE if source else BASED)))
    if source: old, new = ('t[' + expr + '][k jncontext[]]' for expr in (old, new))
    truth = 't[c[' + data['criterion_text'] + '][l[a][k jnperson[] k jncommunity[] k jnolder[] k jnnewer[]]]][k jncontext[]]'
    data['document'] = parse(format_graph(data['document'], 'compact') + ''.join('q[' + expr + '].' for expr in (old, new, truth)))
    return data


def add_criteria_model(data, model, scenes, bits=(True, True, True, True, False), variant='baseline', policy=False):
    adopted, linked, used, believed, actual = bits
    oldphase, newphase, declared, belief = ('selection', 'actual', 'selection', 'w111') if policy else ('past', 'now', 'past', 'alternative')
    judges = {'judgealice': 'alice', 'judgebob': 'bob'}
    def expected(person):
        return data['alias_syntax'] if data['mixed'] and person == 'bob' else data['criterion_syntax']
    def judge(person, judgment, point):
        return judges.get(judgment) == person and point == (newphase if variant == 'late_judgment' else declared)
    def link(judgment, desc, bindings, point):
        person = judges.get(judgment)
        correct = (person, 'alpha', 'old', 'new')
        if variant == 'wrong_owner': correct = ('bob' if person == 'alice' else 'alice', *correct[1:])
        if variant == 'wrong_community': correct = (person, 'beta', 'old', 'new')
        if variant == 'reversed_alternatives': correct = (person, 'alpha', 'new', 'old')
        wanted = data['alias_syntax'] if variant == 'unadopted_alias' else expected(person)
        return linked and person is not None and desc.syntax == wanted and bindings.items == correct and point == declared
    def applies(person, act, judgment, point):
        correct = 'secondact' if person == 'bob' else 'firstact'
        if variant == 'other_act': correct = 'firstact' if person == 'bob' else 'secondact'
        return used and judges.get(judgment) == person and act == correct and point == declared
    def contents(claim):
        return Content(scenes, tuple(claim == 'claimfirst' or claim == 'claimsecond' and (
            variant == 'duplicate_content' or point == belief and believed or point == newphase and actual) for point in scenes))
    model.update(jsphases=lambda community, institution: oldphase if institution == 'old' else newphase,
        jsscopes=lambda person, community: FunctionValue(('individual',), 'truth', lambda claim:
            person in ('alice', 'bob') and community == 'alpha' and claim in ('claimfirst', 'claimsecond')),
        jscorpus=lambda person, claim, phase: person in ('alice', 'bob') and (
            claim == 'claimfirst' and phase in (oldphase, newphase) or claim == 'claimsecond' and phase == newphase),
        jssupported=lambda person, claim, phase: variant != 'unsupported' or claim != 'claimsecond', jscontents=contents,
        jsjudgments=judge, jsmatters=lambda judgment, subject, point: judgment in judges and subject == 'alpha' and point == declared,
        jslinked=link, jscandidates=lambda judgment, point, candidate: judgment in judges and point == declared and candidate == belief and variant != 'empty_candidates',
        jsadopted=lambda person, desc, point: adopted and person in ('alice', 'bob') and desc.syntax == expected(person) and point == declared,
        jsused=applies, jsjudgment=lambda: 'judgealice', jsdeclaration=lambda: declared,
        jschoose=lambda person, left, right: right if person == 'bob' else left)
    for name, source in (('fa', 'jsjudgments'), ('fb', 'jsmatters')):
        if name in model: model[name] = model[source]
    return model


def model_for(data, bits=(True, True, True, True, False), variant='baseline'):
    return add_criteria_model(data, prior.model_for(data), prior.SCENES, bits, variant)


def values(data, model, scenes=prior.SCENES, max_steps=32_000_000, statistics=None):
    return [row['value'] for row in evaluate_document(data['document'], primitives=model, individuals=DOMAIN,
        situations=scenes, max_steps=max_steps, statistics=statistics)]


def selection_checks(texts):
    setups = [setup(texts[0]), *[setup(t, True) for t in texts[1:]]]; cases = []
    for bits in product((False, True), repeat=5):
        expected = [True, all(bits[:4]), bits[4]]
        rows = [values(d, model_for(d, bits)) for d in setups]
        if rows != [expected] * 3: raise ValueError('Judgment treated as truth or unrelated reason: ' + repr((bits, rows)))
        cases.append(dict(inputs=list(bits), results=expected))
    contrasts = {}
    for variant in ('late_judgment', 'wrong_owner', 'wrong_community', 'reversed_alternatives', 'other_act',
                    'unadopted_alias', 'empty_candidates', 'unsupported', 'duplicate_content'):
        expected = [True, False, False]
        rows = [values(d, model_for(d, variant=variant)) for d in setups]
        if rows != [expected] * 3: raise ValueError('Personal criterion contrast: ' + repr((variant, rows)))
        contrasts[variant] = expected
    mixed = []
    for text in texts[1:]:
        d = setup(text, True, True); result = values(d, model_for(d))
        if result != [True, True, False]: raise ValueError('Different adopted descriptions could not coexist')
        mixed.append(result)
    return dict(cases=cases, contrasts=contrasts, personally_different_descriptions=mixed,
        factual_improvement_not_required=True, actual_undertaking_and_reason_share_person_act_point=True)


def policy_setup(text):
    data = assemble(text); doc = parse(format_graph(data['document'], 'compact') + prior.observed.EXTRA)
    bound = {next(i for i, (n, _) in enumerate(POLICY) if n == 'terms'): data['terms'],
        next(i for i, (n, _) in enumerate(POLICY) if n == 'standards'): description(doc, data['standards'])['body']}
    specialized = specialize_definition(doc, 'hzep', 'jspolicy', bound)
    refs = {**prior.observed.REFS, **refs_for(data), 'anchor': 'k jvanchor[]', 'parties': 'p jnpartiesby', 'proponents': 'p jnproponentsby'}
    target = k('jspolicy', *(refs[n] for i, (n, _) in enumerate(POLICY) if i not in bound))
    change_refs = {**refs, 'parties': 'c[p jnpartiesby][k jncommunity[]]'}
    change = k('hzeo', *(change_refs[n] for n, _ in SOURCE))
    doc = parse(format_graph(specialized.document, 'compact') + 'q[t[' + change + '][k jvanchor[]]].q[t[' + target + '][k jvcontext[]]].')
    return dict(data, document=doc, policy_text=target, policy_description=description(doc, target),
        disquotations_removed=specialized.disquotations_removed)


def policy_checks(texts):
    cases = []
    for text in texts:
        d = policy_setup(text)
        for variant in ('baseline', 'wrong_activity', 'no_reason'):
            print('Personal policy', len(text), variant, flush=True)
            model, scenes = prior.policy_model(d, 'wrong_activity' if variant == 'wrong_activity' else 'baseline')
            bits = (True, True, variant != 'no_reason', True, False)
            model = add_criteria_model(d, model, scenes, bits, policy=True)
            statistics = {}
            actual = values(d, model, scenes, max_steps=64_000_000, statistics=statistics)
            expected = [variant != 'no_reason', variant != 'wrong_activity']
            if actual != expected: raise ValueError('Personal condition/policy mismatch: ' + repr((variant, actual)))
            cases.append(dict(variant=variant, result=actual, disquotations_removed=d['disquotations_removed'],
                max_steps=64_000_000, statistics=statistics))
    return cases


def proposal_checks(texts):
    results = []
    for text in texts:
        data = policy_setup(text); base = data['document']; base['statements'] = []
        doc = parse(format_graph(base, 'compact') + prior.deliberation.EXTRA)
        refs = {**prior.deliberation.REFS, 'proposal': 'r[' + data['policy_text'] + ']'}
        expr = k('hzef', *(refs[n] for n, _ in prior.deliberation.SOURCE))
        doc = parse(format_graph(doc, 'compact') + 'q[t[' + expr + '][k jxafter[]]].')
        model = prior.deliberation.model_for(doc); participation = model['jxparticipates']; expected = syntax(data['policy_description'])
        model['jxproposes'] = lambda person, act, desc, point: participation(person, act, point) and desc.syntax == expected
        result = [row['value'] for row in evaluate_document(doc, primitives=model, individuals=prior.deliberation.DOMAIN,
            situations=prior.deliberation.SCENES, max_steps=8_000_000)]
        if result != [True]: raise ValueError('Proposal evaluated unknown personal criteria')
        results.append(result)
    return results


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Personal criteria artifacts differ')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Personal criteria roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    child, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']:
        raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    phrase = 'nach ihren Begriffen der besseren Einsicht'; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_personal_criteria.py', 'scripts/check_personal_criteria.py', 'scripts/check_institutional_choices.py',
        'scripts/compose_institutional_choices.py', 'scripts/compose_mutual_undertakings.py', 'scripts/compose_epistemic_revision.py',
        'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/specialization.py', 'noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_personal_criteria_for_institutional_agreement', documents=documents, sizes=sizes,
        selections=selection_checks(texts), policies=policy_checks(texts[1:]), proposals=proposal_checks(texts[1:]),
        parent_preserved=True, roundtrips=True, new_definitions=6, new_primitives=0, new_author_statements=0,
        alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase,
            definitions=['rlg', 'rlh', 'rli', 'rlj', 'hzeo', 'hzep'])]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    result = build_report()
    if options.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Personal criteria report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(result, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Personal criteria, non-factive judgments and the same undertaking checked')


if __name__ == '__main__': main()
