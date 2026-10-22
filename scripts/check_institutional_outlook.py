"""Check strict improvement, typed attitude targets and same-act purpose binding."""
from copy import deepcopy
from functools import lru_cache
from itertools import product,permutations
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_institutional_outlook import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized
from scripts.check_law_enactment import fixture as law_fixture,model as law_model,DOMAIN as LAW_DOMAIN

REPORT='reports/institutional-outlook-v1.json'
DOC='docs/institutional-outlook-v1.md'
READING='data/institutional-outlook-reading-v1.json'
PRIORS=('reports/temporary-institution-v1.json','reports/institutional-criticism-v1.json','reports/law-enactment-v1.json')
DOMAIN=('actor','activity','community','regime','better','other','people','law')
POINTS=('before','anchor','later','end')
SCENES=('reference','candidate',*POINTS,'outside')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r z'+n+'[] d.' for n in SCENES)
EXTRA+='r zstop[d] c.d zmilestone[] e[b point[k zstop[v point]]].'
EXTRA+='d zothergoal[bindings j[a] reference d candidate d anchor d] e[b point[u[e[v point][v point]]]].'
FRAME='k zreference[] k zcandidate[] k zanchor[]'
STANCE='k zactor[] k zactivity[] k zcommunity[] k zregime[] '+FRAME
ARGS='k zactor[] k zactor[] k zcommunity[] k zother[] k zregime[] k zactivity[] '+FRAME+' k zend[]'
EXPECTED=('actor','actor','community','other','regime','activity','reference','candidate','anchor','end')

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

def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)
def model(doc,bits=(True,True,True,False),variant='baseline'):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in (*DOMAIN,*SCENES)})
    v['zstop']=lambda p:p=='end'
    v['h257z']=lambda r,h,p:(r,h)==('reference','candidate') and p in POINTS and not(variant=='missing_anchor' and p=='anchor')
    def before(a,b,h):
        if h!='candidate' or a not in POINTS or b not in POINTS:return False
        if variant=='cycle' and(a,b)==('end','anchor'):return True
        return POINTS.index(a)<POINTS.index(b)
    v['ic']=before
    v['h26cs']=lambda g,c,r:g in ('regime','better') and(c,r)==('community','reference') and not(variant=='nonreligious' and g=='better')
    comparisons=dict(zip((('law','law'),('better','better'),('better','law'),('law','better')),bits))
    v['h26ca']=lambda l,c,r:l in ('law','better') and(c,r)==('community','reference') and not(variant=='not_public_law' and l=='better')
    v['r5ej']=lambda p,c,l,r,t:(p,c,l,r)==('people','community','other' if variant=='other_law' else 'better','reference') and t in POINTS
    v['h26c2']=lambda l,r,c,ref:(c,ref)==('community','reference') and comparisons.get((l,r),False)
    v['h26cv']=lambda g,c,r,h,p:(g,c,r,h)==('other' if variant=='other_order' else 'better','community','reference','candidate') and p in POINTS
    v['h26cz']=lambda a,g,c,r,h,p:(a,g,c,r,h)==('activity','regime','community','reference','candidate') and p in POINTS
    v['dg']=lambda a,p:a=='activity' and p in POINTS
    def stance(target,bindings,*args):
        return normalized(args)==('actor','activity',(target,1 if target=='r5fk' else 0),bindings,'reference','candidate','anchor')
    v['h26c3']=lambda *a:stance('r5fl',('activity','community','regime'),*a)
    v['h26c4']=lambda *a:stance('r5fk',('people','community','law'),*a)
    v['r5fh']=lambda *a:a==EXPECTED
    v['r5fi']=lambda *a:a[:-1]==EXPECTED and a[-1].values==tuple(p=='end' for p in SCENES)
    return v

def unknowns(doc,names):
    for n in names:
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return list(names)

@lru_cache(None)
def improvement_checks():
    q='q[k r5fj[k zpeople[] k zcommunity[] k zlaw[] k zreference[] k zcandidate[] k zlater[]]].'
    doc=fixture(('r5fj',),q,('r5ej',));rows=[]
    for bits in product((False,True),repeat=4):
        actual=run(doc,model(doc,bits));assert actual==[all(bits[:3]) and not bits[3]]
        rows.append(dict(bits=list(bits),value=actual[0]))
    contrasts={}
    for variant in ('not_public_law','other_law','same_law_only','absent','wrong_people','wrong_community','wrong_reference'):
        v=model(doc,variant=variant)
        if variant=='same_law_only':v['h26ca']=lambda g,c,r:g=='law' and(c,r)==('community','reference')
        if variant=='absent':v['r5ej']=lambda *a:False
        if variant in ('wrong_people','wrong_community','wrong_reference'):
            n='z'+variant[6:];v[n]=lambda:'other' if variant in ('wrong_people','wrong_community') else 'outside'
        actual=run(doc,v);assert actual==[False];contrasts[variant]=actual[0]
    return dict(strict_comparison=rows,same_public_law_and_frame=contrasts,boundary='r5ej; complete clause evaluation checked natively below',
        unknown_rejected=unknowns(doc,('h26ca','h26c2','r5ej')))

