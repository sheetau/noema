"""Check exact task requirements, reported derivations and unachieved goals."""
import argparse
import hashlib
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_calculation_discourse import symbol
from scripts.compose_theory_transition import ROOT, composed, generic_composed

REPORT=ROOT/'reports/theory-transition-v1.json'
DOMAIN=('author','task','a','b','c','proofa','proofb','field','examplea','exampleb','framework','scope','other')


def install_descriptions(doc,name,targets):
    prefix='n:'+''.join('r '+t+'[] e.' for t in targets)
    prefix+='r jz[a i[e] i[e] i[e]] i[e].'
    prefix+='d '+name+'[item a] i[e][k jz[v item '+' '.join('r[k '+t+'[]]' for t in targets)+']].'
    definitions=parse(prefix)['declarations'][-2:]
    index=next(i for i,d in enumerate(doc['declarations']) if d['name']==name)
    doc['declarations'][index:index+1]=definitions
    return doc


def selected_description(label):
    return lambda item,a,b,c:c if item not in ('a','b') or (label=='wrong_description' and item=='a') else a if item=='a' else b


def generic_checks():
    prefix=generic_composed()[0]+'''
r jk[] e.r jl[] e.r jm[] e.
r ja[] a.r jb[] a.r jc[] d.r jd[a] c.r je[a a a d] c.r jf[a] i[e].
r jg[a i[e] d] c.r jh[] a.r ji[a i[e] a d] c.r jj[a a d] c.
r jn[] d.
q[k s5o[k ja[] k jb[] k jc[] p jd p je]].
q[k s5p[k ja[] k jc[] p jd p jf p jg]].
q[t[k s5q[k ja[] k jh[] p jd p jf p ji p jj]][k jc[]]].
q[t[k s5q[k ja[] k jh[] p jd p jf p ji p jj]][k jn[]]].
'''
    doc=install_descriptions(parse(prefix),'jf',('jk','jl','jm'));rows={}
    for label in ('baseline','extra_required','extra_selected','empty_selected','wrong_task','wrong_need_actor',
        'wrong_need_stage','missing_derivation','wrong_derived_actor','wrong_derived_stage','wrong_description',
        'missing_application','unshown_application','wrong_field','wrong_showing_actor','different_example_shown',
        'same_example_for_both','current_goal_achieved'):
        model=guarded(doc)
        for name,value in {'ja':'author','jb':'task','jc':'text','jh':'field','jn':'motion'}.items():model[name]=lambda value=value:value
        selected=set() if label=='empty_selected' else {'a','b','c'} if label=='extra_selected' else {'a','b'}
        needed={'a','b','c'} if label=='extra_required' else {'a','b'}
        model['jd']=lambda item:item in selected;model['jz']=selected_description(label)
        model['je']=lambda who,task,item,stage:item in needed and (who,task,stage)==(
            'other' if label=='wrong_need_actor' else 'author','other' if label=='wrong_task' else 'task','other' if label=='wrong_need_stage' else 'text')
        model['jg']=lambda who,content,stage:(who,stage)==('other' if label=='wrong_derived_actor' else 'author','other' if label=='wrong_derived_stage' else 'text') and symbol(content) in ({'jk'} if label=='missing_derivation' else {'jk','jl'})
        def application(example,content,field,scene):
            pairs={('examplea','jk'),('examplea' if label=='same_example_for_both' else 'exampleb','jl')}
            if label=='missing_application':pairs.discard(('exampleb','jl'))
            return (example,symbol(content)) in pairs and field==('other' if label=='wrong_field' else 'field') and scene in ({'motion','text'} if label=='current_goal_achieved' else {'motion'})
        def shown(who,example,scene):
            choices={'exampleb'} if label=='different_example_shown' else {'examplea'} if label=='unshown_application' else {'examplea','exampleb'}
            return who==('other' if label=='wrong_showing_actor' else 'author') and example in choices and scene in ({'motion','text'} if label=='current_goal_achieved' else {'motion'})
        model.update(ji=application,jj=shown)
        exact=label not in ('extra_required','extra_selected','empty_selected','wrong_task','wrong_need_actor','wrong_need_stage')
        completed=label not in ('extra_selected','empty_selected','missing_derivation','wrong_derived_actor','wrong_derived_stage','wrong_description')
        future=label not in ('extra_selected','empty_selected','wrong_description','missing_application','unshown_application','wrong_field','wrong_showing_actor','different_example_shown')
        actual=values(doc,model,DOMAIN);expected=[exact,completed,label=='current_goal_achieved',future]
        if actual!=expected:raise ValueError('Task-relative summary differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'column_order':['exact_required_scope','all_selected_derivations','current_application_goal','later_application_goal'],
        'claim_descriptions_not_evaluated_as_truth':True,'same_example_must_be_application_and_shown':True,
        'necessary_for_task_not_logical_necessity':True}


