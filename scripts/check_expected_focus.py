"""Distinguish strict expectation, ties, incomparability and unknown input."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json

from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts import check_existential_focus as prior
from scripts.compose_expected_focus import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,READING,MEANINGS,PC,PREDICATE,FRAME,build

REPORT=ROOT/'reports/expected-focus-v1.json'
UNKNOWN=prior.prior.unknown


def evaluate(doc,values):
    return prior.prior.evaluate(doc,values,('person','authority'),('outside','other'))


def unknown_values(doc):
    return {d['name']:UNKNOWN for d in doc['declarations'] if d['kind']=='primitive'}


@lru_cache(maxsize=1)
def preorder_document():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    text='r zview[] a.r zcontext[] d.'
    for name in ('first','second','third'):
        text+='r z'+name+'truth[d] c.d z'+name+'[] e[b point[k z'+name+'truth[v point]]].'
    items=' '.join('r b[k z'+name+'[]]' for name in ('first','second','third'))
    text+='q[k rqtq[l['+PC+']['+items+'] k zview[] k zcontext[] p hzpt]].'
    return parse(format_graph(doc,'compact')+text)


def preorder_checks():
    doc=preorder_document();count=valid=0;names=('zfirst','zsecond','zthird')
    for bits in product((False,True),repeat=9):
        relation={(a,b) for (a,b),present in zip(product(range(3),repeat=2),bits) if present}
        composed={(a,c) for a,b in relation for middle,c in relation if b==middle}
        expected=all((i,i) in relation for i in range(3)) and composed<=relation
        def weak(observer,left,right,context):
            assert (observer,context)==('authority','outside')
            return (names.index(json.loads(left.syntax)['symbol']),names.index(json.loads(right.syntax)['symbol'])) in relation
        values=unknown_values(doc);values.update(zview=lambda:'authority',zcontext=lambda:'outside',hzpt=weak)
        assert evaluate(doc,values)==[expected],bits
        count+=1;valid+=expected
    assert valid==29
    values['hzpt']=UNKNOWN
    try:evaluate(doc,values)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown preorder filled')
    return dict(three_content_relations=count,accepted_preorders=valid,content_truth_never_evaluated=True,
        unknown_comparison_refused=True,all_checks_eager=True)


@lru_cache(maxsize=1)
def generic_document():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    text='r zfocus[a d] c.r zview[] a.r zcontext[] d.'
    text+='d zframe[subgroup '+PREDICATE+'] e[b point[c[s[v subgroup]][k zview[] v point]]].'
    package='k hzpv[r b[p zframe] r[p zfocus] r[k zview[]] r[k zcontext[]]]'
    text+=prior.focused.queries(package,'k zcontext[]')
    text+='q[c[s[k rqtt[r[p zfocus]]]][k zview[] k zcontext[]]].'
    return parse(format_graph(doc,'compact')+text)


def label(description):
    frame,code=prior.focused.subgroup(description)
    if code['kind']=='apply':
        assert code['function']['kind']=='lambda' and code['function']['body']['kind']=='lambda'
        assert code['function']['body']['body']['kind']=='not' and len(code['arguments'])==1
        return frame,'other',code['arguments'][0]
    return frame,'focus',code


def lambda_key(node,scope=()):
    """Compare the closed predicate lambdas independently of binder names."""
    if isinstance(node,list):return [lambda_key(item,scope) for item in node]
    if not isinstance(node,dict):return node
    if node.get('kind')=='variable':
        assert node['name'] in scope, 'Unexpected free variable in closed predicate'
        return dict(kind='bound',index=scope[::-1].index(node['name']))
    if node.get('kind')=='lambda':
        parameters=node['parameters']
        return dict(kind='lambda',types=[p['sort'] for p in parameters],
            body=lambda_key(node['body'],scope+tuple(p['name'] for p in parameters)))
    return {key:lambda_key(value,scope) for key,value in node.items()}


def weak_model(above,reverse,*,native=False,broken_self=False):
    def weak(observer,left,right,context):
        frame,a,focus=label(left);otherframe,b,otherfocus=label(right)
        assert frame==otherframe and lambda_key(focus)==lambda_key(otherfocus)
        if native:
            assert frame['kind']=='call' and frame['symbol']=='rqtp' and len(frame['arguments'])==7
            assert focus['kind']=='lambda' and focus['body']['symbol']=='hzhb'
        else:assert frame==dict(kind='function_ref',symbol='zframe') and focus==dict(kind='function_ref',symbol='zfocus')
        if (observer,context)!=('authority','outside'):return False
        if a==b:return not broken_self
        return above if (a,b)==('other','focus') else reverse
    return weak


def scalar_checks():
    doc=generic_document();count=0;rows={}
    for above,reverse,truth in product((False,True),repeat=3):
        values=unknown_values(doc);values.update(zview=lambda:'authority',zcontext=lambda:'outside',
            zfocus=lambda person,point:truth,hzpt=weak_model(above,reverse))
        actual=evaluate(doc,values);background=above and not reverse
        assert actual==[background,truth,background,not truth,True,not truth],(above,reverse,truth,actual)
        rows[str((above,reverse,truth))]=actual;count+=1
    for variant in ('nonreflexive','wrong_view','wrong_context'):
        values.update(hzpt=weak_model(True,False,broken_self=variant=='nonreflexive'),
            zview=lambda:'person' if variant=='wrong_view' else 'authority',
            zcontext=lambda:'other' if variant=='wrong_context' else 'outside')
        assert evaluate(doc,values)[0] is False,variant
    # The constructed complement uses the same person and point, rather than
    # changing the reference to make the result differ.
    values.update(zview=lambda:'authority',zcontext=lambda:'outside',hzpt=weak_model(True,False),
        zfocus=lambda person,point:(person,point)==('authority','outside'))
    assert evaluate(doc,values)[-1] is False
    values['zcontext']=lambda:'other';assert evaluate(doc,values)[-1] is True
    return dict(expectation_direction_and_truth_combinations=count,contrasts=rows,
        ties_and_incomparability_not_strict=True,invalid_self_comparison_refused=True,
        complement_preserves_person_and_point=True,background_preserved_by_negation=True)


@lru_cache(maxsize=1)
def native_document():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));old=prior.native_document('conditional')
    names={d['name'] for d in doc['declarations']}
    doc['declarations'] += [deepcopy(d) for d in old['declarations'] if d['name'] not in names and d['name']!='zpackage']
    frame='r b[k rqtp['+prior.CONDITION_ARGS+' k znativefamily[]]]'
    guardian='r[i[person a context d][k hzhb[v person k zgoverned[] v context p zappointed p zguardian]]]'
    text=prior.focused.queries('k hzpw['+frame+' '+guardian+']','k hzp3[]')
    parsed=parse(format_graph(doc,'compact')+text)
    parsed['statements']=[parsed['statements'][i] for i in (0,2,4)]
    return parsed


def native_and_unknown_checks():
    doc=native_document();rows={}
    for above,reverse in product((False,True),repeat=2):
        values=unknown_values(doc);values.update(wa=lambda:'authority',hzp3=lambda:'outside',hzpt=weak_model(above,reverse,native=True))
        actual=evaluate(doc,values);expected=above and not reverse
        assert actual==[expected,expected,True],actual;rows[str((above,reverse))]=actual
    for name in ('wa','hzp3','hzpt'):
        bad=dict(values);bad[name]=UNKNOWN
        try:evaluate(doc,bad)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    generic=generic_document();values=unknown_values(generic)
    values.update(zview=lambda:'authority',zcontext=lambda:'outside',zfocus=lambda *args:True)
    assert evaluate(dict(generic,statements=generic['statements'][1:2]),values)==[True]
    values['zfocus']=UNKNOWN
    try:evaluate(dict(generic,statements=generic['statements'][1:2]),values)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown foreground filled')
    return dict(native_conditional_guardian_comparisons=rows,world_primitives_never_evaluated=True,
        source_viewpoint_and_context_fixed=True,unknown_metadata_refused=3,
        foreground_does_not_evaluate_expectation=True,unknown_foreground_refused=True,
        all_checks_eager=True,whole_dissemination_truth_not_claimed=True)


def source_checks():
    reading=json.loads((ROOT/READING).read_text(encoding='utf-8'))
    source=json.loads((ROOT/reading['source_inventory']).read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']==reading['source_unit'])
    assert unit['text_sha256']==reading['unit_sha256']==digest(unit['text'].encode('utf-8'))
    start,end=reading['range'];assert unit['text'][start:end]==reading['text']=='sogar'
    for item in reading['references']:assert digest((ROOT/item['artifact']).read_bytes())==item['sha256']
    previous=json.loads((ROOT/reading['prior_facsimile_collation']).read_text(encoding='utf-8'))
    assert previous['unit_sha256']==unit['text_sha256']
    image=previous['facsimile'];assert digest((ROOT/image['artifact']).read_bytes())==image['sha256']
    return dict(source_unit=unit['id'],source_sha256=unit['text_sha256'],start=start,end=end,
        source=reading['text'],new_nonblank_partial_characters=5,
        source_specific_reading_is_adopted_not_uniquely_proved=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['declarations'][:-8]==old.document['declarations']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==34
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    return dict(new_compositions=7,new_primitives=1,existing_statements=34,seven_review_bindings_preserved=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for name,body in outputs.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/existential-focus-v1.json').read_text(encoding='utf-8'))
    for path,sha in previous['source_sha256'].items():assert digest((ROOT/path).read_bytes())==sha,path
    reading=json.loads((ROOT/READING).read_text(encoding='utf-8'));source=source_checks()
    paths=set(load_catalog(ROOT,BASIS).source_sha256)|set(outputs)|set(previous['source_sha256'])|{
        READING,reading['source_inventory'],reading['prior_facsimile_collation'],'reports/existential-focus-v1.json',
        'scripts/compose_expected_focus.py','scripts/check_expected_focus.py','tests/test_expected_focus.py','docs/expected-focus-v1.md'}
    paths.update(row['artifact'] for row in reading['references'])
    results={}
    for name,check in [('preorders',preorder_checks),('scalar',scalar_checks),('native',native_and_unknown_checks),('structure',structure)]:
        results[name]=check();print(name+' checked',flush=True)
    return dict(status='explicit_qualitative_expectation_reading_with_checked_preorder',document=FULL,**results,source=source,
        roundtrips=True,new_source_assertions=0,alignment=dict(unit=source['source_unit'],unit_sha256=source['source_sha256'],
            start=source['start'],end=source['end'],source=source['source'],definitions=['hzpv','hzpw'],
            status='partial_adopted_expectation_scale',full_semantic_equivalence=False,
            remaining=['closed full source-content binding','full foreground and background attribution','whole paragraph meaning review']),
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Adopted expectation scale and source comparison checked',flush=True)


if __name__=='__main__':main()