def target_query(root,names,point):
    seq='l[a]['+' '.join('k z'+n+'[]' for n in names)+']'
    return 'q[t[k '+root+'['+seq+' '+FRAME+']][k z'+point+'[]]].'

@lru_cache(None)
def law_content_checks():
    from scripts.check_law_enactment import SCENES as law_scenes
    doc=deepcopy(catalog().document);doc.update(declarations=closure(doc,['r5fj']),statements=[])
    supplied=law_fixture(('r5ej',),'');names={d['name'] for d in supplied['declarations']}
    doc['declarations']=supplied['declarations']+[d for d in doc['declarations'] if d['name'] not in names]
    doc=parse(format_graph(doc,'compact')+'q[k r5fj[k zpeople[] k zcommunity[] k zother[] k zreference[] k zcandidate[] k zpoint[]]].')
    def values(bits=(True,True,True),variant='baseline',missing=None):
        v=law_model(doc,variant,states=bits)
        v['h26ca']=lambda l,c,r:l in ('law','other') and(c,r)==('community','reference')
        v['h26c2']=lambda l,r,c,ref:(c,ref)==('community','reference') and(l,r) in (('other','other'),('law','law'),('law','other'))
        if missing:v[missing]=unknown
        return evaluate(doc,v,LAW_DOMAIN,law_scenes,True)
    rows=[]
    for bits in product((False,True),repeat=3):
        actual=values(bits);assert actual==[all(bits)];rows.append(dict(bits=list(bits),value=actual[0]))
    for variant in ('empty_people','missing_person','empty_law','split_times'):assert values(variant=variant)==[False]
    for missing in ('zchoose','h7k','h7l','zpower'):
        try:values(missing=missing)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(missing)
    return dict(complete_people_and_all_three_operative_clauses=rows,no_definition_boundaries=True,
        empty_people_missing_member_empty_law_split_times_rejected=True)

@lru_cache(None)
def target_checks():
    rows={}
    for root,names in (('r5fk',('people','community','law')),('r5fl',('activity','community','regime'))):
        def values(names,variant='baseline'):
            query=''.join(target_query(root,names,p) for p in ('before','anchor','later','end','outside'))
            doc=fixture((root,),query,('r5ej',));v=model(doc,variant=variant)
            if root=='r5fl':v['h26cv']=lambda g,c,r,h,p:(g,c,r,h)==('regime','community','reference','candidate') and p in POINTS
            return run(doc,v)
        expected=[False,root=='r5fl',True,True,False]
        assert values(names)==expected;rows[root]=dict(points=expected)
        tested=[]
        for perm in permutations(names):
            actual=values(perm);assert actual==(expected if perm==names else [False]*5)
            tested.append(dict(bindings=list(perm),values=actual))
        rows[root]['permutations']=tested
        for bad in (names[:-1],(*names,'other')):assert values(bad)==[False]*5
        for variant in ('missing_anchor','cycle'):assert values(names,variant)==[False]*5
        rows[root]['wrong_length_and_invalid_history_rejected']=True
    doc=fixture(('r5fl',),target_query('r5fl',('activity','community','regime'),'later'))
    contrasts={}
    for missing in ('dg','h26cz','h26cv'):
        v=model(doc);v['h26cv']=lambda *a:a==('regime','community','reference','candidate','later')
        v[missing]=lambda *a:False;actual=run(doc,v);assert actual==[False];contrasts[missing]=actual[0]
    rows['introduction_is_more_than_existence']=contrasts
    return rows

