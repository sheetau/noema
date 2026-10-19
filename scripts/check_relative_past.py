"""Distinguish long before the reference from long before every later state."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding
from noema.script import transcribe
from scripts.compose_relative_past import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, MEANINGS, build, parent, closure
from scripts.check_motive_causes import evaluate, unknown, symbol
from scripts.check_designation_order import substantive

REPORT = 'reports/relative-past-v1.json'
AUDIT = 'data/relative-past-reading-v1.json'
INDEX = 'data/semantic-review-index-v41.json'
DOC = 'docs/relative-past-v1.md'
SCENES = ('child', 'release', 'early', 'now', 'late')
DOMAIN = ('person', 'guide', 'change', 'nature')


def temporal(variant='baseline', bits=(False, True, True)):
    reference = 'child' if variant == 'reference_before' else 'release' if variant == 'reference_same' else 'now'
    history = set(SCENES)
    if variant == 'reference_outside':history.remove('now')
    if variant == 'point_outside':history.remove('release')
    extent = set(SCENES[2:])
    if variant == 'empty_extent':extent = set()
    if variant == 'hole':extent.remove('now')
    if variant == 'point_in_extent':extent.add('release')
    if variant == 'recent_but_future_far':extent = {'late'};bits = (False, False, True)
    if variant == 'reference_outside':extent = {'early', 'late'};bits = (True, True, True)
    if variant in ('reference_before', 'reference_same', 'all_distant'):bits = (True, True, True)
    if variant == 'not_long_ago':bits = (False, False, False)
    def before(a, b):
        return SCENES.index(a) < SCENES.index(b) or (variant == 'cycle' and (a, b) == ('late', 'early'))
    distances = {s for s, bit in zip(SCENES[2:], bits, strict=True) if bit}
    if variant in ('reference_before', 'reference_same'):distances.add(reference)
    return reference, lambda s: s in history, lambda s: s in extent, before, lambda a,b: a == 'release' and b in distances


def generic_checks():
    doc = parse((ROOT / LIBRARY).read_text(encoding='utf-8'))
    doc = parse(format_graph(doc, 'compact') +
        'r jhistory[d] c.r jextent[d] c.r jbefore[d d] c.r jdistant[d d] c.r jpoint[] d.r jreference[] d.' +
        'q[k rqxe[p jhistory p jextent p jbefore k jpoint[] k jreference[] p jdistant]].' +
        'q[k tf[p jhistory p jextent p jbefore k jpoint[] p jdistant]].')
    def run(variant='baseline', bits=(False, True, True), missing=None):
        ref, hist, scope, order, distance = temporal(variant, bits)
        v = dict(jhistory=hist, jextent=scope, jbefore=order, jdistant=distance,
            jpoint=lambda: 'release', jreference=lambda: ref)
        if missing:v[missing] = unknown
        return evaluate(doc, v, ('unused',), SCENES)
    rows = []
    for bits in product((False, True), repeat=3):
        actual = run(bits=bits);assert actual == [bits[1], all(bits)], (bits, actual)
        rows.append(dict(distances_to_early_now_late=list(bits), values=actual))
    expectations = dict(baseline=[True, False], all_distant=[True, True],
        recent_but_future_far=[False, True], reference_outside=[False, True], reference_before=[False, True],
        reference_same=[False, True], point_outside=[False, False], empty_extent=[False, False],
        hole=[False, False], point_in_extent=[False, False], cycle=[False, False], not_long_ago=[False, False])
    contrasts = {}
    for variant, expected in expectations.items():
        contrasts[variant] = run(variant);assert contrasts[variant] == expected, (variant, contrasts[variant])
    for name in ('jhistory', 'jextent', 'jbefore', 'jdistant'):
        try:run(missing=name)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(combinations=rows, contrasts=contrasts, unknown_inputs_refused=4, ordinary_evaluation=True)


@lru_cache(None)
def source_document():
    doc = parse((ROOT / FULL).read_text(encoding='utf-8'))
    doc.update(declarations=closure(doc, ['km', 'qg', 'tf']), statements=[])
    for name in ('km', 'qg'):
        row = deepcopy(parent().entries[name]['declaration']);row['name'] = 'zold' + name
        doc['declarations'].append(row)
    text = format_graph(doc, 'compact') + 'r jperson[] a.r jprocess[] a.r jbefore[] d.r jafter[] d.r jreference[] d.'
    for name in ('km', 'zoldkm'):
        text += 'q[k ' + name + '[k jperson[] k jprocess[] k jbefore[] k jafter[] k jreference[]]].'
    for name in ('qg', 'zoldqg'):
        text += 'q[t[k ' + name + '[k jperson[]]][k jreference[]]].'
    return parse(text)


def source_values(variant='baseline'):
    ref, hist, scope, order, distance = temporal(variant)
    def context(person, ctx):
        return person == ('guide' if variant == 'other_history_person' else 'person') and ctx == ref
    def dependency(person, guide, scene):
        return (person, guide) == ('person', 'person' if variant == 'self_guidance_only' else 'guide') and (
            scene == 'child' and variant != 'no_prior_dependence' or scene == 'release' and variant == 'still_dependent')
    def declares(nature, person, state, scene):
        return variant != 'no_declaration' and (nature, person, symbol(state), scene) == (
            'guide' if variant == 'other_declarer' else 'nature', 'guide' if variant == 'other_declared_person' else 'person',
            'kc' if variant == 'other_declared_state' else 'qf', 'early' if variant == 'other_declaration_time' else 'release')
    return dict(jperson=lambda: 'person', jprocess=lambda: 'change', jbefore=lambda: 'child',
        jafter=lambda: 'release', jreference=lambda: ref,
        ia=lambda person, ctx, scene: context(person, ctx) and hist(scene),
        ib=lambda person, ctx, scene: context(person, ctx) and scope(scene),
        ic=lambda a, b, ctx: ctx == ref and order(a,b),
        kd=lambda a, b, ctx: ctx == ('child' if variant == 'other_distance_context' else ref) and distance(a,b),
        aa=lambda person: person in ('person', 'guide'),
        ka=lambda person, scene: person == 'person' and scene != 'child' and variant != 'not_mature',
        kb=dependency,
        ag=lambda process, a, b: variant != 'no_process' and (process, a, b) == ('change', 'child', 'release'),
        la=lambda person, process, a, b: variant != 'no_affected_subject' and (person, process, a, b) == (
            'guide' if variant == 'other_affected_person' else 'person', 'change', 'child', 'release'),
        qb=lambda: 'nature', qc=declares)


def source_checks():
    doc = source_document()
    timing = dict(baseline=[True, False], all_distant=[True, True], recent_but_future_far=[False, True],
        reference_outside=[False, True], reference_before=[False, True], reference_same=[False, True],
        point_outside=[False, False], empty_extent=[False, False], hole=[False, False],
        point_in_extent=[False, False], cycle=[False, False], not_long_ago=[False, False])
    expected = {v: result * 2 for v, result in timing.items()}
    for v in ('no_process', 'no_affected_subject', 'other_affected_person', 'no_prior_dependence', 'self_guidance_only', 'still_dependent', 'not_mature'):
        expected[v] = [False, False, True, False]
    for v in ('no_declaration', 'other_declarer', 'other_declared_person', 'other_declared_state', 'other_declaration_time'):
        expected[v] = [True, False, False, False]
    for v in ('other_history_person', 'other_distance_context'):expected[v] = [False] * 4
    rows = {}
    for variant, result in expected.items():
        rows[variant] = evaluate(doc, source_values(variant), DOMAIN, SCENES)
        assert rows[variant] == result, (variant, rows[variant], result)
    for name in ('ia', 'ib', 'ic', 'kd', 'ag', 'la', 'qc'):
        v = source_values();v[name] = unknown
        try:evaluate(doc, v, DOMAIN, SCENES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows, actual_transition_witness_and_depiction_executed=True,
        old_and_new_bodies_compared=True, unknown_inputs_refused=7, ordinary_evaluation=True,
        population_concession_and_ease_not_reexecuted=True)


def attribution_checks():
    doc = parse((ROOT / CORE).read_text(encoding='utf-8'))
    rows = {}
    for variant in ('baseline', 'other_author', 'other_node', 'other_content', 'reverse_order', 'other_scene', 'reversed_depiction', 'other_depiction'):
        v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        def claims(node, author, content, scene):
            return (node, author, symbol(content), scene) == ('other' if variant == 'other_node' else 'cause',
                'other' if variant == 'other_author' else 'author', 'kf' if variant == 'other_content' else 'mx',
                'other' if variant == 'other_scene' else 'text')
        def depicts(node, author, target, depiction, scene):
            a,b = ('qg','kf') if variant == 'reversed_depiction' else ('kf','qf') if variant == 'other_depiction' else ('kf','qg')
            return (node,author,symbol(target),symbol(depiction),scene) == (
                'other' if variant == 'other_node' else 'cause', 'other' if variant == 'other_author' else 'author', a,b,
                'other' if variant == 'other_scene' else 'text')
        v.update(mw=lambda:'cause',wa=lambda:'author',wh=lambda:'text',wg=lambda:'opening',uc=claims,qa=depicts,
            ue=lambda a,b,s:(a,b,s)==(('cause','opening','text') if variant=='reverse_order' else ('opening','cause','text')))
        rows[variant] = evaluate(doc,v,('cause','opening','author','other'),('text',))
        expected = [variant in ('baseline','reversed_depiction','other_depiction'),variant in ('baseline','other_content','reverse_order')]
        assert rows[variant] == expected,(variant,rows[variant])
    return dict(contrasts=rows, all_temporal_and_causal_facts_unknown=True, ordinary_evaluation=True)


def structure():
    old,new = parent(),load_catalog(ROOT,BASIS)
    assert old.document['statements']==new.document['statements'] and len(new.document['statements'])==42
    assert set(new.entries)-set(old.entries)=={'rqxe'}
    changed=[n for n in old.entries if old.entries[n]['declaration']!=new.entries[n]['declaration']]
    assert set(changed)=={'km','qg'}
    assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in old.entries if n not in MEANINGS)
    affected=[i for i,s in enumerate(new.document['statements']) if set(changed)&{d['name'] for d in closure(new.document,_references(s))}]
    assert affected==[2,3],affected
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[r['index'] for r in review['selection']['statements']]
        before,after=selection_binding(old,indices),selection_binding(new,indices)
        assert before==review['selection'] and before['statements']==after['statements'] and before['dependencies']==after['dependencies']
        assert not set(indices)&set(affected)
        assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in before['dependencies'])
    for name,body in build().items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE,LIBRARY):
        d=parse((ROOT/name).read_text(encoding='utf-8'))
        for style in ('compact','full'):
            text=format_graph(d,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    return dict(preserved_statements=42,changed_definitions=sorted(changed),affected_statements=affected,
        new_definitions=1,new_primitive_relations=0,preserved_review_meanings=11,roundtrips=True)


def audit():
    inv='artifacts/written-units-v1/kant-1784.json'
    unit=next(u for u in json.loads((ROOT/inv).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    phrase='nachdem sie die Natur längst von fremder Leitung frei gesprochen (naturaliter majorennes)'
    start=unit['text'].index(phrase)
    return dict(status='reference_relative_past_repaired_not_whole_sentence_review',reviewer='assistant_review',
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],text=phrase),
        consulted='https://korpora.org/Kant/aa08/035.html',
        findings=['旧km・qgは解放後の範囲の各時点まで十分な時間経過を要求し、解放直後からの継続を排除していた。',
            '逆に遠い将来だけを範囲にすると、基準時点での解放が最近でも旧条件が成立し得た。'],
        decisions=['継続範囲の全体より前という条件teを維持し、長い経過の比較先を明示した基準点へ分離する。',
            '基準点も同じ履歴に属し、解放後にあることを要求する。本文用の基準は引用内容を評価する状況とする。',
            '自然の宣告という描写にも同じ時間構造を用いるが、現実の自然の発話とはしない。'],
        first_sentence_review=dict(release='時間基準の不足を修正。成熟の意味とラテン語の照合は残る。',
            persistence='同じ人物の同じ履歴と範囲を参照する。態度の持続と生涯の粒度は引き続き読解対象。',
            guardians='oiは先行するkgの該当者を保持する。容易さの尺度と他者範囲内の全称条件は部分的な読み。'),
        remaining=['第一文全体の語義・数量・時間範囲・容易さの意味確認','第二段落残部と二作品全文'],
        whole_unit_semantically_verified=False,
        test_limit='現行kmの移行証人とqgの描写を実行し旧版と比較する。kfの全存在探索、人口比率、譲歩、容易さの全定義を再実行したとはしない。',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (inv,PARENT,PARENT_BASIS,
            'docs/transitions-v1.md','docs/persistence-v1.md','docs/easy-roles-v1.md','docs/figurative-frames-v1.md')})


def build_report():
    results={}
    for name,fn in [('generic',generic_checks),('source',source_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=audit();assert json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))==reading
    paths=set(build())|set(parent().source_sha256)|set(reading['source_sha256'])|{AUDIT,INDEX,DOC,
        'scripts/compose_relative_past.py','scripts/check_relative_past.py','tests/test_relative_past.py',
        'scripts/check_motive_causes.py','scripts/check_designation_order.py','scripts/compose_falling_depiction.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py',
        'noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    source=reading['source']
    return dict(status='partial_reference_relative_past',document=FULL,**results,
        alignment=dict(unit=source['unit'],unit_sha256=source['unit_sha256'],range=source['range'],source=source['text'],
            definitions=['rqxe','km','kf','qg'],status='explicit_interpretive_annotation',full_semantic_equivalence=False),
        new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(audit()));write_exact(ROOT/REPORT,encoded(build_report()))
    print('Reference-relative past checked',flush=True)


if __name__=='__main__':main()
