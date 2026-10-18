"""Exercise task-bound ability, completed experiences and prospective acquisition."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.check_falling_depiction import evaluate,ref
from scripts.compose_bodily_acquisition import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure

REPORT='reports/bodily-acquisition-v1.json'
READING='data/bodily-acquisition-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
DOMAIN=('person','other','course','method','bodyact','fallone','falltwo')
SCENES=('now','firstfall','groundone','secondfall','groundtwo','after','pretrial','posttrial','success','failure','late','badend')


def unknown(*args):raise ValueError('Unknown bodily acquisition input')


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    d=deepcopy(catalog().document);d['declarations']=closure(d,roots);d['statements']=[]
    return parse(format_graph(d,'compact')+suffix)


def run(doc,m,memoize=True):return evaluate(doc,m,DOMAIN,SCENES,memoize)


def generic_checks():
    from scripts.check_exercise_capacity import model,DOMAIN as people,SCENES as scenes
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r zperson[] a.r zanchor[] d.r zcases[a i[h[a] e] d d] c.r zpreserved[a i[h[a] e] d d] c.
r zopportunity[a i[h[a] e] d] c.r zpreferred[a i[h[a] e] d d d] c.
r zscope[a i[h[a] e] a d d] c.r zchecked[a i[h[a] e] a d d] c.
r zavailable[a a d] c.r zoutcomes[a a d d] c.r zselected[a a d d] c.r zsuccess[d] c.
d zgoal[person a] e[b scene[k zsuccess[v scene]]].d zother[person a] e[b scene[k zsuccess[v scene]]].
'''
    for goal in ('zgoal','zother'):
        args='k zperson[] k '+goal+'[k zperson[]] r[p '+goal+'] k zanchor[] p zcases p zpreserved p zopportunity p zpreferred p zscope p zchecked p zavailable p zoutcomes p zselected'
        text+=''.join('q[k '+n+'['+args+']].' for n in ('rqvv','rqvw'))
    doc=parse(text)
    def values(variant='baseline',**options):
        m=model(doc,variant,**options)
        for name in ('zcases','zpreserved','zopportunity','zpreferred','zscope','zchecked'):
            original=m[name]
            m[name]=lambda p,g,*args,fn=original:ref(g,'zgoal') and fn(p,*args)
        return m
    rows=[]
    for now,first,second,ordered in product((False,True),repeat=4):
        actual=evaluate(doc,values(now=now,passes=(first,second),prefer_first=ordered),people,scenes)
        assert actual==[True,first and (ordered or second),False,False],(now,first,second,ordered,actual)
        rows.append(actual)
    contrasts={}
    for variant,options,expected in [
        ('training_only',{'passes':(False,False)},[True,False,False,False]),
        ('unclassified_training',{'passes':(False,False)},[False]*4),
        ('empty_profile',{},[False]*4),('missing_assessment',{},[False]*4),
        ('changed_person_state',{},[False]*4),('cyclic_order',{},[False]*4),
    ]:
        result=evaluate(doc,values(variant,**options),people,scenes);assert result==expected,(variant,result);contrasts[variant]=result
    for name in ('zcases','zpreserved','zopportunity','zpreferred','zscope','zchecked'):
        m=values();m[name]=unknown
        try:evaluate(doc,m,people,scenes)
        except ValueError as e:assert 'Unknown bodily' in str(e)
        else:raise AssertionError(name)
    return dict(combinations=len(rows),cases=rows,contrasts=contrasts,unknown_inputs_refused=6,
        equal_truth_does_not_share_task_profiles=True,uncached=True)


def body_model(doc,variant='baseline'):
    m={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    starts={'fallone':'firstfall','falltwo':'secondfall'}
    ends={'fallone':'groundone','falltwo':'groundtwo'}
    def goal(p,g):return p==('other' if variant=='wrong_person' else 'person') and ref(g,'bb' if variant=='wrong_task' else 'zal')
    def before(a,b):return SCENES.index(a)<SCENES.index(b)
    def event(e,a,b):return e in starts and (a,b)==(starts[e],ends[e])
    def changed(e,a,b):return (e,a,b)==('course','now','after') or event(e,a,b)
    def candidates(p,g,a,s):
        return goal(p,g) and ((a,s)==('now','pretrial') or variant!='unassessed_after' and (a,s)==('after','posttrial')) and not(variant=='unassessed_before' and a=='now')
    def available(p,m,s):return (p,m)==('person','method') and s in ('pretrial','posttrial')
    def selected(p,m,s,t):
        passed=(s=='posttrial' and variant!='not_capable_after') or (s=='pretrial' and variant=='already_capable')
        return available(p,m,s) and t==('success' if passed else 'failure')
    m.update(zperson=lambda:'person',zcourse=lambda:'course',zend=lambda:'after',zcontext=lambda:'now',
        zexperience=lambda:'fallone',zstart=lambda:'firstfall',
        hzuq=candidates,hzur=lambda p,g,a,s:goal(p,g) and a in ('now','after'),
        hzus=lambda p,g,s:goal(p,g) and s in ('pretrial','posttrial'),hzut=lambda *args:False,
        hzuu=lambda p,g,m,a,s:goal(p,g) and m=='method' and not(variant=='training_only' and a=='after'),
        hzuv=lambda p,g,m,a,s:goal(p,g) and not(variant=='unclassified_method' and a=='after'),
        ae=available,af=lambda p,m,s,t:available(p,m,s) and t in ('success','failure'),ap=selected,
        zai=lambda p,a,s:(p,a,s)==('person','bodyact','success'),zaj=lambda *args:False,
        fh=lambda course:SequenceValue(() if course!='course' or variant=='empty_experiences' else
            ('fallone','fallone') if variant=='duplicate' else ('falltwo','fallone') if variant=='reversed' else ('fallone','falltwo'),'"individual"'),
        fi=lambda course:'now',f7=lambda e:starts.get(e,'now'),
        fm=lambda count,context:context==('after' if variant=='criterion_at_end' else 'now') and 1<=count<=(1 if variant=='too_many' else 3),
        dd=before,tx=before,dg=lambda e,s:e in starts and s==starts[e],ag=changed,
        la=lambda p,e,a,b:p=='person' and changed(e,a,b),
        fk=lambda e,p,c,a,b:variant!='no_contribution' and e in starts and (p,c,a,b)==
            ('other' if variant=='foreign_contribution' else 'person','other' if variant=='other_course' else 'course','now','after'),
        f5=lambda p,e,g,s:goal(p,g) and e in starts and s==starts[e],
        f6=lambda e,s:variant!='missing_result' and e in ends and s==ends[e],
        hzui=lambda p,s:p=='person' and s in starts.values(),hzuj=lambda p,s:p=='person' and s in ends.values(),
        hzuk=lambda p,e,a,b:p=='person' and event(e,a,b),hzul=lambda *args:variant=='controlled_lowering',
        hzv2=lambda p,g,a,s:variant!='empty_prospects' and goal(p,g) and a=='now' and
            (s==('now' if variant=='not_future' else 'after') or variant=='bad_prospect' and s=='badend'))
    return m


def acquisition_checks():
    doc=fixture(['hzuy','hzuw','hzux'],'''
r zperson[] a.r zcourse[] a.r zend[] d.r zcontext[] d.
q[t[k hzuw[k zperson[]]][k zcontext[]]].q[t[k hzux[k zperson[]]][k zcontext[]]].
q[t[k hzuw[k zperson[]]][k zend[]]].q[t[k hzux[k zperson[]]][k zend[]]].
q[k hzuy[k zperson[] k zcourse[] k zend[] k zcontext[]]].
''');rows={}
    for variant in ('baseline','unassessed_before','unassessed_after','already_capable','not_capable_after',
        'training_only','unclassified_method','wrong_person','wrong_task','empty_experiences','duplicate','reversed',
        'criterion_at_end','too_many','no_contribution','foreign_contribution','other_course','missing_result','controlled_lowering'):
        result=run(doc,body_model(doc,variant));assert result[-1]==(variant=='baseline'),(variant,result);rows[variant]=result
    assert rows['baseline']==[True,False,True,True,True]
    for name in ('hzuq','hzuv','fk','f6','hzul'):
        m=body_model(doc);m[name]=unknown
        try:run(doc,m)
        except ValueError as e:assert 'Unknown bodily' in str(e)
        else:raise AssertionError(name)
    return dict(cases=rows,unknown_inputs_refused=5,native_capacity_fall_and_learning_definitions=True,pure_memoization=True)


def bounded_checks():
    doc=fixture(['hzum','hzv5'],'''
r zperson[] a.r zexperience[] a.r zstart[] d.r zend[] d.
q[t[k hzum[k zperson[] k zexperience[]]][k zstart[]]].
q[k hzv5[k zperson[] k zexperience[] k zstart[] k zend[]]].
''');rows={}
    for variant,finish,expected in [('before','groundone',[True,True]),('equal','after',[True,True]),('late_with_early_nonfall','late',[True,False])]:
        m=body_model(doc);m.update(f6=lambda e,s:e=='fallone' and s in ('groundone',finish),
            ag=lambda e,a,b:(e,a,b)==('fallone','firstfall',finish),
            la=lambda p,e,a,b:(p,e,a,b)==('person','fallone','firstfall',finish),
            hzuj=lambda p,s:(p,s)==('person',finish),
            hzuk=lambda p,e,a,b:(p,e,a,b)==('person','fallone','firstfall',finish))
        result=run(doc,m,False);assert result==expected,(variant,result);rows[variant]=result
    return dict(cases=rows,same_completed_result_required=True,uncached=True)


def prospect_checks():
    doc=fixture(['hzv3'],'r zperson[] a.r zcontext[] d.q[t[k hzv3[k zperson[]]][k zcontext[]]].');rows={}
    for variant in ('baseline','empty_prospects','not_future','bad_prospect','wrong_task','wrong_person','criterion_at_end','no_contribution'):
        result=run(doc,body_model(doc,variant));assert result==[variant=='baseline'],(variant,result);rows[variant]=result
    m=body_model(doc);m['hzv2']=unknown
    try:run(doc,m)
    except ValueError as e:assert 'Unknown bodily' in str(e)
    else:raise AssertionError('Unknown prospects guessed')
    return dict(cases=rows,unknown_prospects_refused=True,original_count_context_preserved=True,pure_memoization=True)


def attribution_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    for variant in ('baseline','other_author','other_clause','other_context','reversed','wrong_target','wrong_depiction'):
        m={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        def attribution(n,a,t,d,s):
            first,second=('hzv3','fr') if variant=='reversed' else ('hzv3' if variant=='wrong_target' else 'fr','fr' if variant=='wrong_depiction' else 'hzv3')
            return (n,a,s)==('other' if variant=='other_clause' else 'clause','other' if variant=='other_author' else 'author',
                'other' if variant=='other_context' else 'context') and ref(t,first) and ref(d,second)
        m.update(fv=lambda:'clause',wa=lambda:'author',wh=lambda:'context',qa=attribution)
        result=evaluate(doc,m,('author','clause','other'),('context',));assert result==[variant=='baseline'],(variant,result);rows[variant]=result
    m['qa']=unknown
    try:evaluate(doc,m,('author','clause','other'),('context',))
    except ValueError as e:assert 'Unknown bodily' in str(e)
    else:raise AssertionError('Unknown attribution guessed')
    return dict(cases=rows,all_world_facts_unknown=True,unknown_attribution_refused=True,uncached=True)


def structure():
    old=parent();new=catalog();assert new.document['declarations'][:-16]==old.document['declarations']
    assert all(new.entries[n]==entry for n,entry in old.entries.items())
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==40
    idx=json.loads((ROOT/'data/semantic-review-index-v33.json').read_text(encoding='utf-8'))
    for path in idx['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[s['index'] for s in review['selection']['statements']]
        assert selection_binding(old,indices)==review['selection']==selection_binding(new,indices)
    names={d['name'] for d in closure(new.document,['hzv3'])}
    assert not names&{'hzsc','hzsd','hzse','hzsf','hzsg','hzsh','up','fo','fr','fl'}
    for path in (FULL,CORE,LIBRARY):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    return dict(new_definitions=9,new_primitive_relations=7,appended_statement_indices=[39],other_statements_preserved=39,
        nine_review_bindings_preserved=True,no_mental_profiles_in_body_content=True,generic_library_has_no_source_primitives=True,roundtrips=True)


def source_record():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0009')
    old=json.loads((ROOT/'reports/experience-acquisition-v1.json').read_text(encoding='utf-8'))['alignment'];a,b=old['start'],old['end']
    return dict(status='task_indexed_bodily_learning_depiction',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[a,b],text=unit['text'][a:b]),
        references=['https://korpora.org/Kant/aa08/036.html'],
        decision='少数回の転倒を経て身体的活動の能力を得る見込みを、自立的な活動の取得見込みへ本人を保持して対応させる。',
        reasoning='Fallenだけでなくgehen lernenとwürdenの接続を構成する。現在の身体能力の評価、経験による取得、仮定的な将来の見込みを別々に定義し、実際の学習の発生は比喩の帰属から要求しない。',
        limits=LIMITS,whole_unit_semantically_verified=False,binding=selection_binding(catalog(),[39]),
        source_sha256={INVENTORY:digest((ROOT/INVENTORY).read_bytes())})


def build_report():
    for p,text in build().items():assert (ROOT/p).read_text(encoding='utf-8')==text,p
    results={}
    for name,fn in [('generic',generic_checks),('acquisition',acquisition_checks),('bounded',bounded_checks),('prospect',prospect_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    reading=source_record();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==reading;s=reading['source']
    prior_path='reports/falling-depiction-v1.json';prior=json.loads((ROOT/prior_path).read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    alignment=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],start=s['range'][0],end=s['range'][1],source=s['text'],
        definitions=list(MEANINGS),status='partial_bodily_acquisition_depiction',full_semantic_equivalence=False)
    paths=set(build())|set(catalog().source_sha256)|set(prior['source_sha256'])|set(reading['source_sha256'])|{READING,prior_path,
        'reports/experience-acquisition-v1.json','scripts/compose_bodily_acquisition.py','scripts/check_bodily_acquisition.py',
        'scripts/check_exercise_capacity.py','scripts/check_standing_ability.py','tests/test_bodily_acquisition.py','docs/bodily-acquisition-v1.md'}
    return dict(status='task_bound_bodily_acquisition_and_prospective_depiction',document=FULL,**results,alignment=alignment,
        verified_full_units={'kant-1784':0,'einstein-1905':0},new_covered_characters=0,source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(source_record()));report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Task-bound ability, completed learning experiences and prospective depiction checked',flush=True)


if __name__=='__main__':main()
