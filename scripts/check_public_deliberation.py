"""Check public grounds, shared proposals and their common temporal milestone."""
import argparse
import hashlib
from itertools import product
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_assessed_payments import description
from scripts.check_conditional_release import values
from scripts.check_described_appraisals import candidate
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts import check_provisional_order as continuing
from scripts.compose_limits import call as k
from scripts.compose_public_deliberation import ROOT, PARENT, BUILDERS, GROUND, PUBLIC, PROPOSAL, POSSIBLE, MILESTONE, SOURCE, CONTINUATION

REPORT = ROOT / 'reports/public-deliberation-v1.json'
DOMAIN = (*continuing.office.DOMAIN, 'p', 'q', 'review', 'reason')
WORLDS = ('w11', 'w10', 'w01', 'w00')
SCENES = ('before', 'after', 'success', 'failure', *WORLDS)
EXTRA = '''r jxholder[] a.r jxgroup[] a.r jxaudience[] a.r jxrecipient[] a.r jxclaim[] a.
r jxsubject[] a.r jxabout[a a d] c.
r jxbefore[] d.r jxafter[] d.r jxassessment[] d.r jxcontext[] d.r jxanchor[] d.
r jxscope[a] c.r jxcorpus[a a d] c.r jxsupported[a a d] c.r jxtruth[a d] c.r jxcomparisons[d] c.
d jxcontents[claim a] e[b point[k jxtruth[v claim v point]]].
r jxreviews[a a a d] c.r jxused[a a d] c.r jxsupports[a a d] c.
r jxaccessible[a a d] c.r jxdisclosed[a a d] c.
r jxmembers[a a d] c.r jxoccurs[a d] c.r jxparticipates[a a d] c.
r jxaddresses[a a d] c.r jxproposes[a a i[e] d] c.
r jxavailable[a a d] c.r jxoutcomes[a a d d] c.
r jxtruthgoal[d] c.d jxdesired[] e[b point[k jxtruthgoal[v point]]].
d jxothergoal[] e[b point[k jxtruthgoal[v point]]].'''
REFS = {n: 'k jx' + n + '[]' for n in ('holder', 'group', 'audience', 'recipient', 'claim', 'before', 'after', 'assessment', 'context', 'anchor')}
REFS.update({n: 'p jx' + n for n in ('scope', 'corpus', 'supported', 'contents', 'comparisons', 'reviews', 'used', 'supports',
    'accessible', 'disclosed', 'members', 'occurs', 'participates', 'addresses', 'proposes', 'available', 'outcomes')})
REFS.update(population=REFS['holder'], stage=REFS['after'], proposal='r[k jxdesired[]]')
REFS.update(subject='k jxsubject[]', about='p jxabout')


def expression(name, fields): return k(name, *(REFS[n] for n, _ in fields))


def setup(text, kind):
    calls = {
        'review': [(n, fields) for n, fields in (('rkm', GROUND), ('rkn', PUBLIC))],
        'proposal': [(n, fields) for n, fields in (('rko', PROPOSAL), ('rkp', POSSIBLE), ('rkq', POSSIBLE))],
        'milestone': [('rkr', MILESTONE)],
        'source': [('hzef', SOURCE)],
    }[kind]
    queries = [expression(n, fields) for n, fields in calls]
    if kind == 'source': queries = ['t[' + x + '][k jxafter[]]' for x in queries]
    return candidate(text, EXTRA + ''.join('q[' + x + '].' for x in queries))


