"""Check local gains, generation turnover, complete futures and unexecuted goals."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_human_enlightenment_block import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/human-enlightenment-block-v1.json'
DOC='docs/human-enlightenment-block-v1.md'
READING='data/human-enlightenment-block-reading-v1.json'
PRIORS=('reports/thinking-reform-v1.json','reports/mediated-guardianship-v1.json','reports/covenant-question-v1.json')
DOMAIN=('old','young','topic','second','body','agreement','creed','subject','community','humanity')
SCENES=('anchor','later','end','outside')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r zt'+n+'[] d.' for n in SCENES)
FORM=' '.join('k z'+n+'[]' for n in ('body','agreement','creed','subject','community'))

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,boundaries=(),extra=EXTRA):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+extra+query)

def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update({'zt'+n:lambda n=n:n for n in SCENES})
    v.update(h255o=lambda:'anchor',h256m=lambda:'humanity',h254z=lambda agreement:'anchor')
    return v
def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)
def content(value):return Content(SCENES,tuple(value and p=='later' for p in SCENES))

@lru_cache(None)
def topic_checks():
    from scripts.check_thinking_reform import values,PEOPLE,SCENES as NORMAL,CONSTANTS
    doc=fixture(('r5aa',),'q[k r5aa[k zp[] k ztopic[] k zscope[] k zanchor[]]].',('r2gy',),CONSTANTS+'r ztopic[] a.')
    rows={}
    for variant in ('baseline','opinions_only','mixed_counterparts','both_normal','empty_cases','changed_basis','no_opportunity','missing_counterpart','cyclic_normality'):
        v=values(doc,variant);v['ztopic']=lambda:'topic'
        actual=evaluate(doc,v,PEOPLE,NORMAL,True);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(native_normal_comparison_and_all_corresponding_judgments=rows,
        boundary='r2gy; its native own-understanding, reasons and no-guidance checks are pinned in thinking-reform-v1')

def population_model(doc,variant='baseline'):
    v=base(doc);history=('anchor','later','end')
    v['h256n']=lambda candidate,point:candidate=='later' and point in history
    v['ic']=lambda first,last,candidate:candidate=='later' and first in history and last in history and (
        first!=last if variant=='cyclic' else history.index(first)<history.index(last))
    v['aa']=lambda person:person in ('old','young')
    def alive(person,candidate,point):
        if candidate!='later':return False
        if variant=='extinction' and point=='end':return False
        if person=='old':return point in history and not (variant in ('turnover','new_generation') and point!='anchor')
        return person=='young' and point in ('later','end')
    v['h256o']=alive
    v['r2qm']=lambda person,scope,point:scope=='anchor' and not(variant=='missing_evaluation' and person=='old' and point=='end')
    v['h226u']=lambda person,scope,topic:person in ('old','young') and scope=='anchor' and topic in ('topic','second')
    def judgment(person,topic,scope,point):
        if scope!='anchor' or person not in ('old','young'):return False
        if topic=='topic':
            if person=='old' and variant=='loss' and point!='anchor':return False
            if person=='old' and variant=='regain' and point=='later':return False
            return True
        return topic=='second' and ((variant=='partial_gain' and person=='old' and point in ('later','end')) or
            (variant=='new_generation' and person=='young' and point in ('later','end')) or
            (variant=='outside_gain' and point=='outside'))
    v['r5aa']=judgment
    return v

@lru_cache(None)
def population_checks():
    query='q[k r5ab[k zold[] k ztanchor[] k ztanchor[] k ztlater[]]].q[k r5ad[k ztanchor[] k ztlater[] k ztanchor[] k ztlater[]]].'
    doc=fixture(('r5ab','r5ad'),query,('r2qm','r5aa'));rows={}
    for variant in ('baseline','partial_gain','turnover','new_generation','loss'):
        actual=run(doc,population_model(doc,variant));expected=[variant=='partial_gain',variant in ('partial_gain','new_generation')]
        assert actual==expected,(variant,actual);rows[variant]=actual
    return dict(native_individual_and_cross_generation_gains=rows,
        no_all_domain_completion_or_global_no_loss_condition=True,
        boundaries=['r2qm','r5aa; normal comparison checked separately'])

@lru_cache(None)
def future_checks():
    query='q[t[k r5af[k ztanchor[] k ztanchor[]]][k ztlater[]]].q[t[k r5ag[k ztanchor[] k ztanchor[]]][k ztlater[]]].'
    doc=fixture(('r5af','r5ag'),query,('r2qm','r5aa'));rows={}
    accepted={'baseline','turnover','loss','outside_gain'}
    for variant in ('baseline','partial_gain','turnover','new_generation','loss','regain','outside_gain','missing_evaluation','extinction','cyclic'):
        actual=run(doc,population_model(doc,variant));assert actual==[variant in accepted,False],(variant,actual);rows[variant]=actual
    d=fixture(('r5af',),'q[t[k r5af[k ztanchor[] k ztoutside[]]][k ztlater[]]].',('r2qm','r5aa'))
    assert run(d,population_model(d))==[False]
    for n in ('h256n','h256o','r2qm','r5aa'):
        v=population_model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(n)
    return dict(native_temporal_order_all_pairs_and_all_living_people=rows,
        missing_anchor_rejected=True,finite_future_never_certifies_unending=True,unknown_rejected=True,
        extinction_not_success=True,regression_then_recovery_is_further_progress=True)

@lru_cache(None)
def causal_checks():
    doc=fixture(('r5ai',),'q[t[k r5ai[k zbody[] k zagreement[] k ztanchor[]]][k ztlater[]]].',('r5ag',));rows={}
    for variant in ('baseline','result_false','no_cause','other_body','other_agreement','other_target','other_population','other_reference','other_candidate'):
        v=base(doc);v['r5ag']=lambda scope,anchor:content(variant!='result_false' and (scope,anchor)==('anchor','anchor'))
        def causes(agreement,body,code,bindings,reference,candidate):
            wanted=['agreement','body','r5ah',('humanity',),'anchor','later']
            changes={'other_agreement':(0,'body'),'other_body':(1,'agreement'),'other_target':(2,'r47a'),
                'other_population':(3,('community',)),'other_reference':(4,'end'),'other_candidate':(5,'end')}
            if variant in changes:
                i,value=changes[variant];wanted[i]=value
            return variant!='no_cause' and code.rank==0 and (agreement,body,symbol(code),tuple(bindings.items),reference,candidate)==tuple(wanted)
        v['h255k']=causes;actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    bindings={}
    for seq in ((),('humanity',),('community',),('humanity','humanity')):
        literal='l[a]['+' '.join('k z'+n+'[]' for n in seq)+']'
        d=fixture(('r5ah',),'q[t[k r5ah['+literal+' k ztanchor[]]][k ztlater[]]].',('r5ag',));v=base(d)
        v['r5ag']=lambda scope,anchor:content((scope,anchor)==('anchor','anchor'))
        actual=run(d,v);assert actual==[seq==('humanity',)];bindings[str(seq)]=actual[0]
    return dict(same_agreement_causal_result=rows,exact_humanity_binding=bindings,
        boundary='r5ag; no claim of true infinite result in the finite model')

@lru_cache(None)
def formation_checks():
    doc=fixture(('r5ak',),'q[k r5ak['+FORM+' k ztanchor[]]].',('r47h','r47d'));rows={}
    names=('body','agreement','creed','subject','community')
    for variant in ('baseline','wrong_kind','no_formation','no_goal','other_agreement','other_goal','swapped_bindings','wrong_anchor'):
        v=base(doc);v['r47h']=lambda *a:variant!='wrong_kind' and a==(*names,'anchor')
        v['r47d']=lambda *a:variant!='no_formation' and a==(*names,'anchor')
        def purpose(body,agreement,goal,bindings,reference):
            wanted=['body','agreement','r5aj',('body','agreement'),'anchor']
            changes={'other_agreement':(1,'body'),'other_goal':(2,'r47c'),'swapped_bindings':(3,('agreement','body')),'wrong_anchor':(4,'end')}
            if variant in changes:
                i,value=changes[variant];wanted[i]=value
            return variant!='no_goal' and goal.rank==0 and (body,agreement,symbol(goal),tuple(bindings.items),reference)==tuple(wanted)
        v['h255l']=purpose;actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert all(v[n] is unknown for n in ('h256n','h256o','h255k','h226v'))
    adapters={};small=('body','agreement');seq=('body','agreement','body','agreement','body')
    for items in (seq,seq[:-1],(*seq,'agreement'),tuple(reversed(seq))):
        literal='l[a]['+' '.join('k z'+n+'[]' for n in items)+']'
        d=fixture(('r5al',),'q[t[k r5al['+literal+']][k ztlater[]]].',('r5ak',));v=base(d)
        v['r5ak']=lambda *a:a==(*seq,'anchor')
        actual=run(d,v,small);assert actual==[items==seq];adapters[str(items)]=actual[0]
    d=fixture(('r5aj',),'q[t[k r5aj[l[a][k zbody[] k zagreement[]] k ztanchor[]]][k ztlater[]]].',('r5ai',));v=base(d)
    v['r5ai']=lambda body,agreement,ref:content((body,agreement,ref)==('body','agreement','anchor'))
    assert run(d,v,small)==[True]
    return dict(same_kind_formation_and_adopted_purpose=rows,exact_formation_bindings=adapters,
        goal_not_executed_or_required_possible=True,boundaries=['r47h','r47d','r5ak for adapter','r5ai for goal adapter'])

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    return dict(status='human_further_enlightenment_and_same_covenant_purpose_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[444,712],text=unit['text'][444:712]),
        primary_page=read('data/covenant-question-reading-v1.json')['original_page'],adopted_readings=LIMITS,
        remaining=['同じ仮定形成から無効性への内容の接続','最高権力・帝国議会・最も厳粛な和平締結の承認の種類と最上級',
            'schlechterdingsの全面性とsollte auchの譲歩の提示','一文全体の著者帰属と意味判断'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    new,old=catalog(),parent()
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):
            assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record();p=read(READING)['primary_page'];assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    assert not new.document['statements'] and len(old.document['statements'])==98
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_manuscript_statements=98)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('topic',topic_checks),('population',population_checks),('future',future_checks),('causal',causal_checks),('formation',formation_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,read(READING)['source_inventory'],read(READING)['primary_page']['path'],
        'scripts/compose_human_enlightenment_block.py','scripts/check_human_enlightenment_block.py','tests/test_human_enlightenment_block.py',
        'scripts/check_thinking_reform.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='human_further_enlightenment_and_same_covenant_purpose_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
