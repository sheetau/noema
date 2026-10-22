"""Check institutional error and same-condition, same-goal hindrance."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_government_self_misunderstanding import ROOT,LIBRARY,BASIS,MEANINGS,PRIMITIVES,LIMITS,STATE,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown

DOC='docs/government-self-misunderstanding-v1.md';READING='data/government-self-misunderstanding-reading-v1.json'
INDEX='data/semantic-review-index-v198.json';INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/social-attitude-paths-v1.json','reports/paired-restriction-influence-v1.json','reports/public-offers-sentence-v1.json')
DOMAIN=('government','community','judgment','item','alias','person','condition','factor','branch')
SCENES=('reference','now','later','offleft','offright','onleft','onright')
FIELDS=('government','community','judgment','item','reference')
SOURCE=('government','community','person','condition','reference','now')
TAIL='k zvariables[] p zequation '+ 'k zfactor[] p zworld p zmatch p zevaluated k zgoal[]'

def z(n):return 'k z'+n+'[]'
def args(ns):return ' '.join(z(n) for n in ns)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
def codeid(c):return c.rank,json.loads(c.syntax)
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query):
    d=deepcopy(catalog().document)
    extra=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))
    extra+='r ztruth[a d d] c.d h26ae[item a scope d] e[b point[k ztruth[v item v scope v point]]].'
    extra+='r zvariables[] j[a].r zequation[a '+STATE+'] c.r zworld['+STATE+'] d.r zmatch['+STATE+' '+STATE+'] c.r zevaluated[d] c.'
    extra+='r zsuccess[d] c.d zgoal[] e[b point[k zsuccess[v point]]].'
    prefix=parse('p:'+extra);ns={r['name'] for r in prefix['declarations']}
    d['declarations']=prefix['declarations']+[r for r in d['declarations'] if r['name'] not in ns]
    d.update(declarations=closure(d,(*roots,*ns)),statements=[])
    return parse(format_graph(d,'compact')+query)
def run(d,v):return evaluate(d,v,DOMAIN,SCENES,True)
def rejects(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e),str(e)
    else:raise AssertionError('Unknown input became a known result')
def model(d,polarity=True,truth=False):
    v={r['name']:unknown for r in d['declarations'] if r['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v.update(aa=lambda p:p=='person',h237n=lambda g,c,t:(g,c,t)==('government','community','now'),
        h256s=lambda g,c,t:(g,c,t)==('government','community','now'),
        h26ad=lambda i,r:i in ('item','alias') and r=='reference',
        h26ag=lambda i,r:'item' if i=='alias' else i,
        h26pk=lambda *a:a==('item','government','community','reference'),
        h247u=lambda *a:a==('government','judgment','now'),
        h26pj=lambda *a:a==('judgment','government','item','reference','now'),
        h245q=lambda j,i,c,r,s,t:(j,i,r,s,t)==('judgment','item','reference',polarity,'now') and codeid(c)==(0,{'kind':'function_ref','symbol':'h26ae'}),
        ztruth=lambda i,r,t:truth if (i,r,t)==('item','reference','now') else True,
        h26pl=lambda *a:a==('condition','government','community','reference'),
        h26pm=lambda *a:a==('condition','person','reference'),
        h26kg=lambda c,r,t:(c,r)==('condition','reference') and t in ('now','onleft','onright'),
        zvariables=lambda:SequenceValue(('factor','branch'),'"individual"'),
        zequation=lambda variable,state:state(variable),
        zworld=lambda state:('on' if state('factor') else 'off')+('right' if state('branch') else 'left'),
        zmatch=lambda on,off:on('branch')==off('branch'),
        zevaluated=lambda t:t in SCENES[3:],
        zsuccess=lambda t:t in ('now','offleft','offright','onright'))
    return v

@lru_cache(None)
def judgment_checks():
    rows={}
    for sign in (False,True):
        literal='e['+z('item')+']['+z('item')+']';literal=literal if sign else 'u['+literal+']'
        q=''.join('q[k '+name+'['+args(FIELDS)+' '+literal+' '+z('now')+']].' for name in ('r56z','r562'))
        q+='q[k r563['+args(('government','community','reference','now'))+']].'
        d=fixture(('r56z','r562','r563'),q)
        for truth in (False,True):
            v=model(d,sign,truth);got=run(d,v);assert got==[True,sign!=truth,sign!=truth],(sign,truth,got)
            rows[str((sign,truth))]=got
    sign='e['+z('item')+']['+z('item')+']'
    q=''.join('q[k r562['+args(('government','community','judgment',item,'reference'))+' '+sign+' '+z('now')+']].' for item in ('item','alias'))
    d=fixture(('r562',),q);v=model(d);assert run(d,v)==[True,True]
    for name in ('h237n','h256s','h26ad','h26pk','h247u','h26pj','h245q'):
        changed=dict(v);changed[name]=lambda *a:False;assert run(d,changed)==[False,False],name
        changed=dict(v);changed[name]=unknown;rejects(d,changed)
    changed=dict(v);changed['ztruth']=unknown;rejects(d,changed)
    # A different self-referential item in the SAME judgment cannot qualify this item.
    changed=dict(v);changed['h26pj']=lambda j,g,i,r,t:i=='alias';assert run(d,changed)==[False,False]
    # Change one input at a time while keeping every relation on the original tuple.
    checks={}
    names=(*FIELDS,'now')
    for i in range(len(names)):
        other=list(names);other[i]='later' if i in (4,5) else 'person'
        q='q[k r562['+args(other[:5])+' '+sign+' '+z(other[5])+']].'
        doc=fixture(('r562',),q);got=run(doc,model(doc));assert got==[False],(i,got);checks[str(i)]=got[0]
    return dict(polarity_truth_matrix=rows,alias_keeps_same_truth=True,wrong_arguments=checks,
        missing_attribution_self_position_topic_content_scope_rejected=True,unknown_rejected=True,
        boundary='No definition boundary. h26ae is a native situation constructor over an explicit content truth fixture; r5cc canonicalization and existential error run natively. Government is not an aa person.')

@lru_cache(None)
def external_checks():
    d=fixture(('r564',),'q[k r564['+args(SOURCE)+']].');v=model(d);assert run(d,v)==[True]
    for name in ('h237n','h256s','aa','h26pl','h26pm','h26kg'):
        changed=dict(v);changed[name]=lambda *a:False;assert run(d,changed)==[False],name
        changed=dict(v);changed[name]=unknown;rejects(d,changed)
    for i in range(6):
        names=list(SOURCE);names[i]='later' if i>=4 else 'alias'
        doc=fixture(('r564',),'q[k r564['+args(names)+']].');assert run(doc,model(doc))==[False],i
    # Mere public presence is independent of actual error and actual causal harm.
    v['ztruth']=lambda *a:True;v['zsuccess']=lambda *a:True;assert run(d,v)==[True]
    return dict(same_public_source_person_condition_reference_point=True,government_not_person=True,
        presence_alone_neither_error_nor_hindrance=True,unknown_rejected=True)

@lru_cache(None)
def hindrance_checks():
    d=fixture(('r566',),'q[k r566['+args(('condition','reference'))+' '+TAIL+']].');v=model(d);rows={}
    cases=('one_branch_harmed','both_harmed','no_harm','neutral_branch_variation','improvement_only','reversed_condition','different_condition',
        'different_reference','unassessed','incomplete_matches','no_matches','missing_on_side','no_solutions','duplicate_variables','factor_outside')
    for case in cases:
        w=dict(v)
        if case=='both_harmed':w['zsuccess']=lambda t:t.startswith('off')
        if case=='no_harm':w['zsuccess']=lambda t:True
        if case=='neutral_branch_variation':w['zsuccess']=lambda t:t.endswith('right')
        if case=='improvement_only':w['zsuccess']=lambda t:t.startswith('on')
        if case=='reversed_condition':w['h26kg']=lambda c,r,t:t.startswith('off')
        if case=='different_condition':w['h26kg']=lambda c,r,t:c=='alias' and t.startswith('on')
        if case=='different_reference':w['h26kg']=lambda c,r,t:r=='later' and t.startswith('on')
        if case=='unassessed':w['zevaluated']=lambda t:t!='onright'
        if case=='incomplete_matches':w['zmatch']=lambda on,off:not on('branch') and not off('branch')
        if case=='no_matches':w['zmatch']=lambda *a:False
        if case=='missing_on_side':w['zequation']=lambda var,s:not s(var) if var=='branch' and s('factor') else s(var)
        if case=='no_solutions':w['zequation']=lambda var,s:not s(var)
        if case=='duplicate_variables':w['zvariables']=lambda:SequenceValue(('factor','branch','branch'),'"individual"')
        if case=='factor_outside':w['zfactor']=lambda:'alias'
        got=run(d,w);assert got==[case in ('one_branch_harmed','both_harmed')],(case,got);rows[case]=got[0]
    for name in ('h26kg','zsuccess','zevaluated','zmatch','zequation'):
        w=dict(v);w[name]=unknown;rejects(d,w)
    return dict(cases=rows,native_intervention_solutions_and_goal_comparison=True,
        actual_success_can_coexist_with_potential_harm=True,unknown_rejected=True,
        boundary='Two Boolean variables; branch-preserving correspondence is fixed independently of outcomes. zgoal is an actual native Noema situation; all comparison/order and solution guards execute.')

@lru_cache(None)
def combined_checks():
    d=fixture(('r567',),'q[k r567['+args(SOURCE)+' '+TAIL+']].');v=model(d);assert run(d,v)==[True];rows={}
    for case in ('correct_self_understanding','other_government_error','other_government_condition','internal_condition','absent_now','other_condition_harm','other_goal'):
        w=dict(v)
        if case=='correct_self_understanding':w['ztruth']=lambda *a:True
        if case=='other_government_error':w['h247u']=lambda g,j,t:g=='alias'
        if case=='other_government_condition':w['h26pl']=lambda c,g,co,r:g=='alias'
        if case=='internal_condition':w['h26pm']=lambda *a:False
        if case=='absent_now':w['h26kg']=lambda c,r,t:(c,r)==('condition','reference') and t.startswith('on')
        if case=='other_condition_harm':w['h26kg']=lambda c,r,t:(c=='condition' and t=='now') or (c=='alias' and t.startswith('on'))
        if case=='other_goal':w['zsuccess']=lambda t:True
        got=run(d,w);assert got==[False],(case,got);rows[case]=got[0]
    return dict(cases=rows,native_joint_government_error_source_and_model=True,
        no_inference_from_misunderstanding_to_cause=True,
        remaining='The goal is generic; it is not yet bound to r56y foreign attitude arrival and retention. Struggle/necessity and source sentence are not verified.')

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0015')
    return dict(status='government_self_misunderstanding_and_external_hindrance_partial',
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[890,1049],text=u['text'][890:1049]),
        interpretation=LIMITS,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_characters=0,
        unresolved=['同じ国外到達・保持を妨害モデルの目標へ結ぶ','複数障害と格闘活動・必要性','本文設定・先行自由例と同じ精神への照応','auch/selbst・全文帰属と通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json')})

@lru_cache(None)
def structure_checks():
    c=catalog();old=parent();assert not c.document['statements'];assert len(old.document['statements'])==114
    for n,e in c.entries.items():
        if n in old.entries:assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    validate_hashes(ROOT,read(BASIS)['import_source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        t=format_graph(c.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==c.document
    t=format_graph(c.document,'compact');ranks={}
    for name in ('r56z','r562','r567'):
        for rank,label in enumerate(('','b','c','d')):
            try:parse(t+'q[e[r '+label+'[p '+name+']][r '+label+'[p '+name+']]].')
            except ValueError as e:assert 'Quoted evaluation' in str(e),str(e)
            else:ranks[name]=rank;break
    assert len(ranks)==3
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),unchanged_manuscript_statements=114,
        inherited_meanings_preserved=True,roundtrips=True,minimum_quote_ranks=ranks,new_verified_characters=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in (('judgment',judgment_checks),('external',external_checks),('hindrance',hindrance_checks),('combined',combined_checks),('structure',structure_checks)):
        results[n]=f();print(n+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INDEX,INVENTORY,*PRIORS,'data/eighth-paragraph-source-reading-v1.json',
        'scripts/compose_government_self_misunderstanding.py','scripts/check_government_self_misunderstanding.py','tests/test_government_self_misunderstanding.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_paired_influence.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='institutional_self_misunderstanding_and_external_hindrance_checked_partial',document=LIBRARY,**results,
        alignment=dict(**read(READING)['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
