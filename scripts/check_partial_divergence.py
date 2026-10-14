"""Check local semantic difference without inferring wholesale rejection."""
import argparse
from copy import deepcopy
import hashlib
from itertools import product
import json
from noema.finite_semantics import Content
from noema.grammar import parse, format_graph
from noema.higher_order_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from noema.specialization import specialize_definition
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_partial_divergence import ROOT, PARENT, BUILDERS, COMPARE, POINT, COLLECTION, SOURCE, DESCRIPTION, MEANINGS

REPORT = ROOT / 'reports/partial-divergence-v1.json'
DOMAIN = ('person', 'other', 'organization', 'issuea', 'issueb', 'judgmenta', 'judgmentb')
SCENES = ('now', 'belief', 'left', 'right', 'outside')
EXTRA = '''r jyperson[] a.r jyorganization[] a.r jysubject[] a.r jyjudgment[] a.r jycontext[] d.
r jyissues[a] c.r jyjudgmentfor[a] a.r jycomparisons[a d] c.r jyjudgments[a a d] c.r jymatters[a a d] c.
r jylinked[a ''' + DESCRIPTION + ''' j[a] d] c.r jycandidates[a d d] c.r jyadopted[a ''' + DESCRIPTION + ''' d] c.
r jyown[j[a]] e.r jystandard[j[a]] e.r jyalias[j[a]] e.'''


def select(data, indices):
    result = dict(data); result['document'] = deepcopy(data['document'])
    result['document']['statements'] = [result['document']['statements'][i] for i in indices]
    return result


def setup(text, source=False):
    base = parse(text); base['statements'] = []; base = parse(format_graph(base, 'compact') + EXTRA)
    refs = {n: 'k jy' + n + '[]' for n in ('person', 'organization', 'subject', 'judgment', 'context')}
    refs.update({n: 'p jy' + n for n in ('issues', 'judgmentfor', 'comparisons', 'judgments', 'matters', 'linked', 'candidates', 'adopted')})
    refs.update(owncriterion='r[p jyown]', standardcriterion='r[p jystandard]', bindings='l[a][k jysubject[]]', cases='i[point d][k jycomparisons[k jysubject[] v point]]')
    if source: refs.update(judgments='p fa', matters='p fb')
    queries = [k(name, *(refs[n] for n, _ in fields)) for name, fields in (('rpb', COMPARE), ('rpc', COMPARE), ('rpd', COMPARE),
        ('rpe', POINT), ('hzgv' if source else 'rpf', SOURCE if source else COLLECTION), ('rpg', COLLECTION), ('hzgw' if source else 'rph', SOURCE if source else COLLECTION))]
    target = 'hzgv' if source else 'rpf'; fields = SOURCE if source else COLLECTION
    fixed = {next(i for i, (n, _) in enumerate(fields) if n == key): description(base, expr) for key, expr in (('owncriterion', 'p jyown'), ('standardcriterion', 'p jystandard'))}
    spec = specialize_definition(base, target, 'jyfixed', fixed); base = spec.document
    closed = k('jyfixed', *(refs[n] for n, _ in fields if n not in ('owncriterion', 'standardcriterion')))
    queries += ['t[c[p jyown][l[a][k jysubject[]]]][k jycontext[]]', 'e[r[' + closed + ']][r[' + closed + ']]', closed]
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    return dict(document=doc, source=source, disquotations_removed=spec.disquotations_removed,
        own_syntax=syntax(description(base, 'p jyown')), standard_syntax=syntax(description(base, 'p jystandard')),
        alias_syntax=syntax(description(base, 'p jyalias')))


