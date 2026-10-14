"""Verify general relative-clause claims without existential or factual import."""
import argparse
import hashlib
from itertools import product
import json
from noema.finite_semantics import Content
from noema.grammar import parse,format_graph
from noema.higher_order_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from noema.specialization import specialize_definition
from scripts import check_action_standards as prior
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_self_reports import SOURCE_BELIEF
from scripts.compose_scoped_nonprescription import HEAD
from scripts.compose_qualified_princes import ROOT,PARENT,BUILDERS,MEANINGS

REPORT=ROOT/'reports/qualified-princes-v1.json'
SCENES=prior.SCENES
DOMAIN=('alice','bob')
SOURCE_DOMAIN=(*prior.DOMAIN,'refusal','label','faculty','method','author','passage')
GENERIC='r jmhead[a] e.r jmappraised[a] e.r jmrefused[a] e.r jmconclusion[a] e.r jmcontext[] d.r jmfirst[] a.r jmsecond[] a.'
EXTRA='r jmlabel[] a.r jmusers[a] c.r jmassigns[a a a d] c.r jmauthor[] a.r jmnode[] a.'


def setup(text):
    base=parse(text);base['statements']=[];base=parse(format_graph(base,'compact')+GENERIC)
    qualified=k('rnz','p jmhead','p jmappraised','p jmrefused')
    at=lambda x:'t['+x+'][k jmcontext[]]'
    qs=[at('c['+qualified+'][k '+n+'[]]') for n in ('jmfirst','jmsecond')]
    qs += [at(k('ro2',qualified,'p jmconclusion')),at(k('ro3',qualified)),at(k('ro4',qualified,'p jmconclusion'))]
    doc=parse(format_graph(base,'compact')+''.join('q['+q+'].' for q in qs))
    return dict(document=doc,source=False,qualified=qualified)


def generic_model(data,first=(True,True,True,True),second=(False,False,False,False),context='now'):
    model=guarded(data['document'])
    for i,name in enumerate(('jmhead','jmappraised','jmrefused','jmconclusion')):
        model[name]=lambda person,i=i:Content(SCENES,tuple((first if person=='alice' else second)[i] if point=='now' else False for point in SCENES))
    model.update(jmcontext=lambda:context,jmfirst=lambda:'alice',jmsecond=lambda:'bob')
    return model


def source_setup(text):
    old=prior.setup(text,True);base=old['document'];base['statements']=[]
    base=parse(format_graph(base,'compact')+EXTRA)
    refs=old['old']['old']['refs']
    headrefs={**refs,'person':'v person','context':'v point'}
    head='i[person a][b point['+k('hzfn',*(headrefs[n] for n,_ in HEAD))+']]'
    spec=specialize_definition(base,'hzfr','jmfit',{0:description(base,old['criterion'])});base=spec.document
    fitrefs={**refs,'linked':'p jvlinked','candidates':'p jvcandidates'}
    fit=k('jmfit',*(fitrefs[n] for n,_ in SOURCE_BELIEF if n!='criterion'))
    message=k('hzfw','k jmlabel[]','p jmusers','p jmassigns')
    refusal='i[person a][b point[g activity a['+k('hzft','v person','v activity','p jmusers','r['+message+']','v point')+']]]'
    qualified=k('rnz',head,fit,refusal);claim=k('hzf7',head,fit,refusal);utterance=k('hzga',head,fit,refusal)
    at=lambda x:'t['+x+']['+refs['context']+']'
    qs=[at('c['+qualified+']['+refs['person']+']'),at(claim),at(k('ro3',qualified)),at(k('ro4',qualified,'p h4l')),
        k('uc','k jmnode[]','k jmauthor[]','r['+claim+']',refs['context']),at(k('h4l',refs['person']))]
    doc=parse(format_graph(base,'compact')+''.join('q['+q+'].' for q in qs))
    return dict(document=doc,source=True,old=old,head=head,fit=fit,refusal=refusal,qualified=qualified,claim=claim,utterance=utterance,
        claim_syntax=syntax(description(base,claim)),message_syntax=syntax(description(base,message)),disquotations_removed=spec.disquotations_removed)