def source_checks():
    text=composed()[0];query='r jv[] d.q[t[k s5r[]][k ri[]]].q[t[k s5s[]][k ri[]]].q[t[k s5s[]][k jv[]]].'
    doc=install_descriptions(candidate(text,query),'zm6',('sso','s3m','s3w'));rows={}
    for label in ('baseline','extra_required','missing_proof','wrong_proof_content','wrong_proof_scope','future_proof_only',
        'wrong_framework','first_principle_missing','second_principle_missing','wrong_description','missing_application',
        'same_example_not_shown','wrong_application_field','current_goal_achieved'):
        model=guarded(doc)
        for name,value in {'rd':'author','ri':'text','zm7':'task','znb':'scope','znc':'framework','zne':'field','jv':'motion'}.items():model[name]=lambda value=value:value
        model.update(zm5=lambda item:item in ('a','b'),jz=selected_description(label),
            zna=lambda who,task,item,stage:(who,task,stage)==('author','task','text') and item in (('a','b','c') if label=='extra_required' else ('a','b')),
            znd=lambda framework,item,stage:(framework,stage)==('other' if label=='wrong_framework' else 'framework','text') and item in ('a','b'))
        def proof(proof,who,content,stage,scope):
            allowed={('proofa','sso'),('proofb','s3w' if label=='wrong_proof_content' else 's3m')}
            if label=='missing_proof':allowed.discard(('proofb','s3m'))
            return (proof,symbol(content)) in allowed and (who,stage,scope)==('author','motion' if label=='future_proof_only' else 'text','other' if label=='wrong_proof_scope' else 'scope')
        def premise(framework,content,scope,stage):
            accepted={'sbd'} if label=='first_principle_missing' else {'saw'} if label=='second_principle_missing' else {'saw','sbd'}
            return (framework,scope,stage)==('framework','scope','text') and symbol(content) in accepted
        def application(example,content,field,scene):
            accepted={('examplea','sso')} if label=='missing_application' else {('examplea','sso'),('exampleb','s3m')}
            return (example,symbol(content)) in accepted and field==('other' if label=='wrong_application_field' else 'field') and scene in ({'motion','text'} if label=='current_goal_achieved' else {'motion'})
        def shown(who,example,scene):
            return who=='author' and example in (('examplea',) if label=='same_example_not_shown' else ('examplea','exampleb')) and scene in ({'motion','text'} if label=='current_goal_achieved' else {'motion'})
        model.update(zfr=proof,zt=premise,znf=application,zng=shown)
        summary=label in ('baseline','missing_application','same_example_not_shown','wrong_application_field','current_goal_achieved')
        future=label not in ('wrong_description','missing_application','same_example_not_shown','wrong_application_field')
        actual=values(doc,model,DOMAIN);expected=[summary,label=='current_goal_achieved',future]
        if actual!=expected:raise ValueError('Source theory transition differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'both_existing_principle_descriptions_required':True,'proof_presentation_not_proof_validity':True,
        'representative_two_result_fixture_not_exhaustive_source_inventory':True,'summary_and_application_share_same_descriptions':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_task','wrong_stage','goal_replaces_summary','summary_replaces_goal'):
        model=guarded(doc)
        for name,value in {'rd':'author','ri':'text','zm7':'task','znb':'scope','zni':'summary','znj':'transition'}.items():model[name]=lambda value=value:value
        common=lambda who,scope,context:(who,scope,context)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text')
        model['uh']=lambda node,who,content,scope,context:node=='summary' and common(who,scope,context) and symbol(content)==('s5s' if label=='goal_replaces_summary' else 's5r')
        model['znh']=lambda node,who,task,goal,stage,scope,context:node=='transition' and common(who,scope,context) and (task,stage,symbol(goal))==('other' if label=='wrong_task' else 'task','other' if label=='wrong_stage' else 'text','s5r' if label=='summary_replaces_goal' else 's5s')
        expected=[label not in ('wrong_author','wrong_scope','wrong_context','goal_replaces_summary'),
            label not in ('wrong_author','wrong_scope','wrong_context','wrong_task','wrong_stage','summary_replaces_goal')]
        actual=values(doc,model,DOMAIN+('summary','transition'))
        if actual!=expected:raise ValueError('Summary/goal attribution differs: '+label)
        rows[label]=actual
    return {'cases':rows,'quoted_goal_not_evaluated_as_current_achievement':True,'same_task_as_required_results_retained':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Transition source inventory differs')
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0150');text=unit['text']
    if hashlib.sha256(text.encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Transition source text differs')
    excluded=[(text.index(word),text.index(word)+len(word)) for word in ('Kinematik','Elektrodynamik')]
    ranges=[];start=0
    for a,b in excluded:ranges.append((start,a));start=b
    ranges.append((start,len(text)))
    common=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=['s5o','s5p','s5q','s5r','s5s'],status='partial_explicit_reading',full_semantic_equivalence=False)
    return {'segments':[dict(common,start=a,end=b,source=text[a:b]) for a,b in ranges],
        'unwritten_field_terms':[text[a:b] for a,b in excluded],'field_references_not_counted_as_concept_definitions':True,
        'verified_full_units':0,'following_electrodynamic_headings_unwritten':True,'facsimile_review':False}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'theory-transition'),(composed,'einstein-theory-transition')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored transition artifacts differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Transition roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=list(documents)+['data/theory-transition-basis-v1.json','data/einstein-theory-transition-basis-v1.json',
        'examples/v014/einstein-derivation-modalities.noema','scripts/compose_theory_transition.py','scripts/check_theory_transition.py',
        'scripts/check_calculation_discourse.py','noema/discourse.py','noema/finite_semantics.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'partial_task_relative_summary_and_application_transition','documents':documents,
        'generic_scope_and_goal':generic_checks(),'source_bindings':source_checks(),'attribution':attribution_checks(),
        'alignment':alignment(),'roundtrips':True,'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/'examples/v014/einstein-derivation-modalities.noema').read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Theory transition report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Task-relative requirements, reported derivations and application goal checked')


if __name__=='__main__':main()
