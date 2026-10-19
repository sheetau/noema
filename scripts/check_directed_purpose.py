"""Compare unanimous purpose with explicit, same-act directed participation."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_directed_purpose import ROOT, FULL, CORE, LIBRARY, BASIS, PARENT, PARENT_BASIS, MEANINGS, LIMITS, parent, build, closure
from scripts.check_supervisory_rank import source_values as previous_values
from scripts.check_guardian_purpose import PEOPLE, SCENES, goal_key
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v65.json'
REPORT = 'reports/directed-purpose-v1.json'
READING = 'data/directed-purpose-reading-v1.json'
DOC = 'docs/directed-purpose-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def generic():
    d = deepcopy(catalog().document)
    d.update(declarations=closure(d, ['rqyu', 'rqyf']), statements=[])
    return parse(format_graph(d, 'compact')+'''
r ja[] a.r js[] d.r jactors[a] c.r occurs[a d] c.r performs[a a d] c.
r aims[a a i[e] d] c.r guides[a a a i[e] d] c.r truth[d] c.
d jgoal[] e[b scene[k truth[v scene]]].
q[k rqyu[p jactors k ja[] r[k jgoal[]] k js[] p occurs p performs p aims p guides]].
q[k rqyf[p jactors k ja[] r[k jgoal[]] k js[] p occurs p performs p aims]].
''')


def generic_values(bits=(True, True, True, True, False, True, False), variant='baseline'):
    occurs, first, second, aim_first, aim_second, forward, reverse = bits
    people = {'one', 'two'}
    if variant == 'empty': people = set()
    if variant == 'singleton': people = {'one'}
    def aims(actor, act, goal, scene):
        return (act, symbol(goal), scene) == ('work', 'jgoal', 'now') and {
            'one': aim_first, 'two': aim_second, 'outsider': True}.get(actor, False)
    link = ['one', 'two', 'work', 'jgoal', 'now']
    changes = {'other_director': (0, 'outsider'), 'other_recipient': (1, 'outsider'),
        'other_act': (2, 'elsewhere'), 'other_goal': (3, 'othergoal'), 'other_scene': (4, 'then')}
    if variant in changes:
        i, value = changes[variant]; link[i] = value
    def guides(director, actor, act, goal, scene):
        args = (director, actor, act, symbol(goal), scene)
        return forward and args == tuple(link) or reverse and args == ('two', 'one', 'work', 'jgoal', 'now')
    return dict(ja=lambda: 'work', js=lambda: 'now', jactors=lambda a: a in people,
        occurs=lambda a, s: occurs and (a, s) == ('work', 'now'),
        performs=lambda a, act, s: (act, s) == ('work', 'now') and {'one': first, 'two': second}.get(a, False),
        aims=aims, guides=guides, truth=unknown)


DOMAIN = ('one', 'two', 'work', 'outsider', 'elsewhere')
CONTEXTS = ('now', 'then')


def truth_checks():
    rows = []
    for bits in product((False, True), repeat=7):
        occurrence, first, second, aim_first, aim_second, forward, reverse = bits
        expected = [occurrence and first and second and (aim_first or aim_second and reverse)
            and (aim_second or aim_first and forward), occurrence and first and second and aim_first and aim_second]
        actual = evaluate(generic(), generic_values(bits), DOMAIN, CONTEXTS)
        assert actual == expected, (bits, actual, expected)
        rows.append(dict(bits=list(bits), values=actual))
    # With no cross-person direction, the new condition is exactly the old all-purpose condition.
    assert all(r['values'][0] == r['values'][1] for r in rows if not any(r['bits'][5:]))
    return dict(combinations=rows,identity_only_equals_unanimity=True,goal_truth_not_executed=True,
        ordinary_evaluation=True,unanimity_not_identified_with_shared_intention=True)


def scope_checks():
    cases = {
        'baseline': ((True, True, True, True, False, True, False), [True, False]),
        'no_direction': ((True, True, True, True, False, False, False), [False, False]),
        'reversed': ((True, True, True, True, False, False, True), [False, False]),
        'all_aim_no_direction': ((True, True, True, True, True, False, False), [True, True]),
        'no_member_goal': ((True, True, True, False, False, True, True), [False, False]),
        'unperformed_director': ((True, False, True, True, False, True, False), [False, False]),
        'unperformed_recipient': ((True, True, False, True, False, True, False), [False, False]),
        'unrealized_activity': ((False, True, True, True, False, True, False), [False, False]),
        'empty': ((True, True, True, True, False, True, False), [False, False]),
        'singleton': ((True, True, False, True, False, False, False), [True, True]),
    }
    rows = {}
    for name, (bits, expected) in cases.items():
        actual = evaluate(generic(), generic_values(bits, name), DOMAIN, CONTEXTS)
        assert actual == expected, (name, actual); rows[name] = actual
    for name in ('other_director', 'other_recipient', 'other_act', 'other_goal', 'other_scene'):
        actual = evaluate(generic(), generic_values(variant=name), DOMAIN, CONTEXTS)
        assert actual == [False, False], (name, actual); rows[name] = actual
    for name in ('occurs', 'performs', 'aims', 'guides'):
        v = generic_values(); v[name] = unknown
        try: evaluate(generic(), v, DOMAIN, CONTEXTS)
        except ValueError as e: assert 'Unknown' in str(e)
        else: raise AssertionError(name)
    # Goal success, failure and lack of an evaluation do not change the action description.
    for truth in (True, False, None):
        v = generic_values(); v['truth'] = unknown if truth is None else lambda s: truth
        assert evaluate(generic(), v, DOMAIN, CONTEXTS) == [True, False]
    chain={}
    for name,links,aimers,want in [
        ('indirect_only',{('one','two'),('two','three')},{'one'},False),
        ('direct_coverage',{('one','two'),('one','three')},{'one'},True),
        ('intermediate_also_aims',{('two','three')},{'one','two'},True)]:
        v=generic_values()
        v.update(jactors=lambda a:a in ('one','two','three'),
            performs=lambda a,act,s:a in ('one','two','three') and (act,s)==('work','now'),
            aims=lambda a,act,q,s:a in aimers and (act,symbol(q),s)==('work','jgoal','now'),
            guides=lambda a,b,act,q,s:(a,b) in links and (act,symbol(q),s)==('work','jgoal','now'))
        actual=evaluate(generic(),v,(*DOMAIN,'three'),CONTEXTS)
        assert actual==[want,False],(name,actual);chain[name]=actual
    return dict(contrasts=rows,direct_and_indirect_coverage=chain,
        unknown_inputs_refused=4,success_failure_unknown_independent=True)


@lru_cache(None)
def source_doc():
    d = deepcopy(catalog().document)
    d.update(declarations=closure(d, ['rqyw', 'do', 'db']), statements=[])
    return parse(format_graph(d, 'compact')+'''
r zc[] d.r jguides[a a a i[e] d] c.
q[t[k rqyw[k db[] p jguides]][k zc[]]].q[t[k do[k db[]]][k zc[]]].
''')


def source_values(variant='baseline'):
    old_variant = 'only_one_goal' if variant in ('mixed', 'no_direction', 'wrong_director', 'wrong_recipient',
        'wrong_act', 'wrong_goal', 'wrong_context', 'reversed') else variant
    v = previous_values(old_variant)
    key = ['guardone', 'guardtwo', 'activity', ('rqyd', 'mv'), 'actual']
    changes = {'wrong_director': (0, 'other'), 'wrong_recipient': (1, 'other'), 'wrong_act': (2, 'activitytwo'),
        'wrong_goal': (3, ('dn', 'mv')), 'wrong_context': (4, 'belief')}
    if variant in changes:
        i, value = changes[variant]; key[i] = value
    if variant == 'reversed': key[:2] = ['guardtwo', 'guardone']
    v['jguides'] = lambda a,b,act,goal,s: variant != 'no_direction' and (a,b,act,goal_key(goal),s) == tuple(key)
    return v


SMALL_PEOPLE=('person','guardone','guardtwo','population','guards','appointment','activity','activitytwo','low','high')
SMALL_SCENES=('actual','belief','prior')


def compact_source_values(variant='baseline'):
    v=source_values(variant);members=v['mp']
    v.update(mp=lambda group:SequenceValue(('person',),'"individual"') if group=='population' else members(group),
        hr=lambda pop,s:pop.items==('person',) and s=='actual',
        uq=lambda p,q,s,t:p=='person' and symbol(q)=='up' and s in ('actual','belief') and t=='belief',
        ur=lambda p,s:(p,s)==('person','belief'))
    # Both guardians supervise the same sole member. They retain separate
    # participation, purpose and guidance facts; rank is tied in this model.
    for relation in ('dc','de','dv','hzxo','hzxn'):
        fn=v[relation]
        v[relation]=lambda *args,fn=fn:fn(*('guardone' if a=='guardtwo' else a for a in args))
    return v


def source_checks():
    expected = {
        'baseline': [True, True], 'mixed': [True, False], 'no_direction': [False, False],
        'wrong_director': [False, False], 'wrong_recipient': [False, False], 'wrong_act': [False, False],
        'wrong_goal': [False, False], 'wrong_context': [False, False], 'reversed': [False, False],
        'no_goal': [False, False], 'empty_guards': [False, False], 'duplicate_guard': [False, False],
        'nonhuman_guard': [False, False], 'separate_activities': [False, False],
        'no_event_cause': [False, False], 'split_purpose_and_cause': [False, False],
        'no_judgment': [False, False], 'no_burden': [False, False], 'different_position': [False, False],
        'actual_danger': [True, True], 'no_adoption': [True, True], 'no_group_cause': [True, True],
        'goal_wrong_act': [False, False], 'goal_wrong_target': [False, False],
        'goal_wrong_content': [False, False], 'goal_wrong_context': [False, False],
        'outsider_goal': [False, False], 'no_activity': [False, False],
    }
    rows = {}
    for name, want in expected.items():
        actual = evaluate(source_doc(), compact_source_values(name), SMALL_PEOPLE, SMALL_SCENES, True)
        assert actual == want, (name, actual, want); rows[name] = actual
        print('source '+name+' checked',flush=True)
    print('source contrasts checked',flush=True)
    larger={}
    for name in ('baseline','mixed'):
        actual=evaluate(source_doc(),source_values(name),PEOPLE,SCENES,True)
        assert actual==rows[name],(name,actual);larger[name]=actual
        print('larger source '+name+' checked',flush=True)
    # Ordinary evaluation of the actual new source binding retains mixed goals.
    d=deepcopy(catalog().document)
    d.update(declarations=closure(d,['rqyv','rqyg','db']),statements=[])
    d=parse(format_graph(d,'compact')+'''r zc[] d.r zact[] a.r jguides[a a a i[e] d] c.
q[k rqyv[k db[] k zact[] k zc[] p jguides]].q[k rqyg[k db[] k zact[] k zc[]]].''')
    ordinary={}
    for name,want in [('mixed',[True,False]),('no_direction',[False,False]),('no_event_cause',[True,True])]:
        v=source_values(name)
        plain=evaluate(d,v,PEOPLE,SCENES)
        cached=evaluate(d,v,PEOPLE,SCENES,True)
        assert plain==cached==want,(name,plain,cached);ordinary[name]=plain
    for name in ('hzu','jguides','hzie'):
        v=compact_source_values('mixed');v[name]=unknown
        try: evaluate(source_doc(),v,SMALL_PEOPLE,SMALL_SCENES,True)
        except ValueError as e: assert 'Unknown' in str(e)
        else: raise AssertionError(name)
    return dict(contrasts=rows,ordinary_purpose_binding_comparisons=ordinary,
        compact_domain=dict(individuals=list(SMALL_PEOPLE),situations=list(SMALL_SCENES)),
        larger_domain_comparisons=larger,
        ordinary_complete_integration=False,unknown_inputs_refused=3,
        current_oversight_purpose_judgment_causation_executed=True,source_adoption=False)


def structure():
    old, new = parent(), catalog()
    size = len(old.document['declarations'])
    assert new.document['declarations'][:size] == old.document['declarations']
    assert set(new.entries)-set(old.entries) == set(MEANINGS)
    assert new.document['statements'] == old.document['statements'] and len(new.document['statements']) == 45
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    validate_hashes(ROOT,index['source_sha256'])
    assert index['works']['kant-1784']['document'] == PARENT
    for path in index['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'))
        ids=[r['index'] for r in review['selection']['statements']]
        assert selection_binding(old,ids) == review['selection'] == selection_binding(new,ids)
    for ids in ([2,3],[4,42],[6],[5,43],[7,44]):
        assert selection_binding(old,ids) == selection_binding(new,ids)
    # Apart from the selected purpose predicate, both surrounding source conditions
    # must be identical. Reparse to compare alpha-normalized bound variables.
    replacements=[]
    for added,previous,call,replacement in [('rqyv','rqyg','rqyu','rqyf'),('rqyw','do','rqyv','rqyg')]:
        declaration=deepcopy(new.entries[added]['declaration'])
        declaration['name']='jcomparison';declaration['parameters'].pop();count=0
        def restore(node):
            nonlocal count
            if isinstance(node,list):return [restore(x) for x in node]
            if not isinstance(node,dict):return node
            if node.get('kind')=='call' and node['symbol']==call:
                count+=1;node=deepcopy(node);node['symbol']=replacement;node['arguments'].pop()
                return node
            return {k:restore(v) for k,v in node.items()}
        declaration['body']=restore(declaration['body']);assert count==1
        doc=deepcopy(new.document);doc['statements']=[];doc['declarations'].append(declaration)
        canonical=parse(format_graph(doc,'compact'))['declarations'][-1]
        expected=deepcopy(old.entries[previous]['declaration']);expected['name']='jcomparison'
        assert canonical==expected,(added,previous)
        replacements.append(dict(candidate=added,previous=previous,replaced_call=call))
    for path, text in build().items(): assert (ROOT/path).read_text(encoding='utf-8') == text
    for path in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(doc,notation)
            assert parse(text) == parse(transcribe(text,alphabet='v2')) == doc
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    return dict(new_primitives=0,new_definitions=5,preserved_statements=45,preserved_review_selections=11,
        unchanged_surrounding_source_conditions=replacements,
        roundtrips=True,active_manuscript_unchanged=True,source_adoption=False)


def reading():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    start=unit['text'].index('dafür sorgen');end=start+len('dafür sorgen')
    return dict(status='purpose_distribution_comparison_not_adopted_claim',reviewer='assistant_review',
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],text=unit['text'][start:end]),
        finding='現行rqyg・doは、選択した後見人全員に同じ目的を要求する。目的を担う参加者が他者の参加を実際に方向付けるモデルは、この全員条件と区別できる。',
        decision='方向付けを明示する比較候補を追加する。Sorgenの保存済み用例は目的的な働きかけを支えるが、各人の同じ意図や特定の指揮関係を確定しないため、現行本文への採用とは分ける。',
        next_requirement='原文の複数主語と後続の活動描写に適した目的の帰属範囲を決める。schon・auchと一文全体の照合も残る。',
        limitations=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,INDEX,PARENT,PARENT_BASIS,
            'data/guardian-causation-evidence-v1.json','data/guardian-purpose-reading-v1.json','docs/guardian-purpose-v1.md')})


def build_report():
    results={}
    for name,fn in [('truth',truth_checks),('scope',scope_checks),('source',source_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    note=reading();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==note
    validate_hashes(ROOT,note['source_sha256'])
    prior='reports/benevolent-framing-v1.json'
    old=json.loads((ROOT/prior).read_text(encoding='utf-8'));validate_hashes(ROOT,old['source_sha256'])
    paths=set(build())|set(parent().source_sha256)|set(note['source_sha256'])|set(old['source_sha256'])|{
        READING,DOC,prior,'scripts/compose_directed_purpose.py','scripts/check_directed_purpose.py',
        'scripts/register_directed_purpose.py','tests/test_directed_purpose.py'}
    return dict(status='directed_purpose_comparison_not_adopted_claim',document=FULL,**results,
        alignment=dict(**note['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(reading()))
    write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':
    main()