def source_model(data,variant='baseline',capable=False,inner_truth=False):
    old=data['old'];model=prior.model_for(old,(False,variant!='no_appraisal',False,inner_truth,inner_truth,inner_truth))
    model.update({n:f for n,f in guarded(data['document']).items() if n not in model})
    occurs,presents,conveys=model['dg'],model['f3'],model['f2']
    model['dg']=lambda act,point:occurs(act,point) or (variant!='no_refusal' and (act,point)==('refusal','now'))
    model['f3']=lambda person,act,point:presents(person,act,point) or (person,act,point)==('coholder' if variant=='other_refuser' else 'leader','refusal','now')
    model['f2']=lambda act,recipient,subject,desc,point:conveys(act,recipient,subject,desc,point) or (
        (act,recipient,subject,point)==('refusal','listener','coholder' if variant=='other_subject' else 'leader','belief' if variant=='other_context' else 'now') and desc.syntax==data['message_syntax'] and variant!='other_message')
    model.update(jmlabel=lambda:'label',jmusers=lambda p:p=='listener',jmassigns=lambda *args:False,
        jmauthor=lambda:'author',jmnode=lambda:'passage',
        uc=lambda node,author,desc,point:(node,author,point)==('passage','author','now') and desc.syntax==data['claim_syntax'] and variant!='no_attribution',
        ab=lambda faculty,person,point:(faculty,person)==('faculty','leader'),
        ac=lambda person,faculty,act,point:capable and (person,faculty,act)==('leader','faculty','act'),
        ad=lambda *args:False,
        ae=lambda person,method,point:(person,method)==('leader','method'),
        af=lambda person,method,start,end:(person,method,end)==('leader','method','elsewhere'),
        ap=lambda person,method,start,end:variant!='unassessed' and (person,method,end)==('leader','method','elsewhere'))
    if variant=='no_head':model['jtholders']=lambda *args:False
    if variant=='empty_appraisal':model['jvcandidates']=lambda *args:False
    return model


def values(data,model):
    return [row['value'] for row in evaluate_document(data['document'],primitives=model,individuals=SOURCE_DOMAIN if data['source'] else DOMAIN,
        situations=SCENES,max_steps=96_000_000)]


def checks(texts):
    data=setup(texts[0]);grid=[]
    for bits in product((False,True),repeat=8):
        first,second=bits[:4],bits[4:];a,b=all(first[:3]),all(second[:3]);counter=a and not first[3] or b and not second[3]
        expected=[a,b,not counter,a or b,counter];result=values(data,generic_model(data,first,second))
        if result!=expected:raise ValueError('Qualified generalization failed: '+repr((bits,result)))
        grid.append(dict(bits=list(bits),result=result))
    print('256 two-person qualification/conclusion profiles passed',flush=True);rows=[]
    for text in texts[1:]:
        data=source_setup(text);cases={}
        for variant in ('baseline','no_head','no_appraisal','empty_appraisal','no_refusal','other_refuser','other_subject','other_context','other_message','no_attribution','unassessed','capable'):
            qualified=variant in ('baseline','no_attribution','unassessed','capable');capable=variant=='capable';counter=qualified and not capable
            expected=[qualified,not counter,qualified,counter,variant!='no_attribution',capable]
            result=values(data,source_model(data,variant,capable))
            if result!=expected:raise ValueError('Source qualification failed: '+repr((variant,result,expected)))
            cases[variant]=result
        rows.append(dict(cases=cases,disquotations_removed=data['disquotations_removed']));print('Source general-claim contrasts passed',flush=True)
    return dict(grid=grid,source=rows)


def build_report():
    texts,documents,sizes=[],{},{}
    for builder,stem in BUILDERS:
        text,basis=builder();texts.append(text);doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Qualified-prince artifact differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Qualified-prince roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=len(text)
    parent,child=parse((ROOT/PARENT).read_text(encoding='utf-8')),parse(texts[1])
    if child['declarations'][:len(parent['declarations'])]!=parent['declarations'] or child['statements']!=parent['statements']:raise ValueError('Historical parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0015')
    end=unit['text'].index(', und verdient')
    paths={*documents,PARENT,'examples/v014/action-standards-core.noema',*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_qualified_princes.py','scripts/check_qualified_princes.py','scripts/check_action_standards.py','scripts/check_self_reports.py',
        'scripts/check_scoped_nonprescription.py','scripts/check_assessed_payments.py','scripts/check_public_assessment.py','scripts/check_rod_setup.py',
        'noema/higher_order_semantics.py','noema/finite_semantics.py','noema/extraction.py','noema/specialization.py','artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_general_claim_about_qualified_princes',documents=documents,sizes=sizes,interpretation=checks(texts),parent_preserved=True,roundtrips=True,
        new_definitions=6,new_primitives=0,new_author_statements=0,alignment=dict(semantic_completion=False,segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation',range=[0,end],text=unit['text'][:end],definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(paths)})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();result=build_report()
    if args.verify_only:
        if result!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Qualified-prince record differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print('General claim, witness, counterexample and author attribution remain distinct')


if __name__=='__main__':main()
