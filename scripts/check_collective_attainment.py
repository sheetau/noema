"""Check collective attainment without silently imposing unanimity."""
import argparse
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,Message,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_collective_attainment import ROOT,PARENT,FULL,CORE,LIBRARY,BASIS,MEANINGS,LIMITS,build,parent

REPORT='reports/collective-attainment-v1.json'
READING='data/collective-attainment-reading-v1.json'
INDEX='data/semantic-review-index-v35.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PEOPLE=('alice','bob','carol')
DOMAIN=(*PEOPLE,'outsider','epoch')
SCENES=('past','now','future')
EXTRA='''r zepoch[] a.r zcontext[] d.r zhistory[d] c.r zbefore[d d] c.r zperiods[a d] c.
r zpeople[a] c.r zpresent[a d] c.r zassessed[a] e.r zcapable[a] e.r zprogress[] e.
r zstandard[h[a] c h[a] c d] c.'''
FRAME='k zepoch[] k zcontext[] p zhistory p zbefore p zperiods p zpeople p zpresent'
SOURCE='k zepoch[] p zhistory p zbefore p zperiods p zpeople p zpresent'
CHECKED=FRAME+' p zassessed p zstandard'
ATTAINED=CHECKED+' p zcapable'


def unknown(*args):raise ValueError('Unknown collective attainment input')


@lru_cache(None)
def generic(messages=False):
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+EXTRA
    # rmj is deliberately compared as the old unanimous special case.
    old=next(d for d in parent().document['declarations'] if d['name']=='rmj')
    d=parse(text);d['declarations'].append(old);text=format_graph(d,'compact')
    calls=[('rmj',FRAME+' p zassessed p zcapable'),('rqwh',CHECKED),('rqwi',ATTAINED),
        ('rmk',FRAME+' k zprogress[]'),('rqwj',ATTAINED+' k zprogress[]')]
    text+=''.join('q[k '+n+'['+a+']].' for n,a in calls)
    if messages:
        text+='l[k rqwk['+SOURCE+' p zassessed p zstandard p zcapable]].'
        text+='l[k rqwl['+SOURCE+' p zassessed p zstandard p zcapable k zprogress[]]].'
    return parse(text)


def evaluate(doc,model,domain=DOMAIN,scenes=SCENES,cache=False):
    return [row['value'] for row in evaluate_document(doc,individuals=domain,situations=scenes,
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=20000000,memoize_definitions=cache,memoize_expressions=cache)]


def model(capable=(True,True,False),assessed=(True,)*3,progress=True,threshold=2,variant='baseline'):
    def standard(people,success,context):
        if variant=='always_true':return True
        if variant=='always_false':return False
        if variant=='inverted':return not any(success(p) for p in PEOPLE)
        expected=(*PEOPLE[:2],'outsider') if variant=='wrong_standard_group' else PEOPLE
        if any(people(p)!=(p in expected) for p in DOMAIN):return False
        if context!=('past' if variant=='wrong_standard_time' else 'now'):return False
        return sum(success(p) for p in DOMAIN)>=threshold
    return dict(zepoch=lambda:'epoch',zcontext=lambda:'now',zhistory=lambda s:True,
        zbefore=lambda a,b:SCENES.index(a)<SCENES.index(b),
        zperiods=lambda e,s:e=='epoch' and (s!='now' if variant=='hole' else True),
        zpeople=lambda p:p in PEOPLE and variant!='empty',
        zpresent=lambda p,s:p in PEOPLE and not(variant=='absent' and p=='carol' and s=='now'),
        zassessed=lambda p:Content(SCENES,tuple(p in PEOPLE and assessed[PEOPLE.index(p)] for s in SCENES)),
        zcapable=lambda p:Content(SCENES,tuple((p=='outsider' if variant=='outside_success' else False) or
            p in PEOPLE and capable[PEOPLE.index(p)] and not(variant=='past_success' and s=='now') for s in SCENES)),
        zprogress=lambda:Content(SCENES,tuple(progress and not(variant=='past_progress' and s=='now') for s in SCENES)),
        zstandard=standard)


def truth_checks():
    count=0
    for capability in product((False,True),repeat=3):
        for assessment in product((False,True),repeat=3):
            for progress in (False,True):
                checked=all(assessment);attained=checked and sum(capability)>=2
                want=[checked and all(capability),checked,attained,progress,checked and not attained and progress]
                got=evaluate(generic(),model(capability,assessment,progress));assert got==want,(capability,assessment,progress,got)
                count+=1
        got=evaluate(generic(),model(capability,threshold=3));assert got[0]==got[2]
    return dict(combinations=count,unanimity_special_cases=8,uncached=True,
        test_threshold_not_language_constant=True,assessment_not_capability=True)


