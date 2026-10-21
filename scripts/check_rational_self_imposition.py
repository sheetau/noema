"""Check normative permission and self-enactment in the same hypothetical history."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_rational_self_imposition import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure,NAMES
from scripts.check_law_enactment import EXTRA,PROVIDER,DOMAIN,model as enactment_model
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

REPORT='reports/rational-self-imposition-v1.json'
DOC='docs/rational-self-imposition-v1.md'
READING='data/rational-self-imposition-reading-v1.json'
PRIORS=('reports/law-enactment-v1.json','reports/posterity-rights-v1.json','reports/self-legislation-v1.json')
SCENES=('reference','candidate','alternative','before','point','outside')
ARGS='k zpeople[] k zcommunity[] k zlaw[]'
SEQ='l[a]['+ARGS+']'
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
def read(p):return json.loads((ROOT/p).read_text(encoding='utf-8'))
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    prefix=deepcopy(parents()[0].document);prefix.update(declarations=closure(prefix,['h7k','h7l']),statements=[])
    provided=parse(format_graph(prefix,'compact')+EXTRA+PROVIDER+'r zalternative[] d.r zpresent[i b[f]] c.')
    ns={d['name'] for d in provided['declarations']}
    doc['declarations']=provided['declarations']+[d for d in doc['declarations'] if d['name'] not in ns]
    return parse(format_graph(doc,'compact')+query)
def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)
def model(doc,variant='baseline',permission=True,prohibition=False):
    v=enactment_model(doc,variant);v.update(zalternative=lambda:'alternative',h26cg=lambda:'actor',h26ch=lambda:'activity')
    candidates=('candidate','alternative') if variant in ('split_witness','second_success','one_of_two') else ('candidate',)
    v['h26cf']=lambda p,c,l,r,h:variant!='empty_candidates' and(p,c,l,r)==('people','community','law','reference') and h in candidates
    if variant=='wrong_candidate_identity':v['h26cf']=lambda p,c,l,r,h:(p,c,l,r,h)==('people','community','other','reference','candidate')
    v['h257z']=lambda r,h,t:variant!='empty_history' and r=='reference' and h in candidates and t in ('before','point')
    v['ic']=lambda a,b,h:h in candidates and ((a,b)==('before','point') or(variant=='cycle' and(a,b)==('point','before')))
    oldcd,oldce=v['h26cd'],v['h26ce']
    enactment_at='alternative' if variant in ('split_witness','second_success') else 'candidate'
    v['h26cd']=lambda a,s,p,c,l,r,h,t:h==enactment_at and oldcd(a,s,p,c,l,r,'candidate',t)
    v['h26ce']=lambda a,p,c,l,r,h,t:h==enactment_at and oldce(a,p,c,l,r,'candidate',t)
    permit_at='alternative' if variant=='second_success' else 'candidate'
    def match(s,p,r,c,b,reference,sign,t):
        expected=['actor','people','activity','r5en',1,('people','community','law'),'reference',True,permit_at]
        changes={'wrong_source':(0,'law'),'wrong_person':(1,'other'),'wrong_role':(2,'people'),
                 'wrong_content':(3,'ztask'),'wrong_reference':(6,'outside'),'wrong_polarity':(7,False),'wrong_permission_candidate':(8,'outside')}
        if variant in changes:
            i,value=changes[variant];expected[i]=value
        if variant.startswith('wrong_binding_'):
            values=list(expected[5]);values[int(variant[-1])]='other';expected[5]=tuple(values)
        return (s,p,r,symbol(c),c.rank,tuple(b.items),reference,sign,t)==tuple(expected)
    v['h245c']=lambda *a:permission and match(*a)
    v['h237z']=lambda s,p,r,c,b,reference,sign,t:prohibition and match(s,p,r,c,b,reference,not sign,t)
    return v
def rejects_unknown(doc,names):
    for n in names:
        v=model(doc);v[n]=unknown
        try:run(doc,v)
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(n)
    return list(names)
@lru_cache(None)
def scope_checks():
    doc=fixture(('r5ep',),'q[k r5ep['+ARGS+' k zcandidate[]]].');rows={}
    for variant in ('baseline','empty_candidates','wrong_candidate_identity','empty_history','cycle','missing_person','empty_law','no_activity','no_effect'):
        v=model(doc,variant,False,True);v['h245c']=unknown;v['h237z']=unknown;v['dg']=unknown
        actual=run(doc,v);assert actual==[variant in ('baseline','no_activity','no_effect')],(variant,actual);rows[variant]=actual[0]
    return dict(candidates_independent_of_conclusion=rows,permission_and_enactment_not_evaluated=True,
        unknown_rejected=rejects_unknown(doc,('h26cf','h257z','ic')))
@lru_cache(None)
def permission_checks():
    doc=fixture(('r5eq',),'q[k r5eq['+ARGS+' k zcandidate[]]].');rows={}
    for allowed,opposed in product((False,True),repeat=2):
        v=model(doc,permission=allowed,prohibition=opposed);v['dg']=unknown;v['h26cf']=unknown
        actual=run(doc,v);assert actual==[allowed and not opposed];rows[str((allowed,opposed))]=actual[0]
    contrasts={}
    for variant in ('wrong_source','wrong_person','wrong_role','wrong_content','wrong_reference','wrong_polarity','wrong_permission_candidate',*('wrong_binding_'+str(i) for i in range(3))):
        actual=run(doc,model(doc,variant));assert actual==[False],(variant,actual);contrasts[variant]=actual[0]
    unrelated_opposition={}
    for variant in contrasts:
        v=model(doc);v['h237z']=model(doc,variant,prohibition=True)['h237z']
        actual=run(doc,v);assert actual==[True],(variant,actual);unrelated_opposition[variant]=actual[0]
    return dict(positive_permission_without_opposite_requirement=rows,exact_normative_tuple=contrasts,
        other_normative_tuple_does_not_conflict=unrelated_opposition,
        quoted_enactment_not_executed=True,unknown_rejected=rejects_unknown(doc,('h245c','h237z')))
@lru_cache(None)
def possibility_checks():
    doc=fixture(('r5es',),'q[k r5es['+ARGS+']].');rows={}
    for variant in ('baseline','reconfirmation','second_success','one_of_two','split_witness','empty_candidates','cycle','missing_person','empty_law','no_activity','no_effect','split_effect_activity','other_actor','split_times'):
        actual=run(doc,model(doc,variant));assert actual==[variant in ('baseline','reconfirmation','second_success','one_of_two')],(variant,actual);rows[variant]=actual[0]
    for p,o in ((False,False),(True,True)):
        assert run(doc,model(doc,permission=p,prohibition=o))==[False]
    return dict(native_same_candidate_possibility=rows,no_definition_boundaries=True,
        existential_not_universal=True,actual_reference_not_required=True,
        unknown_rejected=rejects_unknown(doc,('h26cf','h245c','h237z','h26cd','h26ce')))
@lru_cache(None)
def binding_checks():
    matrix=[];small=('alpha','beta')
    for i,j in product(range(3),repeat=2):
        doc=fixture(('r5et',),'q[t[k r5et['+SEQ+']][k zreference[]]].',('r5es',));v=model(doc)
        v.update({'z'+n:lambda k=k:'beta' if k==i else 'alpha' for k,n in enumerate(NAMES)})
        expected=tuple('beta' if k==j else 'alpha' for k in range(3));v['r5es']=lambda *a:a==expected
        actual=run(doc,v,small);assert actual==[i==j];matrix.append(actual[0])
    for seq in ('l[a][k zpeople[] k zcommunity[]]','l[a]['+ARGS+' k zlaw[]]'):
        d=fixture(('r5et',),'q[t[k r5et['+seq+']][k zpoint[]]].',('r5es',));v=model(d);v['r5es']=lambda *a:True
        v.update({'z'+n:lambda:'alpha' for n in NAMES})
        assert run(d,v,small)==[False]
    return dict(exact_three_positions=matrix,wrong_lengths_rejected=True,boundary='r5es; native modal construction checked separately')
@lru_cache(None)
def question_checks():
    question='k r5eu['+SEQ+']';content='k r5et['+SEQ+']'
    doc=fixture(('r5eu',),'q[e['+question+'][j s['+content+']]].q[t[o['+question+']][k zreference[]]].',('r5es',))
    rows={}
    for answer in (False,True):
        v=model(doc);v['r5es']=lambda *a:answer
        # This boundary test supplies all three arguments with one domain value.
        v.update(zpeople=lambda:'people',zcommunity=lambda:'people',zlaw=lambda:'people')
        actual=run(doc,v,('people',));assert actual==[False,answer];rows[str(answer)]=actual
    quoted=fixture(('r5eu',),'q[k zpresent[r b['+question+']]].');v={d['name']:unknown for d in quoted['declarations'] if d['kind']=='primitive'}
    seen=[]
    def present(description):
        seen.append(description.syntax);return description.rank==1
    v['zpresent']=present;assert run(quoted,v)==[True] and len(seen)==1
    return dict(question_differs_from_assertion=rows,quoted_question_does_not_evaluate_unknown_possibility=True,
        no_answer_asserted=True,boundary='r5es only for evaluated question truth-table; none for quotation')
def reading_record():
    prior=read('data/law-enactment-reading-v1.json')
    return dict(status='normative_hypothetical_self_imposition_dependency',source_inventory=prior['source_inventory'],source=prior['source'],
        primary_evidence=[dict(url='https://korpora.org/kant/aa08/039.html',lines='2–17, 28–37',
            observation='権力による承認でも無効な合意、試金石の問い、暫定的に可能な秩序、啓蒙放棄の不許可を区別する文脈を確認した。'),
            dict(url='https://korpora.org/kant/aa08/297.html',work_year=1793,lines='2–28',
            observation='比較資料。原始契約を実際の事実とせず、人民の可能な共同意思を法の正当性の試金石とする。現在の賛否と可能な同意を区別する。この別作品の全教説は1784年の本文に追加しない。')],
        adopted_readings=LIMITS,remaining=['kannと立法許容の全対象','Probiersteinの判断基準の強さ','wohlと同じ法律への照応・問いの提示・著者帰属','全文通読'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)
@lru_cache(None)
def structure_checks():
    new=catalog();old={n:e for p in parents() for n,e in p.entries.items()}
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):assert e['declaration']==old[n]['declaration'] and e['meaning_ja']==old[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    assert read(READING)==reading_record() and not new.document['statements'] and len(parents()[0].document['statements'])==101
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_manuscript_statements=101)
def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))
def build_report():
    results={}
    for n,f in [('scope',scope_checks),('permission',permission_checks),('possibility',possibility_checks),('bindings',binding_checks),('question',question_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,*PRIORS,reading_record()['source_inventory'],
        'scripts/compose_rational_self_imposition.py','scripts/check_rational_self_imposition.py','tests/test_rational_self_imposition.py',
        'scripts/check_law_enactment.py','scripts/compose_law_enactment.py','scripts/compose_protected_remarks.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/check_scoped_counts.py',
        'scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='normative_hypothetical_self_imposition_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