def model_for(doc, grounds=(True,) * 5, advance=True, available=True, successful=True, variant='baseline'):
    reviewed, used, support, access, disclosed = grounds
    model = guarded(doc)
    target = syntax(description(doc, 'k jxdesired[]'))
    members = ('person', 'other', 'reader') if variant == 'all_citizens' else ('person',) if variant == 'single_member' else () if variant == 'empty_group' else ('person', 'other')
    citizens = ('person', 'reader') if variant == 'outsider' else ('person', 'other', 'reader')
    def membership(group, person, point):
        if group == 'issuer': return person in citizens
        if group != 'office': return False
        if variant == 'changed_membership' and point == 'success': return person == 'reader'
        return person in members
    def corpus(holder, claim, stage):
        if holder != 'issuer' or claim not in ('p', 'q'): return False
        if stage == 'before': return claim == 'p' or variant == 'only_publication'
        return stage in ('after', 'success', 'failure') and (claim == 'p' or advance)
    def truth(claim, point):
        if claim == 'p': return point not in ('w01', 'w00')
        if claim == 'q': return point not in ('w10', 'w00')
        return False
    def review(holder, act, claim, stage):
        return reviewed and holder == ('office' if variant == 'wrong_holder' else 'issuer') and act == 'review' and claim in (
            ('p',) if variant == 'wrong_claim' else ('p', 'q')) and stage == 'after'
    def participate(person, act, point):
        if point != 'success' or not successful: return False
        if variant == 'split_acts': return (person, act) in (('person', 'speech'), ('other', 'duty'))
        if variant == 'missing_member' and person == 'other': return False
        return person in ('person', 'other', 'reader') and act == 'speech'
    def proposes(person, act, desc, point):
        if variant == 'different_proposal' and person == 'other': return False
        return participate(person, act, point) and desc.syntax == target
    model.update(jxholder=lambda: 'issuer', jxgroup=lambda: 'office', jxaudience=lambda: 'audience', jxrecipient=lambda: 'authority', jxclaim=lambda: 'q',
        jxsubject=lambda: 'topic', jxabout=lambda claim, subject, point: claim in ('p', 'q') and subject == ('authority' if variant == 'wrong_topic' else 'topic') and point == 'w11',
        jxbefore=lambda: 'before', jxafter=lambda: 'after', jxassessment=lambda: 'w11', jxcontext=lambda: 'success', jxanchor=lambda: 'after',
        jxscope=lambda claim: claim in ('p', 'q'), jxcorpus=corpus, jxsupported=lambda holder, claim, stage: holder == 'issuer' and claim in ('p', 'q'),
        jxtruth=truth, jxcomparisons=lambda point: point in WORLDS,
        jxreviews=review,
        jxused=lambda act, reason, point: used and (act, reason, point) == ('review', 'reason', 'after'),
        jxsupports=lambda reason, act, point: support and (reason, act, point) == ('reason', 'speech' if variant == 'wrong_review' else 'review', 'after'),
        jxaccessible=lambda audience, reason, point: access and (audience, reason, point) == ('issuer' if variant == 'private_evidence' else 'audience', 'reason', 'after'),
        jxdisclosed=lambda audience, claim, point: disclosed and audience == 'audience' and claim in ('p', 'q') and point == ('before' if variant == 'stale_publication' else 'after'),
        jxmembers=membership,
        jxoccurs=lambda act, point: point == 'success' and act in ('speech', 'duty') and successful,
        jxparticipates=participate, jxproposes=proposes,
        jxaddresses=lambda act, recipient, point: act in ('speech', 'duty') and recipient == ('topic' if variant == 'other_recipient' else 'authority') and point == 'success',
        jxavailable=lambda group, plan, point: available and (group, plan, point) == ('office', 'channel', 'before' if variant == 'stale_ability' else 'after'),
        jxoutcomes=lambda group, plan, start, end: (group, plan, start) == ('office', 'channel', 'after') and end in (
            () if variant == 'empty_outcomes' else ('success', 'failure') if variant == 'mixed_outcomes' else ('success',)),
    )
    for name, ref in (('fc', 'jxused'), ('fd', 'jxsupports'), ('dg', 'jxoccurs'), ('df', 'jxparticipates')):
        if name in model: model[name] = model[ref]
    if 'ic' in model:
        order = (('before', 'after'), ('after', 'success'), ('after', 'failure'))
        model['ic'] = lambda first, last, context: context == 'w11' and (first, last) in order and not (
            variant == 'past_result' and first == 'after' or variant == 'reversed_progress' and first == 'before')
    return model


def evaluate(doc, **kwargs): return values(doc, model_for(doc, **kwargs), DOMAIN, SCENES)


def roundtrip(doc):
    for notation in ('full', 'compact'):
        text = format_graph(doc, notation)
        if parse(text) != doc or parse(decode(encode(text, 'v2'))) != doc: raise ValueError('Public deliberation roundtrip differs')


