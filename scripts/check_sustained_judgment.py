"""Check judgment bindings, all episode judgments and nonliteral attribution."""
import argparse
import hashlib
from itertools import product
import json

from noema.first_order_proofs import verify
from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_conditional_release import values
from scripts.check_controlled_gait import alignment as gait_alignment
from scripts.check_described_appraisals import candidate
from scripts.check_described_explanations import symbol
from scripts.check_rod_setup import guarded
from scripts.compose_sustained_judgment import ROOT, PARENT, generic_composed, source_composed

REPORT = ROOT / 'reports/sustained-judgment-v1.json'


def judgment_checks():
    doc = parse(generic_composed()[0] + '''r za[] a.r zb[] a.r zc[] d.
r zd[a a d] c.r ze[a a a d] c.r zf[a a d] c.r zg[a a d] c.r zh[a a d] c.r zi[a a d] c.r zj[a a a d] c.
q[k rcr[k za[] k zb[] k zc[] p zd p ze p zf p zg p zh p zi p zj]].''')
    domain = ('person', 'other', 'faculty', 'judgment', 'elsewhere', 'matter', 'reason', 'different')
    scenes = ('now', 'past')
    def run(flags, variant='baseline'):
        own, use, judge, matter, reason, support, guidance = flags
        model = guarded(doc)
        model.update(za=lambda: 'person', zb=lambda: 'judgment', zc=lambda: 'now',
            zd=lambda faculty, person, point: own and (faculty, person, point) == ('faculty',
                'other' if variant == 'other_owner' else 'person', 'now'),
            ze=lambda person, faculty, act, point: use and (person, faculty, act, point) == ('person',
                'different' if variant == 'other_faculty' else 'faculty',
                'elsewhere' if variant == 'other_use' else 'judgment', 'now'),
            zf=lambda person, act, point: judge and (person, act, point) == ('person', 'judgment', 'now'),
            zg=lambda act, target, point: matter and (act, target, point) == ('judgment', 'matter', 'now'),
            zh=lambda act, why, point: reason and (act, why, point) == ('judgment', 'reason', 'now'),
            zi=lambda why, act, point: support and (why, act, point) == (
                'different' if variant == 'other_reason' else 'reason',
                'elsewhere' if variant == 'other_supported_judgment' else 'judgment',
                'past' if variant == 'past_support' else 'now'),
            zj=lambda guide, person, act, point: guidance and (guide, person, act, point) == (
                'person' if variant == 'self_guidance' else 'other', 'person',
                'elsewhere' if variant == 'other_guided_judgment' else 'judgment', 'now'))
        return values(doc, model, domain, scenes)
    accepted = 0
    for flags in product((False, True), repeat=7):
        actual = run(flags)
        if actual != [all(flags[:6]) and not flags[6]]:
            raise ValueError('Unbound reason or mere use accepted')
        accepted += actual[0]
    rows = {}
    for variant in ('other_owner', 'other_faculty', 'other_use', 'other_reason',
            'other_supported_judgment', 'past_support', 'self_guidance', 'other_guided_judgment'):
        permitted = variant in ('self_guidance', 'other_guided_judgment')
        actual = run((True,) * 6 + (permitted,), variant)
        if actual != [permitted]:
            raise ValueError('Judgment binding mismatch: ' + variant)
        rows[variant] = actual
    return {'truth_cases': 128, 'accepted_truth_cases': accepted, 'binding_cases': rows}


