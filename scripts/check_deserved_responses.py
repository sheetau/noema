"""Check response-worthiness against actual praise, grounds and general claims."""
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
from scripts import check_qualified_princes as prior
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_deserved_responses import ROOT,PARENT,BUILDERS,RESPONSE,BASIS,STANDARD,MEANINGS

REPORT=ROOT/'reports/deserved-responses-v1.json'
SCENES=prior.SCENES
DOMAIN=('leader','other','caller','listener','praise')
SOURCE_DOMAIN=(*prior.SOURCE_DOMAIN,'caller','praise')
EXTRA='r jnsubject[] a.r jnspeaker[] a.r jnactivity[] a.r jncontext[] d.r jnusers[a] c.r jnbasis[a] e.r jnoccurs[a d] c.r jnpresents[a a d] c.r jnconveys[a a a i[h[a] f] d] c.'
EXTRA+=''.join('r '+n+'[a '+RESPONSE+' '+BASIS+' d] c.' for n in ('jnfirst','jnsecond'))


def setup(text,source=False,empty=False):
    old=prior.source_setup(text) if source else None
    base=old['document'] if source else parse(text);base['statements']=[];base=parse(format_graph(base,'compact')+EXTRA)
    policy=old['old']['old']['old']['policy'] if source else None
    basis='i[person a][c['+policy+'][l[a][v person]]]' if source else 'p jnbasis'
    message=k('ro7',basis)
    response=k('hzgb','p jnusers','r['+message+']') if source else k('roa','p jnusers','r['+message+']','p jnoccurs','p jnpresents','p jnconveys')
    rules=['i[subject a response '+RESPONSE+' basis '+BASIS+'][b point['+k(n,'v subject','v response','v basis','v point')+']]' for n in ('jnfirst','jnsecond')]
    standards='l['+STANDARD+']['+('' if empty else ' '.join(rules))+']'
    spec=specialize_definition(base,'ro6','jnmerit',{1:description(base,basis)});base=spec.document
    merit=k('jnmerit','r['+response+']',standards)
    at=lambda expr:'t['+expr+'][k jncontext[]]'
    queries=[at('c['+basis+'][k jnsubject[]]'),at('c['+merit+'][k jnsubject[]]'),
        at('c['+response+'][k jnspeaker[] k jnactivity[] k jnsubject[]]'),'e[r['+merit+']][r['+merit+']]']
    claim=None;removed=spec.disquotations_removed
    if source:
        spec=specialize_definition(base,'hzgc','jnclaim',{4:description(base,basis)});base=spec.document;removed+=spec.disquotations_removed
        claim=k('jnclaim',old['head'],old['fit'],old['refusal'],'r['+response+']',standards)
        queries += [at(claim),k('uc','k jmnode[]','k jmauthor[]','r['+claim+']','k jncontext[]')]
    doc=parse(format_graph(base,'compact')+''.join('q['+q+'].' for q in queries))
    return dict(document=doc,old=old,source=source,basis=basis,response=response,message=message,merit=merit,claim=claim,standards=standards,
        basis_syntax=syntax(description(base,basis)),response_syntax=syntax(description(base,response)),message_syntax=syntax(description(base,message)),
        claim_syntax=syntax(description(base,claim)) if source else None,disquotations_removed=removed)


def model_for(data,bits=(True,True,True,True,True,True),variant='baseline'):
    ground,first,second,occurs,presents,conveys=bits
    model=prior.source_model(data['old'],capable=variant!='incapable',inner_truth=ground) if data['source'] else guarded(data['document'])
    model.update({n:f for n,f in guarded(data['document']).items() if n not in model})
    def correct(subject,response,basis,point):
        return subject=='leader' and response.syntax==data['response_syntax'] and basis.syntax==data['basis_syntax'] and variant not in ('other_basis','other_response')
    actualoccurs=lambda act,point:occurs and (act,point)==('praise','now')
    actualpresents=lambda speaker,act,point:presents and (speaker,act,point)==('caller','praise','now')
    actualconveys=lambda act,recipient,subject,desc,point:conveys and (act,recipient,subject,point)==('praise','listener','other' if variant=='other_subject' else 'leader','belief' if variant=='other_context' else 'now') and desc.syntax==data['message_syntax']
    model.update(jnsubject=lambda:'leader',jnspeaker=lambda:'caller',jnactivity=lambda:'praise',jncontext=lambda:'now',
        jnusers=lambda person:person=='listener' and variant!='empty_audience',
        jnbasis=lambda person:Content(SCENES,(ground and person=='leader',)*len(SCENES)),
        jnfirst=lambda subject,response,basis,point:first and correct(subject,response,basis,point),
        jnsecond=lambda subject,response,basis,point:second and correct(subject,response,basis,point),
        jnoccurs=actualoccurs,jnpresents=actualpresents,jnconveys=actualconveys)
    if data['source']:
        oldoccurs,oldpresents,oldconveys=model['dg'],model['f3'],model['f2']
        model.update(dg=lambda *args:oldoccurs(*args) or actualoccurs(*args),f3=lambda *args:oldpresents(*args) or actualpresents(*args),f2=lambda *args:oldconveys(*args) or actualconveys(*args),
            uc=lambda node,author,desc,point:(node,author,point)==('passage','author','now') and desc.syntax==data['claim_syntax'] and variant!='no_attribution')
    return model


