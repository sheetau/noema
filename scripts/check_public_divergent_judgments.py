"""Verify one bound speech target across permission, duties and public review."""
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
from scripts.compose_public_divergent_judgments import ROOT, PARENT, BUILDERS, FRAME, SOURCE_JUDGMENT, DESCRIPTION, MEANINGS, bind_presentation
from scripts.compose_retained_duties import PERMISSION, CASES

REPORT = ROOT / 'reports/public-divergent-judgments-v1.json'
DOMAIN = ('person', 'other', 'organization', 'topic', 'other_topic', 'judgment', 'review', 'office', 'scholar', 'reader', 'world', 'channel', 'duty', 'speechact', 'issuer', 'authority', 'entry')
SCENES = ('anchor', 'speech', 'belief', 'left', 'right', 'quiet')
EXTRA = '''r jzperson[] a.r jzactivity[] a.r jzcontext[] d.r jzanchor[] d.r jzsubject[] a.r jzorganization[] a.
r jzrole[] a.r jzrecipient[] a.r jzchannel[] a.r jzaudience[a] c.r jzjudgmentfor[a d] a.
r jzown[j[a]] e.r jzstandard[j[a]] e.r jzalias[j[a]] e.
r jzlinked[a ''' + DESCRIPTION + ''' j[a] d] c.r jzcandidates[a d d] c.r jzcomparisons[a d] c.r jzadopted[a ''' + DESCRIPTION + ''' d] c.
r jzvoices[a a a a a i[h[a] f] d] c.
r jzoffice[] a.r jzitems[a] c.r jzissuers[a] a.r jzactions[a] a.r jzsigns[a] c.
r jzduty[a a] e.r jzcases[d] c.r jzauthority[] a.'''


def select(data, indices):
    result = dict(data); result['document'] = deepcopy(data['document'])
    result['document']['statements'] = [result['document']['statements'][i] for i in indices]
    return result


def setup(text):
    base = parse(text); base['statements'] = []; base = parse(format_graph(base, 'compact') + EXTRA)
    bindings = {n: 'p jz' + n for n in ('linked', 'candidates', 'adopted', 'judgmentfor', 'comparisons', 'audience', 'voices')}
    bindings.update({n: 'k jz' + n + '[]' for n in ('subject', 'organization', 'role', 'recipient', 'channel')})
    bindings.update(owncriterion='r[p jzown]', standardcriterion='r[p jzstandard]')
    bound = bind_presentation(base, bindings); base = bound['document']
    target = 'r[' + bound['action'] + ']'
    spec = specialize_definition(base, 'hzgu', 'jzpermission', {len(PERMISSION) - 1: description(base, bound['action'])}); base = spec.document
    refs = {n: 'p jz' + n for n in ('items', 'issuers', 'actions', 'signs', 'cases')}
    refs['descriptions'] = 'i[item a][r[p jzduty]]'
    refs.update({n: 'k jz' + n + '[]' for n in ('person', 'office', 'anchor', 'authority')})
    refs.update(publicrole=bindings['role'], publicact='k jzactivity[]', publicdescription=target, required='p h7a',
        trigger='c[' + bound['action'] + '][k jzperson[] k jzactivity[]]')
    point = bindings | dict(person=refs['person'], judgment='c[p jzjudgmentfor][k jzperson[] k jzcontext[]]', context='k jzcontext[]',
        cases='i[point d][k jzcomparisons[k jzsubject[] v point]]')
    queries = [k('hzgx', *(point[n] for n, _ in SOURCE_JUDGMENT)), 't[' + refs['trigger'] + '][k jzcontext[]]',
        k('rdm', refs['authority'], refs['person'], refs['publicrole'], refs['publicact'], target, 'e[n p a b][n p a b]', refs['anchor'], 'p h7a', 'p h7b'),
        k('jzpermission', *(refs[n] for n, _ in PERMISSION if n != 'publicdescription')),
        *[k(name, *(refs[n] for n, _ in CASES)) for name in ('rp6', 'rpa')],
        't[s[' + bound['goal'] + ']][k jzcontext[]]', 't[c[p jzown][l[a][k jzsubject[]]]][k jzcontext[]]', 'e[' + target + '][' + target + ']']
    doc = parse(format_graph(base, 'compact') + ''.join('q[' + q + '].' for q in queries))
    return dict(document=doc, bindings=bindings, action=bound['action'], message=bound['message'], goal=bound['goal'],
        disquotations_removed=bound['disquotations_removed'] + spec.disquotations_removed,
        target_syntax=syntax(description(base, bound['action'])), message_syntax=syntax(description(base, bound['message'])['body']),
        goal_syntax=syntax(description(base, bound['goal'])['body']), own_syntax=syntax(description(base, 'p jzown')),
        standard_syntax=syntax(description(base, 'p jzstandard')), alias_syntax=syntax(description(base, 'p jzalias')),
        duty_description=description(base, 'p jzduty'))


