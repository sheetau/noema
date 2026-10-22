"""Check bounded arrangements, public prohibition and actual collective assent."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_fixed_religious_compact import ROOT,LIBRARY,BASIS,PARENT,PRIMITIVES,MEANINGS,LIMITS,build,parent,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

REPORT='reports/fixed-religious-compact-v1.json'
READING='data/fixed-religious-compact-reading-v1.json'
DOC='docs/fixed-religious-compact-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
PRIORS=('reports/provisional-order-sentence-v1.json','reports/congregational-choices-v1.json','reports/temporary-institution-v1.json')
DOMAIN=('p','q','third','actone','acttwo','agreement','community','regime','audience','period','authority','role','other')
SCENES=('reference','candidate','before','start','middle','end','outer')
POINTS=('before','start','middle','end')
BIND=('community','regime','audience','period')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r z'+n+'[] d.' for n in SCENES)+'r zbindings[] j[a].'
OTHER='d zalt[bindings j[a] reference d candidate d anchor d] e[b point[e[n p a b][n p a b]]].'
CTX='k zreference[] k zcandidate[] k zstart[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+EXTRA+OTHER+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def base(d,variant='baseline'):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['zbindings']=lambda:SequenceValue(BIND,'"individual"')
    v['aa']=lambda p:p in ('p','q') or (p=='third' and variant in ('third_person','third_party'))
    v['h257z']=lambda r,c,t:(r,c)==('reference','candidate') and t in POINTS and not(variant=='missing_history' and t=='middle')
    v['ic']=lambda a,b,c:c=='candidate' and a in POINTS and b in POINTS and (POINTS.index(a)<POINTS.index(b) or(variant=='cycle' and(a,b)==('middle','start')))
    v['h26ex']=lambda p,r,c,s,e:(p,r,c)==('period','reference','candidate') and ((s,e)==('start','end') or (variant=='ambiguous_period' and(s,e)==('start','middle')))
    v['ib']=lambda p,c,t:(p,c)==('p','candidate') and t in POINTS and not(variant=='life_gap' and t=='middle') and not(variant=='short_life' and t=='end')
    v['h26cs']=lambda g,c,r:(g,c,r)==('regime','community','reference') and variant!='other_regime'
    v['ce']=lambda a,r:(a,r)==('audience','reference') and variant!='private_audience'
    v['cc']=lambda a,u,r:a in ('actone','acttwo') and(u,r)==('audience','reference') and not(variant=='no_candidates')
    v['h26ey']=lambda a,g,c,r:a in ('actone','acttwo') and(g,c,r)==('regime','community','reference') and variant!='other_topic'
    v['h26ez']=lambda g,c,r:'authority' if(g,c,r)==('regime','community','reference') and variant!='wrong_source' else 'other'
    v['h26e2']=lambda:'role' if variant!='wrong_role' else 'other'
    def prohibition(source,p,role,target,b,polarity,t):
        # The two activity descriptions must both be covered for each person.
        expected=(source,p,role) in (('authority',x,'role') for x in ('p','q')) and normalized(target)==('r5h4',0) and normalized(b) in tuple((p,a,'regime','community','audience') for a in ('actone','acttwo'))
        return expected and polarity is False and t in ('start','middle') and not(variant=='missing_one_prohibition' and p=='q' and normalized(b)[1]=='acttwo') and not(variant=='missing_middle_prohibition' and t=='middle')
    v['h7k']=prohibition
    v['h26cv']=lambda g,c,r,h,t:(g,c,r,h)==('regime','community','reference','candidate') and t in ('start','middle') and not(variant=='missing_middle_regime' and t=='middle')
    return v

@lru_cache(None)
def period_checks():
    d=fixture(('r5hz','r5h2'),'q[k r5hz[k zperiod[] k zreference[] k zcandidate[] k zstart[] k zend[]]].q[k r5h2[k zp[] k zperiod[] k zreference[] k zcandidate[] k zstart[] k zend[]]].')
    rows={}
    for variant in ('baseline','ambiguous_period','cycle','missing_history','life_gap','short_life','nonhuman','other_lifetime','other_period','reverse','zero'):
        v=base(d,variant)
        if variant=='nonhuman':v['aa']=lambda p:False
        if variant=='other_lifetime':v['ib']=lambda p,c,t:(p,c)==('q','candidate') and t in POINTS
        if variant=='other_period':v['zperiod']=lambda:'other'
        if variant=='reverse':v['zstart']=lambda:'end';v['zend']=lambda:'start'
        if variant=='zero':v['zend']=lambda:'start'
        actual=run(d,v);expected=[variant in ('baseline','life_gap','short_life','nonhuman','other_lifetime'),variant=='baseline']
        # Removing an interior history point does not by itself invalidate an otherwise ordered supplied history.
        if variant=='missing_history':expected=[True,False]
        assert actual==expected,(variant,actual);rows[variant]=actual
    return dict(period_and_single_lifetime=rows,native_ta_tb_and_period=True,complete_history_is_input_responsibility=True)

@lru_cache(None)
def prohibition_checks():
    d=fixture(('r5h5',),'q[k r5h5[k zregime[] k zcommunity[] k zaudience[] k zreference[] k zstart[]]].');rows={}
    for variant in ('baseline','third_person','other_regime','private_audience','other_topic','no_candidates','wrong_source','wrong_role','missing_one_prohibition','permission_only','wrong_polarity','wrong_target','wrong_binding','wrong_point'):
        v=base(d,variant)
        if variant=='permission_only':v['h7k']=lambda *args:False
        for selected,pos,wrong in (('wrong_polarity',5,True),('wrong_target',3,('r5h6',0)),('wrong_binding',4,('q','acttwo','other','community','audience')),('wrong_point',6,'end')):
            if variant==selected:
                original=v['h7k'];v['h7k']=lambda *args,original=original,pos=pos,wrong=wrong:original(*(args[:pos]+(wrong,)+args[pos+1:]))
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert v['dg'] is unknown and v['f3'] is unknown
    v=base(d);v['h7k']=unknown
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown prohibition accepted')
    return dict(all_people_all_public_questioning_activities=rows,execution_not_required=True,unknown_rejected=True)

@lru_cache(None)
def terms_checks():
    d=fixture(('r5h6',),'q[t[k r5h6[k zbindings[] '+CTX+']][k zouter[]]].');rows={}
    def compact(variant='baseline',binding=('alpha',)*4):
        v=base(d,variant);community,regime,audience,period=binding
        v['zbindings']=lambda:SequenceValue(binding,'"individual"')
        v['aa']=lambda p:p in ('alpha','beta')
        v['h26cs']=lambda g,c,r:(g,c,r)==(regime,community,'reference') and variant!='other_regime'
        v['ce']=lambda a,r:(a,r)==(audience,'reference') and variant!='private_audience'
        v['cc']=lambda a,u,r:(u,r)==(audience,'reference') and variant!='no_candidates'
        v['h26ey']=lambda a,g,c,r:(g,c,r)==(regime,community,'reference')
        v['h26ez']=lambda g,c,r:'alpha';v['h26e2']=lambda:'alpha'
        v['h7k']=lambda source,p,role,target,b,polarity,t:normalized((source,role,target))==('alpha','alpha',('r5h4',0)) and normalized(b) in tuple((p,a,regime,community,audience) for a in ('alpha','beta')) and polarity is False and t in ('start','middle') and not(variant=='missing_middle_prohibition' and t=='middle')
        v['h26cv']=lambda g,c,r,h,t:(g,c,r,h)==(regime,community,'reference','candidate') and t in ('start','middle') and not(variant=='missing_middle_regime' and t=='middle')
        v['h26ex']=lambda p,r,c,s,e:(p,r,c)==(period,'reference','candidate') and ((s,e)==('start','end') or(variant=='ambiguous_period' and(s,e)==('start','middle')))
        if variant=='late_anchor':v['zstart']=lambda:'middle'
        if variant=='wrong_length':v['zbindings']=lambda:SequenceValue((*binding,'alpha'),'"individual"')
        if variant=='wrong_period':v['zbindings']=lambda:SequenceValue((*binding[:3],'beta'),'"individual"')
        return v
    for variant in ('baseline','missing_middle_regime','missing_middle_prohibition','ambiguous_period','cycle','other_regime','private_audience','no_candidates','late_anchor','wrong_length','wrong_period'):
        actual=run(d,compact(variant),('alpha','beta'));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    positions=[]
    for i in range(4):
        binding=tuple('beta' if j==i else 'alpha' for j in range(4));v=compact(binding=binding)
        assert run(d,v,('alpha','beta'))==[True]
        v['zbindings']=lambda:SequenceValue(('alpha',)*4,'"individual"')
        assert run(d,v,('alpha','beta'))==[False];positions.append(i)
    return dict(same_configuration_and_prohibition_throughout_period=rows,all_four_binding_positions=positions,
        endpoint_state_not_required=True,native_world_definitions=True,finite_model_individuals=2,
        model_limit='Objects may coincide except the tested binding position; separate prohibition and agreement models distinguish people and activities. No definition boundary used.')

@lru_cache(None)
def execution_checks():
    d=fixture(('r5h4',),'q[t[k r5h4[k zbindings[]]][k zstart[]]].');rows={}
    binding=('alpha','beta','alpha','alpha','alpha')
    for variant in ('baseline','not_occurred','other_performer','other_activity','short_binding','long_binding'):
        v=base(d);v['zbindings']=lambda:SequenceValue(binding,'"individual"')
        v['dg']=lambda a,t:(a,t)==('beta','start') and variant!='not_occurred'
        v['f3']=lambda p,a,t:(p,a,t)==('alpha','beta','start') and variant!='other_performer'
        if variant=='other_activity':v['zbindings']=lambda:SequenceValue(('alpha','alpha',*binding[2:]),'"individual"')
        if variant=='short_binding':v['zbindings']=lambda:SequenceValue(binding[:-1],'"individual"')
        if variant=='long_binding':v['zbindings']=lambda:SequenceValue((*binding,'alpha'),'"individual"')
        actual=run(d,v,('alpha','beta'));assert actual==[variant=='baseline'];rows[variant]=actual[0]
    return dict(actual_execution=rows,classification_and_policy_separate=True)

def assent_model(d,variant='baseline',other=False):
    v=base(d,variant);target=('zalt' if other else 'r5h6',0)
    v['h26dk']=lambda a,t,b,r,c,anchor:normalized((a,t,b,r,c,anchor))==('agreement',target,BIND,'reference','candidate','start') and variant!='other_terms'
    members=('p',) if variant=='one_party' else () if variant=='empty' else ('p','q','third') if variant=='third_party' else ('p','q')
    v['h26dj']=lambda a,p,r,c,anchor:(a,r,c,anchor)==('agreement','reference','candidate','start') and p in members
    actions=(('p','actone','before'),('q','acttwo','middle' if variant=='late_assent' else 'start'))
    v['dg']=lambda a,t:(a,t) in tuple((a,t) for p,a,t in actions) and variant!='not_occurred'
    v['f3']=lambda p,a,t:(p,a,t) in actions and variant!='other_performer'
    v['h26dl']=lambda p,a,g,t,b,r,c,anchor,point:normalized((g,t,b,r,c,anchor))==('agreement',target,BIND,'reference','candidate','start') and(p,a,point) in actions and not(variant=='missing_assent' and p=='q')
    if variant=='nonhuman':v['aa']=lambda p:p=='p'
    for name in ('h26ex','h26cv','h26ez','h26ey','h7k','ib'):v[name]=unknown
    return v

@lru_cache(None)
def agreement_checks():
    query='q[k r5jb[k zagreement[] '+' '.join('k z'+n+'[]' for n in BIND)+' '+CTX+']].'
    d=fixture(('r5jb',),query);rows={}
    for variant in ('baseline','one_party','empty','third_party','late_assent','not_occurred','other_performer','missing_assent','nonhuman','other_terms','cycle','private_audience','other_regime'):
        actual=run(d,assent_model(d,variant));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    general=fixture(('r5ja',),'q[k r5ja[k zagreement[] r[p zalt] k zbindings[] '+CTX+']].')
    assert run(general,assent_model(general,other=True))==[True]
    return dict(complete_same_terms_assent=rows,quoted_arrangement_not_executed=True,generic_agreement_accepts_other_subject=True,no_oath_or_all_population_condition=True)

@lru_cache(None)
def structure_checks():
    c=catalog();old=parent()
    for n in read(BASIS)['imported_symbols']:
        assert c.entries[n]['declaration']==old.entries[n]['declaration'] and c.entries[n]['meaning_ja']==old.entries[n]['meaning_ja']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    for notation in ('compact','full'):
        s=format_graph(doc,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==doc
    assert len(old.document['statements'])==103
    assert read(READING)==reading_record()
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),roundtrips=True,main_statements_unchanged=103,semantic_review_characters_added=0)

def reading_record():
    unit=next(u for u in read(INVENTORY)['units'] if u['id']=='kant-1784:u0013');text=unit['text'];end=text.index('sich zu einigen,',2310)+len('sich zu einigen,')
    page='artifacts/law-enactment-v1/page-489.jpg'
    return dict(status='partial_dependency_not_sentence_review',source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[2310,end],text=text[2310:end]),
        interpretation=LIMITS,original_page=dict(path=page,sha256=digest((ROOT/page).read_bytes()),visually_read=True),
        primary_evidence=dict(url='https://korpora.org/kant/aa08/039.html',lines='28–32',observation='期間の限定を含む合意対象と、その結果の二つのdadurchを同じ文の中で区別する。'),
        unresolved=['無期限の合意を含む一般化とauch nurの限定提示','人類の改善過程の期間への因果的影響・消去への見立て・不毛化','後世への害の様相と強調','全面的不許可と前文との対照・著者帰属・全文通読'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,page,*PRIORS)})

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('periods',period_checks),('prohibition',prohibition_checks),('terms',terms_checks),('execution',execution_checks),('agreement',agreement_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(catalog().source_sha256)|{LIBRARY,BASIS,DOC,READING,INVENTORY,*PRIORS,'artifacts/law-enactment-v1/page-489.jpg',
        'scripts/compose_fixed_religious_compact.py','scripts/check_fixed_religious_compact.py','tests/test_fixed_religious_compact.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py'}
    return dict(status='bounded_fixed_religious_arrangement_and_collective_assent',document=LIBRARY,**results,
        alignment=dict(**reading_record()['source'],statements=[],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