def scope_checks():
    cases={}
    for variant,want in [
        ('empty',[False]*5),('hole',[False]*5),('absent',[False]*5),
        ('always_true',[False,False,False,True,False]),('always_false',[False,False,False,True,False]),
        ('inverted',[False,False,False,True,False]),('wrong_standard_group',[False,False,False,True,False]),
        ('wrong_standard_time',[False,False,False,True,False]),
        ('past_success',[False,True,False,True,True]),('past_progress',[False,True,True,False,False]),
    ]:
        result=evaluate(generic(),model(variant=variant));assert result==want,(variant,result);cases[variant]=result
    result=evaluate(generic(),model((True,False,False),variant='outside_success'))
    assert result==[False,True,False,True,True];cases['outside_success']=result
    for name in ('zhistory','zbefore','zperiods','zpeople','zpresent','zassessed','zcapable','zstandard','zprogress'):
        m=model();m[name]=unknown
        try:evaluate(generic(),m)
        except ValueError as e:assert 'Unknown collective' in str(e)
        else:raise AssertionError(name)
    return dict(cases=cases,unknown_inputs_refused=9,other_people_and_times_not_borrowed=True,
        orientation_is_not_general_monotonicity=True)


def message_checks():
    rows=[]
    for capability,progress in product(((False,False,False),(True,True,False)),(False,True)):
        result=evaluate(generic(True),model(capability,progress=progress));question,answer=result[-2:]
        assert isinstance(question,Message) and isinstance(answer,Message)
        assert question.force=='ask' and answer.force=='assert'
        assert question.content.values[1]==result[2] and answer.content.values[1]==result[4]
        rows.append(dict(attained=result[2],progress=progress,answer_content=result[4]))
    return dict(cases=rows,force_distinct_from_content=True,no_actual_dialogue_or_truth_inferred=True)


NATIVE_SCENES=('anchor','trial','success','failure')
NATIVE_DOMAIN=(*DOMAIN,'method','fa','fb','fc','acta','actb','actc')


@lru_cache(None)
def native():
    text=(ROOT/CORE).read_text(encoding='utf-8')+EXTRA
    for n,args in [('hzfb',SOURCE),('hzvc',SOURCE+' p zstandard'),
        ('hzfc',SOURCE+' k zprogress[]'),('hzvd',SOURCE+' p zstandard k zprogress[]')]:
        text+='q[t[k '+n+'['+args+']][k zcontext[]]].'
    return parse(text)


def native_model(capability=(True,True,False),variant='baseline'):
    m={d['name']:unknown for d in native()['declarations'] if d['kind']=='primitive'}
    def available(p,method,s):return p in PEOPLE and (method,s)==('method','trial')
    def selected(p,method,s,t):return available(p,method,s) and not(variant=='unassessed' and p=='carol') and t==('success' if capability[PEOPLE.index(p)] else 'failure')
    def standard(people,success,context):
        if context!='anchor' or any(people(p)!=(p in PEOPLE) for p in NATIVE_DOMAIN):return False
        return sum(success(p) for p in NATIVE_DOMAIN)>=2
    m.update(zepoch=lambda:'epoch',zcontext=lambda:'anchor',zhistory=lambda s:True,
        zbefore=lambda a,b:NATIVE_SCENES.index(a)<NATIVE_SCENES.index(b),
        zperiods=lambda e,s:(e,s)==('epoch','anchor'),zpeople=lambda p:p in PEOPLE,
        zpresent=lambda p,s:p in PEOPLE,zprogress=lambda:Content(NATIVE_SCENES,(variant!='no_progress',False,False,False)),
        zstandard=standard,aa=lambda p:p in PEOPLE,
        ab=lambda f,p,s:p in PEOPLE and f==('fa','fb','fc')[PEOPLE.index(p)],
        ac=lambda p,f,a,s:p in PEOPLE and (f,a,s)==(('fa','fb','fc')[PEOPLE.index(p)],('acta','actb','actc')[PEOPLE.index(p)],'success'),
        ad=lambda *args:False,ae=available,af=lambda p,m,s,t:available(p,m,s) and t in ('success','failure'),ap=selected,
        hzsc=lambda p,a,s:p in PEOPLE and (a,s)==('anchor','trial'),
        hzsd=lambda p,a,s:p in PEOPLE and (a,s)==('anchor','trial'),hzse=lambda p,s:p in PEOPLE and s=='trial',
        hzsf=lambda *args:False,hzsg=lambda p,m,a,s:p in PEOPLE and (m,a,s)==('method','anchor','trial'),
        hzsh=lambda p,m,a,s:p in PEOPLE and (a,s)==('anchor','trial'))
    return m


