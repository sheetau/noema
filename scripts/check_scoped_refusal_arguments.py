"""Check the duty/latitude law independently of scoped refusal arguments."""
import argparse
import hashlib
from itertools import product
import json
from noema.grammar import parse,format_graph
from noema.higher_order_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from noema.specialization import specialize_definition
from scripts import check_scoped_nonprescription as prior
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_self_reports import BELIEF,SOURCE_BELIEF
from scripts.compose_label_refusals import SETTINGS,SOURCE_SETTINGS
from scripts.compose_scoped_refusal_arguments import ROOT,PARENT,BUILDERS,DUTY,SOURCE_DUTY,ARGUMENT,RELATIONS,MEANINGS

REPORT=ROOT/'reports/scoped-refusal-arguments-v1.json'
DOMAIN=(*prior.DOMAIN,'label','caller','speech','premise','conclusion','author','scope')
SCENES=prior.SCENES
EXTRA="""r jkactivity[] a.r jklabel[] a.r jkusers[a] c.r jkassigns[a a a d] c.r jkoccurs[a d] c.r jkpresents[a a d] c.r jkconveys[a a a i[h[a] f] d] c.
r jkauthor[] a.r jkscope[] a.r jkpremise[] a.r jkconclusion[] a.
r jkadopts[a a i[e] a d] c.r jkclaims[a a i[e] a d] c.r jkinfers[a h[a] c a d] c.r jkbefore[a a d] c."""


def setup(text,source=False):
    old=prior.setup(text,source);base=old['document'];base['statements']=[];base=parse(format_graph(base,'compact')+EXTRA)
    refs={**old['refs'],'criterion':'r['+old['duty']+']','judgments':'p fa' if source else 'p jtjudgments','matters':'p fb' if source else 'p jtmatters'}
    spec=specialize_definition(base,'hzfr' if source else 'rna','jkbelief',{0:description(base,old['duty'])});base=spec.document
    belief=k('jkbelief',*(refs[n] for n,_ in (SOURCE_BELIEF if source else BELIEF) if n!='criterion'))
    premise='c['+belief+']['+refs['person']+']'
    labelrefs={'label':'k jklabel[]','users':'p jkusers','assigns':'p jkassigns','occurs':'p dg' if source else 'p jkoccurs','presents':'p f3' if source else 'p jkpresents'}
    message=k('hzfw' if source else 'rnj',*(labelrefs[n] for n,_ in (SOURCE_SETTINGS if source else SETTINGS)))
    reportargs=[refs['person'],'k jkactivity[]','p jkusers','r['+message+']','v point']
    report=k('hzft',*reportargs) if source else k('rnc',*reportargs,labelrefs['occurs'],labelrefs['presents'],'p jkconveys')
    result='b point['+report+']'
    recordrefs={'author':'k jkauthor[]','context':refs['context'],'scope':'k jkscope[]','assumption':'k jkpremise[]','conclusion':'k jkconclusion[]',
        'premise':'r['+premise+']','result':'r['+result+']','adopts':'p jkadopts','claims':'p jkclaims','infers':'p jkinfers','before':'p jkbefore'}
    record=k('hzf5' if source else 'rny',*(recordrefs[n] for n,_ in (ARGUMENT if source else ARGUMENT+RELATIONS)))
    norms={**old['refs'],'policy':'r['+old['policy']+']','required':'p h7k' if source else 'p jtouterrequired','allowed':'p h7l' if source else 'p jtouterallowed'}
    fields=SOURCE_DUTY if source else DUTY
    choice=k('hzfx' if source else 'rnk',*(norms[n] for n,_ in fields))
    law=k('hzf6' if source else 'rnx',*(norms[n] for n,_ in fields))
    at=lambda expr:'t['+expr+']['+refs['context']+']';applied=lambda expr:at('c['+expr+'][l[a]['+refs['person']+']]')
    queries=[applied(old['duty']),applied(choice),applied(law),at(premise),at(result),record]
    doc=parse(format_graph(base,'compact')+''.join('q['+q+'].' for q in queries))
    return dict(document=doc,old=old,source=source,refs=recordrefs,premise=premise,result=result,law=law,message=message,
        premise_syntax=syntax(description(base,premise)),result_syntax=syntax(description(base,result)),message_syntax=syntax(description(base,message)),
        disquotations_removed=spec.disquotations_removed)