def model_for(data, bits=(True, True, True, True, True), variant='baseline', reviewed=False, judged=True):
    performed, intended, permitted, kept, fulfilled = bits
    def own(bindings):
        return Content(SCENES, tuple(bindings.items == ('topic',) and point in ('belief', 'right') for point in SCENES))
    def standard(bindings):
        return Content(SCENES, tuple(bindings.items == ('topic',) and point in ('left', 'right') for point in SCENES))
    def equal_desc(desc, expected): return desc.syntax == data[expected + '_syntax']
    def judgments(person, judgment, point):
        return (judged and (person, judgment) == ('other' if variant == 'other_judge' else 'person', 'judgment')) or (reviewed and (person, judgment, point) == ('reader', 'review', 'speech'))
    def matters(judgment, subject, point):
        return (judgment, subject) in (('judgment', 'other_topic' if variant == 'other_issue' else 'topic'), ('review', 'topic'))
    def linked(judgment, desc, bindings, point):
        return judgment == 'judgment' and equal_desc(desc, 'own') and bindings.items == ('topic',)
    def adopted(organization, desc, point):
        return organization == 'organization' and equal_desc(desc, 'alias' if variant == 'other_standard' else 'standard')
    def norm(source, person, role, act, desc, sign, point):
        if (source, person, role, act, sign) == ('issuer', 'person', 'office', 'duty', True) and desc.syntax == syntax(data['duty_description']):
            return point == 'anchor' or (point in ('speech', 'quiet') and kept)
        return variant == 'public_prohibited' and (source, person, role, act, sign, point) == ('authority', 'person', 'scholar', 'speechact', False, 'anchor') and equal_desc(desc, 'target')
    def allowed(source, person, role, act, desc, sign, point):
        return permitted and (source, person, role, act, sign, point) == ('authority', 'person', 'scholar', 'speechact', True, 'anchor') and equal_desc(desc, 'target' if variant != 'other_permitted_target' else 'goal')
    def aim(person, act, desc, point):
        return intended and (person, act, point) == ('person', 'speechact', 'speech') and equal_desc(desc, 'goal' if variant != 'other_goal' else 'message')
    def conveys(act, reader, subject, desc, point):
        return (act, reader, subject, point) == ('speechact', 'reader', 'topic', 'speech') and equal_desc(desc, 'message' if variant != 'other_message' else 'goal')
    def voices(person, act, principal, role, subject, desc, point):
        return (person, act, principal, role, subject, point) == ('person', 'speechact', 'other' if variant == 'other_voice' else 'person', 'scholar', 'topic', 'speech') and equal_desc(desc, 'message')
    model = guarded(data['document'])
    model.update(jzperson=lambda: 'person', jzactivity=lambda: 'speechact', jzcontext=lambda: 'speech', jzanchor=lambda: 'anchor', jzsubject=lambda: 'topic',
        jzorganization=lambda: 'organization', jzrole=lambda: 'scholar', jzrecipient=lambda: 'world', jzchannel=lambda: 'channel',
        jzaudience=lambda reader: reader == ('other' if variant == 'outsider' else 'reader'), jzjudgmentfor=lambda person, point: 'judgment',
        jzown=own, jzstandard=standard, jzalias=standard, jzlinked=linked, jzcandidates=lambda judgment, anchor, point: variant != 'empty_candidates' and judgment == 'judgment' and point == 'belief',
        jzcomparisons=lambda subject, point: subject == 'topic' and point in ('left', 'right'), jzadopted=adopted, jzvoices=voices,
        jzoffice=lambda: 'office', jzitems=lambda item: item == 'entry', jzissuers=lambda item: 'issuer', jzactions=lambda item: 'duty', jzsigns=lambda item: True,
        jzcases=lambda point: point in ('speech', 'quiet'), jzauthority=lambda: 'authority',
        jzduty=lambda person, act: Content(SCENES, tuple(fulfilled and (person, act, point) == ('person', 'duty', 'speech') for point in SCENES)),
        fa=judgments, fb=matters, h7a=norm, h7b=allowed, hzu=aim,
        hzv=lambda judgment, subject, desc, point: (judgment, subject, point) == ('review', 'topic', 'speech') and equal_desc(desc, 'message'),
        dg=lambda act, point: performed and (act, point) == ('speechact', 'speech'), f3=lambda person, act, point: (person, act, point) == ('person', 'speechact', 'speech'), f2=conveys,
        ca=lambda person, act, point: (person, act, point) == ('person', 'speechact', 'speech'), cb=lambda person, act, role, point: (person, act, role, point) == ('person', 'speechact', 'scholar', 'speech'),
        cc=lambda act, recipient, point: (act, recipient, point) == ('speechact', 'world', 'speech'), cd=lambda role, point: variant != 'not_scholar' and (role, point) == ('scholar', 'speech'),
        ce=lambda recipient, point: (recipient, point) == ('world', 'speech'), aa=lambda person: person in ('person', 'reader'),
        h6n=lambda reader, point: reader == 'reader', h6t=lambda recipient, reader, point: (recipient, reader) == ('world', 'reader'),
        h6u=lambda act, channel, subject, desc, point: (act, channel, subject, point) == ('speechact', 'channel', 'topic', 'speech') and equal_desc(desc, 'message'))
    return model


