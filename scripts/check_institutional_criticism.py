"""Check native remark candidates, separate permissions and all-citizen persistence."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_institutional_criticism import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure,NAMES,CHOICES
from scripts.check_military_remarks import DOMAIN as NOTES_DOMAIN,candidate_model
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

REPORT='reports/institutional-criticism-v1.json'
DOC='docs/institutional-criticism-v1.md'
READING='data/institutional-criticism-reading-v1.json'
PRIORS=('reports/legislative-touchstone-v1.json','reports/military-remarks-v1.json','reports/provisional-order-v1.json')
SCENES=('reference','candidate','first','last','outside')
DOMAIN=tuple(dict.fromkeys((*NOTES_DOMAIN,'community','regime')))
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r z'+n+'[] d.' for n in SCENES)
VALUES={n:n for n in NAMES};VALUES['regime']='institution'
ARGS=' '.join('k z'+VALUES[n]+'[]' for n in NAMES)+' k zreference[] k zcandidate[] k zfirst[]'
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+EXTRA+query)
def run(d,v,domain=DOMAIN):return evaluate(d,v,domain,SCENES,True)
def base(doc,variant='baseline'):
    v=candidate_model(doc,variant);v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['h26cs']=lambda r,c,ref:variant!='not_religious_order' and(r,c,ref)==('institution','community','reference')
    v['h26ct']=lambda f,r,ref:(f,r,ref)==('field','other' if variant=='other_regime_field' else 'institution','reference')
    v['h26cu']=lambda p,c,ref,h,t:variant!='not_citizen' and(p,c,ref,h,t)==('person','community','reference','candidate','first')
    v['h26cv']=lambda r,c,ref,h,t:(r,c,ref,h,t)==('institution','community','reference','candidate','first')
    v['h26cw']=lambda r,c,ref:'office' if(r,c,ref)==('institution','community','reference') else 'other'
    return v
def unknowns(d,names):
    for n in names:
        v=base(d);v[n]=unknown
        try:run(d,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return list(names)
@lru_cache(None)
def candidate_checks():
    d=fixture(('r5e5',),'q[k r5e5['+ARGS+']].');rows={}
    for variant in ('baseline','empty','one_unrelated_remark','other_field','other_scholar','other_audience','other_created_notes','other_routed_notes','not_submitted_for_inspection','not_religious_order','other_regime_field','not_citizen'):
        v=base(d,variant)
        for n in ('hztl','h243u','h243v','cg','h244b','h244c','sc','hzwr','h7k','h7l'):v[n]=unknown
        actual=run(d,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    return dict(native_same_regime_nonempty_written_remarks=rows,execution_permission_defect_truth_and_reader_judgment_goal_not_required=True,
        unknown_rejected=unknowns(d,('h26cs','h26ct','h26cu','h243x','h243y','h243z','h242g')))
def norm_model(doc,allows=(True,True,True),opposes=(False,False,False),variant='baseline'):
    v=base(doc);targets=('r33g','r33h','r33i')
    bindings=(('person','making','notes'),('person','presenting','notes','audience'),('person','making','presenting','notes','audience'))
    expected=[('office','person','scholar',(n,0),bs,'first') for n,bs in zip(targets,bindings)]
    def match(s,p,r,c,b,sign,t):
        actual=normalized((s,p,r,c,b,t))
        for i,row in enumerate(expected):
            row=list(row)
            for label,pos in (('source',0),('person',1),('role',2),('point',5)):
                if variant=='other_'+label:row[pos]='other'
            if variant=='other_target':row[3]=('r33g' if i!=0 else 'r33i',0)
            if variant=='other_bindings':row[4]=tuple(reversed(row[4]))
            if actual==tuple(row):return i
        return None
    def norm(bits,sign,*a):
        i=match(*a);return i is not None and bits[i] and a[5]==sign
    v['h7l']=lambda *a:norm(allows,True,*a);v['h7k']=lambda *a:norm(opposes,False,*a)
    return v
@lru_cache(None)
def permission_checks():
    d=fixture(('r5e6',),'q[k r5e6['+ARGS+']].');rows=[]
    for bits in product((False,True),repeat=6):
        v=norm_model(d,bits[:3],bits[3:]);actual=run(d,v);assert actual==[all(bits[:3]) and not any(bits[3:])]
        rows.append(dict(bits=list(bits),value=actual[0]))
    contrasts={}
    for variant in ('other_source','other_person','other_role','other_point','other_target','other_bindings'):
        actual=run(d,norm_model(d,variant=variant));assert actual==[False];contrasts[variant]=actual[0]
    v=norm_model(d)
    for n in ('cg','sc','hzwr','h244b','h244c'):v[n]=unknown
    assert run(d,v)==[True]
    rejected=[]
    for n in ('h7k','h7l'):
        v=norm_model(d);v[n]=unknown
        try:run(d,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
        rejected.append(n)
    return dict(all_three_permissions_and_separate_conflicts=rows,same_target_norms=contrasts,content_not_executed=True,unknown_rejected=rejected)
@lru_cache(None)
def individual_scope_checks():
    d=fixture(('r5e7',),'q[k r5e7[k zperson[] k zcommunity[] k zregime[] k zreference[] k zcandidate[] k zfirst[]]].',('r5e5','r5e6'))
    rows=[];prefix=('alpha','alpha','alpha');suffix=('reference','candidate','first');choices=(('alpha',)*6,('beta',)*6)
    for c1,c2,p1,p2 in product((False,True),repeat=4):
        v=base(d);v.update(zperson=lambda:'alpha',zcommunity=lambda:'alpha',zregime=lambda:'alpha')
        v['r5e5']=lambda *a:(c1 and a==(*prefix,*choices[0],*suffix)) or(c2 and a==(*prefix,*choices[1],*suffix))
        v['r5e6']=lambda *a:(p1 and a==(*prefix,*choices[0],*suffix)) or(p2 and a==(*prefix,*choices[1],*suffix))
        actual=run(d,v,('alpha','beta'));expected=(c1 or c2) and(not c1 or p1) and(not c2 or p2)
        assert actual==[expected];rows.append(dict(bits=[c1,c2,p1,p2],value=actual[0]))
    matrices=[]
    for i in range(6):
        selected=tuple('beta' if k==i else 'alpha' for k in range(6));v=base(d)
        v.update(zperson=lambda:'alpha',zcommunity=lambda:'alpha',zregime=lambda:'alpha')
        v['r5e5']=lambda *a:a==(*prefix,*selected,*suffix)
        for j in range(6):
            permitted=tuple('beta' if k==j else 'alpha' for k in range(6));v['r5e6']=lambda *a:a==(*prefix,*permitted,*suffix)
            actual=run(d,v,('alpha','beta'));assert actual==[i==j];matrices.append(actual[0])
    return dict(nonempty_all_candidates=rows,six_choice_positions=matrices,boundaries=['r5e5','r5e6'])
@lru_cache(None)
def citizenship_checks():
    q=''.join('q[t[k r5fc[k zcommunity[] k zregime[] k zreference[] k zcandidate[]]][k z'+t+'[]]].' for t in ('first','last'))
    d=fixture(('r5fc',),q,('r5e7',));rows={}
    for variant in ('baseline','second_citizen_denied','new_member_denied','departed_member','no_citizens','nonhuman_member','different_community','different_regime','different_reference','different_candidate','missing_order','split_points'):
        v=base(d);v.update(zcommunity=lambda:'alpha',zregime=lambda:'beta')
        v['h26cs']=lambda r,c,ref:(r,c,ref)==('beta','alpha','reference')
        v['aa']=lambda p:not(variant=='nonhuman_member' and p=='beta')
        def member(p,c,ref,h,t):
            return variant!='no_citizens' and(c,ref,h)==('alpha','reference','candidate') and(
                (t=='first' and p=='alpha') or(t=='last' and(p=='beta' or(p=='alpha' and variant!='departed_member'))))
        v['h26cu']=member
        def freedom(p,c,r,ref,h,t):
            expected=['alpha','beta','reference','candidate']
            for i,k in enumerate(('community','regime','reference','candidate')):
                if variant=='different_'+k:expected[i]='beta' if i==0 else 'alpha' if i==1 else 'other'
            return (c,r,ref,h)==tuple(expected) and t in ('first','last') and not(
                (variant in ('second_citizen_denied','new_member_denied') and p=='beta') or
                (variant=='departed_member' and t=='last' and p=='alpha') or(variant=='split_points' and t=='first'))
        v['r5e7']=freedom
        v['h26cv']=lambda r,c,ref,h,t:variant!='missing_order' and(r,c,ref,h)==('beta','alpha','reference','candidate') and t in ('first','last') and not(variant=='split_points' and t=='last')
        expected=[True,True]
        if variant in ('second_citizen_denied','new_member_denied','nonhuman_member'):expected=[True,False]
        if variant.startswith('different_') or variant in ('missing_order','split_points'):expected=[False,False]
        actual=run(d,v,('alpha','beta'));assert actual==expected,(variant,actual);rows[variant]=actual
    return dict(all_citizens_at_each_point_and_same_order=rows,boundary='r5e7 only; native candidate and permission checked separately',
        no_citizen_existence_from_vacuous_universal=True)
def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(x for x in read(inv)['units'] if x['id']=='kant-1784:u0013')
    return dict(status='continuing_order_and_public_criticism_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1437,2309],text=u['text'][1437:2309]),
        adopted_readings=LIMITS,reuse=['r33a/r326 for notes on deficiencies','r2zi/r3z for scholarly written public use',
          'r33g/r33h/r33i for distinct quoted acts','rdu for each positive permission without conflict'],
        intentionally_not_imported=['military subject h244a','reader-judgment purpose hztl/r327'],
        remaining=['law and introduction of the same religious arrangement','determinate short period and expectation',
          'clerical focus and general self-imposition possibility','public insight, common proposal, protection and non-interference','whole-sentence attribution and review'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)
@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record() and not new.document['statements'] and len(old.document['statements'])==102
    assert not {'h244a','hztl','r327'}&set(new.entries)
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_manuscript_statements=102)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in [('candidate',candidate_checks),('permission',permission_checks),('individual_scope',individual_scope_checks),('citizenship',citizenship_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,reading_record()['source_inventory'],
        'scripts/compose_institutional_criticism.py','scripts/check_institutional_criticism.py','tests/test_institutional_criticism.py',
        'scripts/check_military_remarks.py','scripts/check_covenant_nullity.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='continuing_order_and_public_criticism_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
