"""Check standards against missing, conflicting and cross-bound evidence."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content, evaluate_document
from noema.first_order_proofs import verify
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_use_standards import ROOT, PARENT, TARGETS, generic_composed, source_composed

REPORT = ROOT / 'reports/use-standards-v1.json'
SCENES = ('now', 'other')
DOMAIN = ('standard', 'person', 'resource', 'act', 'c1', 'c2', 'other')
PARAMS = '''r za[] a.r zb[] a.r zc[] a.r zd[] a.r ze[] d.
r zf[a d] c.r zg[a a d] c.r zh[a a a a d] c.r zi[a a a d] c.r zj[a a a a c d] c.
r zk[a] e.r zl[a a a i[h[a] e] d] c.r zm[a a i[h[a] e] d] c.
d zn[person a] e[k zk[v person]].
'''
BASE_ARGS = 'k za[] k zb[] k zc[] k zd[] k ze[] p zf p zg p zh p zi'
ARGS = BASE_ARGS + ' p zj'
NAMES = ('rbh', 'rbi', 'rbj', 'rbk', 'rbl', 'rbm')


def document(source=False, goals=False):
    text = source_composed()[0] if source else generic_composed()[0]
    args = ARGS.replace('p zi', 'p hi2') if source else ARGS
    base = args.rsplit(' p zj', 1)[0]
    extra = PARAMS + ''.join(f'q[k {name}[{base if name == "rbh" else args}]].' for name in NAMES)
    if source:
        source_args = args.replace(' p hi2', '')
        extra += ''.join(f'q[k {name}[{source_args}]].' for name in TARGETS.values())
        extra += f'q[k hu2[{source_args}]].'
    if goals:
        goal_args = 'k zb[] k zc[] k zd[] r[p zk] k ze[]'
        extra += f'q[k rbn[{goal_args} p {"hi2" if source else "zi"} p zl p {"g3" if source else "zm"}]].'
        if source:
            extra += f'q[k hv2[{goal_args} p zl]].'
    return candidate(text, extra)


def values(doc, model):
    return [r['value'] for r in evaluate_document(doc, individuals=DOMAIN, situations=SCENES,
        primitives=model, max_steps=1_000_000, memoize_definitions=True)]


def expected(states, used=True, adopted=True, members=('c1', 'c2'), applicable=('c1', 'c2')):
    selected = [states[i] for i in range(2) if 'c' + str(i + 1) in members and 'c' + str(i + 1) in applicable]
    active = used and adopted and bool(selected)
    conflict = active and any(pos and neg for pos, neg in selected)
    complete = active and all(pos != neg for pos, neg in selected)
    proper = complete and all(pos for pos, _ in selected)
    violation = active and not conflict and any(neg for _, neg in selected)
    gap = active and not conflict and any(not pos and not neg for pos, neg in selected)
    return [active, complete, proper, violation, conflict, gap]


def model_for(doc, states=((True, False), (True, False)), used=True, adopted=True,
        members=('c1', 'c2'), applicable=('c1', 'c2'), variant='', goal=True, purpose=True,
        produces=True, appraisal=(True, False)):
    model = guarded(doc)
    participants = ('person', 'resource', 'act', 'now')
    member_key = ('other' if variant == 'member_standard' else 'standard',
                  'other' if variant == 'member_context' else 'now')
    application_key = list(participants)
    evidence_key = list(participants)
    use_key = list(participants)
    for prefix, key in (('applicable', application_key), ('evidence', evidence_key), ('use', use_key)):
        for position, field in enumerate(('person', 'resource', 'act', 'context')):
            if variant == prefix + '_' + field:
                key[position] = 'other'

    def evidence(criterion, person, resource, act, positive, context):
        if criterion not in ('c1', 'c2') or (person, resource, act, context) != tuple(evidence_key):
            return False
        return states[int(criterion[-1]) - 1][0 if positive else 1]

    def intended(person, resource, act, description, context):
        key = [person, resource, act, symbol(description), context]
        target = ['person', 'resource', 'act', 'zk', 'now']
        for i, field in enumerate(('person', 'resource', 'act', 'description', 'context')):
            if variant == 'purpose_' + field:
                target[i] = 'zn' if field == 'description' else 'other'
        return purpose and key == target

    def caused(act, person, description, context):
        target = ['act', 'person', 'zk', 'now']
        for i, field in enumerate(('act', 'person', 'description', 'context')):
            if variant == 'produces_' + field:
                target[i] = 'zn' if field == 'description' else 'other'
        return produces and [act, person, symbol(description), context] == target

    use = lambda person, resource, act, ctx: used and (person, resource, act, ctx) == tuple(use_key)
    model.update(za=lambda: 'standard', zb=lambda: 'person', zc=lambda: 'resource', zd=lambda: 'act', ze=lambda: 'now',
        zf=lambda standard, ctx: adopted and (standard, ctx) == (
            'other' if variant == 'adopted_standard' else 'standard', 'other' if variant == 'adopted_context' else 'now'),
        zg=lambda standard, criterion, ctx: criterion in members and (standard, ctx) == member_key,
        zh=lambda criterion, person, resource, act, ctx: criterion in applicable and (person, resource, act, ctx) == tuple(application_key),
        zi=use, hi2=use, zj=evidence,
        zk=lambda person: Content(SCENES, (goal and person == 'person', False)), zl=intended, zm=caused, g3=caused,
        hj2=lambda act, positive, ctx: (act, ctx) == ('act', 'now') and appraisal[0 if positive else 1])
    inventory = guarded(doc)
    return {name: fn for name, fn in model.items() if name in inventory}


def evidence_checks():
    doc = document()
    source = document(source=True)
    rows = []
    for bits in product((False, True), repeat=6):
        states = (bits[:2], bits[2:4])
        used, adopted = bits[4:]
        result = expected(states, used, adopted)
        actual = values(doc, model_for(doc, states, used, adopted))
        native = values(source, model_for(source, states, used, adopted, appraisal=(result[2], result[3])))
        adapters = [result[NAMES.index(name)] for name in TARGETS]
        if actual != result or native != result + adapters + [True]:
            raise ValueError('Signed use evidence or native adapter differs')
        rows.append({'evidence': states, 'used': used, 'adopted': adopted, 'result': actual})
    return rows


def scope_checks():
    doc = document()
    rows = []
    states = ((True, False), (False, True))
    subsets = ((), ('c1',), ('c2',), ('c1', 'c2'))
    for members, applicable in product(subsets, repeat=2):
        actual = values(doc, model_for(doc, states, members=members, applicable=applicable))
        if actual != expected(states, members=members, applicable=applicable):
            raise ValueError('Out-of-scope criteria changed the assessment')
        rows.append({'members': members, 'applicable': applicable, 'result': actual})
    return rows


def binding_checks():
    doc = document(source=True)
    variants = ['adopted_standard', 'adopted_context', 'member_standard', 'member_context']
    variants += [prefix + '_' + field for prefix in ('applicable', 'evidence', 'use')
                 for field in ('person', 'resource', 'act', 'context')]
    rows = {}
    for variant in variants:
        actual = values(doc, model_for(doc, variant=variant))
        wanted = [True, False, False, False, False, True] if variant.startswith('evidence_') else [False] * 6
        adapters = [wanted[NAMES.index(name)] for name in TARGETS]
        # An independently given positive appraisal cannot silently be derived
        # from these absent or misbound grounds.
        if actual != wanted + adapters + [False]:
            raise ValueError('Cross-bound evidence or an unasserted bridge supplied an assessment: ' + variant)
        rows[variant] = actual
    return rows


def purpose_checks():
    doc = document(source=True, goals=True)
    rows = []
    for used, purpose, produces, goal in product((False, True), repeat=4):
        for states in (((True, False), (True, False)), ((True, False), (False, True))):
            base = expected(states, used)
            actual = values(doc, model_for(doc, states, used=used, purpose=purpose, produces=produces, goal=goal,
                appraisal=(base[2], base[3])))
            attained = used and purpose and produces and goal
            if actual != base + [base[NAMES.index(name)] for name in TARGETS] + [True, attained, attained]:
                raise ValueError('Goal attainment was confused with proper use')
            rows.append({'used': used, 'purpose': purpose, 'produces': produces, 'goal': goal,
                'proper': base[2], 'violation': base[3], 'attained': actual[-1]})
    bindings = {}
    for prefix, fields in (('purpose', ('person', 'resource', 'act', 'description', 'context')),
                           ('produces', ('act', 'person', 'description', 'context'))):
        for field in fields:
            variant = prefix + '_' + field
            actual = values(doc, model_for(doc, variant=variant))
            if actual[-2:] != [False, False] or not actual[2]:
                raise ValueError('Purpose/result binding changed or leaked into standards: ' + variant)
            bindings[variant] = actual[-2:]
    return {'independence': rows, 'bindings': bindings, 'equal_content_alias_kept_distinct': True}


def bridge_checks():
    doc = document(source=True)
    rows = []
    for proper, violation in product((False, True), repeat=2):
        actual = values(doc, model_for(doc, appraisal=(proper, violation)))
        if actual[-1] != (proper and not violation):
            raise ValueError('An unmatched appraisal was identified with its candidate grounds')
        rows.append({'appraisal': (proper, violation), 'bridge': actual[-1]})
    return rows


def general_laws():
    import z3
    # Situations retain their own sort; no finite enumeration or individual
    # surrogate is used. Every criterion and every relation is arbitrary.
    text = generic_composed()[0] + '''
r zf[a d] c.r zg[a a d] c.r zh[a a a a d] c.r zi[a a a d] c.r zj[a a a a c d] c.
'''
    args = 'v standard v person v resource v act v context p zf p zg p zh p zi p zj'
    active = f'k rbh[{args.rsplit(" p zj", 1)[0]}]'
    expr = {name: f'k {name}[{args}]' for name in NAMES if name != 'rbh'}
    complete, proper, violation, conflict, gap = (expr[name] for name in ('rbi', 'rbj', 'rbk', 'rbl', 'rbm'))
    laws = {
        'complete_decides_exactly_one': f'y[{complete}][u[z[{proper}][{violation}]]]',
        'proper_and_violation_exclusive': f'u[w[{proper}][{violation}]]',
        'conflict_blocks_both': f'y[{conflict}][u[x[{proper}][{violation}]]]',
        'complete_has_no_gap_or_conflict': f'y[{complete}][u[x[{gap}][{conflict}]]]',
        'proper_requires_complete': f'y[{proper}][{complete}]',
        'gap_entails_violation': f'y[{gap}][{violation}]',
        'violation_requires_complete': f'y[{violation}][{complete}]',
        'active_without_conflict_implies_complete': f'y[w[{active}][u[{conflict}]]][{complete}]',
    }
    statuses = ['valid'] * 5 + ['invalid'] * 3
    for body in laws.values():
        for name, sort in reversed((('standard', 'a'), ('person', 'a'), ('resource', 'a'), ('act', 'a'), ('context', 'd'))):
            body = f'f {name} {sort}[{body}]'
        text += f's[{body}].'
    results = verify(parse(text), timeout_ms=10000, max_expansion=500_000)
    if [row['status'] for row in results] != statuses:
        raise ValueError('Use standard general laws failed: ' + str([row['status'] for row in results]))
    return {'domain': 'arbitrary nonempty individual and situation sorts', 'solver_version': z3.get_version_string(),
        'document_sha256': hashlib.sha256(text.encode()).hexdigest(),
        'claims': {name: {'status': row['status'], 'formula_sha256': hashlib.sha256(row['formula'].encode()).hexdigest(),
            'countermodel_found': row['countermodel'] is not None} for name, row in zip(laws, results, strict=True)}}


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'use-standards'), (source_composed, 'kant-use-standards')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored use standards differ')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Use standards roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']:
        raise ValueError('Previous Kant draft changed')
    paths = list(documents) + [PARENT, 'data/use-standards-basis-v1.json', 'data/kant-use-standards-basis-v1.json',
        'scripts/compose_use_standards.py', 'scripts/check_use_standards.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'noema/first_order_proofs.py']
    # Normalize tuples before both storing and comparing reports.
    report = {'status': 'explicit_candidate_use_standards_not_new_source_translation', 'documents': documents,
        'evidence': evidence_checks(), 'scope': scope_checks(), 'bindings': binding_checks(),
        'purpose': purpose_checks(), 'bridge': bridge_checks(), 'general_laws': general_laws(), 'roundtrips': True, 'parent_preserved': True,
        'alignment': {'segments': [], 'new_source_ranges': False, 'candidate_standard_not_attributed_to_kant': True},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'notation_size': {'canonical_source_document_characters': len(text), 'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}
    return json.loads(json.dumps(report, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Use standards report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Explicit standards, missing/conflicting evidence and independent goal attainment checked')


if __name__ == '__main__':
    main()