def generic_checks(texts):
    reviews = [setup(t, 'review') for t in texts]; proposals = [setup(t, 'proposal') for t in texts]
    review_cases, proposal_cases = [], []
    for bits in product((False, True), repeat=5):
        want = [all(bits)] * 2
        if [evaluate(d, grounds=bits) for d in reviews] != [want] * len(reviews): raise ValueError('Review used another ground')
        review_cases.append(dict(bits=list(bits), results=want))
    review_contrasts = {}
    for variant in ('wrong_holder', 'wrong_claim', 'wrong_review', 'private_evidence', 'stale_publication', 'only_publication'):
        want = [True, False] if variant == 'only_publication' else [False, False]
        rows = [evaluate(d, variant=variant) for d in reviews]
        if rows != [want] * len(reviews): raise ValueError('Public review contrast ' + variant + ': ' + repr(rows))
        review_contrasts[variant] = want
    if [evaluate(d, advance=False) for d in reviews] != [[True, False]] * len(reviews): raise ValueError('Publicity substituted for information growth')
    for available, successful in product((False, True), repeat=2):
        want = [successful, available and successful, available and successful]
        if [evaluate(d, available=available, successful=successful) for d in proposals] != [want] * len(proposals): raise ValueError('Possibility confused with performance')
        proposal_cases.append(dict(available=available, successful=successful, results=want))
    proposal_contrasts = {}
    for variant in ('all_citizens', 'single_member', 'empty_group', 'outsider', 'changed_membership', 'split_acts', 'missing_member',
                    'different_proposal', 'other_recipient', 'empty_outcomes', 'mixed_outcomes', 'stale_ability'):
        want = [True, True, True] if variant in ('all_citizens', 'changed_membership') else [True, True, False] if variant == 'mixed_outcomes' else [True, False, False] if variant in ('empty_outcomes', 'stale_ability') else [False] * 3
        rows = [evaluate(d, variant=variant) for d in proposals]
        if rows != [want] * len(proposals): raise ValueError('Proposal contrast ' + variant + ': ' + repr(rows))
        proposal_contrasts[variant] = want
    for docs, names in ((reviews, ('jxreviews', 'jxused', 'jxsupports', 'jxaccessible', 'jxdisclosed', 'jxtruth')),
                        (proposals, ('jxmembers', 'jxoccurs', 'jxparticipates', 'jxproposes', 'jxavailable', 'jxoutcomes'))):
        for doc in docs:
            for name in names:
                model = model_for(doc); model[name] = guarded(doc)[name]
                try: values(doc, model, DOMAIN, SCENES)
                except ValueError as exc:
                    if 'Unrelated primitive' not in str(exc): raise
                else: raise ValueError('Unknown public deliberation input guessed: ' + name)
    return dict(review_cases=review_cases, review_contrasts=review_contrasts, proposal_cases=proposal_cases, proposal_contrasts=proposal_contrasts,
        unknown_relations_refused=True, proposal_truth_not_executed=True, fixed_membership=True)


def milestone_checks(texts):
    docs = [setup(texts[0], 'milestone'), *[setup(t, 'source') for t in texts[1:]]]
    cases = []
    for advance, public, available, successful in product((False, True), repeat=4):
        want = [advance and public and available and successful]
        rows = [evaluate(d, advance=advance, grounds=(True, True, True, public, True), available=available, successful=successful) for d in docs]
        if rows != [want] * len(docs): raise ValueError('Milestone disconnected: ' + repr(rows))
        cases.append(dict(advance=advance, public=public, available=available, successful=successful, results=want))
    contrasts = {}
    for variant in ('stale_ability', 'reversed_progress', 'past_result', 'split_acts', 'private_evidence', 'wrong_topic'):
        rows = [evaluate(d, variant=variant) for d in docs[1:]]
        if rows != [[False]] * (len(docs) - 1): raise ValueError('Source milestone contrast ' + variant)
        contrasts[variant] = [False]
    return dict(cases=cases, contrasts=contrasts, same_stage=True, future_results=True, standalone_agrees=True)


def continuation_setup(text):
    refs = dict(REFS, population=REFS['holder'], regime='k zi[]', role='k zf[]', channel='k zh[]',
        criticism='r[' + continuing.MESSAGE + ']', authority='k zj[]', active='p jyactive', citizens='p jycitizens', histories='i[anchor d][p jyhistory]')
    queries = ''.join('q[t[' + k(name, *(refs[n] for n, _ in CONTINUATION)) + '][k jxbefore[]]].' for name in ('hzeg', 'hzeh', 'hzei'))
    return candidate(text, EXTRA + continuing.office.EXTRA + continuing.EXTRA + continuing.SOURCE_EXTRA + queries)