def values(data,model):
    return [row['value'] for row in evaluate_document(data['document'],primitives=model,individuals=SOURCE_DOMAIN if data['source'] else DOMAIN,situations=SCENES,max_steps=128_000_000)]


def checks(texts):
    data=setup(texts[0]);grid=[]
    for bits in product((False,True),repeat=6):
        expected=[bits[0],all(bits[:3]),all(bits[3:]),True];result=values(data,model_for(data,bits))
        if result!=expected:raise ValueError('Desert and response conflated: '+repr((bits,result)))
        grid.append(dict(bits=list(bits),result=result))
    print('64 ground/standard/performance profiles passed',flush=True);rows=[]
    variants=('baseline','unworthy','no_ground','unperformed','other_subject','other_basis','other_response','empty_audience','other_context','incapable','no_attribution')
    for text in texts[1:]:
        data=setup(text,True);cases={}
        for variant in variants:
            ground=variant!='no_ground';worthy=ground and variant not in ('unworthy','other_basis','other_response')
            performed=variant not in ('unperformed','other_subject','empty_audience','other_context')
            bits=(ground,True,variant!='unworthy',variant!='unperformed',True,True)
            expected=[ground,worthy,performed,True,worthy and variant!='incapable',variant!='no_attribution']
            result=values(data,model_for(data,bits,variant))
            if result!=expected:raise ValueError('Deserved source response failed: '+repr((variant,result,expected)))
            cases[variant]=result
        rows.append(dict(cases=cases,disquotations_removed=data['disquotations_removed']));print('Source response-worthiness contrasts passed',flush=True)
    return dict(grid=grid,source=rows)


def build_report():
    texts,documents,sizes=[],{},{}
    for builder,stem in BUILDERS:
        text,basis=builder();texts.append(text);doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Deserved-response artifact differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Deserved-response roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=len(text)
    parent,child=parse((ROOT/PARENT).read_text(encoding='utf-8')),parse(texts[1])
    if child['declarations'][:len(parent['declarations'])]!=parent['declarations'] or child['statements']!=parent['statements']:raise ValueError('Historical parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0015')
    ranges=[(unit['text'].index(phrase),unit['text'].index(phrase)+len(phrase)) for phrase in ('und verdient','gepriesen zu werden')]
    paths={*documents,PARENT,'examples/v014/qualified-princes-core.noema',*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_deserved_responses.py','scripts/check_deserved_responses.py','scripts/check_qualified_princes.py','scripts/check_action_standards.py','scripts/check_self_reports.py',
        'scripts/check_scoped_nonprescription.py','scripts/check_assessed_payments.py','scripts/check_public_assessment.py','scripts/check_rod_setup.py',
        'noema/higher_order_semantics.py','noema/finite_semantics.py','noema/extraction.py','noema/specialization.py','artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_grounded_fitting_response_not_actual_praise',documents=documents,sizes=sizes,interpretation=checks(texts),parent_preserved=True,roundtrips=True,
        new_definitions=6,new_primitives=0,new_author_statements=0,alignment=dict(semantic_completion=False,segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation',range=[a,b],text=unit['text'][a:b],definitions=list(MEANINGS)) for a,b in ranges]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sorted(paths)})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();result=build_report()
    if args.verify_only:
        if result!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Deserved-response record differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print('Deserved response, performance, basis and author attribution remain distinct')


if __name__=='__main__':main()