def model_for(data, bits=(False, True, True, True, True, True), variant='baseline', adopted=True, judged_a=True):
    al, sl, ar, sr, bl, bs = bits
    def criterion(own, bindings):
        issue = bindings.items[0] if len(bindings.items) == 1 else None
        row = []
        for point in SCENES:
            if issue not in ('issuea', 'issueb'): value = False
            elif point == 'belief': value = own
            elif point == 'left': value = (al if own else sl) if issue == 'issuea' else (bl if own else bs)
            elif point == 'right': value = (ar if own else sr) if issue == 'issuea' else True
            elif point == 'outside': value = own if variant == 'outside_difference' else False
            else: value = False
            row.append(value)
        return Content(SCENES, tuple(row))
    def judgments(person, judgment, point):
        who = 'other' if variant == 'other_person' else 'person'
        return (person, point) == (who, 'now') and (judgment == 'judgmentb' or (judged_a and judgment == 'judgmenta'))
    def matters(judgment, subject, point):
        return point == 'now' and (judgment, subject) in (('judgmenta', 'issueb' if variant == 'other_subject' else 'issuea'), ('judgmentb', 'issuea' if variant == 'other_subject' else 'issueb'))
    def linked(judgment, desc, bindings, point):
        issue = 'issuea' if judgment == 'judgmenta' else 'issueb'
        expected = data['standard_syntax'] if variant == 'wrong_judgment_description' else data['own_syntax']
        if variant == 'wrong_binding': issue = 'issueb' if issue == 'issuea' else 'issuea'
        return judgment in ('judgmenta', 'judgmentb') and point == 'now' and desc.syntax == expected and bindings.items == (issue,)
    def adoption(organization, desc, point):
        expected = data['alias_syntax'] if variant == 'other_adopted_description' else data['standard_syntax']
        return adopted and organization == ('other' if variant == 'other_organization' else 'organization') and point == ('belief' if variant == 'other_adoption_time' else 'now') and desc.syntax == expected
    model = guarded(data['document'])
    model.update(jyperson=lambda: 'person', jyorganization=lambda: 'organization', jysubject=lambda: 'issuea', jyjudgment=lambda: 'judgmenta', jycontext=lambda: 'now',
        jyissues=lambda issue: variant != 'empty_issues' and issue in ('issuea', 'issueb'), jyjudgmentfor=lambda issue: 'judgmenta' if issue == 'issuea' else 'judgmentb',
        jycomparisons=lambda issue, point: variant != 'empty_comparisons' and issue in ('issuea', 'issueb') and point in ('left', 'right'),
        jyjudgments=judgments, jymatters=matters, jylinked=linked, jycandidates=lambda judgment, anchor, point: variant != 'empty_candidates' and judgment in ('judgmenta', 'judgmentb') and (anchor, point) == ('now', 'belief'),
        jyadopted=adoption, jyown=lambda bindings: criterion(True, bindings), jystandard=lambda bindings: criterion(False, bindings), jyalias=lambda bindings: criterion(False, bindings))
    if data['source']: model.update(fa=judgments, fb=matters)
    return model


def values(data, model):
    return [row['value'] for row in evaluate_document(data['document'], primitives=model, individuals=DOMAIN, situations=SCENES, max_steps=30_000_000)]


def checks(texts):
    data = setup(texts[0]); grid = []
    for bits in product((False, True), repeat=6):
        al, sl, ar, sr, bl, bs = bits; da, db = (al != sl or ar != sr), bl != bs
        conflict = (al or ar) and (sl or sr) and not ((al and sl) or (ar and sr))
        expected = [da, not da, conflict, da, da or db, da and db, da != db, False, True, da or db]
        result = values(data, model_for(data, bits))
        if result != expected: raise ValueError('Content-comparison grid differs: ' + repr((bits, result, expected)))
        grid.append(dict(bits=list(bits), result=result))
    print('64 content-comparison profiles passed', flush=True); rows = []
    for text in texts[1:]:
        data = setup(text, True); profiles, cases = [], {}
        for adopted, judged, da, db in product((False, True), repeat=4):
            some = adopted and ((judged and da) or db)
            all_ = adopted and judged and da and db
            mixed = some and ((judged and not da) or not db)
            expected = [da, not da, False, judged and da, some, all_, mixed, False, True, some]
            result = values(data, model_for(data, (False, da, True, True, False, db), adopted=adopted, judged_a=judged))
            if result != expected: raise ValueError('Adoption/judgment grid differs: ' + repr((adopted, judged, da, db, result, expected)))
            profiles.append(dict(bits=[adopted, judged, da, db], result=result))
        for variant, expected in (
            ('empty_issues', [True, False, False, True, False, False, False, False, True, False]),
            ('empty_comparisons', [False] * 8 + [True, False]),
            *[(name, [True, False, False, False, False, False, False, False, True, False]) for name in ('other_person', 'other_subject', 'wrong_binding', 'wrong_judgment_description', 'empty_candidates')],
            *[(name, [True, False, False, True, False, False, False, False, True, False]) for name in ('other_organization', 'other_adoption_time', 'other_adopted_description')]):
            result = values(data, model_for(data, variant=variant))
            if result != expected: raise ValueError('Divergence contrast differs: ' + repr((variant, result, expected)))
            cases[variant] = result
        rows.append(dict(profiles=profiles, cases=cases, disquotations_removed=data['disquotations_removed'])); print('Source partial-divergence contrasts passed', flush=True)
    return dict(grid=grid, source=rows)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Partial-divergence artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Partial-divergence roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']: raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0015')
    phrase = 'vom angenommenen Symbol hier oder da abweichenden Urtheile'; start = unit['text'].index(phrase)
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_partial_divergence.py', 'scripts/check_partial_divergence.py', 'scripts/compose_personal_criteria.py', 'scripts/compose_policy_norms.py',
        'scripts/compose_origin_clock.py', 'scripts/compose_limits.py', 'scripts/compose_situated_criticism.py',
        'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/grammar.py', 'noema/meaning_basis.py', 'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py', 'noema/specialization.py',
        'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_same_issue_personal_judgments_and_adopted_criteria', documents=documents, sizes=sizes, interpretation=checks(texts), parent_preserved=True, roundtrips=True,
        new_definitions=9, new_primitives=0, new_author_statements=0, alignment=dict(semantic_completion=False, segments=[dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation', range=[start, start + len(phrase)], text=phrase, definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args(); result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Partial-divergence record differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as f: json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
    print('Adoption, personal belief, local difference and incompatibility remain distinct')


if __name__ == '__main__': main()
