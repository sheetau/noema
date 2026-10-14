"""Verify hypothetical label criticism without actual use or unearned attribution."""
import argparse
import hashlib
from itertools import product
import json
from noema.grammar import parse,format_graph
from noema.higher_order_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from noema.specialization import specialize_definition
from scripts import check_described_labels as prior
from scripts.check_assessed_payments import description
from scripts.check_public_assessment import syntax
from scripts.check_rod_setup import guarded
from scripts.compose_limits import call as k
from scripts.compose_described_labels import FIXED,SOURCE_FIXED
from scripts.compose_policy_discretion import CLAIM,SOURCE_CLAIM
from scripts.compose_attribution_choices import CHOSEN,SOURCE_CHOSEN
from scripts.compose_label_appraisals import ROOT,PARENT,BUILDERS,SETTINGS,ASSESS,MEANINGS

REPORT=ROOT/'reports/label-appraisals-v1.json'
DOMAIN=('leader','coholder','crown','suboffice','alice','bob','faith','act','otheract','assessor','discretion','label','author','passage')
SCENES=prior.SCENES
EXTRA='r jzpeople[a a d] c.r jzcases[a d d] c.r jznode[] a.r jzauthor[] a.r jzclaims[a a i[e] d] c.'


def setup(text,source=False):
    old=prior.setup(text,source);base=old['document'];base['statements']=[]
    base=parse(format_graph(base,'compact')+EXTRA)
    fields=[('selected','a')]+(SOURCE_FIXED if source else FIXED)
    index=next(i for i,(n,_) in enumerate(fields) if n=='argument')
    spec=specialize_definition(base,'hzf4' if source else 'rnt','jzknown',{index:description(base,'k jtperson[]')})
    base=spec.document
    assumed=k('jzknown',old['refs']['standing'],*(old['refs'][n] for n,_ in fields[1:] if n!='argument'))
    selected='e[v label][k jylabel[]]'
    used='i[person a activity a label a point d][w['+selected+'][c['+assumed+'][v person v activity k jxstanding[] v point]]]'
    claimrefs={**old['old']['refs'],'person':'v person','activity':'v activity','assumes':assumed}
    deficient=k('hzf2' if source else 'rno',*(claimrefs[n] for n,_ in (SOURCE_CLAIM if source else CLAIM)))
    defects='i[person a activity a label a point d][w['+selected+'][t['+deficient+'][v point]]]'
    refs={'label':'k jylabel[]','context':'k jtcontext[]','people':'p jzpeople','cases':'p jzcases','uses':used,'deficient':defects}
    property_expr=k('rnw',*(refs[n] for n,_ in SETTINGS))
    content='c['+property_expr+'][k jylabel[]]'
    quoted='r['+content+']'
    attribution={'node':'k jznode[]','author':'k jzauthor[]','candidates':'l[i[e]]['+quoted+']','selected':quoted,
        'context':refs['context'],'claims':'p jzclaims'}
    actual='c['+assumed+'][k jtperson[] k jxactivity[] k jxstanding[] k jtcontext[]]'
    nowdefect='c['+defects+'][k jtperson[] k jxactivity[] k jylabel[] k jtcontext[]]'
    queries=[actual,*[k(n,*(refs[f] for f,_ in ASSESS)) for n in ('rnu','rnv')],
        k('hzd2' if source else 'rj6',*(attribution[n] for n,_ in (SOURCE_CHOSEN if source else CHOSEN))),
        't[c['+old['old']['policies'][0]+'][l[a][k jtperson[]]]][k jtcontext[]]',nowdefect]
    doc=parse(format_graph(base,'compact')+''.join('q['+q+'].' for q in queries))
    return dict(document=doc,old=old,source=source,refs=refs,assumed=assumed,content=content,property=property_expr,
        content_syntax=syntax(description(base,content)),disquotations_removed=spec.disquotations_removed)