def general_laws():
    text = generic_composed()[0] + '''r za[] a.r zb[] a.r zc[] d.
r zd[a a d] c.r ze[a a a d] c.r zf[a a d] c.r zg[a a d] c.r zh[a a d] c.r zi[a a d] c.r zj[a a a d] c.'''
    judgment = 'k rcr[k za[] k zb[] k zc[] p zd p ze p zf p zg p zh p zi p zj]'
    performed = 'k zf[k za[] k zb[] k zc[]]'
    ownuse = 'g faculty a[w[k zd[v faculty k za[] k zc[]]][k ze[k za[] v faculty k zb[] k zc[]]]]'
    supported = 'g reason a[w[k zh[k zb[] v reason k zc[]]][k zi[v reason k zb[] k zc[]]]]'
    independent = 'u[g other a[w[u[e[v other][k za[]]]][k zj[v other k za[] k zb[] k zc[]]]]]'
    claims = {'same_person_judged': f'y[{judgment}][{performed}]',
        'same_owned_faculty_used': f'y[{judgment}][{ownuse}]',
        'same_used_reason_supports_judgment': f'y[{judgment}][{supported}]',
        'no_other_directs_this_judgment': f'y[{judgment}][{independent}]',
        'own_use_alone_suffices': f'y[{ownuse}][{judgment}]',
        'supported_reason_alone_suffices': f'y[{supported}][{judgment}]'}
    results = verify(parse(text + ''.join(f's[{body}].' for body in claims.values())))
    if [row['status'] for row in results] != ['valid'] * 4 + ['invalid'] * 2:
        raise ValueError('Independent judgment laws failed')
    return {name: {'status': row['status'], 'countermodel_found': row['countermodel'] is not None,
        'formula_sha256': hashlib.sha256(row['formula'].encode()).hexdigest()}
        for name, row in zip(claims, results, strict=True)}


def source_checks():
    doc = candidate(source_composed()[0], '''r za[] a.r zb[] a.r zc[] d.r zd[] d.
q[k h5d[k za[] k zb[] k zc[] k zd[]]].q[t[k h5e[k za[]]][k zd[]]].''')
    domain = ('person', 'other', 'faculty', 'episode', 'foreign', 'early', 'late', 'matter', 'rfirst', 'rlast')
    scenes = ('start', 'middle', 'end', 'future')
    variants = ('baseline', 'reasons_change', 'middle_unsupported',
        'middle_guided', 'foreign_judgment_guided', 'no_endpoint_judgment', 'no_earlier_judgment', 'no_judgments',
        'other_owner', 'other_faculty', 'other_judgment_reason', 'no_occurrence', 'no_human',
        'empty_scope', 'singleton_scope', 'omitted_middle', 'scope_after_end', 'wrong_episode_scope',
        'wrong_completion_scope', 'wrong_episode_parts', 'future_completion', 'cycle', 'anchor_outside')
    rows = {}
    for variant in variants:
        end = 'future' if variant == 'future_completion' else 'end'
        def judgments(person, act, point):
            if person != 'person' or variant == 'no_judgments':
                return False
            return (variant != 'no_earlier_judgment' and (act, point) == ('early', 'middle')) or (
                variant != 'no_endpoint_judgment' and (act, point) == ('late', end)) or (
                variant == 'foreign_judgment_guided' and (act, point) == ('foreign', 'middle'))
        def parts(act, episode, point):
            return episode == ('foreign' if variant == 'wrong_episode_parts' else 'episode') and (
                (act, point) == ('early', 'middle') or (act, point) == ('late', end))
        def scope(episode, last, point):
            if variant == 'empty_scope' or (episode, last) != (
                    'foreign' if variant == 'wrong_episode_scope' else 'episode',
                    'start' if variant == 'wrong_completion_scope' else end):
                return False
            if variant == 'singleton_scope':
                return point == end
            return point in scenes[:3] and not (variant == 'omitted_middle' and point == 'middle') or (
                variant in ('scope_after_end', 'future_completion') and point == 'future')
        def reasons(act, reason, point):
            if variant == 'other_judgment_reason':
                return act == 'foreign'
            return (act, reason, point) in (('early', 'rfirst', 'middle'),
                ('late', 'rlast' if variant == 'reasons_change' else 'rfirst', end))
        model = guarded(doc)
        model.update(za=lambda: 'person', zb=lambda: 'episode', zc=lambda: end, zd=lambda: 'end',
            aa=lambda person: variant != 'no_human' and person == 'person',
            ia=lambda person, anchor, point: person == 'person' and not (variant == 'anchor_outside' and point == anchor),
            ic=lambda first, last, anchor: scenes.index(first) < scenes.index(last) or (
                variant == 'cycle' and (first, last) == ('end', 'start')),
            dg=lambda act, point: variant != 'no_occurrence' and (act, point) == ('episode', end),
            h5a=scope, h5b=parts, fa=judgments,
            ab=lambda faculty, person, point: (faculty, person) == ('faculty',
                'other' if variant == 'other_owner' else 'person'),
            ac=lambda person, faculty, act, point: person == 'person' and faculty == (
                'other' if variant == 'other_faculty' else 'faculty') and judgments(person, act, point),
            fb=lambda act, matter, point: matter == 'matter' and judgments('person', act, point),
            fc=reasons, fd=lambda reason, act, point: reasons(act, reason, point) and not (
                variant == 'middle_unsupported' and point == 'middle'),
            ad=lambda guide, person, act, point: (guide, person, act, point) == ('other', 'person',
                'early' if variant == 'middle_guided' else 'foreign', 'middle'))
        actual = values(doc, model, domain, scenes)
        expected = variant in ('baseline', 'reasons_change', 'foreign_judgment_guided')
        if actual != [expected, expected]:
            raise ValueError('Sustained judgment mismatch: ' + str((variant, actual)))
        rows[variant] = actual
    return {'cases': rows, 'gait_and_achievement_primitives_guarded_against_execution': True}