@lru_cache(None)
def attitude_checks():
    q='q[k r5fm['+STANCE+']].q[k r5fn[k zactor[] k zactivity[] k zpeople[] k zcommunity[] k zlaw[] '+FRAME+']].'
    doc=fixture(('r5fm','r5fn'),q);rows=[]
    for purpose,expectation in product((False,True),repeat=2):
        v=model(doc);aim,expect=v['h26c3'],v['h26c4']
        v['h26c3']=lambda *a:purpose and aim(*a);v['h26c4']=lambda *a:expectation and expect(*a)
        for n in ('h26cs','h26ca','h26cb','h26cc','h26c2','h26cv','h26cz','dg','h257z','ic'):v[n]=unknown
        actual=run(doc,v);assert actual==[purpose,expectation];rows.append(actual)
    contrasts={}
    for n in ('h26c3','h26c4'):
        for pos,label in enumerate(('actor','activity','target','bindings','reference','candidate','anchor')):
            if pos==2:continue # Real wrong-target calls are evaluated below.
            v=model(doc);old=v[n]
            def changed(*a,old=old,pos=pos):
                args=list(a)
                if pos==3:
                    from noema.constructed_semantics import SequenceValue
                    args[pos]=SequenceValue(tuple(reversed(args[pos].items)),'"individual"')
                else:args[pos]='other' if pos<2 else 'outside'
                return old(*args)
            v[n]=changed;actual=run(doc,v);expected=[n!='h26c3',n!='h26c4']
            assert actual==expected;contrasts[n+'_'+label]=actual
    # Evaluate wrong-target calls explicitly; a truth stub would not check quotation identity.
    for relation,root,bs,rank in (('h26c3','zothergoal',('activity','community','regime'),''),('h26c4','r5fl',('people','community','law'),' b')):
        seq='l[a]['+' '.join('k z'+n+'[]' for n in bs)+']'
        roots=(relation,) if root=='zothergoal' else (relation,root)
        d=fixture(roots,'q[k '+relation+'[k zactor[] k zactivity[] r'+rank+'[p '+root+'] '+seq+' '+FRAME+']].')
        actual=run(d,model(d));assert actual==[False];contrasts[relation+'_target']=actual
    return dict(independent_aim_and_expectation=rows,seven_argument_positions=contrasts,
        wrong_quoted_target_rejected=True,targets_not_executed=True,unknown_rejected=unknowns(doc,('h26c3','h26c4')))

@lru_cache(None)
def connection_checks():
    q='q[k r5fo['+ARGS+']].q[k r5fp['+ARGS+' k zmilestone[]]].'
    doc=fixture(('r5fo','r5fp'),q,('r5fh','r5fi'));rows=[]
    for actual,purpose,until in product((False,True),repeat=3):
        v=model(doc);oldh,oldi,oldp=v['r5fh'],v['r5fi'],v['h26c3']
        v['r5fh']=lambda *a:actual and oldh(*a);v['r5fi']=lambda *a:until and oldi(*a)
        v['h26c3']=lambda *a:purpose and oldp(*a)
        for n in ('h26c4','h26c2','h26cz','h26cv','dg','h257z','ic'):v[n]=unknown
        expected=[actual and purpose,actual and purpose and until]
        got=run(doc,v);assert got==expected,(actual,purpose,until,got);rows.append(dict(bits=[actual,purpose,until],values=got))
    contrasts={}
    for pos,label in enumerate(('actor','activity','target','bindings','reference','candidate','anchor')):
        if pos==2:continue # Explicit wrong quotation tested in attitude_checks.
        v=model(doc);old=v['h26c3']
        def wrong(*a,old=old,pos=pos):
            a=list(a)
            if pos==3:
                from noema.constructed_semantics import SequenceValue
                a[pos]=SequenceValue(('activity','regime','community'),'"individual"')
            else:a[pos]='other' if pos<2 else 'outside'
            return old(*a)
        v['h26c3']=wrong;got=run(doc,v);assert got==[False,False];contrasts[label]=got
    return dict(same_actual_introduction_aim_and_until=rows,same_purpose_frame=contrasts,
        expectation_and_improvement_not_asserted=True,boundaries=['r5fh','r5fi'],
        unknown_rejected=unknowns(doc,('r5fh','r5fi','h26c3')))

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(x for x in read(inv)['units'] if x['id']=='kant-1784:u0013')
    return dict(status='institutional_introduction_purpose_and_figurative_outlook_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1437,2309],text=u['text'][1437:2309]),
        antecedent=dict(primary_text_url='https://litgloss.buffalo.edu/kant/text.php',
            observation='前文のein solches Gesetzに続くeines bessernを、よりよい法と読む。einesの中性形と直前のGesetzに基づく照応の解釈であり、女性名詞Ordnungを同じ個体へ置き換えない。'),
        adopted_readings=LIMITS,
        remaining=['gleichsam mapping to the same whole policy and author','public insight and corroboration sufficient for common proposal',
            'reforming congregations, protection and nonhindrance','clerical focus, possibility, discourse and whole-sentence review'],
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
    assert read(READING)==reading_record() and not new.document['statements']
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),no_manuscript_mutation=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('improvement',improvement_checks),('law_contents',law_content_checks),('targets',target_checks),('attitudes',attitude_checks),('connection',connection_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,reading_record()['source_inventory'],
        'scripts/compose_institutional_outlook.py','scripts/check_institutional_outlook.py','tests/test_institutional_outlook.py',
        'scripts/compose_temporary_institution.py','scripts/compose_protected_remarks.py','scripts/check_covenant_nullity.py',
        'scripts/check_law_enactment.py','scripts/check_scoped_counts.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='institutional_introduction_purpose_and_figurative_outlook_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
