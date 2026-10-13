"""Check a composed evaluative reading without pretending to certify word equivalence."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import Content
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode,decode
from scripts.check_conditional_release import values
from scripts.check_rod_setup import guarded
from scripts import check_situated_criticism as situated
from scripts.compose_assumed_standing import ROOT,PARENT,BUILDERS,PREMISE_FIELDS,ALL_FIELDS,CONTEXT,generic_composed

REPORT=ROOT/'reports/assumed-standing-v1.json'
EVIDENCE=ROOT/'data/vorwitzig-reading-v1.json'
DOMAIN=(*situated.DOMAIN,'standing')


def setup(text,criteria=('zqc','zqd')):
    base,payment,criticism=situated.setup(text)
    base['statements']=[]
    extra='r zqa[] a.r zqb[a a a d] c.r zqc[a a] e.r zqd[a a] e.'
    base=parse(format_graph(base,'compact')+extra)
    expressions=situated.EXPRESSIONS|dict(standing='k zqa[]',criteria='l[h[a a] e]['+' '.join('p '+name for name in criteria)+']',assumes='p zqb')
    queries=[('hza4',PREMISE_FIELDS+CONTEXT),('hza5',ALL_FIELDS+[('cases','h[d] c')]),
        ('hza6',PREMISE_FIELDS+[('cases','h[d] c')])]
    text=''.join('q[k '+name+'['+' '.join(expressions[n] for n,_ in fields)+']].' for name,fields in queries)
    return parse(format_graph(base,'compact')+text),payment,criticism


def model_for(doc,payment,criticism,bits=(True,False,True,True,True,True),variant='baseline'):
    assumes,first,second,required,causal,sanction=bits
    model=situated.model_for(doc,payment,criticism,(required,True,True,True,causal,sanction))
    model['zph']=guarded(doc)['zph']
    model['zqa']=lambda:'standing'
    model['zqb']=lambda person,activity,standing,context:assumes and (person,activity,standing,context)==(
        'other' if variant=='wrong_actor' else 'person',
        'payment' if variant=='wrong_activity' else 'speech',
        'role' if variant=='wrong_standing' else 'standing',
        'causal' if variant=='wrong_context' else 'now')
    def criterion(truth,person,standing):
        target=('other' if variant=='criterion_other_person' else 'person',
            'role' if variant=='criterion_other_standing' else 'standing')
        return Content(situated.SCENES,tuple(truth if (person,standing)==target and scene==(
            'causal' if variant=='criterion_other_context' else 'now') else True for scene in situated.SCENES))
    model['zqc']=lambda person,standing:criterion(first,person,standing)
    model['zqd']=lambda person,standing:criterion(second,person,standing)
    return model


def evaluate(doc,model):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return values(doc,{k:v for k,v in model.items() if k in names},DOMAIN,situated.SCENES)


def source_checks(texts):
    setups=[setup(text) for text in texts]
    rows=[]
    for bits in product((False,True),repeat=6):
        assumes,first,second,required,causal,sanction=bits
        premise=required and assumes and not(first and second)
        expected=[premise,not premise or causal and sanction,premise]
        actual=[evaluate(doc,model_for(doc,payment,criticism,bits)) for doc,payment,criticism in setups]
        if actual!=[expected]*len(setups):raise ValueError('Composed evaluative condition differs: '+repr((bits,actual)))
        rows.append({'states':list(bits),'results':actual[0]})
    contrasts={}
    for name in ('wrong_actor','wrong_activity','wrong_standing','wrong_context',
                 'criterion_other_person','criterion_other_standing','criterion_other_context'):
        actual=[evaluate(doc,model_for(doc,payment,criticism,variant=name)) for doc,payment,criticism in setups]
        if actual!=[[False,True,False]]*len(setups):raise ValueError('Evaluative binding differs: '+name)
        contrasts[name]=actual[0]
    lists={}
    for name,criteria,expected in (('empty',(),[False,True,False]),
        ('duplicate_failure',('zqc','zqc'),[True,True,True]),
        ('reordered',('zqd','zqc'),[True,True,True]),
        ('fulfilled_only',('zqd',),[False,True,False])):
        actual=[]
        for text in texts:
            doc,payment,criticism=setup(text,criteria)
            actual.append(evaluate(doc,model_for(doc,payment,criticism)))
        if actual!=[expected]*len(texts):raise ValueError('Criterion list changed its meaning: '+name)
        lists[name]=actual[0]
    doc,payment,criticism=setups[0]
    model=model_for(doc,payment,criticism);model['zqc']=guarded(doc)['zqc']
    try:evaluate(doc,model)
    except ValueError as exc:
        if 'Unrelated primitive' not in str(exc):raise
    else:raise ValueError('Unknown criterion treated as a failed criterion')
    parse(generic_composed()[0]+'q[e[r[p rfr]][r[p rfr]]].')
    return {'cases':rows,'binding_contrasts':contrasts,'list_contrasts':lists,'standalone_agrees':True,
        'opaque_quality_parameter_not_executed':True,'permission_and_message_truth_not_executed':True,
        'unknown_criterion_refused':True,'composed_property_can_be_quoted':True}


def alignment():
    source=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']=='kant-1784:u0012')
    excerpt='vorwitziger Tadel'
    if unit['text'].count(excerpt)!=1:raise ValueError('Ambiguous source range')
    start=unit['text'].index(excerpt)
    return {'segments':[{'unit':unit['id'],'unit_sha256':unit['text_sha256'],'range':[start,start+len(excerpt)],
        'text':excerpt,'definitions':['rfp','rfq','rfr','hza4','hza5','hza6'],'status':'partial',
        'review_ja':'出過ぎた発言という読解候補を、自ら発言上の立場を取ることと、その立場の条件不足から合成した。辞書の用例は読解候補の根拠であり、当該語義の唯一性・必要十分性・全文の同義性は未確認。'}],
        'semantic_completion':False,'lexical_equivalence_certified':False}


def evidence_checks():
    record=json.loads(EVIDENCE.read_text(encoding='utf-8'))
    if len(record['sources'])!=3:raise ValueError('Missing lexical sources')
    for row in record['sources']:
        if not row['url'].startswith('https://') or len(row['raw_sha256'])!=64 or not row['excerpts']:
            raise ValueError('Incomplete lexical evidence record')
    return {'record':'data/vorwitzig-reading-v1.json','sources':len(record['sources']),
        'historical_usage_supports_a_candidate_not_unique_interpretation':True,
        'online_sources_not_consulted_by_noema_parser_or_interpreter':True,
        'checks_are_offline_metadata_integrity_not_new_web_verification':True}


def build_report():
    documents,sizes,texts={},{},[]
    for builder,stem in BUILDERS:
        text,basis=builder();doc=parse(text);texts.append(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text or json.loads((ROOT/('data/'+stem+'-basis-v1.json')).read_text(encoding='utf-8'))!=basis:
            raise ValueError('Stored assumed standing differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
        sizes[stem]={'characters':len(text),'statements':len(doc['statements'])}
    doc,parent=parse(texts[1]),parse((ROOT/PARENT).read_text(encoding='utf-8'))
    if doc['declarations'][:len(parent['declarations'])]!=parent['declarations'] or doc['statements']!=parent['statements']:
        raise ValueError('Parent changed')
    paths=[*documents,PARENT,*['data/'+stem+'-basis-v1.json' for _,stem in BUILDERS],
        'scripts/compose_assumed_standing.py','scripts/check_assumed_standing.py','scripts/check_situated_criticism.py',
        'data/vorwitzig-reading-v1.json','noema/finite_semantics.py','noema/extraction.py',
        'artifacts/written-units-v1/kant-1784.json']
    return json.loads(json.dumps({'status':'partial_composed_assumed_standing_interpretation',
        'documents':documents,'sizes':sizes,'source':source_checks(texts[1:]),'alignment':alignment(),'lexical_evidence':evidence_checks(),
        'parent_preserved':True,'roundtrips':True,'new_primitives':0,'new_author_statements':0,
        'verified_full_units':{'kant-1784':0,'einstein-1905':0},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}},ensure_ascii=False))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Assumed standing report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Composed standing criteria and source bindings checked; lexical equivalence remains unverified')


if __name__=='__main__':main()