def source_checks():
    rows={}
    for name,capability,variant,want in [
        ('two_of_three',(True,True,False),'baseline',[False,True,True,False]),
        ('one_of_three',(True,False,False),'baseline',[False,False,True,True]),
        ('all_three',(True,True,True),'baseline',[True,True,False,False]),
        ('unassessed',(True,True,False),'unassessed',[False]*4),
        ('no_progress',(True,False,False),'no_progress',[False]*4),
    ]:
        result=evaluate(native(),native_model(capability,variant),NATIVE_DOMAIN,NATIVE_SCENES,True)
        assert result==want,(name,result);rows[name]=result
    m=native_model();m['hzsh']=unknown
    try:evaluate(native(),m,NATIVE_DOMAIN,NATIVE_SCENES,True)
    except ValueError as e:assert 'Unknown collective' in str(e)
    else:raise AssertionError('Unknown native assessment accepted')
    return dict(cases=rows,native_fo_up_h4l_executed=True,no_definition_lowering=True,
        pure_scalar_memoization=True,unknown_native_assessment_refused=True)


def structure():
    old=parent();new=load_catalog(ROOT,BASIS)
    for name,text in build().items():assert (ROOT/name).read_text(encoding='utf-8')==text,name
    size=len(old.document['declarations']);assert new.document['declarations'][:size]==old.document['declarations']
    assert len(new.document['declarations'])==size+10
    assert old.document['statements']==new.document['statements'] and len(new.document['statements'])==41
    for name in (FULL,CORE,LIBRARY):
        d=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'));validate_hashes(ROOT,index['source_sha256'])
    active=index['works']['kant-1784'];assert active['document']==PARENT and len(active['reviews'])==10
    for name in active['reviews']:
        review=json.loads((ROOT/name).read_text(encoding='utf-8'));indices=[r['index'] for r in review['selection']['statements']]
        assert selection_binding(old,indices)==review['selection']==selection_binding(new,indices)
    return dict(new_definitions=10,new_primitives=0,roundtrips=True,preserved_statements=41,
        preserved_review_selections=10,active_manuscript_unchanged=True,source_adoption=False)


def reading():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0014')
    return dict(status='collective_attainment_comparison_not_adopted_claim',reviewer='assistant_review',
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,147],text=unit['text'][:147]),
        references=[dict(url='https://korpora.org/Kant/aa08/040.html',use='時代についての問答と、続くim Ganzen genommenを含む説明を照合。')],
        decision='全員一致だけを許す既存候補に代えて、集団・現在・到達基準を保持する一般構成を比較する。原文の全体判断に必要な基準の意味規約と残る述語を確定するまでは本文へ採用しない。',
        limitations=LIMITS,whole_unit_semantically_verified=False)


def build_report():
    results={}
    for name,fn in [('truth',truth_checks),('scope',scope_checks),('messages',message_checks),('source',source_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    note=reading();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==note;s=note['source']
    prior='reports/explanatory-question-v1.json';validate_hashes(ROOT,json.loads((ROOT/prior).read_text(encoding='utf-8'))['source_sha256'])
    paths=set(build())|set(parent().source_sha256)|{READING,INVENTORY,INDEX,prior,
        'scripts/compose_collective_attainment.py','scripts/check_collective_attainment.py','scripts/compose_falling_depiction.py',
        'tests/test_collective_attainment.py','docs/collective-attainment-v1.md','noema/constructed_semantics.py',
        'noema/constructed.py','noema/constructed_discourse.py','noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='partial_collective_attainment_comparison',document=FULL,**results,
        alignment=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],start=0,end=147,source=s['text'],definitions=list(MEANINGS),
            status='explicit_interpretive_annotation',full_semantic_equivalence=False),new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(reading()));report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Collective attainment, assessment and progress checked',flush=True)


if __name__=='__main__':main()
