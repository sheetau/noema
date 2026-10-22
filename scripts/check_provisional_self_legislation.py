"""Check the modal frame, same adoption, bound period and separate expectation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_provisional_self_legislation import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,NAMES,parents,build,closure
from scripts.check_law_enactment import fixture as law_fixture,DOMAIN
from scripts.check_rational_self_imposition import model as self_model
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown
from scripts.check_covenant_nullity import normalized

REPORT='reports/provisional-self-legislation-v1.json'
DOC='docs/provisional-self-legislation-v1.md'
READING='data/provisional-self-legislation-reading-v1.json'
PRIORS=('reports/legislative-touchstone-v1.json','reports/insight-threshold-v1.json','reports/institutional-outlook-v1.json','reports/temporary-institution-v1.json','reports/rational-self-imposition-v1.json')
POINTS=('before','point','middle','end','after')
SCENES=('reference','assessment','candidate','alternative',*POINTS,'outside')
OBJECTS=dict(zip(NAMES,('people','community','law','community','activity','law','people','p','actor','other')))
ARGS=' '.join('k z'+n+'[]' for n in NAMES)
SEQ='l[a]['+ARGS+']'
EXTRA=''.join('r z'+n+'[] a.' for n in NAMES)+''.join('r z'+n+'[] d.' for n in SCENES)
EXTRA+='r zpossible[i b[h[j[a] d] e]] c.r zdepiction[i b[h[j[a] d d d] e]] c.'
FRAME=ARGS+' k zassessment[] k zcandidate[] k zpoint[] k zend[]'

def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

@lru_cache(None)
def fixture(roots,query,boundaries=(),provider=False):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    extra=parse('p:'+EXTRA)['declarations']
    if provider:
        supplied=law_fixture(('r5ek',),'')['declarations'];names={d['name'] for d in supplied}
        doc['declarations']=supplied+[d for d in doc['declarations'] if d['name'] not in names]
    names={d['name'] for d in doc['declarations']}
    doc['declarations']+= [d for d in extra if d['name'] not in names]
    return parse(format_graph(doc,'compact')+query)

def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)

def model(doc,variant='baseline',permission=True,prohibition=False):
    v=self_model(doc,variant,permission,prohibition)
    v.update({'z'+n:lambda value=value:value for n,value in OBJECTS.items()})
    v.update({'z'+n:lambda n=n:n for n in SCENES})
    candidates=('candidate','alternative') if variant in ('split_witness','second_success','one_of_two') else ('candidate',)
    v['h257z']=lambda r,h,t:r=='reference' and h in candidates and t in POINTS and not(variant=='missing_end' and t=='end')
    v['ic']=lambda a,b,h:h in candidates and a in POINTS and b in POINTS and(POINTS.index(a)<POINTS.index(b) or(variant=='cycle' and(a,b)==('end','point')))
    effect_at='alternative' if variant in ('split_witness','second_success') else 'candidate'
    expected=('people','people','community','law','community','activity','reference',effect_at,'point','end','law','people','p','actor','other','assessment')
    if variant=='wrong_assessment':expected=(*expected[:-1],'outside')
    v['r5gr']=lambda *a:variant!='no_provisional_order' and a==expected
    v['h26cx']=lambda a,r,h,s,e:variant!='unspecified' and(a,r,h,s,e)==('activity','reference','candidate','point','end')
    v['h26cy']=lambda c,g,r,h,s,e:variant!='long' and(c,g,r,h,s,e)==('community','community','reference','candidate','point','end')
    v['h26cs']=lambda g,c,r:(g,c,r)==('community','community','reference')
    v['h26cz']=lambda a,g,c,r,h,t:variant!='not_introduced' and(a,g,c,r,h,t)==('activity','community','community','reference','candidate','point')
    v['h26cv']=lambda g,c,r,h,t:(g,c,r,h)==('community','community','reference','candidate') and t in ('point','middle')
    v['r5fa']=lambda c,g,r,h,t:(c,g,r,h)==('community','community','reference','candidate') and t in ('point','middle') and not(variant=='freedom_gap' and t=='middle')
    purpose=('people','activity',('r5fl',0),('activity','community','community'),'reference','candidate','point')
    v['h26c3']=lambda *a:variant!='no_purpose' and normalized(a)==purpose
    def threshold(*a):
        exact=a==('p','community','community','law','people','actor','other','reference','assessment','candidate','point')
        return Content(SCENES,tuple(exact and variant!='no_threshold' and(t in ('end','after') or(variant=='earlier_threshold' and t=='middle')) for t in SCENES))
    v['r5gq']=threshold
    return v

def reject_unknown(doc,names):
    for n in names:
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return list(names)

@lru_cache(None)
def possibility_checks():
    doc=fixture(('r5gt',),'q[k r5gt['+ARGS+' k zassessment[]]].',('r5gr',),provider=True);rows={}
    for variant in ('baseline','second_success','one_of_two','split_witness','empty_candidates','missing_person','empty_law','cycle','no_provisional_order','wrong_assessment'):
        v=model(doc,variant);v['h26c4']=unknown
        actual=run(doc,v);assert actual==[variant in ('baseline','second_success','one_of_two')],(variant,actual);rows[variant]=actual[0]
    normative={}
    for permit,oppose in ((False,False),(True,False),(False,True),(True,True)):
        actual=run(doc,model(doc,permission=permit,prohibition=oppose));assert actual==[permit and not oppose]
        normative[str((permit,oppose))]=actual[0]
    return dict(same_candidate_existential_possibility=rows,positive_permission_without_conflict=normative,
        native_candidate_scope_and_normative_permission=True,
        boundary='r5gr; native adoption and bounded period checked separately below; threshold evidence preserved',
        actual_expectation_not_required=True,unknown_rejected=reject_unknown(doc,('h26cf','h245c','h237z','r5gr')))

@lru_cache(None)
def integration_checks():
    doc=fixture(('r5gs',),'q[k r5gs['+FRAME+']].',('r5gq','r5fa'),provider=True);rows={}
    for variant in ('baseline','no_activity','no_effect','split_effect_activity','other_actor','no_purpose','not_introduced','unspecified','long','freedom_gap','no_threshold','earlier_threshold','missing_end','cycle'):
        v=model(doc,variant);v['h26c4']=unknown
        actual=run(doc,v);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
    identity={}
    # A distinct wrong target at every parameter position, including actor,
    # people, law, candidate, start, end and fixed truth assessment.
    bound=fixture(('r5gs',),'q[k r5gs['+FRAME+']].',('r5gr',),provider=True)
    for i in range(16):
        v=model(bound);old=v['r5gr']
        def changed(*a,i=i,old=old):
            a=list(a);a[i]='outside' if i in (6,7,8,9,15) else 'thirdclause';return old(*a)
        v['r5gr']=changed;actual=run(bound,v);assert actual==[False],(i,actual);identity[str(i)]=actual[0]
    return dict(native_self_adoption_short_period_purpose_and_until=rows,exact_sixteen_arguments=identity,
        native_definitions=['r5ep','r5eq','r5gr','r5fp','r5fo','r5fi','r5fh','r5ek','r5ej','rkh'],
        boundaries=['r5gq reached public-insight threshold; preserved insight-threshold evidence','r5fa all-citizen freedom; preserved institutional-criticism evidence'],
        unknown_rejected=reject_unknown(doc,('h26cd','h26ce','h26cx','h26cy','h26cz','h26c3','r5gq','r5fa')))

@lru_cache(None)
def binding_checks():
    rows={};small=('alpha','beta')
    for root,target,suffix in (('r5gu','r5gt',' k zassessment[]'),('r5gv','r5ei',''),('r5gw','r5fn',' k zreference[] k zcandidate[] k zpoint[]'),('r5gx','r5es','')):
        d=fixture((root,),'q[t[k '+root+'['+SEQ+suffix+']][k zreference[]]].',(target,));checks=[]
        positions=range(10) if root in ('r5gu','r5gw') else range(3)
        for i in positions:
            v=model(d);values=tuple('beta' if k==i else 'alpha' for k in range(10))
            v.update({'z'+n:lambda value=value:value for n,value in zip(NAMES,values)})
            if root=='r5gu':wanted=(*values,'assessment')
            elif root=='r5gv':wanted=(*values[:3],'reference')
            elif root=='r5gx':wanted=values[:3]
            else:wanted=(values[0],values[4],*values[:3],'reference','candidate','point')
            v[target]=lambda *a,wanted=wanted:a==wanted
            assert run(d,v,small)==[True]
            # Changes to unused slots do not alter the narrower antecedent or
            # literal depiction. Only slots actually used by it must reject.
            relevant=range(10) if root=='r5gu' else ((0,1,2,4) if root=='r5gw' else range(3))
            if i in relevant:
                v['z'+NAMES[i]]=lambda:'alpha';assert run(d,v,small)==[False]
            checks.append(dict(position=i,used=i in relevant))
        for length in (9,11):
            names=NAMES[:length] if length<10 else (*NAMES,'law')
            seq='l[a]['+' '.join('k z'+n+'[]' for n in names)+']'
            wrong=fixture((root,),'q[t[k '+root+'['+seq+suffix+']][k zreference[]]].',(target,));v=model(wrong)
            v.update({'z'+n:lambda:'alpha' for n in NAMES});v[target]=lambda *a:True
            assert run(wrong,v,small)==[False]
        rows[root]=checks
    return dict(exact_ten_object_binding=rows,wrong_lengths_rejected=True,
        boundaries=['r5gt','r5ei','r5fn','r5es; separately checked native constructions'])

@lru_cache(None)
def depiction_checks():
    # The depiction itself attributes an expectation, but never evaluates the
    # better-law target. It remains absent from the modal world's conjunction.
    d=fixture(('r5gw',),'q[t[k r5gw['+SEQ+' k zreference[] k zcandidate[] k zpoint[]]][k zend[]]].')
    rows={}
    # Use one individual marker to avoid ten-domain existential bindings here;
    # the distinct slots are tested independently in binding_checks.
    expected=('alpha','alpha',('r5fk',1),('alpha',)*3,'reference','candidate','point')
    for present in (False,True):
        v={x['name']:unknown for x in d['declarations'] if x['kind']=='primitive'}
        v.update({'z'+n:lambda:'alpha' for n in NAMES});v.update({'z'+n:lambda n=n:n for n in SCENES})
        v['h26c4']=lambda *a:present and normalized(a)==expected
        actual=run(d,v,('alpha',));assert actual==[present];rows[str(present)]=actual[0]
    quoted=fixture(('r5gu','r5gw'),'q[k zpossible[r b[p r5gu]]].q[k zdepiction[r b[p r5gw]]].')
    v={x['name']:unknown for x in quoted['declarations'] if x['kind']=='primitive'}
    v['zpossible']=lambda x:normalized(x)==('r5gu',1);v['zdepiction']=lambda x:normalized(x)==('r5gw',1)
    assert run(quoted,v)==[True,True]
    return dict(literal_expectation_truth_table=rows,better_law_not_evaluated=True,
        possibility_and_depiction_can_be_quoted_with_unknown_world=True,
        no_existence_or_actual_expectation_from_quotation=True)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';u=next(x for x in read(inv)['units'] if x['id']=='kant-1784:u0013')
    return dict(status='provisional_self_legislation_modal_dependency',source_inventory=inv,
        source=dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[1437,2309],text=u['text'][1437:2309]),
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/039.html',lines='15–27',
            observation='diesesの直前は人民による自己賦課可能性を問う文。一定の短期・批評の自由・制度継続・洞察到達は同じ暫定構成の条件として続く。')],
        adopted_readings=LIMITS,reuse=['r5ep conclusion-independent candidates','r5eq normative self-imposition permission','r5gr same bounded institutional order','r5fn separate expectation depiction','r5es preceding self-imposition possibility'],
        remaining=['whole sentence quantification and contextual scope','purpose focus concession metonymy and figurative presentation','author attribution and whole-sentence reading'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    sources=parents();new=catalog();old={n:e for s in sources for n,e in s.entries.items()}
    for n,e in new.entries.items():
        if n not in MEANINGS:assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record() and not new.document['statements'] and len(sources[0].document['statements'])==102
    # The reference/depiction adapters bind the same sequence but the world
    # candidate never calls literal expectation or general actor permission.
    reached={d['name'] for d in closure(new.document,['r5gt'])}
    assert 'r5eq' in reached and 'r5gr' in reached and not reached&{'r5fn','h26c4','r5ew'}
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        no_literal_expectation_in_world=True,preserved_manuscript_statements=102)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('possibility',possibility_checks),('integration',integration_checks),('bindings',binding_checks),('depiction',depiction_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,reading_record()['source_inventory'],
        'scripts/compose_provisional_self_legislation.py','scripts/check_provisional_self_legislation.py','tests/test_provisional_self_legislation.py',
        'scripts/check_law_enactment.py','scripts/check_rational_self_imposition.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_covenant_nullity.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    return dict(status='provisional_self_legislation_modal_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
