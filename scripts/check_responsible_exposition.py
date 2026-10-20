"""Check same-content exposition, undertaking and possible admissible acts."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content,SequenceValue
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_responsible_exposition import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,TARGETS,GOAL,parents,build,closure
from scripts.check_representative_teaching import model as teaching_model,EXTRA_LOCAL,PROVIDERS,SMALL,SCENES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_scoped_counts import arithmetic
from scripts.fetch_pastoral_role_evidence import entry

DOC='docs/responsible-exposition-v1.md'
REPORT='reports/responsible-exposition-v1.json'
EVIDENCE='data/responsible-exposition-evidence-v1.json'
PRIORS=('reports/doctrinal-statutes-v1.json','reports/representative-teaching-v1.json')
ADDED=('bundle','rulea','ruleb','undertaking','otherundertaking')
DOMAIN=(*SMALL,*ADDED)
EXTRA=EXTRA_LOCAL+''.join('r z'+n+'[] a.' for n in ADDED)+'r zactual[] d.r zrecord[i[h[a] f]] c.'
ARGS=' '.join('k z'+n+'[]' for n in TARGETS)+' k zref[]'
SEQ='l[a]['+' '.join('k z'+n+'[]' for n in TARGETS)+']'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(target='r42s'):
    doc=deepcopy(catalog().document);doc['statements']=[]
    prefix=parse('p:'+EXTRA+PROVIDERS)
    providers={d['name']:d for d in prefix['declarations'] if d['name'] in ('h246e','h246j')}
    doc['declarations']=[d for d in prefix['declarations'] if d['name'] not in providers]+[providers.get(d['name'],d) for d in doc['declarations']]
    query='q[k zrecord[k r42n[k zbundle[] k zref[]]]].'
    if target=='r42o':query+='q[t[k r42o['+ARGS+' k zoccasion[] k zactivity[]]][k zpoint[]]].'
    else:query+='q[k r42s['+ARGS+' k zactual[]]].'
    return parse(format_graph(doc,'compact')+query)


def model(doc,variant='baseline',bits=(True,True,True,True)):
    feasible,undertakes,occurs,allowed=bits
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update(teaching_model(variant));v.update(arithmetic())
    v.update({'z'+n:(lambda n=n:n) for n in ADDED});v['zactual']=lambda:'other'
    observed=dict(message=None,undertakings=[],candidates=[],admissible=[])
    def record(code):observed['message']=code;return code.rank==0
    v['zrecord']=record
    def matches(actual,expected,category,fields):
        expected=list(expected)
        for i,n in enumerate(fields):
            if variant==category+'_'+n:expected[i]='other'
        return tuple(actual)==tuple(expected)
    v['h252g']=lambda bundle,ref:SequenceValue(('rulea','ruleb') if (bundle,ref)==('bundle','reference') else (), '"individual"')
    v['zchoosebelief']=lambda form,ref,first,second:first if ref=='reference' and form in ('creed','rulea') else second
    v['h246g']=lambda church,form,code,ref:(church,ref)==('church','reference') and symbol(code)==(
        'zbelief' if form in ('creed','rulea') else 'zotherbelief' if form=='ruleb' else 'none')
    member=v['h6t'];v['h6t']=lambda group,item,ref:((group=='bundle' and item in ('rulea','ruleb') and ref=='reference') or member(group,item,ref))
    v['h252e']=lambda standard,rule,ref:(standard,ref)==('standard','reference') and rule in ('rulea','ruleb') and variant!='not_prescribed'
    def same(code):return code.rank==0 and code.syntax==observed['message'].syntax
    v['h246l']=lambda person,activity,subject,code,point:variant!='not_exposition' and (person,activity,subject,point)==('person','activity','subject','outcome') and same(code)
    recipients=('member','overlap') if variant=='congregation_task' else ('learner','overlap')
    v['f2']=lambda activity,recipient,subject,code,point:(activity,subject,point)==('activity','subject','outcome') and recipient in recipients and same(code) and variant!='no_recipient_reached' and not (variant=='one_recipient_only' and recipient=='overlap')
    v['zjudge']=lambda subject,code:Content(SCENES,tuple(subject=='subject' and same(code) and not (variant=='criterion_failed' and point=='outcome') for point in SCENES))
    v['h247o']=lambda activity,principal,subject,code,point:matches((activity,principal,subject,point),('activity','church','subject','outcome'),
        'voice',('activity','principal','subject','point')) and same(code)
    occurrence=v['dg']
    v['dg']=lambda act,point:(act=='undertaking' and point=='outcome' and occurs) or occurrence(act,point)
    v['df']=lambda person,act,point:matches((person,act,point),('person','undertaking','outcome'),'actor',('person','act','point'))
    expected=tuple(TARGETS)
    def goal_matches(goal,bindings):return goal.rank==1 and symbol(goal)=='r42p' and bindings.items==expected
    def undertaken(person,act,goal,bindings,ref,point):
        observed['undertakings'].append((person,act,symbol(goal),bindings.items,ref,point))
        return undertakes and goal_matches(goal,bindings) and matches((person,act,ref,point),('person','undertaking','reference','outcome'),
            'undertaking',('person','act','reference','point'))
    def candidate(person,goal,bindings,ref,actual,point):
        observed['candidates'].append((person,symbol(goal),bindings.items,ref,actual,point))
        return feasible and goal_matches(goal,bindings) and matches((person,ref,actual,point),('person','reference','other','outcome'),
            'candidate',('person','reference','actual','point'))
    def admissible(person,act,ref,point):
        observed['admissible'].append((person,act,ref,point))
        return allowed and matches((person,act,ref,point),('person','undertaking','reference','outcome'),
            'admissible',('person','act','reference','point'))
    v.update(h252h=undertaken,h252i=candidate,h252j=admissible)
    return v,observed


def run(doc,pair):
    values,_=pair;result=evaluate(doc,values,DOMAIN,SCENES,True)
    assert result[0] is True
    return result[1:]


@lru_cache(None)
def exposition_checks():
    doc=fixture('r42o');rows={}
    for variant in ('baseline','congregation_task','no_event','not_exposition','no_recipient_reached','one_recipient_only',
        'criterion_failed','not_prescribed','other_task_activity','not_entrusted','no_current_service','voice_principal','voice_subject'):
        pair=model(doc,variant);assert pair[0]['zbelief'] is unknown and pair[0]['zotherbelief'] is unknown
        result=run(doc,pair);assert result==[variant in ('baseline','congregation_task')],(variant,result)
        rows[variant]=result
    return dict(contrasts=rows,native_r42j_r374_r357_r356=True,
        same_constructed_message_in_explanation_representation_and_criteria=True,
        teaching_without_executing_doctrine_truth_or_personal_conviction=True)


@lru_cache(None)
def possibility_checks():
    doc=fixture();rows=[]
    for bits in product((False,True),repeat=4):
        pair=model(doc,bits=bits)
        for n in ('h246l','f2','h247o','zjudge'):pair[0][n]=unknown
        result=run(doc,pair);assert result==[all(bits)],(bits,result)
        rows.append(dict(feasible=bits[0],undertaken=bits[1],occurs=bits[2],admissible=bits[3],result=result))
    # Endorsement, office appointment and goal execution are all left unknown.
    pair=model(doc);run(doc,pair)
    assert pair[1]['undertakings'] and pair[1]['candidates'] and pair[1]['admissible']
    assert all(goal=='r42p' and bindings==TARGETS and ref=='reference'
        for person,act,goal,bindings,ref,point in pair[1]['undertakings'])
    return dict(independent_conditions=rows,empty_practical_scope_false=True,
        exact_rank_one_goal_same_person_and_ten_bindings=True,
        exposition_goal_not_executed_to_establish_undertaking=True,
        possible_undertaking_not_current_undertaking_or_appointment=True)


@lru_cache(None)
def reference_checks():
    doc=fixture();rows={}
    for category,fields in [('actor',('person','act','point')),('undertaking',('person','act','reference','point')),
        ('candidate',('person','reference','point')),('admissible',('person','act','reference','point'))]:
        for field in fields:
            variant=category+'_'+field;result=run(doc,model(doc,variant))
            assert result==[False],(variant,result);rows[variant]=result
    # Change the actual evaluation independently: "other" is normally actual.
    pair=model(doc);pair[0]['zactual']=lambda:'reference';assert run(doc,pair)==[False]
    for name in ('h252g','h252h','h252i','h252j','df','dg'):
        pair=model(doc);pair[0][name]=unknown
        try:run(doc,pair)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,same_actual_reference_candidate_act_and_actor=True,unknown_inputs_refused=True)


@lru_cache(None)
def generic_checks():
    doc=deepcopy(catalog().document);doc.update(declarations=closure(doc,['r42q','r42r']),statements=[])
    extra='r zperson[] a.r zact[] a.r zother[] a.r zref[] d.r zpoint[] d.r zgoal[j[a] d] e.r zalias[j[a] d] e.'
    def make(seq,code='zgoal'):
        return parse(format_graph(doc,'compact')+extra+'q[k r42q[k zperson[] k zact[] r b[p '+code+'] '+seq+' k zref[] k zpoint[]]].')
    values=dict(zperson=lambda:'person',zact=lambda:'act',zother=lambda:'other',zref=lambda:'reference',zpoint=lambda:'outcome',
        zgoal=unknown,zalias=unknown,dg=lambda a,p:True,df=lambda p,a,t:True,
        h252h=lambda p,a,g,b,r,t:g.rank==1 and symbol(g)=='zgoal',h252i=unknown,h252j=unknown)
    for seq,expected in [('l[a][]',False),('l[a][k zother[]]',False),('l[a][k zperson[] k zother[]]',True)]:
        assert evaluate(make(seq),values,('person','act','other'),SCENES,True)==[expected]
    assert evaluate(make('l[a][k zperson[]]','zalias'),values,('person','act','other'),SCENES,True)==[False]
    return dict(first_binding_is_same_actor=True,closed_goal_not_executed=True,same_truth_alias_not_substituted=True)


@lru_cache(None)
def binding_checks():
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name']=='r42o':d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,['r42p']),statements=[])
    prefix='r zl[] a.r zr[] a.r zref[] d.r zpoint[] d.'
    pattern=('left','right')*5;seq='l[a]['+' '.join('k '+('zl' if n=='left' else 'zr')+'[]' for n in pattern)+']'
    seen=[]
    def body(*args):
        seen.append(args)
        return Content(SCENES,tuple(tuple(args[:10])==pattern and args[10:] == ('reference','left','right') and p=='outcome' for p in SCENES))
    values=dict(zl=lambda:'left',zr=lambda:'right',zref=lambda:'reference',zpoint=lambda:'outcome',r42o=body)
    def runseq(s):
        case=parse(format_graph(doc,'compact')+prefix+'q[t[k r42p['+s+' k zref[]]][k zpoint[]]].')
        return evaluate(case,values,('left','right'),SCENES,True)
    assert runseq(seq)==[True]
    assert runseq('l[a][]')==[False]
    assert runseq(seq.replace('k zl[]','k zr[]',1))==[False]
    assert runseq(seq[:-1]+' k zl[]]')==[False]
    assert (*pattern,'reference','left','right') in seen
    return dict(ten_bindings_exact_length_order=True,occasion_and_activity_existential=True,
        diagnostic_boundary='r42o only; native r42o checked separately',individual_domain=['left','right'])


@lru_cache(None)
def structure_checks():
    old={n:e for c in parents() for n,e in c.entries.items()};new=catalog()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        t=format_graph(new.document,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==new.document
    evidence=read(EVIDENCE);raw=(ROOT/evidence['path']).read_bytes()
    assert digest(raw)==evidence['sha256'] and entry(raw.decode(evidence['encoding']))==evidence['entry_text']
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        no_source_sentence_added=True,lexical_evidence_pinned=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    result={n:f() for n,f in [('exposition',exposition_checks),('possibility',possibility_checks),('references',reference_checks),
        ('generic',generic_checks),('binding',binding_checks),('structure',structure_checks)]}
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,EVIDENCE,read(EVIDENCE)['path'],
        'scripts/compose_responsible_exposition.py','scripts/check_responsible_exposition.py','tests/test_responsible_exposition.py',
        'scripts/check_representative_teaching.py','scripts/check_teaching_policy.py','scripts/check_confessional_teaching.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py',
        'scripts/fetch_pastoral_role_evidence.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/compose_confessional_teaching.py','scripts/compose_protected_remarks.py'}
    return dict(status='same_doctrinal_exposition_and_admissible_responsible_undertaking',document=LIBRARY,**result,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
