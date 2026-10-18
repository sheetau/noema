"""Check topic preservation, standing ability and the same enabling endpoint."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_topical_standing import ROOT,FULL,CORE,LIBRARY,BASIS,MEANINGS,LIMITS,PROFILES,build,parent,closure

REPORT='reports/topical-standing-v1.json'
READING='data/topical-standing-reading-v1.json'
INDEX='data/semantic-review-index-v35.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
DOMAIN=('person','other','one','two','methodone','methodtwo','helper')
SCENES=('now','after','pretrial','posttrial','good','bad')
NATIVE_DOMAIN=(*DOMAIN,'faculty','actone','acttwo','reason')
EXTRA='''r zperson[] a.r zone[] a.r ztwo[] a.r zcontext[] d.r zanchor[] d.r ztopic[] a.
r zchoose[a i[a] i[a]] i[a].r ztopics[a a a d] c.r zrelevant[a a] c.
r zcases[a i[h[a] e] d d] c.r zpreserved[a i[h[a] e] d d] c.r zopportunity[a i[h[a] e] d] c.
r zpreferred[a i[h[a] e] d d d] c.r zscope[a i[h[a] e] a d d] c.r zchecked[a i[h[a] e] a d d] c.
r zavailable[a a d] c.r zoutcomes[a a d d] c.r zselected[a a d d] c.
r zgoal[a a d] c.r zagents[a a d] c.r zenabling[a a a d] c.r zeffects[a a a d d] c.
d znames[m a] i[a][k zchoose[v m r[k zone[]] r[k ztwo[]]]].
d ztarget[m a] h[a] e[i[p a][b s[k zgoal[v p v m v s]]]].
d ztasks[m a] i[h[a] e][o a[r[p ztarget]][k znames[v m]]].
'''
TAIL='p zcases p zpreserved p zopportunity p zpreferred p zscope p zchecked p zavailable p zoutcomes p zselected'
ARGS='k zperson[] k zcontext[] p zrelevant p ztasks '+TAIL
TOPIC='k ztopic[] k zanchor[] p ztopics p znames'
SUPPORT=TOPIC+' p zagents p zenabling p zeffects'


def unknown(*args):raise ValueError('Unknown topical standing input')


def task_matter(code,target='ztarget'):
    body=json.loads(code.syntax)
    if body.get('kind')!='apply' or body.get('function')!={'kind':'function_ref','symbol':target}:return None
    args=body.get('arguments',[])
    if len(args)!=1:return None
    return {'zone':'one','ztwo':'two'}.get(args[0].get('symbol')) if args[0].get('kind')=='call' else None


@lru_cache(None)
def generic():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+EXTRA
    return parse(text+''.join('q[k '+n+'['+ARGS+']].' for n in ('rqwm','rqwn')))


def evaluate(doc,model,domain=DOMAIN,scenes=SCENES):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,situations=scenes,
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=60000000,memoize_definitions=True,memoize_expressions=True)]


def model(current=(True,True),future=(True,True),variant='baseline',native=False):
    def identity(p,g):return p=='person' and task_matter(g,'hzvg' if native else 'ztarget') in ('one','two')
    def cases(p,g,a,s):return identity(p,g) and ((a,s) in (('now','pretrial'),('after','posttrial')) or variant=='split_results' and (a,s)==('bad','posttrial')) and variant!='empty_profile'
    def available(p,m,s):return p=='person' and m in ('methodone','methodtwo') and (s in ('pretrial','posttrial') or variant=='immediate_only' and s=='now')
    def selected(p,m,s,t):
        if not available(p,m,s):return False
        if variant=='unassessed_after' and s=='posttrial':return False
        if variant=='unassessed_one' and m=='methodone':return False
        passed=True if s=='now' else (current if s=='pretrial' else future)[m=='methodtwo']
        return t==('good' if passed else 'bad')
    def scope(p,g,m,a,s):
        matter=task_matter(g,'hzvg' if native else 'ztarget')
        return identity(p,g) and m==('methodone' if matter=='one' else 'methodtwo') and variant!='preparation_only' and not(
            variant=='split_results' and (a,matter) in (('after','two'),('bad','one')))
    def choose(m,one,two):return one if m=='one' or variant=='wrong_reference' and m=='two' else two
    def topics(p,t,m,a):return p=='person' and t=='one' and m in ('one','two') and variant!='empty_topic' and (a=='now' or m=='one')
    def enabling(a,p,m,s):return (a,p,m,s)==('helper','person','methodone','now') and variant!='no_enabling'
    m=dict(zperson=lambda:'person',zone=lambda:'one',ztwo=lambda:'two',zcontext=lambda:'now',zanchor=lambda:'now',ztopic=lambda:'one',
        zchoose=choose,ztopics=topics,zrelevant=lambda p,m:topics(p,'one',m,'now'),zcases=cases,
        zpreserved=lambda p,g,a,s:identity(p,g) and variant!='changed_basis',
        zopportunity=lambda p,g,s:identity(p,g) and s in ('pretrial','posttrial'),zpreferred=lambda *args:False,
        zscope=scope,zchecked=lambda p,g,m,a,s:identity(p,g) and not(variant=='unclassified_one' and m=='methodone'),
        zavailable=available,zoutcomes=lambda p,m,s,t:available(p,m,s) and t in ('good','bad'),zselected=selected,
        zgoal=lambda p,m,s:p=='person' and m in ('one','two') and s=='good',
        zagents=lambda a,p,s:(a,p,s)==('helper','person','now') and variant!='empty_agents',zenabling=enabling,
        zeffects=lambda a,p,m,s,t:enabling(a,p,m,s) and t in (('after','bad') if variant=='split_results' else ('after',)) and variant!='no_effect')
    if variant=='wrong_task':
        m['zcases']=lambda p,g,a,s:False
    if variant=='foreign_person':m['zgoal']=lambda p,m,s:p=='other' and s=='good'
    if native:
        m.update(aa=lambda p:p in ('person','other'),ab=lambda f,p,s:(f,p)==('faculty','person'),
            ac=lambda p,f,a,s:(p,f)==('person','faculty') and a in ('actone','acttwo') and s=='good',
            fa=lambda p,a,s:p=='person' and a in ('actone','acttwo') and s=='good',
            fb=lambda a,topic,s:(a,topic) in (('actone','one'),('acttwo','two')) and s=='good' and not(variant=='wrong_matter' and topic=='two'),
            fc=lambda a,r,s:a in ('actone','acttwo') and r=='reason' and s=='good',
            fd=lambda r,a,s:r=='reason' and a in ('actone','acttwo') and s=='good' and variant!='unsupported',
            ad=lambda o,p,a,s:variant=='guided' and (o,p,s)==('helper','person','good'),
            ae=m['zavailable'],af=m['zoutcomes'],ap=m['zselected'])
        for (field,symbol,_),name in zip(PROFILES,('zcases','zpreserved','zopportunity','zpreferred','zscope','zchecked'),strict=True):m[symbol]=m[name]
    return m


def capacity_checks():
    rows=[]
    for current in product((False,True),repeat=2):
        result=evaluate(generic(),model(current));assert result==[True,all(current)],(current,result);rows.append(result)
    cases={}
    for variant,want in [('empty_profile',[False,False]),('changed_basis',[False,False]),('preparation_only',[True,False]),
        ('unclassified_one',[False,False]),('unassessed_one',[False,False]),('empty_topic',[False,False]),
        ('wrong_task',[False,False]),('foreign_person',[True,False])]:
        result=evaluate(generic(),model(variant=variant));assert result==want,(variant,result);cases[variant]=result
    for name in ('zrelevant','zchoose','zcases','zpreserved','zopportunity','zpreferred','zscope','zchecked','zselected','zgoal'):
        m=model();m[name]=unknown
        try:evaluate(generic(),m)
        except ValueError as e:assert 'Unknown topical' in str(e)
        else:raise AssertionError(name)
    return dict(combinations=len(rows),cases=cases,unknown_inputs_refused=10,standing_not_immediate_opportunity=True,
        goal_content_obtained_from_same_task_description=True,pure_memoization=True)


@lru_cache(None)
def support_fixture():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zp[] a.r znow[] d.r za[a] e.r zc[a] e.r zeligible[a a] c.r zenabling[a a a d] c.r zeffects[a a a d d] c.
'''
    args='k zp[] k znow[] p za p zeligible p zenabling p zeffects'
    return parse(text+'q[k rqwo['+args+']].q[k rqwp['+args+' p zc]].')


def support_model(assessed=True,capable=True,variant='baseline'):
    def offered(a,p,m,s):return (a,p,s)==('helper','person','now') and m in (('methodone','methodtwo') if variant=='other_method_unassessed' else ('methodone',)) and variant!='no_method'
    def effects(a,p,m,s,t):return offered(a,p,m,s) and m=='methodone' and t in (('after','bad') if variant=='mixed_unassessed' else ('after',)) and variant!='empty_effects'
    return dict(zp=lambda:'person',znow=lambda:'now',zeligible=lambda a,p:(a,p)==('helper','person') and variant!='empty_agents',
        zenabling=offered,zeffects=effects,
        za=lambda p:Content(SCENES,tuple(p=='person' and assessed and not(variant=='mixed_unassessed' and s=='bad') for s in SCENES)),
        zc=lambda p:Content(SCENES,tuple(p==('other' if variant=='foreign_success' else 'person') and capable and (s=='now' if variant=='wrong_time' else s=='after') for s in SCENES)))


def enabling_checks():
    rows=[]
    for assessed,capable in product((False,True),repeat=2):
        result=evaluate(support_fixture(),support_model(assessed,capable));assert result==[assessed,assessed and capable];rows.append(result)
    cases={}
    for variant,want in [('no_method',[True,False]),('empty_agents',[True,False]),('empty_effects',[False,False]),
        ('mixed_unassessed',[False,True]),('other_method_unassessed',[False,True]),('foreign_success',[True,False]),('wrong_time',[True,False])]:
        result=evaluate(support_fixture(),support_model(variant=variant));assert result==want,(variant,result);cases[variant]=result
    for name in ('za','zc','zeligible','zenabling','zeffects'):
        m=support_model();m[name]=unknown
        try:evaluate(support_fixture(),m)
        except ValueError as e:assert 'Unknown topical' in str(e)
        else:raise AssertionError(name)
    return dict(combinations=len(rows),cases=cases,unknown_inputs_refused=5,
        possibility_not_full_assessment_or_guarantee=True)


@lru_cache(None)
def native(support=False,compare=False):
    d=parse((ROOT/CORE).read_text(encoding='utf-8'));d['declarations']=closure(d,(['hzvl','hzvm'] if support else ['hzvj','hzvk'])+(['hzeq','hzer'] if compare else []));d['statements']=[]
    text=format_graph(d,'compact')+EXTRA
    for name in (('hzvl','hzvm') if support else ('hzvj','hzvk')):
        text+='q[t[c[k '+name+'['+(SUPPORT if support else TOPIC)+']][k zperson[]]][k zcontext[]]].'
    if compare:
        old='k ztopic[] k zanchor[] p ztopics i[p a m a plan a s d][k zavailable[v p v plan v s]]'
        old+=' i[p a m a plan a s d t d][k zoutcomes[v p v plan v s v t]] i[p a m a plan a s d t d][k zselected[v p v plan v s v t]]'
        text+=''.join('q[t[c[k '+n+'['+old+']][k zperson[]]][k zcontext[]]].' for n in ('hzeq','hzer'))
    return parse(text)


def source_checks():
    rows={}
    for variant,current,future,want in [('baseline',(True,True),(True,True),[True,True]),
        ('wrong_reference',(True,True),(True,True),[False,False]),('wrong_matter',(True,True),(True,True),[True,False]),
        ('guided',(True,True),(True,True),[True,False])]:
        result=evaluate(native(),model(current,future,variant,True),NATIVE_DOMAIN);assert result==want,(variant,result);rows[variant]=result
    for variant,current,future,want in [('baseline',(False,False),(True,True),[True,True]),
        ('fixed_scope',(False,False),(True,False),[True,False]),('unassessed_after',(False,False),(True,True),[False,False]),
        ('split_results',(False,False),(True,True),[True,False])]:
        result=evaluate(native(True),model(current,future,variant,True),NATIVE_DOMAIN);assert result==want,(variant,result);rows['enable_'+variant]=result
    for variant,current,want in [('baseline',(True,True),[True,True,True,False]),('immediate_only',(False,False),[True,False,True,True])]:
        result=evaluate(native(compare=True),model(current,variant=variant,native=True),NATIVE_DOMAIN)
        assert result==want,(variant,result);rows['old_comparison_'+variant]=result
    return dict(cases=rows,native_rlk_and_task_profiles_executed=True,same_person_topic_anchor_at_result=True,
        no_primitive_substitution_for_definitions=True)


def construction_checks():
    d=parse((ROOT/CORE).read_text(encoding='utf-8'));d['declarations']=closure(d,['hzvh']);d['statements']=[]
    text=format_graph(d,'compact')+'r zone[] a.r zinspect[i[h[a] e]] c.q[k zinspect[k hzvh[r[k zone[]]]]].'
    doc=parse(text);m={x['name']:unknown for x in doc['declarations'] if x['kind']=='primitive'}
    m['zinspect']=lambda code:code.rank==0 and task_matter(code,'hzvg')=='one'
    assert evaluate(doc,m,NATIVE_DOMAIN)==[True]
    # Executing the same description demands its referent; construction did not.
    doc=parse(format_graph({**doc,'statements':[]},'compact')+'r zperson[] a.r zcontext[] d.q[t[c[s[k hzvh[r[k zone[]]]]][k zperson[]]][k zcontext[]]].')
    m.update(zperson=lambda:'person',zcontext=lambda:'now')
    try:evaluate(doc,m,NATIVE_DOMAIN)
    except ValueError as e:assert 'Unknown topical' in str(e)
    else:raise AssertionError('Unknown referent silently evaluated')
    return dict(closed_rank_zero_task=True,unknown_referent_and_judgment_not_executed=True,
        explicit_execution_requires_referent=True)


@lru_cache(None)
def collective_fixture():
    d=parse((ROOT/CORE).read_text(encoding='utf-8'));d['declarations']=closure(d,['hzvn','hzvo']);d['statements']=[]
    text=format_graph(d,'compact')+EXTRA+'''
r zepoch[] a.r zhistory[d] c.r zbefore[d d] c.r zperiods[a d] c.r zpeople[a] c.r zpresent[a d] c.
r zstandard[h[a] c h[a] c d] c.r zprogress[] e.
'''
    args='k zepoch[] p zhistory p zbefore p zperiods p zpeople p zpresent p zstandard '+TOPIC
    return parse(text+'q[t[k hzvn['+args+']][k zcontext[]]].q[t[k hzvo['+args+' k zprogress[]]][k zcontext[]]].')


def collective_checks():
    rows={};domain=(*NATIVE_DOMAIN,'epoch')
    for variant,current,want in [('baseline',(True,True),[True,False]),('not_attained',(True,False),[False,True]),('wrong_reference',(True,True),[False,False])]:
        m=model(current,variant=variant,native=True)
        m.update(zepoch=lambda:'epoch',zhistory=lambda s:True,zbefore=lambda a,b:SCENES.index(a)<SCENES.index(b),
            zperiods=lambda e,s:(e,s)==('epoch','now'),zpeople=lambda p:p=='person',zpresent=lambda p,s:(p,s)==('person','now'),
            zstandard=lambda people,success,s:s=='now' and all(people(p)==(p=='person') for p in domain) and success('person'),
            zprogress=lambda:Content(SCENES,(True,False,False,False,False,False)))
        result=evaluate(collective_fixture(),m,domain);assert result==want,(variant,result);rows[variant]=result
    return dict(cases=rows,collective_criterion_receives_same_topical_ability=True)


def structure():
    old=parent();new=load_catalog(ROOT,BASIS)
    for name,text in build().items():assert (ROOT/name).read_text(encoding='utf-8')==text,name
    size=len(old.document['declarations']);assert new.document['declarations'][:size]==old.document['declarations']
    assert len(new.document['declarations'])==size+13 and old.document['statements']==new.document['statements']
    assert len(new.document['statements'])==41
    for name in (FULL,CORE,LIBRARY):
        d=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    index=json.loads((ROOT/INDEX).read_text(encoding='utf-8'));validate_hashes(ROOT,index['source_sha256'])
    active=index['works']['kant-1784'];assert active['document']=='examples/v016/kant-explanatory-question.noema'
    cat=load_catalog(ROOT,active['meaning_basis']);assert len(active['reviews'])==10
    for name in active['reviews']:
        review=json.loads((ROOT/name).read_text(encoding='utf-8'));indices=[r['index'] for r in review['selection']['statements']]
        assert selection_binding(cat,indices)==review['selection']==selection_binding(new,indices)
    return dict(new_definitions=13,new_primitives=0,preserved_statements=41,preserved_review_selections=10,
        roundtrips=True,source_adoption=False)


def reading():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0014')
    return dict(status='topical_standing_and_enabling_comparison',reviewer='assistant_review',
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[148,412],text=unit['text'][148:412]),
        references=[dict(url='https://korpora.org/Kant/aa08/040.html',lines=[19,22],use='現在の能力とその能力を持つ状態へ置く可能性を区別し、宗教上の事柄という対象を両方に保持する。')],
        decision='主題付き能力だけが旧式の現在地の方法評価に残る不一致を除く。元の事柄の範囲と本人を固定し、既有能力・その取得可能性・集団の到達を接続する比較候補。',
        limitations=LIMITS,whole_unit_semantically_verified=False)


def build_report():
    results={}
    for name,fn in [('capacity',capacity_checks),('enabling',enabling_checks),('source',source_checks),('construction',construction_checks),('collective',collective_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    note=reading();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==note;s=note['source']
    prior='reports/collective-attainment-v1.json';validate_hashes(ROOT,json.loads((ROOT/prior).read_text(encoding='utf-8'))['source_sha256'])
    paths=set(build())|set(parent().source_sha256)|{READING,INVENTORY,INDEX,prior,'scripts/compose_topical_standing.py','scripts/check_topical_standing.py',
        'scripts/compose_bodily_acquisition.py','scripts/compose_collective_attainment.py','scripts/compose_falling_depiction.py',
        'tests/test_topical_standing.py','docs/topical-standing-v1.md','noema/constructed_semantics.py','noema/constructed.py',
        'noema/constructed_discourse.py','noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='partial_topical_standing_and_enabling_comparison',document=FULL,**results,
        alignment=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],start=148,end=412,source=s['text'],definitions=list(MEANINGS),
            status='explicit_interpretive_annotation',full_semantic_equivalence=False),new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(reading()));report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Topical standing and fixed enabling endpoints checked',flush=True)


if __name__=='__main__':main()
