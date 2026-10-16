"""Check causal/modal scope without equating an excluded cause with an impossible state."""
import argparse,hashlib,json,subprocess,sys
from copy import deepcopy
from functools import lru_cache
from itertools import product
from noema.grammar import parse,format_graph
from noema.finite_semantics import Content,evaluate_document
from noema.diagnostic_short_circuit import lower
from noema.extraction import extract_document
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.compose_causal_outcome_contrast import ROOT,PARENT,FULL,CORE,LIBRARY,MEANINGS,build
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded

REPORT=ROOT/'reports/causal-outcome-contrast-v1.json'
DOMAIN=('act1','act2','otheract','target','othergroup')
SCENES=('now','one','two','outside')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model,*,short=True,memoize=True):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'};model={n:model[n] for n in names}
    if short:doc,model=lower(doc,model)
    return [x['value'] for x in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=model,
        max_steps=3_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


@lru_cache(None)
def fixture(path=LIBRARY,variant='normal'):
    extra='''r jcotarget[] a.r jcoanchor[] d.r jcokind[a] c.r jcoprospects[a d d] c.
r jcooccurs[a d] c.r jcoproduces[a a i[h[a] e] d] c.
r jcoleft[a] e.r jcoright[a] e.r jcoalias[a] e.'''
    left,right=('jcoright','jcoleft') if variant=='swapped' else ('jcoleft','jcoleft' if variant=='same_effect' else 'jcoright')
    source=path!=LIBRARY
    rel='p dg p g3' if source else 'p jcooccurs p jcoproduces'
    head='k jcotarget[] p jcokind '
    tail=' k jcoanchor[] p jcoprospects '+rel
    pair=head+'r[p '+left+'] r[p '+right+']'
    queries='q[k rqc['+head+'r[p '+left+']'+tail+']].q[k rqd['+head+'r[p '+right+']'+tail+']].'
    queries+='q[k rqe['+pair+tail+']].q[t[k jcoleft[k jcotarget[]]][k jcoanchor[]]].'
    if source:queries+='q[k hzhk['+pair+' k jcoanchor[] p jcoprospects]].'
    return candidate(text(path),extra+queries)


def model(doc,bits=(True,True,True,False,False,False),variant='baseline'):
    oa,ca,ta,ob,cb,tb=bits
    bad=variant in ('second_activity','second_outcome')
    separate=variant=='other_activity'
    def kind(activity):
        if variant=='unknown_kind':raise ValueError('unknown activity kind')
        return variant!='empty_kind' and activity in ('act1','act2')
    def prospects(activity,anchor,scene):
        if variant=='unknown_prospects':raise ValueError('unknown prospects')
        return variant!='empty_candidates' and activity in ('act1','act2','otheract') and anchor==('outside' if variant=='wrong_anchor' else 'now') and scene in ('one','two')
    def occurs(activity,scene):
        if bad or separate:
            badact='act2' if variant=='second_activity' else 'otheract' if separate else 'act1'
            if (activity,scene)==(badact,'two'):return True
        return activity=='act1' and ((oa and scene==('now' if variant in ('split_occurrence','actual_only') else 'one')) or ob and scene=='two')
    def produces(activity,target,description,scene):
        if variant=='unknown_cause':raise ValueError('unknown cause')
        symbol=json.loads(description.syntax).get('symbol')
        if symbol=='jcoleft':
            return ca and variant!='cooccurrence_only' and (activity,target,scene)==(
                'act2' if variant=='wrong_causal_activity' else 'act1',
                'othergroup' if variant=='wrong_target' else 'target',
                'two' if variant=='split_cause' else 'now' if variant=='actual_only' else 'one') and variant!='wrong_description'
        if symbol=='jcoalias':return variant=='wrong_description' and (activity,target,scene)==('act1','target','one')
        if symbol=='jcoright':
            if bad or separate:
                badact='act2' if variant=='second_activity' else 'otheract' if separate else 'act1'
                return (activity,target,scene)==(badact,'target','two')
            return (cb or variant=='right_cause_no_occurrence') and (activity,target,scene)==('act1','target','two')
        return False
    def effect(target,right=False):
        if variant=='unknown_effect':raise ValueError('unknown result interpretation')
        if target!='target':return Content(SCENES,(False,)*len(SCENES))
        if right:
            values=(False,variant=='same_truth_different_description',tb or bad or separate or variant in ('right_true_only','right_cause_no_occurrence'),False)
        else:values=(ta if variant=='actual_only' else False,ta if variant!='actual_only' else False,False,False)
        return Content(SCENES,values)
    result=guarded(doc);result.update(jcotarget=lambda:'target',jcoanchor=lambda:'now',jcokind=kind,jcoprospects=prospects,
        jcooccurs=occurs,jcoproduces=produces,dg=occurs,g3=produces,
        jcoleft=lambda target:effect(target),jcoright=lambda target:effect(target,True),jcoalias=lambda target:effect(target))
    return result


@lru_cache(None)
def checks():
    rows={};count=0
    for path in (LIBRARY,CORE):
        doc=fixture(path)
        for bits in product((False,True),repeat=6):
            first=all(bits[:3]);excluded=not all(bits[3:]);wanted=[first,excluded,first and excluded,False]
            if path!=LIBRARY:wanted.append(first and excluded)
            actual=evaluate(doc,model(doc,bits));assert actual==wanted,(path,bits,actual);count+=1
    cases={n:[False,True,False,False] for n in ('empty_kind','empty_candidates','wrong_anchor','cooccurrence_only',
        'wrong_causal_activity','wrong_target','wrong_description','split_cause','split_occurrence')}
    cases.update(baseline=[True,True,True,False],second_activity=[True,False,False,False],second_outcome=[True,False,False,False],
        other_activity=[True,True,True,False],right_true_only=[True,True,True,False],right_cause_no_occurrence=[True,True,True,False],
        same_truth_different_description=[True,True,True,False],actual_only=[False,True,False,True])
    for path in (LIBRARY,CORE,FULL):
        rows[path]={};doc=fixture(path)
        for name,wanted in cases.items():
            expected=wanted+([wanted[2]] if path!=LIBRARY else [])
            actual=evaluate(doc,model(doc,variant=name));assert actual==expected,(path,name,actual);rows[path][name]=actual
        for variant,wanted in (('same_effect',[True,False,False,False]),('swapped',[False,False,False,False])):
            doc2=fixture(path,variant);expected=wanted+([wanted[2]] if path!=LIBRARY else [])
            actual=evaluate(doc2,model(doc2));assert actual==expected,(path,variant,actual);rows[path][variant]=actual
    refused=[];doc=fixture(CORE)
    for name in ('unknown_kind','unknown_prospects','unknown_cause','unknown_effect'):
        try:evaluate(doc,model(doc,variant=name))
        except ValueError as exc:assert 'unknown' in str(exc);refused.append(name)
        else:raise AssertionError(name)
    for variant in ('baseline','second_activity','right_true_only'):
        assert evaluate(doc,model(doc,variant=variant),short=False,memoize=False)==rows[CORE][variant]
    return dict(truth_cases=count,contrasts=rows,unknown_inputs_refused=refused,unlowered_uncached_examples=3,
        actual_rfk_executed=True,all_activity_candidates_quantified=True,
        nonphysics_example='a reset can clear a pending task without repairing a damaged component; repair by a different process remains expressible')


def structure():
    old=parse(text(PARENT));doc=parse(text(FULL));assert doc['statements']==old['statements']
    assert doc['declarations'][:len(old['declarations'])]==old['declarations']
    added=doc['declarations'][len(old['declarations']):]
    assert all(d['kind']=='definition' for d in added) and {d['name'] for d in added}==set(MEANINGS)
    assert extract_document(doc,roots=['hzhk'],statement_indices=[]).document==parse(text(CORE))
    return dict(new_definitions=len(added),new_primitives=0,new_assertions=0,previous_15_statements_unchanged=True)


def alignment():
    units=json.loads(text('artifacts/written-units-v1/kant-1784.json'))['units'];unit=next(u for u in units if u['id']=='kant-1784:u0011')
    assert hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()==unit['text_sha256']
    segments=[]
    for phrase in ('vielleicht wohl','aber niemals','zu Stande kommen'):
        start=unit['text'].index(phrase)
        segments.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],start=start,end=start+len(phrase),source=phrase,
            definitions=['rqc','rqd','rqe','hzhk'],status='partial_causal_possibility_contrast',full_semantic_equivalence=False,
            remaining=['epistemic vielleicht and pragmatic wohl','future range and completeness of prospects','aber discourse presentation',
                'revolution, personal despotism, gain/control-motivated oppression and true reform of thought',
                'new and old prejudices and whole-paragraph attribution']))
    return dict(segments=segments)


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    for p in (FULL,CORE,LIBRARY):
        doc=parse(text(p));basis=next(json.loads(x) for q,x in files.items() if q.endswith('-basis-v1.json') and json.loads(x)['document']==p)
        audits[p]={k:v for k,v in audit_basis(doc,basis).items() if k!='definition_dependencies'}
        for notation in ('full','compact'):
            formatted=format_graph(doc,notation);assert parse(formatted)==parse(transcribe(formatted,alphabet='v2'))==doc
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==doc
    paths=set(files)|{PARENT,'data/kant-independent-profiles-basis-v1.json','artifacts/written-units-v1/kant-1784.json',
        'tests/test_causal_outcome_contrast.py','docs/causal-outcome-contrast-v1.md'}
    paths.update('scripts/'+n+'.py' for n in ('compose_causal_outcome_contrast','check_causal_outcome_contrast','compose_origin_clock',
        'compose_limits','compose_situated_criticism','check_described_appraisals','check_rod_setup'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script',
        'diagnostic_short_circuit','constructed_discourse'))
    return dict(status='partial_causal_outcome_contrast_with_unfilled_source_concepts',document=FULL,basis_audits=audits,
        finite=checks(),structure=structure(),alignment=alignment(),roundtrips=True,cli_parse=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Possible and excluded causal results checked without global impossibility',flush=True)


if __name__=='__main__':main()
