"""Check policy decomposition, hypothetical selection and nonliteral presentation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_protective_petition_discourse import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,PETITION,CASES,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

REPORT='reports/protective-petition-discourse-v1.json'
DOC='docs/protective-petition-discourse-v1.md'
READING='data/protective-petition-discourse-reading-v1.json'
PRIORS=('reports/protective-petition-v1.json','reports/personal-insight-grounds-v1.json','reports/congregational-choices-v1.json','reports/joint-petition-v1.json','reports/civic-participation-discourse-v1.json')
SCENES=('reference','candidate','anchor','actual','outside','context')
NODES=('thronenode','purposenode','selectionnode','reservationnode','author')
EXTRA='r zbindings[] j[a].'+''.join('r z'+n+'[] d.' for n in SCENES)+''.join('r z'+n+'[] a.' for n in NODES)
EXTRA+='r ztruth[d] c.d zwhole[] e[b point[k ztruth[v point]]].'
CONTEXT=('reference','candidate','anchor')
CONTEXT_CODE='k zreference[] k zcandidate[] k zanchor[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries and d['kind']=='definition':d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+EXTRA+query)
def query(root):return 'q[t[k '+root+'[k zbindings[] '+CONTEXT_CODE+']][k zactual[]]].'
def run(d,v,domain=('alpha','beta')):return evaluate(d,v,domain,SCENES,True)
def base(doc,bindings=('alpha',)*4):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*SCENES,*NODES)})
    v['zbindings']=lambda:SequenceValue(bindings,'"individual"')
    return v
def content(value):return Content(SCENES,tuple(value and t=='actual' for t in SCENES))

def policy_model(doc,variant='both'):
    v=base(doc)
    v['h26ds']=lambda p,c,r,h,t:(p,c,r,h,t)==('alpha','alpha','reference','candidate','actual') and variant!='inactive'
    def reform(g,c,cong,f,s,old,new,r,h,a):
        return variant not in ('only_retention','empty') and(g,c,cong,f,s,old,new,r,h,a)==('alpha','alpha','alpha','alpha','alpha','alpha','beta','reference','candidate','actual' if variant=='late_selection' else 'anchor')
    def retention(c,cong,f,s,old,r,h,a):
        return variant not in ('only_reform','empty') and(c,cong,f,s,old,r,h,a)==('alpha','alpha' if variant=='overlap' else 'beta','alpha','alpha','alpha',*CONTEXT)
    v['r5ge']=reform;v['r5f7']=retention
    def effect(kind,*a):
        wanted=('beta' if variant=='other_policy' else 'alpha','alpha','alpha' if kind=='protect' or variant=='overlap' else 'beta','alpha','alpha','alpha' if kind=='retain' or variant=='other_configuration' else 'beta',*CONTEXT)
        valid=a==wanted and variant!=('unprotected' if kind=='protect' else 'hindered')
        return Content(SCENES,tuple(valid and t==('anchor' if variant=='other_effect_time' else 'actual') for t in SCENES))
    v['r5gg']=lambda *a:effect('protect',*a);v['r5gh']=lambda *a:effect('retain',*a)
    return v

@lru_cache(None)
def policy_checks():
    roots=('r5hf','r5hg','r5hh');d=fixture(roots,''.join(query(n) for n in roots),('r5ge','r5f7','r5gg','r5gh'));rows={}
    for variant,expected in (
        ('both',[True,True,True]),('only_reform',[True,True,True]),('only_retention',[True,True,True]),
        ('empty',[True,True,True]),('overlap',[True,True,True]),('late_selection',[True,True,True]),
        ('unprotected',[False,False,True]),('hindered',[False,True,False]),
        ('other_policy',[False,False,False]),('other_configuration',[False,False,True]),
        ('other_effect_time',[False,False,False]),('inactive',[False,False,False])):
        actual=run(d,policy_model(d,variant));assert actual==expected,(variant,actual)
        assert actual[0]==(actual[1] and actual[2]);rows[variant]=actual
    rejected=[]
    for n in ('h26ds','r5ge','r5f7','r5gg','r5gh'):
        v=policy_model(d);v[n]=unknown
        try:run(d,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
        rejected.append(n)
    return dict(combined_equals_protection_and_nonhindrance=rows,
        empty_recipients_do_not_remove_policy=True,selection_held_at_anchor=True,
        boundaries=['r5ge/r5f7 selectors and r5gg/r5gh effects; native components preserved in prior reports'],unknown_rejected=rejected)

@lru_cache(None)
def binding_checks():
    rows={}
    specifications=(
      ('r5he','r5fx',PETITION,(0,1,2,3)),('r5hf','r5gi',PETITION,(3,1)),('r5hi','r2uj',PETITION,(2,1)),
      ('r5hk','r5ge',CASES,(9,1,4,5,6,7,8)),('r5hl','r5f7',CASES,(1,4,5,6,7)),
      ('r5hm','r5gg',CASES,(3,1,4,5,6,8)),('r5hn','r5gh',CASES,(3,1,4,5,6,7)),
      ('r5ho','r5fz',CASES,(1,4,5,6)))
    for root,target,names,positions in specifications:
        d=fixture((root,),query(root),(target,));checked=[]
        def target_tuple(vals):
            if root=='r5he':return (*vals[:3],('r5gj',1),(vals[3],vals[1]),*CONTEXT,'actual')
            suffix=('actual',) if root=='r5hi' else ('reference',) if root=='r5ho' else CONTEXT
            return (*[vals[i] for i in positions],*suffix)
        def install(vals,wanted):
            v=base(d,vals);v['h257z']=lambda r,h,t:(r,h,t)==CONTEXT
            if root in ('r5hf','r5hm','r5hn'):v[target]=lambda *a:content(a==wanted)
            else:v[target]=lambda *a:normalized(a)==wanted
            return v
        for i in range(len(names)):
            vals=tuple('beta' if k==i else 'alpha' for k in range(len(names)));wanted=target_tuple(vals)
            assert run(d,install(vals,wanted))==[True],(root,i)
            if i in positions:assert run(d,install(('alpha',)*len(names),wanted))==[False],(root,i)
            checked.append(i)
        for length in (len(names)-1,len(names)+1):
            assert run(d,install(('alpha',)*length,target_tuple(('alpha',)*len(names))))==[False],root
        rows[root]=checked
    return dict(exact_four_and_ten_positions=rows,wrong_lengths_rejected=True,
        shared_reference_candidate_anchor_and_later_effect=True,
        boundaries=[target for _,target,_,_ in specifications])

@lru_cache(None)
def submission_checks():
    d=fixture(('r5he',),query('r5he'),('r2uj',));rows={}
    for variant in ('baseline','no_activity','missing_voice','wrong_policy','wrong_recipient','wrong_anchor','wrong_reference'):
        v=base(d,('alpha','alpha','beta','beta'))
        v['h26db']=lambda g,p,r,h,t:(g,r,h,t)==('alpha',*CONTEXT) and p in ('alpha','beta')
        v['aa']=lambda p:p in ('alpha','beta')
        v['h26cu']=lambda p,c,r,h,t:p in ('alpha','beta') and(c,r,h,t)==('alpha',*CONTEXT)
        v['r2uj']=lambda p,c,t:(p,c,t)==('beta','alpha','actual')
        v['dg']=lambda a,t:variant!='no_activity' and(a,t)==('alpha','actual')
        v['h26dc']=lambda a,p,r,h,t:(a,p,r,h,t)==('alpha','alpha' if variant=='wrong_recipient' else 'beta','reference','candidate','actual')
        v['df']=lambda p,a,t:p in ('alpha','beta') and(a,t)==('alpha','actual')
        wanted=(('r5gj',1),('alpha' if variant=='wrong_policy' else 'beta','alpha'),'outside' if variant=='wrong_reference' else 'reference','candidate','outside' if variant=='wrong_anchor' else 'anchor','actual')
        v['h26dd']=lambda p,a,target,b,r,h,anchor,t:p in ('alpha','beta') and a=='alpha' and normalized((target,b,r,h,anchor,t))==wanted and not(variant=='missing_voice' and p=='beta')
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        for name in ('h26ds','h26dt','h26ea'):assert name not in v or v[name] is unknown
    return dict(native_shared_protective_submission=rows,policy_and_literal_throne_not_executed=True,
        boundary='r2uj only; native office construction preserved in joint-petition report')

@lru_cache(None)
def metonymy_checks():
    roots=('r5hi','r5hj');d=fixture(roots,''.join(query(n) for n in roots),('r2uj',));rows={}
    for variant in ('baseline','no_seat','different_holder','different_community','different_point','not_monarch'):
        v=base(d,('alpha','alpha','beta','beta'))
        v['r2uj']=lambda p,c,t:(p,c,t)==('beta','alpha','actual') and variant!='not_monarch'
        wanted=('alpha','alpha' if variant=='different_holder' else 'beta','beta' if variant=='different_community' else 'alpha','anchor' if variant=='different_point' else 'actual')
        v['h26ea']=lambda *a:variant!='no_seat' and a==wanted
        actual=run(d,v);assert actual==[variant!='not_monarch',variant=='baseline'],(variant,actual);rows[variant]=actual
    return dict(authority_and_associated_seat_are_distinct=rows,
        physical_seat_used_only_in_literal_depiction=True,boundary='r2uj; preserved native office evidence')

@lru_cache(None)
def discourse_checks():
    q='q[k r5hp['+' '.join('k z'+n+'[]' for n in NODES)+' r d[k zwhole[]] k zcontext[]]].'
    d=fixture(('r5hp',),q);f=lambda n:(n,1);whole=('zwhole',3)
    expected={
      'h26eb':{('thronenode','author',whole,f('r5g6'),f('r5hi'),f('r5hj'),'context')},
      'h26ec':{('purposenode','author',whole,f('r5g6'),f('r5he'),f('r5hg'),'context')},
      'h26ed':{('reservationnode','author',whole,f('r5g6'),f('r5hf'),f('r5hg'),f('r5hh'),'context')},
      'h26ee':{('selectionnode','author',whole,f('r5ho'),f('r5hk'),f('r5hm'),'context')},
      'ue':{('thronenode','purposenode','context'),('purposenode','selectionnode','context'),('selectionnode','reservationnode','context')}}
    rows={}
    for variant in ('baseline',*expected,'wrong_author','wrong_context','wrong_whole','swapped_metonymy','wrong_purpose','only_protection','actual_instead_of_selection','merged_nodes'):
        v=base(d);wanted=deepcopy(expected)
        if variant=='wrong_author':v['zauthor']=lambda:'thronenode'
        if variant=='wrong_context':v['zcontext']=lambda:'reference'
        changes={'wrong_whole':('h26eb',2,('r5gi',3)),
          'swapped_metonymy':('h26eb',4,f('r5hj')),'wrong_purpose':('h26ec',5,f('r5hh')),
          'only_protection':('h26ed',6,f('r5hg')),'actual_instead_of_selection':('h26ee',4,f('r5hm'))}
        if variant in changes:
            name,index,value=changes[variant];row=list(next(iter(wanted[name])));row[index]=value;wanted[name]={tuple(row)}
        v.update({n:lambda *a,n=n,values=values:n!=variant and normalized(a) in values for n,values in wanted.items()})
        if variant=='merged_nodes':
            v['zreservationnode']=lambda:'selectionnode'
            for n in expected:v[n]=lambda *a:True
        actual=run(d,v,NODES);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        for n in ('ztruth','h26ea','h26ds','h26di','h26dm'):assert n not in v or v[n] is unknown
    for name in expected:
        v=base(d);v.update({n:lambda *a,values=values:normalized(a) in values for n,values in expected.items()});v[name]=unknown
        try:run(d,v,NODES)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(name)
    return dict(same_whole_purpose_selection_reservation_metonymy_and_order=rows,
        quoted_world_and_physical_depiction_not_executed=True,unknown_rejected=True)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(x for x in read(inv)['units'] if x['id']=='kant-1784:u0013');text=u['text'];parts=[]
    for fragment,names in (
        ('einen Vorschlag vor den Thron bringen könnte',['r5he','r5hi','r5hj','r5hp']),
        ('um diejenigen Gemeinden in Schutz zu nehmen',['r5hf','r5hg','r5hp']),
        ('die sich etwa nach ihren Begriffen der besseren Einsicht zu einer veränderten Religionseinrichtung geeinigt hätten',['r5hk','r5hm','r5ho','r5hp']),
        ('ohne doch diejenigen zu hindern, die es beim Alten wollten bewenden lassen.',['r5hh','r5hl','r5hn','r5hp'])):
        start=text.index(fragment,1437,2309);parts.append(dict(range=[start,start+len(fragment)],text=fragment,definitions=names))
    return dict(status='protective_petition_discourse_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1437,2309],text=text[1437:2309]),parts=parts,
        primary_evidence=[
          dict(url='https://korpora.org/kant/aa08/039.html',lines='24–27',observation='同じ提案に目的節・仮定的な改革対象・非妨害の留保が続く構文を照合した。'),
          dict(url='https://lexika.digitale-sammlungen.de/adelung/lemma/bsb00009134_2_3_3550',entry='Der Stuhl',section='2.(3)(a).2 Figürlich',
            observation='座を王の威厳や統治者側に対応させる転義がある。本文のThronを公的な宛先と読む補助根拠であり、単独で唯一の語義を証明しない。')],
        adopted_readings=LIMITS,remaining=['whole-sentence quantification','Nun wohl gleichsam and preceding anaphora','application to same whole content and holistic review'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    sources=parents();new=catalog();old={n:e for s in sources for n,e in s.entries.items()}
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record() and not new.document['statements'] and len(sources[0].document['statements'])==102
    actual={d['name'] for d in closure(new.document,['r5he'])}
    assert not actual&{'r5hj','h26ea','h26eb','h26ec','h26ed','h26ee'}
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        metonymy_not_a_physical_submission_condition=True,preserved_manuscript_statements=102)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('policy',policy_checks),('bindings',binding_checks),('submission',submission_checks),('metonymy',metonymy_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,reading_record()['source_inventory'],
        'scripts/compose_protective_petition_discourse.py','scripts/check_protective_petition_discourse.py','tests/test_protective_petition_discourse.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py','scripts/compose_civic_participation_discourse.py'}
    return dict(status='protective_petition_discourse_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
