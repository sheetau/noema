"""Check alternative-method bindings and nonempty necessity scopes."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_comoving_labels import values
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import guarded
from scripts.check_calculation_discourse import sequence, symbol
from scripts.compose_derivation_modalities import ROOT, STEPS, composed, generic_composed

REPORT=ROOT/'reports/derivation-modalities-v1.json'
SCENES=('motion','text','other')


def install_program(doc,program,oldpairs,newpairs):
    # Quoted descriptions must be issued by this interpretation; construct both
    # sequences in Noema, then pass their actual values to a selector callback.
    names={name for pair in oldpairs+newpairs for name in pair}
    prefix='n:'+''.join('r '+name+'[] e.' for name in sorted(names))
    prefix+='r jz[a d '+STEPS+' '+STEPS+'] '+STEPS+'.'
    replacement=parse(prefix+'d '+program+'[method a stage d] '+STEPS+'[k jz[v method v stage '+sequence(oldpairs)+' '+sequence(newpairs)+']].')['declarations'][-2:]
    position=next(i for i,d in enumerate(doc['declarations']) if d['name']==program)
    doc['declarations'][position:position+1]=replacement
    return doc


def derivation_checks(source=False):
    if source:
        text=composed()[0];names=('s3c','s4s','s3m','s4r','s5f')
        query='q[t[k s5m[]][k ri[]]].'
        actor,previous,stage,available,program,rules='rd','zlv','zly','zlw','zlx','zla'
    else:
        text=generic_composed()[0]+'''r ja[] a.r jb[] a.r jc[] d.r jd[] e.r je[] e.r jf[] e.r jg[] e.r jn[] e.
r jh[a a d] c.r ji[i[e] i[e] d] c.r jk[a d] '''+STEPS+'.'
        names=('jd','je','jf','jg','jn');actor,previous,stage,available,program,rules='ja','jb','jc','jh','jk','ji'
        query='q[k s5j[k ja[] k jb[] k jc[] r[k jd[]] r[k je[]] r[k jf[]] r[k je[]] r[k jg[]] p jh p jk p ji]].'
    old,start,end,middle,wrong=names;rows={}
    labels=('baseline','unavailable','wrong_actor','wrong_stage','wrong_rule_stage','missing_baseline',
        'different_baseline_conclusion','broken_chain','wrong_conclusion','missing_required_step','reversed_required_step',
        'unapproved_step','only_previous_method_available','required_step_in_other_method')
    if source:labels+=('stage_not_earlier','same_stage')
    for label in labels:
        oldpairs=[(old,end)];newpairs=[(start,middle),(middle,end)]
        if label=='missing_baseline':oldpairs=[]
        if label=='different_baseline_conclusion':oldpairs=[(old,wrong)]
        if label=='broken_chain':newpairs=[(start,middle),(old,end)]
        if label=='wrong_conclusion':newpairs=[(start,middle),(middle,wrong)]
        if label in ('missing_required_step','required_step_in_other_method'):newpairs=[(start,end)]
        if label=='required_step_in_other_method':oldpairs=[(old,start),(start,middle),(middle,end)]
        if label=='reversed_required_step':newpairs=[(middle,start),(start,end)]
        doc=install_program(candidate(text,query),program,oldpairs,newpairs);model=guarded(doc)
        selected_stage='text' if label=='same_stage' else 'other'
        for name,value in ((actor,'author'),(previous,'old'),(stage,selected_stage)):model[name]=lambda value=value:value
        if source:
            model['ri']=lambda:'text'
            model['zm4']=lambda earlier,later:(earlier,later)==('other','text') and label!='stage_not_earlier'
        allowed={(old,end),(old,start),(old,wrong),(start,middle),(middle,end),(middle,wrong),(start,end),(middle,start)}
        if label=='unapproved_step':allowed.remove((middle,end))
        def available_method(who,method,when):
            return label!='unavailable' and (who,method,when)==(
                'stranger' if label=='wrong_actor' else 'author',
                'old' if label=='only_previous_method_available' else 'new',
                'text' if label=='wrong_stage' else selected_stage)
        def choose(method,when,oldseq,newseq):
            if label=='required_step_in_other_method' and method=='unused':return oldseq
            return oldseq if method=='old' else newseq
        model[available]=available_method
        model['jz']=choose
        model[rules]=lambda before,after,when:(symbol(before),symbol(after)) in allowed and when==('text' if label=='wrong_rule_stage' else selected_stage)
        actual=values(doc,model,('author','stranger','old','new','unused'))
        if actual!=[label=='baseline']:raise ValueError('Alternative derivation differs: '+label+repr(actual))
        rows[label]=actual
    return {'cases':rows,'quoted_premises_and_conclusions_never_evaluated':True,
        'same_method_stage_sequence_and_conclusion_required':True,'actual_execution_not_required':True,
        'fixture_steps_not_claimed_as_historical_or_machine_checked_proof':True}


def necessity_checks():
    doc=parse(generic_composed()[0]+'''r ja[] e.r jb[] d.r jc[e d d] c.
q[k s5k[k ja[] k jb[] p jc]].q[k s5l[k ja[] k jb[] p jc]].q[t[k ja[]][k jb[]]].''');rows=[]
    for first,second,firsttruth,secondtruth,current in product((False,True),repeat=5):
        content=Content(SCENES,(firsttruth,current,secondtruth));model=guarded(doc)
        model.update(ja=lambda:content,jb=lambda:'text',jc=lambda subject,here,there:subject==content and here=='text' and
            ((first and there=='motion') or (second and there=='other')))
        expected=(first or second) and (not first or firsttruth) and (not second or secondtruth)
        actual=values(doc,model,('object',))
        if actual!=[expected,expected and current,current]:raise ValueError('Necessity scope differs')
        rows.append(dict(selected=[first,second],candidate_truths=[firsttruth,secondtruth],current_truth=current,accepted=actual))
    return {'cases':rows,'empty_candidates_do_not_establish_necessity':True,
        'current_truth_not_inferred_from_selected_candidates':True,'universal_candidates_not_single_success':True}


def source_necessity_checks():
    doc=abstract(candidate(composed()[0],'q[t[k s5n[]][k ri[]]].'),{'s5f'});rows={}
    for label in ('baseline','false_current','one_failing_candidate','empty_candidates','wrong_context','wrong_content'):
        content=Content(SCENES,(True,label!='false_current',label!='one_failing_candidate'))
        other=Content(SCENES,(False,label!='false_current',True))
        model=guarded(doc);model.update(ri=lambda:'text',s5f=lambda:content,
            zlz=lambda subject,here,there:label!='empty_candidates' and subject==(other if label=='wrong_content' else content)
                and here==('motion' if label=='wrong_context' else 'text') and there in ('motion','other'))
        actual=values(doc,model,('object',))
        if actual!=[label in ('baseline','false_current')]:raise ValueError('Source necessity target differs: '+label)
        rows[label]=actual
    return {'cases':rows,'group_content_and_candidate_selection_are_explicit_test_oracles':True,
        'candidate_truth_is_not_a_proof_of_real_transform_group':True}


def attribution_checks():
    doc=parse(composed()[0]);doc['statements']=doc['statements'][-2:];rows={}
    for label in ('baseline','wrong_author','wrong_scope','wrong_context','possibility_replaced_by_result','necessity_replaced_by_group'):
        model=guarded(doc)
        for name,value in {'zm2':'alternative','zm3':'necessity','rd':'author','zlq':'scope','ri':'text'}.items():model[name]=lambda value=value:value
        def attributed(node,who,content,scope,context):
            expected={'alternative':'s3m' if label=='possibility_replaced_by_result' else 's5m',
                'necessity':'s5f' if label=='necessity_replaced_by_group' else 's5n'}
            return (who,scope,context)==('other' if label=='wrong_author' else 'author','other' if label=='wrong_scope' else 'scope','other' if label=='wrong_context' else 'text') and symbol(content)==expected.get(node)
        model['uh']=attributed;actual=values(doc,model,('alternative','necessity','author','scope','other'))
        expected={'baseline':[True,True],'possibility_replaced_by_result':[False,True],'necessity_replaced_by_group':[True,False]}.get(label,[False,False])
        if actual!=expected:raise ValueError('Modal attribution differs: '+label)
        rows[label]=actual
    return {'cases':rows,'possibility_necessity_and_bare_result_are_distinct_descriptions':True,
        'attributed_contents_not_executed_as_truth':True}


def alignment():
    path=ROOT/'artifacts/written-units-v1/einstein-1905.json';source=json.loads(path.read_text(encoding='utf-8'))
    inventory=json.loads((ROOT/'reports/written-units-v1.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=inventory['works']['einstein-1905']['units_sha256']:raise ValueError('Modal source inventory differs')
    rows=[]
    for index,defs in ((147,['s5h','s5i','s5j','s5m']),(149,['s5k','s5n'])):
        unit=next(u for u in source['units'] if u['id']==f'einstein-1905:u{index:04}')
        if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=unit['text_sha256']:raise ValueError('Modal source text differs')
        text=unit['text'];start=0 if index==147 else text.index('—');end=text.index('Führen wir') if index==147 else text.rindex('—')+1
        common=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],definitions=defs,status='partial_explicit_reading',full_semantic_equivalence=False)
        rows.append(dict(common,start=start,end=end,source=text[start:end]))
        if index==147:
            for mid in ('M0274','M0275'):
                item=next(m for m in source['math'] if m['id']==mid)
                if hashlib.sha256(item['mathml'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('Modal source symbol differs')
                rows.append(dict(common,math_id=mid,math_sha256=item['sha256']))
    return {'segments':rows,'verified_full_units':0,'could_have_read_as_past_available_derivation':True,
        'necessity_read_relative_to_explicit_candidates':True,'unique_historical_reading_claimed':False}


def build_report():
    documents={}
    for builder,name in ((generic_composed,'derivation-modalities'),(composed,'einstein-derivation-modalities')):
        text,basis=builder();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+name+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Stored modal artifacts differ')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Modal roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=list(documents)+['data/derivation-modalities-basis-v1.json','data/einstein-derivation-modalities-basis-v1.json',
        'examples/v014/einstein-transform-group.noema','scripts/compose_derivation_modalities.py','scripts/check_derivation_modalities.py',
        'scripts/compose_calculation_discourse.py','scripts/check_calculation_discourse.py','noema/discourse.py','noema/finite_semantics.py',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json']
    return {'status':'partial_alternative_derivation_and_scoped_necessity','documents':documents,
        'derivations':derivation_checks(),'necessity':necessity_checks(),'source_derivations':derivation_checks(True),
        'source_necessity':source_necessity_checks(),'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(text),'added_characters':len(text)-len((ROOT/'examples/v014/einstein-transform-group.noema').read_text(encoding='utf-8'))},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Derivation modality report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Available alternative derivations, necessity scope and attribution checked')


if __name__=='__main__':main()