def model_for(data,bits=(False,True,True,False,False,True),variant='baseline',actual_choice=False):
    actual,first,second,first_choice,second_choice,attributed=bits
    profiles={point:prior.model_for(data['old'],(use,True,True,True,choice,True)) for point,use,choice in
        (('now',actual,actual_choice),('belief',first,first_choice),('elsewhere',second,second_choice))}
    def dispatch(name):
        def call(*args):
            point=args[-1] if args and isinstance(args[-1],str) and args[-1] in SCENES else 'now'
            fixed=(*args[:-1],'now') if args and isinstance(args[-1],str) and args[-1] in SCENES else args
            return profiles[point][name](*fixed)
        return call
    model={name:dispatch(name) for name in profiles['now']}
    model.update({n:f for n,f in guarded(data['document']).items() if n not in model})
    model.update(jznode=lambda:'passage',jzauthor=lambda:'author',
        jzpeople=lambda label,person,context:variant!='empty_people' and (label,person,context)==('coholder' if variant=='other_label_scope' else 'label','leader','now'),
        jzcases=lambda label,context,point:variant!='empty_cases' and (label,context)==('label','now') and point in ('belief','elsewhere'))
    claim=lambda node,author,content,point:attributed and (node,author,point)==('coholder' if variant=='other_node' else 'passage',
        'coholder' if variant=='other_author' else 'author','belief' if variant=='other_attribution_context' else 'now') and content.syntax==data['content_syntax'] and variant!='other_content'
    model['jzclaims']=claim
    if data['source']:model['uc']=claim
    return model


def values(data,model):
    return [row['value'] for row in evaluate_document(data['document'],primitives=model,individuals=DOMAIN,situations=SCENES,max_steps=24_000_000)]


def checks(texts):
    data=setup(texts[0]);grid=[]
    for bits in product((False,True),repeat=6):
        actual,first,second,first_choice,second_choice,attributed=bits
        conditional=(not first or not first_choice) and (not second or not second_choice)
        strong=conditional and (first or second)
        expected=[actual,conditional,strong,attributed,False,actual]
        result=values(data,model_for(data,bits))
        if result!=expected:raise ValueError('Hypothetical evaluation conflated: '+repr((bits,result)))
        grid.append(dict(bits=list(bits),result=result))
    print('64 hypothetical-appraisal/actual-use/attribution profiles passed',flush=True);rows=[]
    for text in texts[1:]:
        data=setup(text,True);cases={}
        for variant in ('baseline','empty_people','empty_cases','other_label_scope','other_node','other_author','other_attribution_context','other_content'):
            expected=[False,True,True,True,False,False]
            if variant in ('empty_people','empty_cases','other_label_scope'):expected[1:3]=[False,False]
            elif variant!='baseline':expected[3]=False
            result=values(data,model_for(data,variant=variant))
            if result!=expected:raise ValueError('Appraisal source contrast failed: '+repr((variant,result)))
            cases[variant]=result
        rows.append(dict(cases=cases,disquotations_removed=data['disquotations_removed']));print('Source label-appraisal contrasts passed',flush=True)
    return dict(grid=grid,source=rows)


def build_report():
    texts,documents,sizes=[],{},{}
    for builder,stem in BUILDERS:
        text,basis=builder();texts.append(text);doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:raise ValueError('Label-appraisal artifact differs')
        for notation in ('full','compact'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Label-appraisal roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis);sizes[stem]=len(text)
    parent,child=parse((ROOT/PARENT).read_text(encoding='utf-8')),parse(texts[1])
    if child['declarations'][:len(parent['declarations'])]!=parent['declarations'] or child['statements']!=parent['statements']:raise ValueError('Historical parent changed')
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0015')
    start=unit['text'].index('den hoch');end=unit['text'].index(': ist selbst')
    paths={*documents,PARENT,'examples/v014/described-labels.noema','examples/v014/described-labels-core.noema',*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_label_appraisals.py','scripts/check_label_appraisals.py','scripts/check_described_labels.py','scripts/check_policy_discretion.py','scripts/check_scoped_nonprescription.py',
        'scripts/check_assessed_payments.py','scripts/check_public_assessment.py','scripts/check_described_routines.py','scripts/check_rod_setup.py',
        'noema/higher_order_semantics.py','noema/finite_semantics.py','noema/extraction.py','noema/specialization.py','noema/description_templates.py','artifacts/written-units-v1/kant-1784.json'}
    return dict(status='partial_hypothetical_label_appraisal',documents=documents,sizes=sizes,interpretation=checks(texts),parent_preserved=True,roundtrips=True,
        new_definitions=3,new_primitives=0,new_author_statements=0,alignment=dict(semantic_completion=False,segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],
            status='explicit_interpretive_annotation',range=[start,end],text=unit['text'][start:end],definitions=list(MEANINGS))]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},source_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sorted(paths)})


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args();result=build_report()
    if args.verify_only:
        if result!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Label-appraisal record differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Label appraisal, hypothetical witness, current use and author attribution remain distinct')


if __name__=='__main__':main()
