"""Check cross-sentence person scope without filtering inconvenient cases."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_shared_fetters_scope import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts import check_generic_fetters as previous

INDEX='data/semantic-review-index-v102.json'
REPORT='reports/shared-fetters-scope-v1.json'
AUDIT='data/shared-fetters-scope-reading-v1.json'
DOC='docs/shared-fetters-scope-v1.md'
PRIOR='reports/generic-fetters-v1.json'
PEOPLE=('first','othernode','case1','case2','person','other','object')
SCENES=('scope','use')

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def document():return parse((ROOT/FULL).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)

def fixture(roots,extra,replacements=''):
    doc=deepcopy(document());doc['statements']=[]
    if replacements:
        added=parse('p:'+replacements)['declarations']
        mapping={d['name']:d for d in added if d['kind']=='definition'}
        doc['declarations']=[d for d in added if d['kind']=='primitive']+[
            deepcopy(mapping.get(d['name'],d)) for d in doc['declarations']]
    doc['declarations']=closure(doc,roots)
    return parse(format_graph(doc,'compact')+extra)

def unknowns(doc):return {d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
def refuse(doc,values,names,people=PEOPLE,scenes=SCENES):
    for name in names:
        v=dict(values);v[name]=unknown
        try:evaluate(doc,v,people,scenes,True)
        except ValueError as error:assert 'Unknown' in str(error),(name,str(error))
        else:raise AssertionError(name)

@lru_cache(None)
def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''r zcases[a] c.r zrole[a] a.r zreferents[a] c.
q[k r2fx[p zcases p zrole p zreferents]].''')
    for bits in product((False,True),repeat=6):
        selected={c for c,b in zip(('case1','case2'),bits[:2]) if b}
        allowed={p for p,b in zip(('person','other'),bits[2:4]) if b}
        role={c:('other' if b else 'person') for c,b in zip(('case1','case2'),bits[4:])}
        values=dict(zcases=lambda c:c in selected,zrole=lambda c:role.get(c,'person'),zreferents=lambda p:p in allowed)
        assert evaluate(doc,values,PEOPLE,SCENES,True)==[bool(selected) and all(role[c] in allowed for c in selected)],bits
    values=dict(zcases=lambda c:c=='case1',zrole=lambda c:'person',zreferents=lambda p:p=='person')
    refuse(doc,values,('zcases','zrole','zreferents'))
    return dict(combinations=64,unknown_inputs_refused=3,noninjective_roles_allowed=True,unused_referents_allowed=True)

def scope_values(doc):
    values=unknowns(doc)
    values.update(wh=lambda:'scope',hzzq=lambda:'first',
        hzzzb=lambda s,c:s=='scope' and c in ('case1','case2'),
        hzzzd=lambda s,c:'other' if c=='case2' else 'person',
        aa=lambda p:p in ('person','other'),
        hzzn=lambda n,p,s:n=='first' and s=='scope' and p in ('person','other'))
    return values

@lru_cache(None)
def scope_checks():
    doc=fixture(['r2fy','wh'],'q[k r2fy[k wh[]]].')
    for bits in product((False,True),repeat=6):
        selected={c for c,b in zip(('case1','case2'),bits[:2]) if b}
        allowed={p for p,b in zip(('person','other'),bits[2:4]) if b}
        human={p for p,b in zip(('person','other'),bits[4:]) if b}
        values=scope_values(doc)
        values.update(hzzzb=lambda s,c:s=='scope' and c in selected,
            aa=lambda p:p in human,hzzn=lambda n,p,s:n=='first' and s=='scope' and p in allowed)
        roles={'case1':'person','case2':'other'}
        assert evaluate(doc,values,PEOPLE,SCENES,True)==[bool(selected) and all(roles[c] in allowed&human for c in selected)],bits
    cases={}
    for variant in ('baseline','wrong_antecedent','use_time_scope','empty_cases','empty_people','outsider','nonhuman','same_person','unused_person'):
        v=scope_values(doc)
        if variant=='wrong_antecedent':v['hzzq']=lambda:'othernode'
        if variant=='use_time_scope':v['hzzn']=lambda n,p,s:n=='first' and s=='use' and p in ('person','other')
        if variant=='empty_cases':v['hzzzb']=lambda *args:False
        if variant=='empty_people':v['hzzn']=lambda *args:False
        if variant=='outsider':v['hzzn']=lambda n,p,s:(n,p,s)==('first','person','scope')
        if variant=='nonhuman':v['aa']=lambda p:p=='person'
        if variant=='same_person':v['hzzzd']=lambda s,c:'person'
        if variant=='unused_person':v['hzzzb']=lambda s,c:(s,c)==('scope','case1')
        actual=evaluate(doc,v,PEOPLE,SCENES,True);assert actual==[variant in ('baseline','same_person','unused_person')],(variant,actual)
        cases[variant]=actual
    refuse(doc,scope_values(doc),('hzzq','hzzn','hzzzb','hzzzd','aa'))
    return dict(combinations=64,cases=cases,unknown_inputs_refused=5,presentation_context_not_use_time=True)

@lru_cache(None)
def binding_checks():
    doc=fixture(['r2fu','r2fz','r2ft','r2g3','wh'],'''r zobject[] a.r zperson[] a.r zuse[] d.
q[t[k r2fu[]][k wh[]]].q[t[k r2fz[]][k wh[]]].
q[t[k r2ft[l[a][k zobject[] k zperson[]]]][k zuse[]]].
q[t[k r2g3[l[a][k zobject[] k zperson[]]]][k zuse[]]].''',
        '''r zclaim[d] c.r zprofile[d a a d] c.
d r2fu[] e[b s[k zclaim[v s]]].d r2fs[s d o a p a t d] c[k zprofile[v s v o v p v t]].''')
    cases={}
    for variant in ('baseline','outside_range','claim_false','profile_false','wrong_use_time','wrong_scope','wrong_person','same_person'):
        v=scope_values(doc)
        v.update(zobject=lambda:'object',zperson=lambda:'person',zuse=lambda:'use',
            zclaim=lambda s:s=='scope' and variant!='claim_false',
            zprofile=lambda s,o,p,t:(s,o,p,t)==('scope','object','person','use') and variant!='profile_false')
        if variant=='outside_range':v['hzzn']=lambda *args:False
        if variant=='wrong_use_time':v['zuse']=lambda:'scope'
        if variant=='wrong_scope':v['hzzn']=lambda n,p,s:n=='first' and s=='use'
        if variant=='wrong_person':v['zperson']=lambda:'other'
        if variant=='same_person':v['hzzzd']=lambda s,c:'person'
        want=[variant!='claim_false',variant not in ('claim_false','outside_range','wrong_scope'),
              variant not in ('profile_false','wrong_use_time','wrong_person'),
              variant not in ('profile_false','wrong_use_time','wrong_person','outside_range','wrong_scope')]
        actual=evaluate(doc,v,PEOPLE,SCENES,True);assert actual==want,(variant,actual,want);cases[variant]=actual
    assert cases['outside_range']==[True,False,True,False]
    return dict(cases=cases,old_candidate_accepts_outsider_counterexample=True,scope_and_effect_boundaries_isolated=True)

@lru_cache(None)
def native_checks():
    doc=fixture(['r2fu','r2fz','wh'],'q[t[k r2fu[]][k wh[]]].q[t[k r2fz[]][k wh[]]].',
        '''r zkindrule[a d] c.r zkindform[a d] c.
d hd2[object a] e[b point[k zkindrule[v object v point]]].
d r2fg[object a] e[b point[k zkindform[v object v point]]].''')
    rows={}
    for outsider in (False,True):
        v=previous.source_values(doc,boundary=False)
        v.update(hzzq=lambda:'judgment',hzzn=lambda n,p,s:not outsider and (n,p,s)==('judgment','person','anchor'))
        actual=evaluate(doc,v,previous.previous.PEOPLE,previous.previous.SCENES,True)
        assert actual==[True,not outsider],actual
        rows['outside_range' if outsider else 'baseline']=actual
        print('native '+str(outsider)+' checked',flush=True)
    return dict(cases=rows,native_generic_capacity_cause_and_continuation_executed=True,classification_boundary_explicit=True)

@lru_cache(None)
def presentation_checks():
    doc=fixture(['r2g2'],'q[k r2g2[]].')
    for bits in product((False,True),repeat=5):
        v=previous.presentation_values(doc,bits)
        v['uc']=lambda n,a,d,s:bits[0] and (n,a,json.loads(d.syntax),s)==('third','author',{'kind':'call','symbol':'r2fz','arguments':[]},'now')
        v['rbt']=lambda n,a,t,d,s:bits[1] and (n,a,symbol(t),symbol(d),s)==('third','author','r2g3','h2b','now')
        assert evaluate(doc,v,previous.PRESENTATION_PEOPLE,('now',),True)==[all(bits)],bits
    baseline=dict(v)
    for name in ('uc','rbt'):
        bad=dict(baseline);bad[name]=previous.presentation_values(doc)[name]
        assert evaluate(doc,bad,previous.PRESENTATION_PEOPLE,('now',),True)==[False]
    refuse(doc,baseline,('uc','rbt','rbf','ibbdenotes','ibbclarifies','ue'),previous.PRESENTATION_PEOPLE,('now',))
    return dict(combinations=32,old_assertion_and_depiction_rejected=True,unknown_inputs_refused=6,world_contents_not_executed_by_attribution=True)

def reading():
    old=read(previous.AUDIT)
    paths={INDEX,PARENT,PARENT_BASIS,FULL,BASIS,previous.AUDIT,PRIOR,previous.FIRST,previous.SECOND,previous.INVENTORY}
    return dict(status='third_sentence_shared_person_scope_candidate',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=old['source'],selection=selection_binding(catalog(),[10,52]),
        decision='第三文の比較事例と比喩の利用者を、前二文と同じ人物範囲へ明示的に結ぶ。通しの意味一致判断は未完。',
        interpretation_limits=LIMITS,preceding_reading=previous.AUDIT,revised_statement_indices=[52],
        preserved_reviewed_sentence_characters=247,new_verified_sentence_characters=0,
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-5]==old.document['declarations']
    assert all(new.entries[n]==e for n,e in old.entries.items())
    assert len(new.document['statements'])==len(old.document['statements'])==54
    assert [i for i,(a,b) in enumerate(zip(old.document['statements'],new.document['statements'])) if a!=b]==[52]
    for path in read(INDEX)['works']['kant-1784']['reviews']:
        row=read(path);ids=[s['index'] for s in row['selection']['statements']]
        assert row['selection']==selection_binding(old,ids)==selection_binding(new,ids)
    for p,ids in ((previous.FIRST,[51]),(previous.SECOND,[11,12])):
        row=read(p);validate_hashes(ROOT,row['source_sha256']);assert row['selection']==selection_binding(new,ids)
    validate_hashes(ROOT,read(PRIOR)['source_sha256'])
    assert closure(new.document,['r2fu','r2fs','r2fw','ho2','h3b'])==closure(old.document,['r2fu','r2fs','r2fw','ho2','h3b'])
    for p,body in build().items():assert (ROOT/p).read_text(encoding='utf-8')==body,p
    for p in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/p).read_text(encoding='utf-8'))
        for style in ('compact','full'):
            text=format_graph(doc,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    assert read(AUDIT)==reading()
    return dict(added_definitions=5,added_primitives=0,authored_statements=54,preserved_statements=53,revised_statement_indices=[52],
        preserved_review_selections=12,reviewed_nonblank_characters=2212,preserved_reviewed_sentence_characters=247,roundtrips=True)

def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    for p,body in build().items():write_exact(ROOT/p,body)
    write_exact(ROOT/AUDIT,encoded(reading()))

def build_report():
    results={}
    for name,fn in [('generic',generic_checks),('scope',scope_checks),('binding',binding_checks),('native',native_checks),('presentation',presentation_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    record=reading();paths=set(build())|set(catalog().source_sha256)|set(record['source_sha256'])|set(read(PRIOR)['source_sha256'])|{
        AUDIT,DOC,'scripts/compose_shared_fetters_scope.py','scripts/check_shared_fetters_scope.py','scripts/register_shared_fetters_scope.py','tests/test_shared_fetters_scope.py'}
    paths.update(read(INDEX)['works']['kant-1784']['reviews'])
    return dict(status='shared_fetters_person_scope_candidate_checked',document=FULL,**results,
        alignment=dict(**record['source'],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_covered_characters=0,new_verified_sentence_characters=0,
        preserved_reviewed_sentence_characters=247,verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))