def continuation_model(doc, variant='baseline'):
    # Reuse the public activity classification, but all times and semantic milestone
    # conditions are supplied by this fixture rather than the old jystop truth bit.
    model = model_for(doc, variant=variant)
    old = continuing.source_model(doc)
    for name in ('za', 'zb', 'zc', 'zd', 'ze', 'zf', 'zg', 'zh', 'zi', 'zj', 'zk', 'aa'):
        if name in model: model[name] = old[name]
    for name in ('cb', 'ca', 'cc', 'cd', 'ce', 'h6n', 'h6t', 'h6u', 'h7a', 'h7b'):
        def adapted(*a, name=name):
            a = list(a)
            a[-1] = {'before': 'start', 'after': 'end'}.get(a[-1], 'elsewhere')
            return old[name](*a)
        model[name] = adapted
    model.update(jyhistory=lambda point: point in ('before', 'after'),
        jyactive=lambda regime, point: regime == 'topic' and point in ('before', 'after') and not (variant == 'boundary_order' and point == 'after'),
        jycitizens=lambda population, person, point: population == 'issuer' and person in (('person',) if variant == 'foreign_citizen' else ('person', 'other')) and point in ('before', 'after'),
        ic=lambda first, last, context: (first, last) in (('before', 'after'), ('after', 'success'), ('after', 'failure')) and context in ('before', 'w11'))
    return model


def continuation_checks(texts):
    contrasts = {}
    for variant, want in (('baseline', [True] * 3), ('boundary_order', [True, True, False]),
                          ('private_evidence', [False, True, False]), ('split_acts', [False, True, False]),
                          ('wrong_topic', [False, True, False]), ('foreign_citizen', [False, True, False])):
        rows = []
        for text in texts:
            doc = continuation_setup(text)
            rows.append(values(doc, continuation_model(doc, variant), DOMAIN, SCENES))
        if rows != [want] * len(texts): raise ValueError('Concrete milestone continuation ' + variant + ': ' + repr(rows))
        contrasts[variant] = want
    return dict(contrasts=contrasts, arbitrary_milestone_bit_not_used=True, actual_criticism_not_executed=True)


def build_report():
    texts, documents, sizes = [], {}, {}
    for builder, stem in BUILDERS:
        text, basis = builder(); doc = parse(text); texts.append(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads((ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis: raise ValueError('Stored public deliberation differs')
        roundtrip(doc); documents[basis['document']] = audit_basis(doc, basis)
        sizes[stem] = dict(characters=len(text), statements=len(doc['statements']))
    doc, parent = parse(texts[1]), parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'] != parent['statements']: raise ValueError('Parent changed')
    unit = next(u for u in json.loads((ROOT / 'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id'] == 'kant-1784:u0013')
    phrases = ['bis die Einsicht in die Beschaffenheit dieser Sachen öffentlich so weit gekommen und bewähret worden',
        'daß sie durch Vereinigung ihrer Stimmen (wenn gleich nicht aller) einen Vorschlag vor den Thron bringen könnte']
    segments = []
    for phrase in phrases:
        if unit['text'].count(phrase) != 1: raise ValueError('Ambiguous source range')
        start = unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'], unit_sha256=unit['text_sha256'], status='explicit_interpretive_annotation', range=[start, start + len(phrase)],
            text=phrase, definitions=['rkm', 'rkn', 'rko', 'rkp', 'rkr', 'hzef', 'hzeg', 'hzeh', 'hzei']))
    paths = [*documents, PARENT, *['data/' + stem + '-basis-v1.json' for _, stem in BUILDERS],
        'scripts/compose_public_deliberation.py', 'scripts/check_public_deliberation.py', 'scripts/check_provisional_order.py',
        'scripts/check_assessed_payments.py', 'scripts/check_conditional_release.py', 'scripts/check_described_appraisals.py',
        'scripts/check_public_assessment.py', 'scripts/check_rod_setup.py', 'noema/finite_semantics.py', 'noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json']
    return dict(status='partial_public_deliberation_milestone', documents=documents, sizes=sizes,
        generic=generic_checks([texts[0], texts[2]]), milestone=milestone_checks(texts), continuation=continuation_checks(texts[1:]),
        alignment=dict(segments=segments, semantic_completion=False), new_definitions=10, new_primitives=0,
        new_author_statements=0, parent_preserved=True, roundtrips=True,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
        source_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest() for n in paths})


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--verify-only', action='store_true'); options = parser.parse_args()
    report = build_report()
    if options.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')): raise ValueError('Public deliberation report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream: json.dump(report, stream, ensure_ascii=False, indent=2); stream.write('\n')
    print('Public grounds, shared proposals, possibility and the concrete continuation milestone checked')


if __name__ == '__main__': main()
