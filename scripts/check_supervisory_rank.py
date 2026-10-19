"""Test a greatest supervisory position, its scope, and its acquisition."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_supervisory_rank import ROOT, FULL, CORE, LIBRARY, BASIS, ANNOTATIONS, PARENT, PARENT_BASIS, parent, build, closure
from scripts.check_guardian_purpose import source_values as previous_values, PEOPLE, SCENES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_designation_order import substantive
from scripts.fetch_supervisory_rank_evidence import PATH as EVIDENCE, validate

INDEX = 'data/semantic-review-index-v63.json'
REPORT = 'reports/supervisory-rank-v1.json'
AUDIT = 'data/supervisory-rank-reading-v1.json'
DOC = 'docs/supervisory-rank-v1.md'


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


def order_checks():
    d = parse((ROOT / LIBRARY).read_text(encoding='utf-8') + '''
r ja[] a.r scope[a] c.r order[a a] c.q[k rqyi[k ja[] p scope p order]].''')
    people = ('one', 'two'); edges = list(product(people, repeat=2)); rows = []
    for mask, selected, candidate in product(product((False, True), repeat=4), product((False, True), repeat=2), people):
        relation = {edge for edge, bit in zip(edges, mask) if bit}
        scope = {p for p, bit in zip(people, selected) if bit}
        reflexive = all((p, p) in relation for p in scope)
        transitive = all((a, c) in relation for a, b, c in product(scope, repeat=3) if (a, b) in relation and (b, c) in relation)
        expected = candidate in scope and reflexive and transitive and all((candidate, p) in relation for p in scope)
        actual = evaluate(d, dict(ja=lambda: candidate, scope=lambda p: p in scope, order=lambda a, b: (a, b) in relation), people, ('now',))
        assert actual == [expected]
        rows.append(dict(edges=list(mask), scope=list(selected), candidate=candidate, value=actual[0]))
    cases = {}
    for name, relation, expected in (
        ('top_with_incomparable_lower_positions', {('one','one'),('two','two'),('three','three'),('one','two'),('one','three')}, True),
        ('maximal_but_not_greatest', {('one','one'),('two','two'),('three','three'),('one','two')}, False),
        ('top_candidate_but_nontransitive', {('one','one'),('two','two'),('three','three'),('one','two'),('one','three'),('two','three'),('three','one')}, False),
        ('all_tied', set(product(('one','two','three'), repeat=2)), True)):
        actual = evaluate(d, dict(ja=lambda:'one', scope=lambda p:True, order=lambda a,b:(a,b) in relation), ('one','two','three'), ('now',))[0]
        assert actual == expected; cases[name] = actual
    for name in ('scope', 'order'):
        v = dict(ja=lambda:'one', scope=lambda p:True, order=lambda a,b:True); v[name] = unknown
        try: evaluate(d, v, people, ('now',))
        except ValueError as e: assert 'Unknown' in str(e)
        else: raise AssertionError(name)
    return dict(combinations=rows, three_position_cases=cases, ordinary_evaluation=True, unknown_inputs_refused=2)


@lru_cache(None)
def questions():
    d = deepcopy(catalog().document)
    d.update(declarations=closure(d, ['di', 'rqyk', 'rqyj']), statements=[])
    text = format_graph(d, 'compact') + 'r za[] a.r zb[] a.r zc[] d.'
    for n in ('di', 'rqyk', 'rqyj'): text += 'q[t[k '+n+'[k za[] k zb[]]][k zc[]]].'
    return parse(text)


def source_values(variant='baseline'):
    v = previous_values(variant); old_dc = v['dc']; old_dv = v['dv']
    def controls(actor, target, scene):
        if scene == 'prior':
            if variant == 'no_past_position': return False
            if variant == 'past_subordinate' and (actor,target) == ('guardtwo','person'): return True
            if variant == 'other_past_target_superior' and (actor,target) == ('guardtwo','other'): return True
            return old_dc(actor,target,'actual')
        if variant in ('subordinate', 'tied_top', 'incomparable', 'nontransitive') and (actor, target, scene) == ('guardtwo', 'person', 'actual'): return True
        if variant == 'nontransitive' and (actor, target, scene) == ('third', 'person', 'actual'): return True
        if variant in ('other_target_superior', 'lower_in_all_assignments') and actor == 'guardtwo' and target == 'other' and scene == 'actual': return True
        if variant == 'lower_in_all_assignments' and (actor,target,scene) == ('guardtwo','person','actual'): return True
        if variant == 'other_context_superior' and (actor,target,scene) == ('guardtwo','person','belief'): return True
        return old_dc(actor, target, scene)
    def order(first, second, target, scene):
        if variant == 'wrong_rank_target' and target != 'other': return False
        if variant == 'wrong_rank_context' and scene != 'prior': return False
        if variant == 'nonreflexive' and first == second: return False
        if variant == 'incomparable': return first == second
        if variant == 'nontransitive':
            return first == second or (first,second) in {('guardone','guardtwo'),('guardone','third'),('guardtwo','third'),('third','guardone')}
        if variant == 'tied_top': return True
        levels = {'guardone':1, 'guardtwo':2}
        return levels.get(first,0) >= levels.get(second,0)
    def assumed(act, actor, target, description, scene):
        return variant != 'no_described_assumption' and old_dv(act, actor, target, scene) and (
            act, actor, target, symbol(description), scene) == (
            'appointmenttwo' if variant == 'different_assumption_act' else 'appointment',
            'other' if variant == 'wrong_assuming_actor' else actor,
            'guards' if variant == 'wrong_assumption_target' else target,
            'rqyk' if variant == 'different_position' else 'rqyj',
            'actual' if variant == 'wrong_assumption_context' else 'prior')
    v.update(za=lambda:'guardone', zb=lambda:'person', zc=lambda:'actual', dc=controls, hzxn=order, hzxo=assumed)
    return v


def source_checks():
    expected_true = {'baseline', 'tied_top', 'other_target_superior', 'other_context_superior', 'other_past_target_superior'}
    inherited_false = {'no_current_role', 'not_prior', 'wrong_assumption_act', 'claimed_only'}
    variants = ('baseline','subordinate','tied_top','incomparable','nontransitive','nonreflexive',
        'other_target_superior','other_context_superior','wrong_rank_target','wrong_rank_context',
        'no_described_assumption','different_assumption_act','wrong_assuming_actor','wrong_assumption_target',
        'different_position','wrong_assumption_context','no_current_role','not_prior','wrong_assumption_act','claimed_only',
        'past_subordinate','no_past_position','other_past_target_superior')
    rows = {}
    for variant in variants:
        actual = evaluate(questions(), source_values(variant), PEOPLE, SCENES, True)
        assert actual[0] == (variant in expected_true), (variant,actual)
        assert actual[1] == (variant not in inherited_false), (variant,actual)
        rows[variant] = actual
    small_people = ('person','guardone','guardtwo','appointment','appointmenttwo','other')
    small_scenes = ('actual','prior','belief'); ordinary = {}
    for variant in ('baseline','subordinate','different_position'):
        v = source_values(variant)
        plain = evaluate(questions(), v, small_people, small_scenes)
        cached = evaluate(questions(), v, small_people, small_scenes, True)
        assert plain == cached == rows[variant]
        ordinary[variant] = dict(ordinary=plain,memoized=cached)
    for name in ('dc','hzxn','hzxo','de','dv'):
        v=source_values();v[name]=unknown
        try:evaluate(questions(),v,PEOPLE,SCENES,True)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    return dict(contrasts=rows,ordinary_comparisons=ordinary,unknown_inputs_refused=5,
        ordinary_domain=dict(individuals=list(small_people),situations=list(small_scenes)),
        existing_definitions_executed=True,same_position_and_assumption_act_required=True,
        position_holds_at_current_and_assumption_situations=True)


def integration_checks():
    d=deepcopy(catalog().document);d.update(declarations=closure(d,['do','db']),statements=[])
    d=parse(format_graph(d,'compact')+'r zc[] d.q[t[k do[k db[]]][k zc[]]].')
    rows={}
    for variant in ('baseline','lower_in_all_assignments','different_position'):
        actual=evaluate(d,source_values(variant),PEOPLE,SCENES,True)
        assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    return dict(contrasts=rows,current_purpose_and_causation_executed=True)


def attribution_checks():
    d=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    for variant in ('baseline','other_node','other_author','other_content','other_context','reversed_order'):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        v.update(dq=lambda:'guardians',wa=lambda:'author',t4=lambda:'payment',wh=lambda:'text',
            uc=lambda n,a,p,s:(n,a,symbol(p),s)==('other' if variant=='other_node' else 'guardians',
                'other' if variant=='other_author' else 'author','un' if variant=='other_content' else 'dp',
                'actual' if variant=='other_context' else 'text'),
            ue=lambda a,b,s:(a,b,s)==(('guardians','payment','text') if variant=='reversed_order' else ('payment','guardians','text')))
        actual=evaluate(d,v,('guardians','payment','author','other'),('text','actual'))
        assert actual==[variant=='baseline'];rows[variant]=actual
    return dict(contrasts=rows,rank_assumption_purpose_and_cause_not_executed=True)


def structure():
    old,new=parent(),catalog()
    assert old.document['statements']==new.document['statements'] and len(new.document['statements'])==44
    assert set(new.entries)-set(old.entries)=={'rqyi','rqyj','rqyk','hzxn','hzxo'}
    assert [n for n in old.entries if old.entries[n]['declaration']!=new.entries[n]['declaration']]==['di']
    assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in old.entries if n!='di')
    saved=deepcopy(old.entries['di']['declaration']);saved['name']='rqyk';assert new.entries['rqyk']['declaration']==saved
    affected=[i for i,s in enumerate(new.document['statements']) if 'di' in {d['name'] for d in closure(new.document,_references(s))}]
    assert affected==[7]
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    for path in index['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));ids=[s['index'] for s in review['selection']['statements']]
        a,b=selection_binding(old,ids),selection_binding(new,ids)
        assert a==review['selection'] and a['statements']==b['statements'] and a['dependencies']==b['dependencies']
        assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in a['dependencies'])
    for ids in ([2,3],[4,42],[6],[5,43]):
        a,b=selection_binding(old,ids),selection_binding(new,ids)
        assert a['statements']==b['statements'] and a['dependencies']==b['dependencies']
        assert all(substantive(old.entries[n])==substantive(new.entries[n]) for n in a['dependencies'])
    for path,text in build().items():assert (ROOT/path).read_text(encoding='utf-8')==text
    for path in (FULL,CORE,LIBRARY):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('compact','full'):
            text=format_graph(d,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    validate(json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8')))
    return dict(preserved_statements=44,changed_definitions=['di'],affected_statements=affected,
        new_primitives=2,new_definitions=3,preserved_review_meanings=11,preceding_four_sentence_meanings_preserved=True,roundtrips=True)


def audit():
    previous='data/guardian-purpose-reading-v1.json';r=json.loads((ROOT/previous).read_text(encoding='utf-8'))
    paths=(PARENT,PARENT_BASIS,INDEX,previous,EVIDENCE,'artifacts/written-units-v1/kant-1784.json',
        'artifacts/first-cause-reading-v1/page-482.jpg','reports/guardian-purpose-v1.json')
    return dict(status='highest_scoped_supervision_not_whole_sentence_review',reviewer='assistant_review',source=r['source'],
        reading='Oberaufsichtを同じ対象への最高位の監督と読み、その特定の立場を同じ先行行為で引き受けて現在も保持する。',
        counterexample='旧diは、同じ対象への上位監督者が別に存在する場合も、以前に引き受けた立場が最高位でない場合も許す。',
        decisions=['既存dcを最高位と同一視せず、その同じ対象への監督主体の範囲で弱い順位を比較する。',
            '反射性と推移性を検査し、全対象以上の最高位を、比較不能な相手を残す極大から分ける。',
            '複数の最高位と、監督者一人だけの範囲を許す。中間担当者や下位者を補わない。',
            '同じ引受け行為が最高位の立場rqyjを指すことをhzxoで要求し、引受け状況でもrqyjを評価する。別行為や別の立場を流用せず、二時点の間の連続保持は補わない。'],
        evidence_limit='歴史辞典は最高位の監督という語義と、他者の行動を定める監督の用法を示す。現実の管轄・順位・制度の正当性や本文全体の等価性までは証明しない。',
        remaining=['監督の実践・順位・立場取得の基礎説明','集団目的の読み、gütigst・schon・auchの働き',
            '当該文・第二段落・二作品全文の意味確認'],whole_sentence_semantically_verified=False,
        whole_unit_semantically_verified=False,semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def build_report():
    results={}
    for name,fn in [('order',order_checks),('source',source_checks),('integration',integration_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=audit();assert json.loads((ROOT/AUDIT).read_text(encoding='utf-8'))==r;validate_hashes(ROOT,r['source_sha256'])
    previous=json.loads((ROOT/'reports/guardian-purpose-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,previous['source_sha256'])
    paths=set(build())|set(parent().source_sha256)|set(r['source_sha256'])|set(previous['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_supervisory_rank.py','scripts/check_supervisory_rank.py','scripts/register_supervisory_rank.py',
        'scripts/fetch_supervisory_rank_evidence.py','tests/test_supervisory_rank.py'}
    return dict(status='highest_supervision_and_matching_assumption',document=FULL,**results,
        alignment=dict(**r['source'],definitions=['rqyi','rqyj','rqyk','di','dk','do','dp'],status='explicit_interpretive_annotation'),
        new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(audit()));write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
