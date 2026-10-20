"""Check institutional attribution, proof-ground scope and nonfactive reports."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_institutional_teaching_grounds import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,parent,build,closure
from scripts.check_motive_causes import unknown,symbol
from scripts.check_pastoral_roles import evaluate
from scripts.check_teaching_discretion import extract

DOC='docs/institutional-teaching-grounds-v1.md'
REPORT='reports/institutional-teaching-grounds-v1.json'
EVIDENCE='data/institutional-teaching-grounds-evidence-v1.json'
PRIOR='reports/clerical-explanation-v1.json'
DOMAIN=('church','judgment','subject','r1','r2','r3','other')
SCENES=('now','other')
EXTRA='''r zchurch[] a.r zjudgment[] a.r zsubject[] a.r zpoint[] d.r zreasons[a] c.
r ztruth[a d] c.r zshown[i b[h[a] f]] c.
d zmessage[subject a] f[j s[b point[k ztruth[v subject v point]]]].
d zalias[subject a] f[k zmessage[v subject]].
d zquestion[subject a] f[j q[b point[k ztruth[v subject v point]]]].'''
ARGS='k zchurch[] k zjudgment[] k zsubject[] r[p zmessage]'
TEACH='k r4r[k zchurch[] r[p zmessage]]'
GROUNDS='k r4s[k zchurch[] k zjudgment[] r[p zmessage] p zreasons]'


def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(query=None):
    doc=deepcopy(catalog().document);doc['statements']=[]
    if query is None:query='q[k r4n['+ARGS+' k zpoint[]]].q[k r4o[k zchurch[] k zsubject[] r[p zmessage] k zpoint[]]].q[k r4q['+ARGS+' p zreasons k zpoint[]]].'
    return parse(format_graph(doc,'compact')+EXTRA+query)


def model(doc,bits=(True,)*4,variant='baseline',members=('r1','r2'),used=('r1','r2'),epistemic=('r1','r2')):
    attribution,about,examined,teaching=bits
    v={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    def match(actual,expected,category,fields):
        expected=list(expected)
        for i,field in enumerate(fields):
            if variant==category+'_'+field:expected[i]='other'
        return tuple(actual)==tuple(expected)
    v.update(zchurch=lambda:'church',zjudgment=lambda:'judgment',zsubject=lambda:'subject',zpoint=lambda:'now',zreasons=lambda r:r in members)
    v['h247u']=lambda org,j,at:attribution and match((org,j,at),('church','judgment','now'),'attribution',('church','judgment','point'))
    v['fb']=lambda j,s,at:about and match((j,s,at),('judgment','subject','now'),'about',('judgment','subject','point'))
    v['hzv']=lambda j,s,m,at:examined and match((j,s,at),('judgment','subject','now'),'content',('judgment','subject','point')) and symbol(m)==(
        'zalias' if variant=='alias' else 'zquestion' if variant=='force' else 'zmessage') and m.rank==0
    v['h247v']=lambda org,j,at:teaching and match((org,j,at),('church','judgment','now'),'teaching',('church','judgment','point'))
    v['fc']=lambda j,r,at:match((j,at),('judgment','now'),'use',('judgment','point')) and r in used
    v['h247w']=lambda j,r,at:match((j,at),('judgment','now'),'epistemic',('judgment','point')) and r in epistemic
    return v


def run(doc,v):return evaluate(doc,v,DOMAIN,SCENES,True)


@lru_cache(None)
def teaching_checks():
    doc=fixture();rows=[]
    for bits in product((False,True),repeat=4):
        result=run(doc,model(doc,bits));assert result==[all(bits)]*3,(bits,result)
        rows.append(dict(bits=list(bits),results=result))
    return dict(truth_table=rows,native_definitions=True,no_individual_judgment_or_actual_lecture_required=True)


@lru_cache(None)
def scope_checks():
    doc=fixture();rows=[]
    cases=[((),('r1','r2'),('r1','r2'),False),
        (('r1','r2'),('r1','r2'),('r1','r2'),True),
        (('r1','r2'),('r1','r2','r3'),('r1','r2'),True),
        (('r1','r2'),('r1','r2'),('r1','r2','r3'),True),
        (('r1','r2'),('r1','r2','r3'),('r1','r2','r3'),False),
        (('r1','r2','r3'),('r1','r2','r3'),('r1','r2'),False),
        (('r1',),('r1','r2'),('r1',),True),
        (('r1',),('r1','r2'),('r1','r2'),False)]
    for members,used,epistemic,expected in cases:
        result=run(doc,model(doc,members=members,used=used,epistemic=epistemic))
        assert result==[True,True,expected],(members,used,epistemic,result)
        rows.append(dict(members=members,used=used,epistemic=epistemic,result=result))
    # All 64 independent classifications of use and epistemic role over 3 reasons.
    for bits in product((False,True),repeat=6):
        used=tuple(r for r,b in zip(('r1','r2','r3'),bits[:3]) if b)
        ep=tuple(r for r,b in zip(('r1','r2','r3'),bits[3:]) if b)
        result=run(doc,model(doc,used=used,epistemic=ep))
        assert result==[True,True,set(used)&set(ep)=={'r1','r2'}],(bits,result)
    return dict(scope_cases=rows,independent_use_and_epistemic_classifications=64,unused_arguments_excluded=True,
        practical_motives_not_forced_into_proof_ground_inventory=True,objective_support_not_executed=True)


@lru_cache(None)
def reference_checks():
    doc=fixture();rows={}
    for category,fields in [('attribution',('church','judgment','point')),('about',('judgment','subject','point')),
        ('content',('judgment','subject','point')),('teaching',('church','judgment','point')),
        ('use',('judgment','point')),('epistemic',('judgment','point'))]:
        for field in fields:
            variant=category+'_'+field;result=run(doc,model(doc,variant=variant))
            expected=[True,True,False] if category in ('use','epistemic') else [False]*3
            assert result==expected,(variant,result);rows[variant]=result
    for variant in ('alias','force'):
        result=run(doc,model(doc,variant=variant));assert result==[False]*3;rows[variant]=result
    for name in ('h247u','h247v','h247w','fb','hzv','fc'):
        v=model(doc);v[name]=unknown
        try:run(doc,v)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,unknown_relations_refused=True,same_message_not_replaced_by_alias_or_question=True)


@lru_cache(None)
def report_checks():
    quote='q[k zshown[r b['+TEACH+']]].q[k zshown[r b['+GROUNDS+']]].'
    truth=''.join('q[t[o[c['+term+'][k zsubject[]]]][k zpoint[]]].' for term in (TEACH,GROUNDS))
    doc=fixture(quote+truth);only=deepcopy(doc);only['statements']=doc['statements'][:2]
    seen=[]
    v=model(doc)
    def shown(code):
        seen.append((code.rank,json.loads(code.syntax)))
        return code.rank==1
    v['zshown']=shown
    for n in ('h247u','h247v','h247w','fb','hzv','fc','ztruth'):v[n]=unknown
    assert run(only,v)==[True,True]
    assert [node['symbol'] for rank,node in seen]==['r4r','r4s']
    rows=[]
    for teaching,used in product((False,True),repeat=2):
        v=model(doc,bits=(True,True,True,teaching),used=('r1','r2') if used else ())
        v['zshown']=lambda code:True
        result=run(doc,v);assert result==[True,True,teaching,teaching and used],(teaching,used,result)
        rows.append(dict(teaching=teaching,grounds_used=used,result=result))
    v=model(doc);v['zshown']=lambda code:False
    assert run(doc,v)==[False,False,True,True]
    # Evaluate exact quoted report bodies, not just parallel unquoted functions.
    quoted_truth=''.join('q[t[o[c[s[r b['+term+']]][k zsubject[]]]][k zpoint[]]].' for term in (TEACH,GROUNDS))
    exact=fixture(quoted_truth)
    assert run(exact,model(exact))==[True,True]
    for name in ('h247u','h247v','h247w','fb','hzv','fc'):
        v=model(exact);v[name]=unknown
        try:run(exact,v)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(cases=rows,rank_one_closed_report_descriptions=True,quotation_does_not_execute_reported_facts=True,
        exact_quoted_bodies_evaluated=True,inner_truth_not_executed=True,reported_facts_do_not_create_presentations=True,
        presentation_callback_is_diagnostic_not_source_sentence=True)


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    doc=new.document
    for notation in ('compact','full'):
        t=format_graph(doc,notation);assert parse(t)==parse(transcribe(t,alphabet='v2'))==doc
    evidence=read(EVIDENCE);raw=(ROOT/evidence['path']).read_bytes()
    assert digest(raw)==evidence['sha256'] and evidence['excerpt'] in extract(raw.decode(evidence['encoding']))
    validate_hashes(ROOT,read(PRIOR)['source_sha256'])
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        no_source_sentence_added=True,lexical_evidence_pinned=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    result={name:fn() for name,fn in [('teaching',teaching_checks),('scope',scope_checks),('references',reference_checks),
        ('reports',report_checks),('structure',structure_checks)]}
    paths=set(build())|set(catalog().source_sha256)|{DOC,EVIDENCE,read(EVIDENCE)['path'],PRIOR,
        'scripts/compose_institutional_teaching_grounds.py','scripts/check_institutional_teaching_grounds.py',
        'tests/test_institutional_teaching_grounds.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py',
        'scripts/check_teaching_discretion.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py',
        'scripts/compose_confessional_teaching.py'}
    return dict(status='institutional_teaching_and_exhaustive_used_justificatory_grounds',document=LIBRARY,**result,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