def episode_laws():
    text = generic_composed()[0] + '''r za[d] c.r zb[d d] c.r zc[d] c.r zd[] a.r ze[] a.r zf[] d.
r zg[a d] c.r zh[a a d] c.r zi[a a d] c.r zj[a a d] c.r zk[] d.'''
    episode = lambda last: f'k rcs[p za p zb p zc k zd[] k ze[] k {last}[] p zg p zh p zi p zj]'
    body = episode('zf')
    endpoint = 'g judgment a[w[k zh[v judgment k ze[] k zf[]]][w[k zi[k zd[] v judgment k zf[]]][k zj[k zd[] v judgment k zf[]]]]]'
    all_judgments = 'f point d[f judgment a[y[w[k zc[v point]][w[k zh[v judgment k ze[] v point]][k zi[k zd[] v judgment v point]]]][k zj[k zd[] v judgment v point]]]]'
    finished = 'f point d[y[k zc[v point]][x[e[v point][k zf[]]][k zb[v point k zf[]]]]]'
    earlier_judgment = 'g point d[w[k zc[v point]][w[k zb[v point k zf[]]][g judgment a[w[k zh[v judgment k ze[] v point]][k zi[k zd[] v judgment v point]]]]]]'
    structure = 'w[k tb[p za p zc p zb]][w[k zc[k zf[]]][w[' + earlier_judgment + '][w[k zg[k ze[] k zf[]]][' + finished + ']]]]'
    claims = {
        'completed_episode_has_adequate_endpoint_judgment': f'y[{body}][{endpoint}]',
        'every_performed_component_judgment_is_adequate': f'y[{body}][{all_judgments}]',
        'same_episode_scope_has_unique_completion': f'y[w[{body}][{episode("zk")} ]][e[k zf[]][k zk[]]]',
        'good_endpoint_alone_is_enough': f'y[w[{structure}][{endpoint}]][{body}]',
    }
    results = verify(parse(text + ''.join(f's[{formula}].' for formula in claims.values())))
    if [row['status'] for row in results] != ['valid'] * 3 + ['invalid']:
        raise ValueError('Whole episode judgment laws failed')
    return {name: {'status': row['status'], 'countermodel_found': row['countermodel'] is not None,
        'formula_sha256': hashlib.sha256(row['formula'].encode()).hexdigest()}
        for name, row in zip(claims, results, strict=True)}


