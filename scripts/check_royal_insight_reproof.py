"""Check quoted self-appraisal, authority limits and possible justified reproof."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue,Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_royal_insight_reproof import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,NAMES,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

DOC='docs/royal-insight-reproof-v1.md';READING='data/royal-insight-reproof-reading-v1.json';REPORT='reports/royal-insight-reproof-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
EVIDENCE='artifacts/royal-insight-reproof-v1/suetonius-grammaticis.html'
PRIORS=('reports/royal-writing-oversight-v1.json','reports/monarchical-religion-sentence-v1.json','reports/personal-insight-grounds-v1.json')
DOMAIN=('alpha','beta','gamma');SCENES=('reference','candidate','comparison','other')
EXTRA=''.join('r z'+n+'[] '+('a' if n in DOMAIN else 'd')+'.' for n in (*DOMAIN,*SCENES))+'r zbindings[] j[a].'
A='k zalpha[]';B='k zbeta[]';C='k zgamma[]';R='k zreference[]';P='k zcandidate[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(root,query,boundaries=()):
    d=deepcopy(catalog().document)
    for x in d['declarations']:
        if x['name'] in boundaries:x.update(kind='primitive',parameters=[p['sort'] for p in x['parameters']]);x.pop('body')
    d.update(declarations=closure(d,[root]),statements=[])
    return parse(format_graph(d,'compact')+EXTRA+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def base(d,bindings=('alpha',)*7):
    v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['zbindings']=lambda:SequenceValue(bindings,'"individual"')
    v['h26ag']=lambda i,r:i
    v['h26ad']=lambda i,r:r=='reference'
    v['h26c5']=lambda i,f,r:(f,r)==('alpha','reference')
    v['h26iv']=lambda i,f,r:(f,r)==('alpha','reference')
    v['h26dn']=lambda s,f,l,h,r,p:(s,f,r,p)==('beta','alpha','reference','candidate') and DOMAIN.index(l)>=DOMAIN.index(h)
    v['h26ai']=lambda p,j,r,t:(p,r,t)==('alpha','reference','candidate') and j in ('beta','gamma')
    v['h26iu']=lambda *a:a==('alpha','beta','alpha','reference','candidate')
    v['h245q']=lambda *a:normalized(a)==('beta','gamma',('h26ae',0),'reference',True,'candidate')
    v['h26dq']=lambda *a:normalized(a)==('gamma',('r5pp',0),('gamma','alpha','beta'),'reference',True,'candidate')
    v['h26dr']=lambda *a:a==('alpha','beta','beta','reference','candidate','candidate')
    return v
def unknown_rejected(d,v):
    try:run(d,v)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown accepted')
def mismatches(d,model,lengths):
    rows={}
    for name,length in lengths:
        for pos in range(length):
            v=model(d);old=v[name]
            def changed(*a,pos=pos,old=old):
                a=list(a);a[pos]='mismatch';return old(*a)
            v[name]=changed;actual=run(d,v);assert actual==[False],(name,pos,actual);rows[name+'_'+str(pos)]=False
    return rows

@lru_cache(None)
def maximum_checks():
    d=fixture('r5po','q[k r5po['+' '.join((C,A,B,R,P))+']].');rows={}
    for variant in ('baseline','empty','nonreflexive','cycle','incomparable','not_highest','ties','one_unclassified_item','outside_field','wrong_standard','wrong_reference','wrong_assessment','alias','unknown'):
        v=base(d)
        if variant=='empty':v['h26iv']=lambda *a:False
        if variant=='nonreflexive':v['h26dn']=lambda s,f,l,h,r,p:DOMAIN.index(l)>DOMAIN.index(h)
        if variant=='cycle':v['h26dn']=lambda s,f,l,h,r,p:l==h or (l,h) in {('alpha','beta'),('beta','gamma'),('gamma','alpha')}
        if variant=='incomparable':v['h26dn']=lambda s,f,l,h,r,p:l==h
        if variant=='not_highest':v['zgamma']=lambda:'beta'
        if variant=='ties':v['h26dn']=lambda *a:True
        if variant=='one_unclassified_item':v['h26ad']=lambda i,r:i!='alpha'
        if variant=='outside_field':v['h26c5']=lambda i,f,r:i!='alpha'
        if variant=='wrong_standard':v['zbeta']=lambda:'gamma'
        if variant=='wrong_reference':v['zreference']=lambda:'other'
        if variant=='wrong_assessment':v['zcandidate']=lambda:'other'
        if variant=='alias':v['h26ag']=lambda i,r:'gamma' if i=='beta' else i;v['zgamma']=lambda:'beta'
        if variant=='unknown':v['h26dn']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant in ('baseline','ties','alias')],(variant,actual);rows[variant]=actual[0]
    return dict(native_full_range_maximum=rows,unknown_rejected=True)

def subjective(d):
    v=base(d)
    # These remain unknown even in positive cases: descriptions do not execute.
    for n in ('h26dn','h26iv','h26ae'):v[n]=unknown
    return v

@lru_cache(None)
def held_checks():
    d=fixture('r5pq','q[k r5pq['+' '.join((A,B,C,C,A,B,R,P))+']].');rows={}
    for missing in (None,'h26ai','h26iu','h245q','h26dq','h26ad','h26c5'):
        v=subjective(d)
        if missing:v[missing]=lambda *a:False
        actual=run(d,v);assert actual==[missing is None],(missing,actual);rows[missing or 'baseline']=actual[0]
    contrasts=mismatches(d,subjective,(('h26ai',4),('h26iu',5),('h245q',6),('h26dq',6)))
    v=subjective(d);v['h26dn']=lambda *a:False;v['h26ae']=lambda *a:Content(SCENES,(False,)*len(SCENES));assert run(d,v)==[True]
    # The two judgment roles need not be different individuals.
    v=subjective(d);v['zgamma']=lambda:'beta';v['h245q']=lambda *a:normalized(a)==('beta','beta',('h26ae',0),'reference',True,'candidate')
    v['h26dq']=lambda *a:normalized(a)==('beta',('r5pp',0),('beta','alpha','beta'),'reference',True,'candidate');assert run(d,v)==[True]
    for n in ('h26ai','h26iu','h245q','h26dq','h26ag'):
        v=subjective(d);v[n]=unknown;unknown_rejected(d,v)
    return dict(own_held_content_and_maximum=rows,exact_arguments=contrasts,objective_false_content_allowed=True,
        quoted_truth_and_rank_not_executed=True,same_judgment_allowed=True,no_current_formation_required=True,unknown_rejected=True)

@lru_cache(None)
def reason_checks():
    d=fixture('r5pr','q[k r5pr['+' '.join((A,B,A,R,P))+']].');rows={}
    for missing in (None,'h26dr','h26dq','h245q','h26iu','h26ai'):
        v=subjective(d)
        if missing:v[missing]=lambda *a:False
        actual=run(d,v);assert actual==[missing is None],(missing,actual);rows[missing or 'baseline']=actual[0]
    contrasts=mismatches(d,subjective,(('h26dr',6),))
    v=subjective(d);v['h26dr']=lambda *a:a==('alpha','beta','gamma','reference','candidate','candidate');assert run(d,v)==[False]
    v=subjective(d);v['h26dr']=unknown;unknown_rejected(d,v)
    return dict(native_held_reason_for_same_act=rows,reason_arguments=contrasts,ranking_judgment_alone_not_reason=True,
        quoted_comparison_not_executed=True,unknown_rejected=True)

def authority(d):
    v=base(d)
    v['r2uj']=lambda *a:a==('alpha','alpha','candidate')
    v['h234f']=lambda *a:a==('beta','alpha','candidate')
    v['r2ui']=lambda *a:a==('alpha','beta','alpha','candidate')
    v['h26ix']=lambda s,f,r:s in ('alpha','gamma') and (f,r)==('alpha','reference')
    v['h26iw']=lambda *a:False
    v['h26iy']=lambda f,r:(f,r)==('alpha','reference')
    return v

@lru_cache(None)
def authority_checks():
    d=fixture('r5pu','q[k r5pu['+' '.join((A,A,A,R,P))+']].',('r2uj','r2ui'));rows={}
    for variant in ('baseline','one_specialist_exception','second_office_exception','other_person','other_office','other_specialist','other_field','other_reference','other_point','not_monarch','unknown'):
        v=authority(d)
        if variant=='not_monarch':v['r2uj']=lambda *a:False
        if variant not in ('baseline','not_monarch','unknown'):
            wanted=['alpha','beta','gamma','alpha','reference','candidate']
            changes={'other_person':(0,'beta'),'other_office':(1,'alpha'),'other_specialist':(2,'beta'),'other_field':(3,'beta'),'other_reference':(4,'other'),'other_point':(5,'other')}
            if variant in changes:i,x=changes[variant];wanted[i]=x
            if variant=='second_office_exception':
                v['h234f']=lambda o,c,p:o in ('beta','gamma') and (c,p)==('alpha','candidate')
                v['r2ui']=lambda a,o,c,p:o in ('beta','gamma') and (a,c,p)==('alpha','alpha','candidate');wanted[1]='gamma'
            v['h26iw']=lambda *a:a==tuple(wanted)
        if variant=='unknown':v['h26iw']=unknown;unknown_rejected(d,v);continue
        actual=run(d,v);assert actual==[variant not in ('one_specialist_exception','second_office_exception','not_monarch')],(variant,actual);rows[variant]=actual[0]
    d=fixture('r5pv','q[t[k r5pv['+R+']]['+P+']].',('r2uj','r2ui'));literal={}
    for variant in ('baseline','grammar_exception','nongrammar_exception','second_community_exception'):
        v=authority(d)
        if variant=='grammar_exception':v['h26iw']=lambda *a:a==('alpha','beta','gamma','alpha','reference','candidate')
        if variant=='nongrammar_exception':
            v['h26ix']=lambda s,f,r:s=='gamma' and r=='reference'
            v['h26iw']=lambda a,o,s,f,r,p:f=='beta'
        if variant=='second_community_exception':
            v['r2uj']=lambda *a:a in (('alpha','alpha','candidate'),('gamma','beta','candidate'))
            v['h234f']=lambda *a:a in (('beta','alpha','candidate'),('gamma','beta','candidate'))
            v['r2ui']=lambda *a:a in (('alpha','beta','alpha','candidate'),('gamma','gamma','beta','candidate'))
            v['h26iw']=lambda *a:a==('gamma','gamma','alpha','alpha','reference','candidate')
        actual=run(d,v);assert actual==[variant in ('baseline','nongrammar_exception')],(variant,actual);literal[variant]=actual[0]
    return dict(all_same_offices_and_specialists=rows,literal_grammar_domain_and_all_rulers=literal,
        boundaries=['r2uj','r2ui'],contextual_extension_not_inferred_from_literal=True,unknown_rejected=True)

def reproach(d):
    v=base(d)
    v['dg']=lambda *a:a==('beta','candidate')
    v['df']=lambda *a:a==('alpha','beta','candidate')
    v['h26iz']=lambda *a:a==('beta','alpha','reference','candidate','comparison')
    v['fa']=lambda *a:a==('gamma','beta','comparison')
    v['h26i2']=lambda *a:normalized(a)==('beta','alpha','beta',('r5pw',0),('alpha','gamma','beta'),'reference','comparison')
    v['h247i']=lambda *a:a==('beta','reference','comparison')
    return v

@lru_cache(None)
def reproof_checks():
    d=fixture('r5py','q[k r5py['+' '.join((A,C,B,B,R,P))+']].');rows={}
    for missing in (None,'dg','df','h26iz','fa','h26i2','h247i'):
        v=reproach(d)
        if missing:v[missing]=lambda *a:False
        actual=run(d,v);assert actual==[missing is None],(missing,actual);rows[missing or 'baseline']=actual[0]
    contrasts=mismatches(d,reproach,(('h26iz',5),('fa',3),('h26i2',7),('h247i',3)))
    v=reproach(d);v['fa']=lambda *a:a==('gamma','beta','candidate');assert run(d,v)==[False]
    v=reproach(d);v['h247i']=lambda *a:a==('beta','reference','candidate');assert run(d,v)==[False]
    v=reproach(d);v['h26iz']=lambda *a:a[:4]==('beta','alpha','reference','candidate') and a[4] in ('comparison','other');assert run(d,v)==[True]
    for n in ('h26iz','fa','h26i2','h247i'):
        v=reproach(d);v[n]=unknown;unknown_rejected(d,v)
    return dict(native_possible_justified_reproof=rows,exact_arguments=contrasts,
        actuality_not_required=True,one_admissible_response_suffices=True,same_candidate_required=True,
        quoted_principle_not_executed=True,unknown_rejected=True)

@lru_cache(None)
def joining_checks():
    args=('alpha','alpha','beta','alpha','beta','alpha','beta','reference','candidate');terms=(A,A,B,A,B,A,B,R,P);rows={}
    for root,left,right in (('r5ps','r5pe','r5pr'),('r5pz','r5ps','r5py')):
        d=fixture(root,'q[k '+root+'['+' '.join(terms)+']].',(left,right))
        wanted=('alpha','beta','alpha','reference','candidate') if right=='r5pr' else ('alpha','alpha','alpha','beta','reference','candidate')
        for pos in (None,*range(len(wanted))):
            v=base(d);v[left]=lambda *a:a==args;expected=list(wanted)
            if pos is not None:expected[pos]='other' if pos>=len(wanted)-2 else ('beta' if expected[pos]=='alpha' else 'alpha')
            v[right]=lambda *a:a==tuple(expected)
            actual=run(d,v);assert actual==[pos is None];rows[root+'_'+str(pos)]=actual[0]
        v=base(d);v[left]=lambda *a:False;v[right]=lambda *a:a==wanted;assert run(d,v)==[False]
    adapters={}
    for root,target,length in (('r5pp','r5po',3),('r5pw','r5pu',3),('r5pt','r5ps',7),('r5p2','r5pz',7),('r5px','r5pv',0)):
        d=fixture(root,'q[t[k '+root+'[k zbindings[] '+R+']]['+P+']].',(target,));positions=[]
        for pos in range(max(length,1)):
            b=tuple('beta' if i==pos else 'alpha' for i in range(length));v=base(d,b)
            if length:v[target]=lambda *a:a==(*b,'reference','candidate')
            else:v[target]=lambda r:Content(SCENES,tuple(r=='reference' and p=='candidate' for p in SCENES))
            assert run(d,v,DOMAIN[:2])==[True]
            if length:
                v['zbindings']=lambda:SequenceValue(('alpha',)*length,'"individual"');assert run(d,v,DOMAIN[:2])==[False];positions.append(pos)
        for bad in ((length-1,) if length else ())+(length+1,):
            v['zbindings']=lambda:SequenceValue(('alpha',)*bad,'"individual"');assert run(d,v,DOMAIN[:2])==[False]
        v['zbindings']=lambda:SequenceValue(b,'"individual"');v['zreference']=lambda:'other';assert run(d,v,DOMAIN[:2])==[False]
        v['zreference']=lambda:'reference';v['zcandidate']=lambda:'other';assert run(d,v,DOMAIN[:2])==[False]
        adapters[root]=dict(independent_positions=positions,wrong_lengths_reference_and_point_rejected=True)
    return dict(same_intervention_and_possible_reproof=rows,adapters=adapters,boundaries=['r5pe','r5pr','r5ps','r5py','r5po','r5pu','r5pz','r5pv'])

def reading_record():
    u=next(x for x in read(INVENTORY)['units'] if x['id']=='kant-1784:u0013')
    fragment='sowohl wenn er dieses aus eigener höchsten Einsicht thut, wo er sich dem Vorwurfe aussetzt: Caesar non est supra Grammaticos'
    start=u['text'].index(fragment,3645);previous=read('data/royal-writing-oversight-reading-v1.json')
    quote='Caesar non est supra Grammaticos';qstart=u['text'].index(quote,start)
    return dict(status='self_assessed_highest_insight_and_possible_justified_reproof_partial',
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[start,start+len(fragment)],text=fragment),
        literal_quotation=dict(range=[qstart,qstart+len(quote)],text=quote,content='r5pv',quoted_family='r5px',contextual_application='r5pw',presentation_not_integrated=True),
        interpretation=LIMITS,primary_pages=previous['primary_pages'],new_verified_characters=0,whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/040.html',observation='第十二文の自己の見識・批判への曝露・ラテン語引用を同じ介入に結ぶ。'),
          dict(url='https://penelope.uchicago.edu/Thayer/L/Roman/Texts/Suetonius/de_Grammaticis*.html',path=EVIDENCE,chapters=[4,22],observation='grammaticiの学識の射程、およびMarcellusとTiberiusの言語用法をめぐる並行例。Kantと同一文言又は直接の典拠とは主張しない。')],
        unresolved=['引用文言の提示と著者帰属','selbstの取り立て・würdigtの皮肉','聖職者の専制支援・残余臣民','二側の同一基準での比較とnoch weit mehr','全仮定範囲と威厳損傷への条件接続・全文通読'],
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (LIBRARY,BASIS,DOC,INVENTORY,EVIDENCE,*PRIORS,'data/royal-writing-oversight-reading-v1.json',*(x['path'] for x in previous['primary_pages']))})

@lru_cache(None)
def structure_checks():
    new=catalog();old={n:e for c in parents() for n,e in c.entries.items()}
    for n,e in new.entries.items():
        if n not in MEANINGS and n not in PRIMITIVES:assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja']
    assert len(parents()[1].document['statements'])==107 and not new.document['statements']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    assert read(READING)==reading_record()
    for notation in ('compact','full'):
        s=format_graph(new.document,notation);assert parse(s)==parse(transcribe(s,alphabet='v2'))==new.document
    return dict(new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),inherited_meanings_unchanged=True,main_statements_unchanged=107,roundtrips=True,verified_characters_added=0)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for name,fn in (('maximum',maximum_checks),('held',held_checks),('reason',reason_checks),('authority',authority_checks),('reproof',reproof_checks),('joining',joining_checks),('structure',structure_checks)):
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{READING,DOC,INVENTORY,EVIDENCE,*PRIORS,*(p['path'] for p in read(READING)['primary_pages']),
        'data/royal-writing-oversight-reading-v1.json','scripts/compose_royal_insight_reproof.py','scripts/check_royal_insight_reproof.py','tests/test_royal_insight_reproof.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='self_assessed_highest_insight_and_possible_justified_reproof_partial',**results,
        alignment=dict(**read(READING)['source'],document=LIBRARY,definitions=list(MEANINGS),status='partial_semantic_dependency'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
