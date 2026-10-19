"""Verify scoped viewpoint emphasis and its independence from permission truth."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_insistent_framing import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,PARENT,PARENT_BASIS,MEANINGS,PRIMITIVES,LIMITS,parent,build,closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol
from scripts.check_quiet_depiction import attribution_values as prior_attribution
from scripts.check_step_depiction import body_values,BODY_DOMAIN,BODY_TIMES
from scripts.fetch_insistent_framing_evidence import PATH as EVIDENCE,PRIOR as PRIOR_EVIDENCE,validate

INDEX='data/semantic-review-index-v75.json'
REPORT='reports/insistent-framing-v1.json'
AUDIT='data/insistent-framing-reading-v1.json'
DOC='docs/insistent-framing-v1.md'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
SELECTION=[9,35,36,46,47,48,49]
DOMAIN=('node','author','perspective','other')
TIMES=('context','elsewhere')


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def fixture(roots,suffix):
    d=deepcopy(catalog().document);d.update(declarations=closure(d,roots),statements=[])
    return parse(format_graph(d,'compact')+suffix)


@lru_cache(None)
def generic():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+'''
r jnode[] a.r jauthor[] a.r jperspective[] a.r jcontext[] d.r jtruth[d] c.
d jclaim[] e[b s[k jtruth[v s]]].d jother[] e[b s[k jtruth[v s]]].
d jtarget[p a prior d anchor d] c[k jtruth[v prior]].
d jdepiction[p a prior d anchor d] c[k jtruth[v prior]].
r jclaims[a a i[e] d] c.
r jaligns[a a i[e] i[h[a d d] c] i[h[a d d] c] d] c.
r jinsists[a a i[e] a i[h[a d d] c] d] c.
q[k r2ab[k jnode[] k jauthor[] r[k jclaim[]] k jperspective[] r[p jtarget] r[p jdepiction] k jcontext[] p jclaims p jaligns p jinsists]].
''')


KEYS={
 'claim':['node','author','jclaim','context'],
 'alignment':['node','author','jclaim','jtarget','jdepiction','context'],
 'insistence':['node','author','jclaim','perspective','jdepiction','context'],
}


def generic_values(bits=(True,True,True),truth=None,change=None):
    keys=deepcopy(KEYS)
    if change:
        relation,index,value=change;keys[relation][index]=value
    return dict(jnode=lambda:'node',jauthor=lambda:'author',jperspective=lambda:'perspective',jcontext=lambda:'context',
        jtruth=unknown if truth is None else lambda s:truth,
        jclaims=lambda n,a,c,s:bits[0] and (n,a,symbol(c),s)==tuple(keys['claim']),
        jaligns=lambda n,a,c,t,b,s:bits[1] and (n,a,symbol(c),symbol(t),symbol(b),s)==tuple(keys['alignment']),
        jinsists=lambda n,a,c,p,f,s:bits[2] and (n,a,symbol(c),p,symbol(f),s)==tuple(keys['insistence']))


def generic_checks():
    rows=[]
    for bits in product((False,True),repeat=3):
        for truth in (False,True,None):
            actual=evaluate(generic(),generic_values(bits,truth),DOMAIN,TIMES)
            assert actual==[all(bits)],(bits,truth,actual)
            rows.append(dict(claim_alignment_insistence=bits,world_truth=truth,presentation=actual[0]))
    return dict(combinations=rows,world_content_not_executed=True,ordinary_evaluation=True)


def scope_checks():
    rows={}
    alternatives={'node':'other','author':'other','jclaim':'jother','context':'elsewhere',
        'jtarget':'jdepiction','jdepiction':'jtarget','perspective':'author'}
    for relation,keys in KEYS.items():
        for i,value in enumerate(keys):
            actual=evaluate(generic(),generic_values(change=(relation,i,alternatives[value])),DOMAIN,TIMES)
            assert actual==[False],(relation,i,actual);rows[relation+'_'+str(i)]=actual
    v=generic_values()
    v.update(jclaims=lambda n,a,c,s:(n,a,s)==('node','author','context') and symbol(c) in ('jclaim','jother'),
        jaligns=lambda n,a,c,t,b,s:(n,a,symbol(c),symbol(t),symbol(b),s)==('node','author','jother','jtarget','jdepiction','context'),
        jinsists=lambda n,a,c,p,f,s:(n,a,symbol(c),p,symbol(f),s)==('node','author','jother','perspective','jdepiction','context'))
    assert evaluate(generic(),v,DOMAIN,TIMES)==[False]
    d=deepcopy(generic());d['statements'][0]['body']['arguments'][5]=deepcopy(d['statements'][0]['body']['arguments'][4])
    v=generic_values();v.update(jclaims=lambda *args:True,jaligns=lambda *args:True,jinsists=lambda *args:True)
    assert evaluate(d,v,DOMAIN,TIMES)==[False]
    for name in ('jclaims','jaligns','jinsists'):
        v=generic_values();v[name]=unknown
        try:evaluate(generic(),v,DOMAIN,TIMES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,same_node_multiple_claims_not_conflated=True,same_description_rejected=True,
        unknown_inputs_refused=3,viewpoint_not_replaced_by_presenter=True,ordinary_evaluation=True)


def source_values(d,variant='baseline'):
    v=prior_attribution(d);v['db']=lambda:'guards'
    def insists(n,a,c,p,f,s):
        wanted=dict(kind='call',symbol='hztr',arguments=[dict(kind='call',symbol='db',arguments=[])])
        if variant=='other_claim':wanted['symbol']='hztf'
        if variant=='other_group':wanted['arguments'][0]['symbol']='mv'
        viewpoint='author' if variant=='presenter_viewpoint' else 'other' if variant=='other_viewpoint' else 'guards'
        focus='rqzw' if variant=='target_focus' else 'rqz7' if variant=='quiet_focus' else 'rqzx'
        return (variant!='no_insistence' and (n,a,p,s)==('relative' if variant=='other_node' else 'clause',
            'other' if variant=='other_author' else 'author',viewpoint,'elsewhere' if variant=='other_context' else 'context')
            and json.loads(c.syntax)==wanted and symbol(f)==focus)
    v['hzye']=insists
    if variant=='no_claim':v['uc']=lambda *args:False
    if variant=='no_alignment':v['hzyb']=lambda *args:False
    return v


def source_checks():
    d=fixture(['r2ac'],'q[k r2ac[]].');domain=('clause','relative','livestock','previous','author','guards','other');rows={}
    for name in ('baseline','no_claim','no_alignment','no_insistence','other_claim','other_group','other_node','other_author',
            'other_viewpoint','presenter_viewpoint','target_focus','quiet_focus','other_context'):
        actual=evaluate(d,source_values(d,name),domain,TIMES)
        assert actual==[name=='baseline'],(name,actual);rows[name]=actual
    core=parse((ROOT/CORE).read_text(encoding='utf-8'))
    assert evaluate(core,source_values(core),domain,TIMES)==[True]*7
    for name in ('uc','hzyb','hzye'):
        v=source_values(d);v[name]=unknown
        try:evaluate(d,v,domain,TIMES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,seven_excerpt_statements_evaluated=True,world_contents_all_unknown=True,
        unknown_inputs_refused=3,viewpoint_and_focal_depiction_bound=True,ordinary_evaluation=True)


def norm_checks():
    d=fixture(['rqzx','r2ac'],'r jp[] a.r jprior[] d.r janchor[] d.'+
        'q[k rqzx[k jp[] k jprior[] k janchor[]]].q[k r2ac[]].')
    domain=tuple(dict.fromkeys(BODY_DOMAIN+('clause','relative','livestock','previous','author')))
    times=tuple(dict.fromkeys(BODY_TIMES+TIMES));rows=[]
    for flags in ((False,False,False,False),(True,False,False,False),(False,False,False,True),(True,True,True,True)):
        for emphatic in (False,True):
            v=source_values(d,'baseline' if emphatic else 'no_insistence')
            v.update({k:f for k,f in body_values(d,flags).items() if f is not unknown})
            actual=evaluate(d,v,domain,times)
            assert actual==[not any(flags),emphatic],(flags,emphatic,actual)
            rows.append(dict(four_permissions=flags,emphasis=emphatic,world_and_presentation=actual))
    return dict(combinations=rows,actual_permission_definition_evaluated=True,
        emphatic_presentation_does_not_change_world_permission=True,
        permission_absence_does_not_create_emphasis=True,ordinary_evaluation=True)


def reading():
    validate(json.loads((ROOT/EVIDENCE).read_text(encoding='utf-8')))
    old=json.loads((ROOT/'data/quiet-depiction-reading-v1.json').read_text(encoding='utf-8'));clauses=deepcopy(old['clauses'])
    c=next(c for c in clauses if c['id']=='emphasis')
    c.update(status='partial',definitions=['r2ab','r2ac','rqzx'],
        interpretation_ja='同じ複文の身体側の不許容rqzxを、同じ後見人群dbの緩めない姿勢として強く描く。視点と著者を分け、現実の命令・発話・制裁や、全候補への明示的禁止を補わない。原刊から音声の強勢を確定したという判断ではない。')
    paths=(INDEX,PARENT,PARENT_BASIS,FULL,BASIS,ANNOTATIONS,INVENTORY,EVIDENCE,PRIOR_EVIDENCE,
        'data/quiet-depiction-reading-v1.json','reports/step-depiction-v1.json','artifacts/first-cause-reading-v1/page-482.jpg')
    return dict(status='insistent_viewpoint_framing_connected_to_same_permission_depiction',reviewer='assistant_review',
        decision='partial_source_framing_adopted_whole_sentence_not_verified',document=FULL,meaning_basis=BASIS,
        source=old['source'],clauses=clauses,selection=selection_binding(catalog(),SELECTION),
        interpretation_limits=LIMITS,source_review=old['source_review'],
        remaining=['家畜・局面上の落ち着き・歩行とjaの読解を含む複文の通し確認',
            '節間の指示・時点・因果・描写の整合','第二段落末尾と段落全体','二作品全文'],
        whole_sentence_semantically_verified=False,whole_unit_semantically_verified=False,new_verified_sentence_characters=0,
        semantic_equivalence_automatically_proved=False,source_sha256={p:digest((ROOT/p).read_bytes()) for p in paths})


def structure():
    old,new=parent(),catalog()
    assert new.document['declarations'][:-3]==old.document['declarations']
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==50
    assert all(new.entries[n]==e for n,e in old.entries.items())
    assert set(new.entries)-set(old.entries)==set(MEANINGS)|set(PRIMITIVES)
    idx=json.loads((ROOT/INDEX).read_text(encoding='utf-8'));active=load_catalog(ROOT,idx['works']['kant-1784']['meaning_basis'])
    assert selection_binding(active,list(range(49)))==selection_binding(new,list(range(49)))
    for path in idx['works']['kant-1784']['reviews']:
        r=json.loads((ROOT/path).read_text(encoding='utf-8'));ids=[s['index'] for s in r['selection']['statements']]
        assert 49 not in ids and r['selection']==selection_binding(new,ids)
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body
    for path in (FULL,CORE,LIBRARY):
        d=parse((ROOT/path).read_text(encoding='utf-8'))
        for style in ('full','compact'):
            text=format_graph(d,style);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    r=reading();assert r==json.loads((ROOT/AUDIT).read_text(encoding='utf-8'));validate_hashes(ROOT,r['source_sha256'])
    assert ''.join(c['text'] for c in r['clauses'])==r['source']['text']
    assert not [c for c in r['clauses'] if c['status']=='unresolved']
    assert any(c['status']=='partial' for c in r['clauses']) and not r['whole_sentence_semantically_verified']
    return dict(preserved_statements=49,new_statements=[49],new_definitions=2,new_primitives=1,
        preserved_review_selections=11,roundtrips=True,whole_sentence_verified=False)


def prepare():
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('generic',generic_checks),('scope',scope_checks),('source',source_checks),('norms',norm_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    r=reading();unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']==r['source']['unit'])
    span=[1032,1114]
    paths=set(build())|set(catalog().source_sha256)|set(r['source_sha256'])|{AUDIT,DOC,
        'scripts/compose_insistent_framing.py','scripts/check_insistent_framing.py','scripts/register_insistent_framing.py',
        'tests/test_insistent_framing.py','scripts/fetch_insistent_framing_evidence.py',
        'scripts/fetch_recognizable_consequence_evidence.py','scripts/fetch_pastoral_role_evidence.py',
        'scripts/compose_grounded_step.py','scripts/compose_falling_depiction.py','scripts/check_step_depiction.py',
        'scripts/check_quiet_depiction.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'noema/constructed.py','noema/constructed_semantics.py','noema/meaning_catalog.py','noema/semantic_reviews.py','noema/script.py'}
    return dict(status='partial_insistent_framing_of_existing_bodily_permission_depiction',document=FULL,**results,
        alignment=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=span,text=unit['text'][span[0]:span[1]],
            definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=False,new_verified_sentence_characters=0,new_covered_characters=0,
        verified_full_units={'kant-1784':0,'einstein-1905':0},semantic_equivalence_automatically_proved=False,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact,encoded
    prepare();write_exact(ROOT/REPORT,encoded(build_report()))


if __name__=='__main__':main()