def attribution_checks():
    doc = candidate(source_composed()[0], 'q[k h5g[]].')
    rows = {}
    for variant in ('baseline', 'node', 'author', 'target', 'depiction', 'context', 'reversed'):
        expected = ['node', 'author', 'h5e', 'h4z', 'now']
        if variant in ('node', 'author', 'target', 'depiction', 'context'):
            expected[('node', 'author', 'target', 'depiction', 'context').index(variant)] = 'other'
        if variant == 'reversed':
            expected[2:4] = ['h4z', 'h5e']
        model = guarded(doc)
        model.update(h5f=lambda: 'node', wa=lambda: 'author', wh=lambda: 'now',
            qa=lambda node, author, target, depiction, point: [node, author, symbol(target), symbol(depiction), point] == expected)
        actual = values(doc, model, ('node', 'author', 'other'), ('now', 'other'))
        if actual != [variant == 'baseline']:
            raise ValueError('Figurative attribution executed contents or reversed direction')
        rows[variant] = actual
    return {'cases': rows, 'all_content_primitives_guarded_against_execution': True}


def alignment():
    row = gait_alignment()
    row['definitions'] = ['h5c', 'h5d', 'h5e', 'h5g']
    row['remaining'] = ['full meanings of stability and secure gait', 'support criteria and cognitive foundations',
        'temporal connection to self-achievement', 'dennoch concession and Daher inference',
        'final counting of people satisfying the complete conclusion']
    return row


def build_report():
    documents = {}
    for builder, stem in ((generic_composed, 'sustained-judgment'), (source_composed, 'kant-sustained-judgment')):
        text, basis = builder()
        doc = parse(text)
        if (ROOT / basis['document']).read_text(encoding='utf-8') != text or json.loads(
                (ROOT / ('data/' + stem + '-basis-v1.json')).read_text(encoding='utf-8')) != basis:
            raise ValueError('Stored sustained judgment differs')
        for notation in ('compact', 'full'):
            form = format_graph(doc, notation)
            if parse(form) != doc or parse(decode(encode(form, 'v2'))) != doc:
                raise ValueError('Sustained judgment roundtrip differs')
        documents[basis['document']] = audit_basis(doc, basis)
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])] != parent['declarations'] or doc['statements'][:-1] != parent['statements']:
        raise ValueError('Earlier source changed')
    paths = list(documents) + [PARENT, 'data/sustained-judgment-basis-v1.json', 'data/kant-sustained-judgment-basis-v1.json',
        'scripts/compose_sustained_judgment.py', 'scripts/check_sustained_judgment.py',
        'scripts/check_controlled_gait.py', 'noema/discourse.py', 'noema/finite_semantics.py',
        'noema/first_order_proofs.py', 'artifacts/written-units-v1/kant-1784.json', 'reports/written-units-v1.json']
    return json.loads(json.dumps({'status': 'partial_sustained_judgment_as_gait_target', 'documents': documents,
        'generic': judgment_checks(), 'general_laws': general_laws(), 'episode_laws': episode_laws(), 'source_cases': source_checks(),
        'attribution_cases': attribution_checks(), 'alignment': alignment(),
        'roundtrips': True, 'parent_preserved': True, 'new_source_assertions': 1,
        'notation_size': {'canonical_source_document_characters': len(text),
            'added_characters': len(text) - len((ROOT / PARENT).read_text(encoding='utf-8'))},
        'verified_full_units': {'kant-1784': 0, 'einstein-1905': 0},
        'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in paths}}, ensure_ascii=False))


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--verify-only', action='store_true')
    args = cli.parse_args()
    report = build_report()
    if args.verify_only:
        if report != json.loads(REPORT.read_text(encoding='utf-8')):
            raise ValueError('Sustained judgment report differs')
    else:
        with REPORT.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print('Independent judgments throughout one episode and nonliteral gait attribution checked')


if __name__ == '__main__':
    main()
