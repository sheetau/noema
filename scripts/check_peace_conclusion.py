"""Check peace terms, political principals, same declarations and chronology."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_peace_conclusion import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,LIMITS,parents,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.fetch_peace_conclusion_evidence import RECORD as EVIDENCE,validate

REPORT='reports/peace-conclusion-v1.json'
DOC='docs/peace-conclusion-v1.md'
READING='data/peace-conclusion-reading-v1.json'
PRIORS=('reports/public-confirmation-v1.json','reports/irrevisable-confession-v1.json')
DOMAIN=('left','right','ally','agreement','person','second','act','otheract','contract','community')
SCENES=('prior','anchor','candidate','outside')
EXTRA=''.join('r z'+n+'[] a.' for n in DOMAIN)+''.join('r zt'+n+'[] d.' for n in SCENES)

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)
@lru_cache(None)
def fixture(roots,query,boundaries=()):
    doc=deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:d.update(kind='primitive',parameters=[p['sort'] for p in d['parameters']]);d.pop('body')
    doc.update(declarations=closure(doc,roots),statements=[])
    return parse(format_graph(doc,'compact')+EXTRA+query)
def base(doc):
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    v.update({'z'+n:lambda n=n:n for n in DOMAIN});v.update({'zt'+n:lambda n=n:n for n in SCENES})
    v['h254z']=lambda agreement:'anchor'
    return v
def run(doc,v,domain=DOMAIN):return evaluate(doc,v,domain,SCENES,True)
def timeline(v,variant='baseline'):
    history=('prior','anchor','candidate')
    v['h257k']=lambda agreement,candidate,p:agreement=='agreement' and candidate=='candidate' and p in history and not (variant=='missing_anchor' and p=='anchor') and not (variant=='missing_candidate' and p=='candidate')
    order=('prior','candidate','anchor') if variant=='future_formation' else history
    v['ic']=lambda a,b,c:c=='candidate' and a in order and b in order and (a!=b if variant=='cycle' else order.index(a)<order.index(b))

@lru_cache(None)
def terms_checks():
    doc=fixture(('r5bb',),'q[t[k r5bb[k zleft[] k zagreement[] k ztanchor[]]][k ztcandidate[]]].');rows={}
    for war,attack in product((False,True),repeat=2):
        v=base(doc);v['h257e']=lambda *a:a==('agreement','left','anchor')
        v['h257f']=lambda *a:a==('agreement','right','left','anchor')
        v['h257g']=lambda *a:war and a==('right','left','candidate')
        v['h257h']=lambda *a:attack and a==('left','right','candidate')
        result=run(doc,v);assert result==[not war and not attack];rows[str((war,attack))]=result[0]
    contrasts={}
    for variant in ('unrelated_war','other_agreement_pair','other_reference_pair','other_point_attack','not_party'):
        v=base(doc);v['h257e']=lambda *a:variant!='not_party' and a==('agreement','left','anchor')
        v['h257f']=lambda *a:a==('contract' if variant=='other_agreement_pair' else 'agreement','left','right','outside' if variant=='other_reference_pair' else 'anchor')
        v['h257g']=lambda *a:a==('left','ally','candidate')
        v['h257h']=lambda *a:a==('left','right','outside' if variant=='other_point_attack' else 'candidate')
        result=run(doc,v);expected=variant in ('other_agreement_pair','other_reference_pair','other_point_attack');assert result==[expected];contrasts[variant]=result[0]
    # Adapter runs the actual content and enforces exactly [party, agreement].
    adapters={}
    for seq in (('left','agreement'),('agreement','left'),('left',),('left','agreement','right')):
        literal='l[a]['+' '.join('k z'+x+'[]' for x in seq)+']'
        d=fixture(('r5bc',),'q[t[k r5bc['+literal+']][k ztcandidate[]]].');v=base(d)
        v['h257e']=lambda *a:a==('agreement','left','anchor');v['h257f']=lambda *a:a==('agreement','left','right','anchor')
        v['h257g']=lambda *a:False;v['h257h']=lambda *a:False
        result=run(d,v,('left','agreement','right'));assert result==[seq==('left','agreement')];adapters[str(seq)]=result[0]
    return dict(native_war_and_hostilities=rows,scope_contrasts=contrasts,exact_native_term_bindings=adapters,
        truce_with_continued_war_relation_not_peace=True)

@lru_cache(None)
def prior_war_checks():
    doc=fixture(('r5bg',),'q[k r5bg[k zagreement[] k ztanchor[] k ztcandidate[]]].');rows={}
    for variant in ('baseline','neutral_ally','no_pairs','self_pair','outsider_pair','missing_second_war','no_prior_war','wrong_history','war_at_anchor','war_later','wrong_reference'):
        v=base(doc);timeline(v)
        parties=('left','right','ally') if variant in ('neutral_ally','missing_second_war') else ('left','right')
        v['h257e']=lambda ag,p,r:ag=='agreement' and p in parties and r=='anchor'
        pairs=set() if variant=='no_pairs' else {('left','left')} if variant=='self_pair' else {('left','ally')} if variant=='outsider_pair' else {('left','right')}
        if variant=='missing_second_war':pairs.add(('left','ally'))
        v['h257f']=lambda ag,a,b,r:ag=='agreement' and (a,b) in pairs and r==('outside' if variant=='wrong_reference' else 'anchor')
        point={'war_at_anchor':'anchor','war_later':'candidate','wrong_history':'outside'}.get(variant,'prior')
        v['h257g']=lambda *a:variant!='no_prior_war' and a==('right','left',point)
        result=run(doc,v);assert result==[variant in ('baseline','neutral_ally')],(variant,result);rows[variant]=result[0]
    return dict(native_nonempty_all_opponent_pairs=rows,neutral_guarantor_not_required_to_have_fought=True,
        domain_scope_completeness_is_explicit_input=True)

@lru_cache(None)
def declaration_checks():
    query='q[k r5be[k zagreement[] k ztanchor[] k zleft[] k zact[] r[p r5bc] l[a][k zleft[] k zagreement[]] k ztanchor[]]].'
    doc=fixture(('r5be','r5bc'),query);rows={}
    for variant in ('baseline','not_human','not_performer','not_authorized','other_party','other_activity','other_agreement','other_terms','swapped_bindings','other_point','missing_counterparty','split_humans'):
        v=base(doc);v['h257e']=lambda ag,p,r:ag=='agreement' and p in ('left','right','ally') and r=='anchor'
        v['aa']=lambda p:variant!='not_human' and p in ('person','second')
        v['f3']=lambda p,a,s:variant!='not_performer' and p in ('person','second') and (a,s)==('act','anchor')
        v['h257i']=lambda p,party,a,ag,s:variant!='not_authorized' and p in ('person','second') and (party,a,ag,s)==('left','act','agreement','anchor')
        def declares(p,party,other,a,ag,code,bindings,s):
            wanted=['left','act','agreement','r5bc',('left','agreement'),'anchor']
            changes={'other_party':(0,'right'),'other_activity':(1,'otheract'),'other_agreement':(2,'contract'),
                'other_terms':(3,'r46u'),'swapped_bindings':(4,('agreement','left')),'other_point':(5,'candidate')}
            if variant in changes:i,x=changes[variant];wanted[i]=x
            person='second' if variant=='split_humans' and other=='ally' else 'person'
            return p==person and other in ('right','ally') and not (variant=='missing_counterparty' and other=='ally') and code.rank==0 and (party,a,ag,symbol(code),tuple(bindings.items),s)==tuple(wanted)
        v['h257j']=declares
        result=run(doc,v);assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
        assert all(v[n] is unknown for n in ('h257g','h257h'))
    d=fixture(('r5bd',),'q[k r5bd[k zleft[] k zact[] k zagreement[] k ztanchor[]]].');v=base(d)
    v['aa']=lambda p:p=='person';v['f3']=lambda *a:a==('person','act','anchor');v['h257i']=lambda *a:a==('person','left','act','agreement','anchor')
    assert run(d,v)==[True]
    v['h257i']=lambda *a:False;assert run(d,v)==[False]
    return dict(native_same_human_act_principal_and_all_counterparties=rows,quote_not_executed=True,native_representation_adapter=True)

@lru_cache(None)
def formation_checks():
    doc=fixture(('r5bf',),'q[k r5bf[k zagreement[] k ztanchor[] k ztcandidate[]]].',('r5bd','r5be'));rows={}
    for variant in ('baseline','single_party','private_party','unassigned_terms','wrong_terms','missing_undertaking','wrong_binding','no_occurrence','no_representation','later_declaration','other_history','moving_reference'):
        v=base(doc);timeline(v);parties=('left',) if variant=='single_party' else ('left','right','ally')
        v['h257e']=lambda ag,p,r:ag=='agreement' and p in parties and r=='anchor'
        v['h257d']=lambda p,r:p in parties and not (variant=='private_party' and p=='right') and r=='anchor'
        if variant=='moving_reference':v['h254z']=lambda a:'candidate'
        v['h255a']=lambda a,code,r:variant!='unassigned_terms' and code.rank==0 and (a,symbol(code),r)==('agreement','r46u' if variant=='wrong_terms' else 'r5bc','anchor')
        v['dg']=lambda a,p:variant!='no_occurrence' and a=='act' and p in ('prior','anchor','candidate','outside')
        v['r5bd']=lambda party,a,ag,p:variant!='no_representation' and party in parties and (a,ag)==('act','agreement')
        def declares(ag,ref,party,a,code,bindings,p):
            expected=('agreement',party) if variant=='wrong_binding' else (party,'agreement')
            point='candidate' if variant=='later_declaration' else 'outside' if variant=='other_history' else 'anchor'
            return party in parties and not (variant=='missing_undertaking' and party=='right') and code.rank==0 and (ag,ref,a,symbol(code),tuple(bindings.items),p)==('agreement','anchor','act','r5bc',expected,point)
        v['r5be']=declares
        result=run(doc,v,('left','right','ally','agreement','act'));assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
        assert v['h257g'] is unknown and v['h257h'] is unknown
    return dict(native_rhz_all_political_parties_and_history=rows,boundaries=['r5bd','r5be'],
        all_roles_native_separately=True,peace_performance_not_required_for_conclusion=True)

@lru_cache(None)
def classification_checks():
    doc=fixture(('r5bh',),'q[k r5bh[k zagreement[] k ztcandidate[]]].',('r5bg','r5bf'));rows={}
    for variant in ('baseline','missing_anchor','missing_candidate','future_formation','cycle','no_war_scope','no_formation','other_agreement','other_candidate'):
        v=base(doc);timeline(v,variant)
        wanted=('contract' if variant=='other_agreement' else 'agreement','anchor','outside' if variant=='other_candidate' else 'candidate')
        v['r5bg']=lambda *a:variant!='no_war_scope' and a==wanted
        v['r5bf']=lambda *a:variant!='no_formation' and a==wanted
        result=run(doc,v);assert result==[variant=='baseline'],(variant,result);rows[variant]=result[0]
    for n in ('h257k','r5bg','r5bf'):
        v=base(doc);timeline(v);v.update(r5bg=lambda *a:True,r5bf=lambda *a:True);v[n]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(n)
    return dict(native_valid_timeline_and_fixed_anchor=rows,unknown_rejected=True,boundaries=['r5bg','r5bf'])

@lru_cache(None)
def confirmation_checks():
    rows={}
    for root,query in (
        ('r5bi','q[k r5bi[k zcontract[] k ztanchor[] k ztcandidate[]]].'),
        ('r5bj','q[t[k r5bj[k zcontract[] k zcommunity[] k ztanchor[]]][k ztcandidate[]]].')):
        doc=fixture((root,),query,('r5bh','r5au','r5an','r5as'))
        for variant in ('baseline','not_peace','not_solemn','wrong_instrument','wrong_contract','wrong_reference','wrong_point'):
            v=base(doc);v['r5bh']=lambda ag,p:variant!='not_peace' and (ag,p)==('agreement','candidate')
            v['r5au']=lambda *a:variant!='not_solemn' and a==('agreement','outside' if variant=='wrong_reference' else 'anchor','candidate')
            v['h256y']=lambda *a:a==('act' if variant=='wrong_instrument' else 'agreement','agreement' if variant=='wrong_contract' else 'contract','outside' if variant=='wrong_point' else 'candidate')
            v['r5an']=lambda *a:False;v['r5as']=lambda *a:False;v['h256x']=lambda *a:False
            result=run(doc,v);assert result==[variant=='baseline'],(root,variant,result);rows[root+':'+variant]=result[0]
    return dict(native_typed_confirmation_adapters=rows,boundaries=['r5bh','r5au','r5an','r5as'],peace_kind_supplied=True)

@lru_cache(None)
def integrated_checks():
    # All new peace definitions and the existing rhz/ta machinery execute natively.
    # Only the already checked solemn-form classifier is supplied at its boundary.
    doc=fixture(('r5bi',),'q[k r5bi[k zcontract[] k ztanchor[] k ztcandidate[]]].',('r5au',));rows={}
    domain=('left','right','agreement','person','second','act','contract')
    representatives={'left':'person','right':'second'}
    for variant in ('baseline','wrong_counterparty','no_prior_war','other_confirmed_contract'):
        v=base(doc);timeline(v)
        v['h257e']=lambda ag,p,r:ag=='agreement' and p in representatives and r=='anchor'
        v['h257d']=lambda p,r:p in representatives and r=='anchor'
        v['h257f']=lambda *a:a==('agreement','left','right','anchor')
        v['h257g']=lambda *a:variant!='no_prior_war' and a==('right','left','prior')
        v['aa']=lambda p:p in representatives.values()
        v['f3']=lambda p,a,s:p in representatives.values() and (a,s)==('act','anchor')
        v['dg']=lambda *a:a==('act','anchor')
        v['h257i']=lambda person,party,a,ag,s:representatives.get(party)==person and (a,ag,s)==('act','agreement','anchor')
        v['h255a']=lambda ag,code,r:code.rank==0 and (ag,symbol(code),r)==('agreement','r5bc','anchor')
        def declares(person,party,other,a,ag,code,bindings,s):
            recipient='left' if party=='right' else 'right'
            if variant=='wrong_counterparty' and party=='right':recipient='agreement'
            return representatives.get(party)==person and code.rank==0 and (other,a,ag,symbol(code),tuple(bindings.items),s)==(recipient,'act','agreement','r5bc',(party,'agreement'),'anchor')
        v['h257j']=declares
        v['r5au']=lambda *a:a==('agreement','anchor','candidate')
        v['h256y']=lambda *a:a==('agreement','agreement' if variant=='other_confirmed_contract' else 'contract','candidate')
        actual=run(doc,v,domain);assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual[0]
        assert v['h257h'] is unknown
    return dict(native_peace_formation_through_instrument_confirmation=rows,
        sole_boundary='r5au, whose native solemnity is pinned in public-confirmation-v1',
        peace_terms_not_executed=True,political_parties_distinct_from_human_representatives=True)

def reading_record():
    inv='artifacts/written-units-v1/kant-1784.json';unit=next(u for u in read(inv)['units'] if u['id']=='kant-1784:u0013')
    return dict(status='peace_conclusion_and_confirming_instrument_dependency',source_inventory=inv,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[444,712],text=unit['text'][444:712]),
        primary_page=read('data/covenant-question-reading-v1.json')['original_page'],evidence=EVIDENCE,adopted_readings=LIMITS,
        remaining=['同種契約の仮定形成と全帰結についての無効性の内容を接続する','三種類の確認の列挙とschlechterdings・sollte auchの全面性・譲歩を提示する','一文の著者帰属と通読による意味判断'],
        new_verified_characters=0,whole_sentence_semantically_verified=False)

@lru_cache(None)
def structure_checks():
    new=catalog();old,confirmation=parents();imported=dict(old.entries);imported.update(confirmation.entries)
    for n,e in new.entries.items():
        if n not in set(PRIMITIVES)|set(MEANINGS):
            assert e['declaration']==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
    for p,b in build().items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for p in PRIORS:validate_hashes(ROOT,read(p)['source_sha256'])
    validate(read(EVIDENCE));assert read(READING)==reading_record();p=read(READING)['primary_page'];assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    assert not new.document['statements'] and len(old.document['statements'])==98
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),preserved_manuscript_statements=98)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,b in build().items():write_exact(ROOT/p,b)
    write_exact(ROOT/READING,encoded(reading_record()))

def build_report():
    results={}
    for n,f in [('terms',terms_checks),('prior_war',prior_war_checks),('declarations',declaration_checks),('formation',formation_checks),('classification',classification_checks),('confirmation',confirmation_checks),('integrated',integrated_checks),('structure',structure_checks)]:
        results[n]=f();print(n+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|{DOC,READING,EVIDENCE,*PRIORS,read(READING)['source_inventory'],read(READING)['primary_page']['path'],
        'scripts/compose_peace_conclusion.py','scripts/check_peace_conclusion.py','scripts/fetch_peace_conclusion_evidence.py','tests/test_peace_conclusion.py',
        'scripts/check_pastoral_roles.py','scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py','scripts/compose_protected_remarks.py'}
    paths|={r['path'] for r in read(EVIDENCE)['sources']}
    return dict(status='political_peace_conclusion_and_typed_confirmation_dependency',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