def model_for(data,bits=(True,False,True,True,True),norms=(True,False,True,True),variant='baseline'):
    belief,refusal,adopted,claimed,inferred=bits;require,prohibit,allow,abstain=norms
    model=prior.model_for(data['old'],(False,False,True,True,require,belief))
    model.update({n:f for n,f in guarded(data['document']).items() if n not in model})
    def target(source,person,office,desc,bindings):
        return (source,person,office)==('assessor','leader','crown') and desc.syntax==data['old']['policy_syntax'] and bindings.items==('leader',)
    required=lambda source,person,office,desc,bindings,sign,point:target(source,person,office,desc,bindings) and ((belief and sign) if point=='belief' else (require if sign else prohibit))
    allowed=lambda source,person,office,desc,bindings,sign,point:target(source,person,office,desc,bindings) and (allow if sign else abstain)
    occurs=lambda act,point:refusal and (act,point)==('speech','now')
    presents=lambda person,act,point:(person,act,point)==('leader','speech','now')
    conveys=lambda act,recipient,subject,desc,point:(act,recipient,subject,point)==('speech','caller','leader','now') and desc.syntax==data['message_syntax']
    def adopts(node,author,desc,scope,point):
        return adopted and (node,author,scope,point)==('premise','coholder' if variant=='other_author' else 'author',
            'coholder' if variant=='other_assumption_scope' else 'scope','now') and desc.syntax==data['premise_syntax'] and variant!='other_premise_content'
    def claims(node,author,desc,scope,point):
        return claimed and (node,author,scope,point)==('premise' if variant=='merged_nodes' else 'conclusion','author',
            'coholder' if variant=='other_conclusion_scope' else 'scope','belief' if variant=='other_context' else 'now') and desc.syntax==data['result_syntax'] and variant!='other_result_content'
    def infers(author,premises,conclusion,point):
        return inferred and (author,conclusion,point)==('author','premise' if variant=='merged_nodes' else 'conclusion','now') and [x for x in DOMAIN if premises(x)]==(['coholder'] if variant=='other_reason' else ['premise'])
    before=lambda first,last,point:variant!='reversed_order' and (first,last,point)==('premise','premise' if variant=='merged_nodes' else 'conclusion','now')
    model.update(jtouterrequired=required,jtouterallowed=allowed,jkactivity=lambda:'speech',jklabel=lambda:'label',jkusers=lambda p:p=='caller',
        jkassigns=lambda *args:False,jkoccurs=occurs,jkpresents=presents,jkconveys=conveys,
        jkauthor=lambda:'author',jkscope=lambda:'scope',jkpremise=lambda:'premise',jkconclusion=lambda:'premise' if variant=='merged_nodes' else 'conclusion',
        jkadopts=adopts,jkclaims=claims,jkinfers=infers,jkbefore=before)
    if data['source']:model.update(h7k=required,h7l=allowed,dg=occurs,f3=presents,f2=conveys,ug=adopts,uh=claims,ud=infers,ue=before)
    return model


def values(data,model):
    return [row['value'] for row in evaluate_document(data['document'],primitives=model,individuals=DOMAIN,situations=SCENES,max_steps=16_000_000)]


def checks(texts):
    data=setup(texts[0]);laws=[];grid=[]
    for norms in product((False,True),repeat=4):
        actual=values(data,model_for(data,norms=norms));require,prohibit,allow,abstain=norms
        expected=[require,allow and abstain and not require and not prohibit,True]
        if actual[:3]!=expected:raise ValueError('Duty/choice law failed: '+repr((norms,actual)))
        laws.append(dict(norms=list(norms),result=actual[:3]))
    for bits in product((False,True),repeat=5):
        belief,refusal,adopted,claimed,inferred=bits
        expected=[True,False,True,belief,refusal,adopted and claimed and inferred]
        actual=values(data,model_for(data,bits))
        if actual!=expected:raise ValueError('Scoped argument conflated with truth: '+repr((bits,actual)))
        grid.append(dict(bits=list(bits),result=actual))
    print('16 norm profiles and 32 belief/refusal/discourse profiles passed',flush=True);rows=[]
    for text in texts[1:]:
        data=setup(text,True);cases={}
        for variant in ('baseline','other_author','other_assumption_scope','other_conclusion_scope','other_context','other_premise_content','other_result_content','other_reason','reversed_order','merged_nodes'):
            expected=[True,False,True,True,False,variant=='baseline']
            actual=values(data,model_for(data,variant=variant))
            if actual!=expected:raise ValueError('Scoped argument contrast failed: '+repr((variant,actual)))
            cases[variant]=actual
        rows.append(dict(cases=cases,disquotations_removed=data['disquotations_removed']));print('Source scoped-refusal contrasts passed',flush=True)
    return dict(laws=laws,grid=grid,source=rows)


def build_report():
    texts,documents,sizes=[],{},{}
    for builder,stem in BUILDERS:
        text,basis=builder();texts.append(text);doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Scoped argument artifact differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Scoped argument roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=len(text)
    parent,child=parse((ROOT/PARENT).read_text(encoding='utf-8')),parse(texts[1])
    if child['declarations'][:len(parent['declarations'])]!=parent['declarations'] or child['statements']!=parent['statements']:raise ValueError('Historical parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0015')
    start=unit['text'].index('der also');end=unit['text'].index(': ist selbst')
    paths={*documents,PARENT,'examples/v014/policy-discretion.noema','examples/v014/policy-discretion-core.noema',*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_scoped_refusal_arguments.py','scripts/check_scoped_refusal_arguments.py','scripts/compose_curve_discourse.py','scripts/check_scoped_nonprescription.py',
        'scripts/check_assessed_payments.py','scripts/check_public_assessment.py','scripts/check_rod_setup.py','noema/higher_order_semantics.py','noema/finite_semantics.py',
        'noema/extraction.py','noema/specialization.py','artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_scoped_argument_for_name_refusal',documents=documents,sizes=sizes,interpretation=checks(texts),parent_preserved=True,roundtrips=True,
        new_definitions=4,new_primitives=2,new_author_statements=0,shared_imports=['ug','uh'],alignment=dict(semantic_completion=False,segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation',range=[start,end],text=unit['text'][start:end],definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();result=build_report()
    if args.verify_only:
        if result!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Scoped argument record differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Duty/choice implication, belief, refusal and scoped argument remain distinct')


if __name__=='__main__':main()