def values(data, model):
    return [r['value'] for r in evaluate_document(data['document'], individuals=DOMAIN, situations=SCENES, primitives=model, max_steps=60_000_000)]


def checks(texts):
    results = []
    for text in texts[1:]:
        data = setup(text); grid, cases = [], {}
        for bits in product((False, True), repeat=5):
            performed, intended, permitted, kept, fulfilled = bits; actual = performed and intended; conditional = not actual or kept
            expected = [True, actual, permitted, permitted and conditional, actual and kept, actual and kept and fulfilled, False, False, True]
            actual_values = values(data, model_for(data, bits))
            if actual_values != expected: raise ValueError('Bound presentation grid differs: ' + repr((bits, actual_values, expected)))
            grid.append(dict(bits=list(bits), result=actual_values))
        for variant in ('other_judge', 'other_issue', 'other_standard', 'empty_candidates', 'other_message', 'other_goal', 'other_voice', 'outsider', 'not_scholar', 'other_permitted_target', 'public_prohibited'):
            qualification = variant not in ('other_judge', 'other_issue', 'other_standard', 'empty_candidates')
            actual = variant in ('other_permitted_target', 'public_prohibited')
            permission = variant not in ('other_permitted_target', 'public_prohibited')
            expected = [qualification, actual, permission, permission, actual, actual, False, False, True]
            actual_values = values(data, model_for(data, variant=variant))
            if actual_values != expected: raise ValueError('Bound presentation contrast differs: ' + repr((variant, actual_values, expected)))
            cases[variant] = actual_values
        results.append(dict(grid=grid, cases=cases, disquotations_removed=data['disquotations_removed'])); print('Bound source presentation/permission contrasts passed', flush=True)
    return results


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); texts.append(text); doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Public divergent judgment artifact differs')
        for notation in ('full', 'compact'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc: raise ValueError('Public divergent judgment roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis); sizes[stem] = len(text)
    parent, child = parse((ROOT / PARENT).read_text(encoding='utf-8')), parse(texts[1])
    if child['declarations'][:len(parent['declarations'])] != parent['declarations'] or child['statements'] != parent['statements']: raise ValueError('Historical parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0015')
    segments = []
    for phrase in ('unbeschadet ihrer Amtspflicht', 'vom angenommenen Symbol hier oder da abweichenden Urtheile',
            'in der Qualität der Gelehrten, frei und öffentlich der Welt zur Prüfung darlegen'):
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation',
            range=[start, start + len(phrase)], text=phrase, definitions=list(MEANINGS) + ['hzgu', 'hzx', 'hzb4']))
    paths = {*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_public_divergent_judgments.py', 'scripts/check_public_divergent_judgments.py', 'scripts/compose_partial_divergence.py', 'scripts/compose_speech_principals.py', 'scripts/compose_retained_duties.py',
        'scripts/compose_origin_clock.py', 'scripts/compose_limits.py', 'scripts/compose_situated_criticism.py',
        'scripts/check_assessed_payments.py', 'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py',
        'noema/grammar.py', 'noema/discourse.py', 'noema/meaning_basis.py', 'noema/higher_order_semantics.py', 'noema/finite_semantics.py', 'noema/extraction.py', 'noema/specialization.py',
        'artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_bound_public_presentation_and_nonwaiver', documents=documents, sizes=sizes, interpretation=checks(texts), parent_preserved=True, roundtrips=True,
        new_definitions=5, new_primitives=0, new_author_statements=0, alignment=dict(semantic_completion=False, segments=segments),
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in sorted(paths)})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); args = parser.parse_args(); result = build_report()
    if args.verify_only:
        if result != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Public divergent judgment record differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as f: json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
    print('One message, review goal, action description and retained-duty target verified')


if __name__ == '__main__': main()
