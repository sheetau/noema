"""Check actual discernment, fallible belief, fixed names and hypothetical scope."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,validate_hashes
from noema.script import transcribe
from scripts.compose_perceived_doctrinal_conflict import ROOT,LIBRARY,BASIS,PRIMITIVES,MEANINGS,PREMISE,parent,build
from scripts.check_latent_truth_compatibility import fixture as old_fixture,model as old_model,DOMAIN,SCENES,read
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown,symbol

DOC='docs/perceived-doctrinal-conflict-v1.md'
REPORT='reports/perceived-doctrinal-conflict-v1.json'
EVIDENCE='data/perceived-doctrinal-conflict-evidence-v1.json'
PRIORS=tuple('reports/'+n+'-v1.json' for n in ('clerical-practical-benefit','latent-truth-compatibility','personal-conviction'))
NAMES='r[k zperson[]] r[k zbundle[]] r[k zreligion[]] r[k zref[]]'
VALUES='k zperson[] k zbundle[] k zreligion[] k zref[]'
CLASH='k r43m[r[k zbundle[]] r[k zreligion[]] r[k zref[]]]'
FOUND='k r43o['+NAMES+']'
PREM='k r43q['+NAMES+']'
BELIEF='k r43p['+VALUES+' '+NAMES+' k zactual[]]'
CONDITION='k r43r['+VALUES+' '+NAMES+' p zconsequent k zactual[]]'
MORE='r zclashrecord[i[e]] c.r zfoundrecord[i[e]] c.r zpremiserecord['+PREMISE+'] c.r zconsequent[d] c.r zalias[] a.'


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


@lru_cache(None)
def fixture(query=None,records=True):
    doc=deepcopy(old_fixture(''));seen={d['name'] for d in doc['declarations']}
    doc['declarations'] += [d for d in catalog().document['declarations'] if d['name'] not in seen]
    saved='q[k zclashrecord['+CLASH+']].q[k zfoundrecord['+FOUND+']].q[k zpremiserecord['+PREM+']].' if records else ''
    if query is None:query='q[t[k r43l[k zbundle[] k zreligion[] k zref[]]][k zactual[]]].q[t[s['+FOUND+']][k zactual[]]].q['+BELIEF+'].'
    return parse(format_graph(doc,'compact')+MORE+saved+query)


def model(doc,strict=(),recognized=(),beliefs=('actual',),selected=('p1','p2'),consequences=('p1','p2'),variant='baseline'):
    v,observed=old_model(doc,strict=strict);observed.update(clash=None,found=None,premise=None,recognitions=[],beliefs=[],hypotheticals=[])
    def save(key,code):observed[key]=code;return code.rank==0
    v.update(zclashrecord=lambda c:save('clash',c),zfoundrecord=lambda c:save('found',c),zpremiserecord=lambda c:save('premise',c),
        zconsequent=lambda at:at in consequences,zalias=lambda:'person')
    def recognize(person,obj,criterion,code,ref,at):
        observed['recognitions'].append((person,obj,criterion,code.syntax,ref,at))
        wanted=('person','bundle','religion','reference')
        for i,name in enumerate(('person','object','criterion','reference')):
            if variant=='recognition_'+name:wanted=tuple('other' if j==i else x for j,x in enumerate(wanted))
        return (person,obj,criterion,ref)==wanted and code.rank==0 and symbol(code)==('r43n' if variant=='recognition_code' else 'r43l') and at in recognized
    v['h252z']=recognize
    def belief(person,code,at):
        observed['beliefs'].append((person,code.syntax,at))
        expected=observed['clash'] if variant=='bare_conflict_belief' else observed['found']
        return person==('other' if variant=='other_believer' else 'person') and code.rank==0 and code.syntax==expected.syntax and at in beliefs
    v['h233c']=belief
    def chosen(person,code,actual,at):
        observed['hypotheticals'].append((person,code.syntax,actual,at))
        return (person,actual)==('person','other' if variant=='other_evaluation' else 'actual') and code.rank==0 and code.syntax==observed['premise'].syntax and at in selected
    v['hzko']=chosen
    return v,observed


def run(doc,pair):return evaluate(doc,pair[0],DOMAIN,SCENES,True)


@lru_cache(None)
def native_checks():
    doc=fixture();rows=[]
    for actual,recognized,believed in product((False,True),repeat=3):
        pair=model(doc,strict=('actual',) if actual else (),recognized=('actual',) if recognized else (),beliefs=('actual',) if believed else ())
        result=run(doc,pair);expected=[True,True,True,actual,actual and recognized,believed]
        assert result==expected,(actual,recognized,believed,result)
        rows.append(dict(conflict=actual,recognition=recognized,belief=believed,result=result[3:]))
    # The same positive containment and fixed normative code are evaluated,
    # independent of whether any contained doctrine happens to be true.
    query='q[t[k r43l[k zbundle[] k zreligion[] k zref[]]][k zactual[]]].'
    d=fixture(query);absent=model(d,strict=('actual',))
    absent[0]['h252f']=lambda *args:False
    # The whole first rule can still conflict; remove its clash to isolate part.
    old=absent[0]['h252n']
    absent[0]['h252n']=lambda c,n,r,p:symbol(c)=='zpartbody' and old(c,n,r,p)
    assert run(d,absent)==[True,True,True,False]
    present=model(d,strict=('actual',));old=present[0]['h252n']
    present[0]['h252n']=lambda c,n,r,p:symbol(c)=='zpartbody' and old(c,n,r,p)
    assert run(d,present)==[True,True,True,True]
    for variant in ('recognition_person','recognition_object','recognition_criterion','recognition_code','recognition_reference','bare_conflict_belief','other_believer'):
        result=run(doc,model(doc,strict=('actual',),recognized=('actual',),variant=variant))
        assert result[3:]==([True,False,True] if variant.startswith('recognition_') else [True,True,False]),(variant,result)
    for name in ('h252z','h252n','h6t'):
        pair=model(doc,strict=('actual',),recognized=('actual',));pair[0][name]=unknown
        try:run(doc,pair)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(actual_discernment_belief_table=rows,native_containment_and_content_clash=True,
        false_belief_allowed=True,belief_in_bare_conflict_not_self_discernment=True,recognition_without_conflict_not_actual_discovery=True,
        unknown_actual_membership_clash_or_recognition_refused=True)


@lru_cache(None)
def nonfactive_checks():
    d=fixture('q['+BELIEF+'].');pair=model(d)
    for name in pair[0]:
        if name not in ('zclashrecord','zfoundrecord','zpremiserecord','zperson','zbundle','zreligion','zref','zactual','h233c'):
            pair[0][name]=unknown
    assert run(d,pair)==[True,True,True,True]
    assert pair[1]['recognitions']==[] and pair[1]['clashes']==[] and pair[1]['providers']==[]
    # Quoting the complete belief claim itself also refrains from running it.
    q=fixture('q[k zshown[r b['+BELIEF+']]].',False)
    v={decl['name']:unknown for decl in q['declarations'] if decl['kind']=='primitive'};seen=[]
    def shown(code):seen.append((code.rank,json.loads(code.syntax)));return code.rank==1
    v['zshown']=shown
    assert run(q,(v,{}))==[True] and seen[0][1]['symbol']=='r43p'
    return dict(belief_does_not_evaluate_conflict_membership_recognition_or_content_providers=True,
        closed_rank_one_belief_quotation=True,quotation_does_not_execute_belief=True)


@lru_cache(None)
def binding_checks():
    rows=[]
    for position,(name,sort) in enumerate((('person','a'),('bundle','a'),('religion','a'),('ref','d'))):
        wrong=NAMES.replace('r[k z'+name+'[]]','r[k z'+('actual' if sort=='d' else 'outsider')+'[]]')
        q='q[k r43p['+VALUES+' '+wrong+' k zactual[]]].q[k r43r['+VALUES+' '+wrong+' p zconsequent k zactual[]]].'
        d=fixture(q);pair=model(d,beliefs=('actual','p1','p2'))
        # Even permissive belief/selection/consequent inputs cannot repair the
        # actual name-to-individual equality requirements.
        pair[0].update(h233c=lambda *a:True,hzko=lambda *a:True,zconsequent=lambda *a:True)
        assert run(d,pair)==[True,True,True,False,False],position
        rows.append(position)
    alias=NAMES.replace('r[k zperson[]]','r[k zalias[]]')
    d=fixture('q[k r43p['+VALUES+' '+alias+' k zactual[]]].');pair=model(d)
    observed=[]
    def belief(p,c,at):observed.append(c.syntax);return p=='person' and at=='actual'
    pair[0]['h233c']=belief
    assert run(d,pair)==[True,True,True,True] and observed[-1]!=pair[1]['found'].syntax
    return dict(independent_name_identity_checks=rows,alias_may_denote_same_person=True,distinct_code_not_automatically_identical=True)


@lru_cache(None)
def hypothetical_checks():
    d=fixture('q['+CONDITION+'].');rows=[]
    for bits in product((False,True),repeat=6):
        selected=tuple(p for p,b in zip(('p1','p2'),bits[:2]) if b)
        beliefs=tuple(p for p,b in zip(('p1','p2'),bits[2:4]) if b)
        consequences=tuple(p for p,b in zip(('p1','p2'),bits[4:]) if b)
        pair=model(d,selected=selected,beliefs=beliefs,consequences=consequences)
        actual=run(d,pair);want=bool(selected) and set(selected)<=set(beliefs)&set(consequences)
        assert actual==[True,True,True,want],(bits,actual)
        assert not pair[1]['recognitions'] and not pair[1]['clashes']
        rows.append([*bits,actual[-1]])
    for actual_belief in (False,True):
        pair=model(d,beliefs=('p1','p2')+(('actual',) if actual_belief else ()))
        assert run(d,pair)==[True,True,True,True]
    for name in ('h233c','hzko','zconsequent'):
        pair=model(d,beliefs=('p1','p2'));pair[0][name]=unknown
        try:run(d,pair)
        except ValueError as error:assert 'Unknown' in str(error),str(error)
        else:raise AssertionError(name)
    return dict(two_candidate_selection_belief_consequence_table=rows,nonempty_all_candidates=True,
        actual_belief_not_required_false=True,actual_consequent_not_required=True,actual_conflict_not_required=True,unknown_refused=True)


@lru_cache(None)
def structure_checks():
    old,new=parent(),catalog()
    for n,e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration']==old.entries[n]['declaration'] and e['meaning_ja']==old.entries[n]['meaning_ja'],n
    for path,body in build().items():assert (ROOT/path).read_text(encoding='utf-8')==body,path
    for notation in ('compact','full'):
        text=format_graph(new.document,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==new.document
    for prior in PRIORS:validate_hashes(ROOT,read(prior)['source_sha256'])
    evidence=read(EVIDENCE)
    for p in evidence['pages']:assert digest((ROOT/p['path']).read_bytes())==p['sha256']
    return dict(unchanged_imports=True,roundtrips=True,new_definitions=len(MEANINGS),new_primitives=len(PRIMITIVES),
        no_source_sentence_added=True,primary_comparison_evidence_pinned=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path,body in build().items():write_exact(ROOT/path,body)


def build_report():
    results={}
    for name,fn in [('native',native_checks),('nonfactive',nonfactive_checks),('bindings',binding_checks),('hypothetical',hypothetical_checks),('structure',structure_checks)]:
        results[name]=fn();print(name+' checked',flush=True)
    paths=set(build())|set(catalog().source_sha256)|set(PRIORS)|{DOC,EVIDENCE,*[p['path'] for p in read(EVIDENCE)['pages']],
        'scripts/compose_perceived_doctrinal_conflict.py','scripts/check_perceived_doctrinal_conflict.py','tests/test_perceived_doctrinal_conflict.py',
        'scripts/check_latent_truth_compatibility.py','scripts/check_doctrinal_statutes.py','scripts/check_pastoral_roles.py',
        'scripts/check_motive_causes.py','scripts/compose_grounded_step.py','scripts/compose_qualitative_influence.py'}
    return dict(status='believed_self_discovery_of_fixed_doctrinal_conflict',document=LIBRARY,**results,
        whole_sentence_semantically_verified=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
