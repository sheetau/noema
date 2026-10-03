"""Check signed judgments, differing criteria, observer scope and non-factivity."""
import argparse
import hashlib
from itertools import product
import json

from noema.finite_semantics import evaluate_document
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from noema.script import encode, decode
from scripts.check_described_appraisals import candidate
from scripts.check_rod_comparison import callbacks, guarded
from scripts.check_rod_measurements import cut, fingerprint
from scripts.compose_observer_judgments import ROOT, TRUE, FALSE, generic_composed, source_composed

REPORT=ROOT/'reports/observer-judgments-v1.json'


def symbol(description):
    return json.loads(description.syntax)['symbol']


def values(doc,model,domain):
    return [r['value'] for r in evaluate_document(doc,individuals=domain,
        situations=('motion','text','other'),primitives=model,
        max_steps=1_000_000,memoize_definitions=True,memoize_expressions=True)]


def judgment_checks():
    # Also usable for two qualification criteria; no physics primitives occur.
    text=generic_composed()[0]+'''
r ja[] a.r jb[] d.r jc[d] c.r jd[d] c.r je[a i[e] c d] c.
d jf[] e[b context[k jc[v context]]].d jg[] e[b context[k jd[v context]]].
'''
    for content in ('jf','jg'):
        for definition in ('sdk','sdl'):
            for polarity in (TRUE,FALSE):
                text+=f'q[k {definition}[k ja[] r[k {content}[]] {polarity} k jb[] p je]].'
    doc=parse(text);rows=[]
    for positive,negative,first,second in product((False,True),repeat=4):
        model={'ja':lambda:'person','jb':lambda:'motion',
            'jc':lambda ctx:first if ctx=='motion' else not first,
            'jd':lambda ctx:second if ctx=='motion' else not second,
            'je':lambda who,desc,polarity,ctx:(who,ctx)==('person','motion') and symbol(desc)=='jf' and (positive if polarity else negative)}
        actual=values(doc,model,('person','other'))
        expected=[positive,negative,positive and first,negative and not first,False,False,False,False]
        if actual!=expected:raise ValueError('Signed, non-factive judgment differs')
        rows.append({'positive':positive,'negative':negative,'first_criterion':first,'second_criterion':second,'results':actual})
    return {'cases':rows,'same_truth_does_not_identify_descriptions':True,
        'no_judgment_does_not_mean_negative_judgment':True,'inconsistent_judgments_are_representable':True}


def source_checks():
    doc=candidate(source_composed()[0],'''
r ja[] d.r jb[] h[a i[e] c d] c.
q[k sdq[k ja[] k jb[]]].q[k sdr[k ja[] k jb[]]].q[k sds[k ja[] k jb[]]].''')
    domain=('moving_a','moving_b','rest_a','rest_b','outsider','frame','other')
    names=('baseline','missing_moving_a','missing_moving_b','positive_instead_of_negative',
        'wrong_moving_criterion','wrong_rest_criterion','negative_instead_of_positive',
        'one_rest_observer_dissents','no_rest_observers','outsider_dissents',
        'wrong_context','wrong_frame','different_moving_observer','same_truth_different_description')
    rows={}
    for name in names:
        model=guarded(doc)
        model.update(ja=lambda:'other' if name=='wrong_context' else 'motion',
            zay=lambda:'moving_a',zaz=lambda:'outsider' if name=='different_moving_observer' else 'moving_b',
            ra=lambda:'other' if name=='wrong_frame' else 'frame',
            xb=lambda who:who in ('moving_a','moving_b','rest_a','rest_b','outsider'),
            x4=lambda who,frame,ctx:name!='no_rest_observers' and who in ('rest_a','rest_b') and (frame,ctx)==('frame','motion'))
        def judges(who,desc,polarity,ctx):
            if ctx!='motion':return False
            key=symbol(desc)
            if who in ('moving_a','moving_b'):
                if name=='missing_moving_a' and who=='moving_a' or name=='missing_moving_b' and who=='moving_b':return False
                wanted='sdp' if name in ('wrong_moving_criterion','same_truth_different_description') else 'sdo'
                return key==wanted and polarity==(name=='positive_instead_of_negative')
            if who in ('rest_a','rest_b'):
                if name=='one_rest_observer_dissents' and who=='rest_b':return False
                return key==('sdo' if name=='wrong_rest_criterion' else 'sdp') and polarity!=(name=='negative_instead_of_positive')
            return name!='outsider_dissents' and key=='sdp' and polarity
        callbacks(doc,model,{'jb':judges})
        actual=values(doc,model,domain)
        moving_bad={'missing_moving_a','missing_moving_b','positive_instead_of_negative','wrong_moving_criterion',
            'different_moving_observer','same_truth_different_description','wrong_context'}
        rest_bad={'wrong_rest_criterion','negative_instead_of_positive','one_rest_observer_dissents',
            'no_rest_observers','wrong_context','wrong_frame'}
        a,b=name not in moving_bad,name not in rest_bad
        if actual!=[a,b,a and b]:raise ValueError('Observer scope differs: '+name+' '+repr(actual))
        rows[name]=actual
    return {'cases':rows,'judgment_contents_executed':False,'nonempty_rest_observer_range_required':True}


def criterion_checks():
    doc=candidate(source_composed()[0],'''
r ja[] d.r jb[] h[h[b] c h[b] c h[b] c] c.r jc[] h[a d] c.
q[k sdm[k jb[]]].q[k sdn[k ja[] k jc[]]].''')
    domain=('first','middle','last','clock_a','clock_b','other')
    rows={}
    for name in ('moving','stationary_limit','wrong_middle_record','wrong_return_record',
        'clock_a_not_tracking','clock_b_not_tracking','neither_tracking','different_clock','wrong_context'):
        model=guarded(doc)
        times={'first':2,'middle':6,'last':10 if name=='stationary_limit' else 8,'other':6}
        constants={'ja':'other' if name=='wrong_context' else 'motion',
            'zas':'first','zat':'last' if name=='wrong_middle_record' else 'middle',
            'zau':'middle' if name=='wrong_return_record' else 'last',
            'zaj':'clock_a','zak':'other' if name=='different_clock' else 'clock_b'}
        for key,val in constants.items():model[key]=lambda val=val:val
        model['zag']=lambda record:cut(times[record])
        known={fingerprint(cut(n)):n for n in times.values()}
        def midpoint(a,b,c):
            first,middle,last=(known[fingerprint(x)] for x in (a,b,c))
            return middle-first==last-middle
        def tracking(clock,ctx):
            return ctx=='motion' and clock in ('clock_a','clock_b') and name!='neither_tracking' and not(
                name=='clock_a_not_tracking' and clock=='clock_a' or name=='clock_b_not_tracking' and clock=='clock_b')
        callbacks(doc,model,{'jb':midpoint,'jc':tracking})
        actual=values(doc,model,domain)
        expected=[name=='stationary_limit',name not in ('clock_a_not_tracking','clock_b_not_tracking','neither_tracking','different_clock','wrong_context')]
        if actual!=expected:raise ValueError('Observer criteria differ: '+name+' '+repr(actual))
        rows[name]=actual
    return {'cases':rows,'finite_integer_reading_oracle':True,'full_real_cut_midpoint_evaluated':False,
        'tracking_callback_is_a_fixture_not_a_physical_derivation':True}


def attribution_checks():
    doc=parse(source_composed()[0]);doc['statements']=doc['statements'][-2:]
    rows={}
    for name in ('baseline','wrong_author','wrong_scope','wrong_context','wrong_node',
        'wrong_premise','wrong_conclusion','reversed_contrast','missing_contrast'):
        model=guarded(doc)
        for key,val in {'zbb':'node','rd':'author','xy':'scope','ri':'text'}.items():model[key]=lambda val=val:val
        def common(node,author,scope,ctx):
            return (node,author,scope,ctx)==('other' if name=='wrong_node' else 'node',
                'other' if name=='wrong_author' else 'author','other' if name=='wrong_scope' else 'scope',
                'other' if name=='wrong_context' else 'text')
        model['zc']=lambda node,author,premise,conclusion,scope,ctx:common(node,author,scope,ctx) and (
            symbol(premise),symbol(conclusion))==('sdj' if name=='wrong_premise' else 'sdu','sdp' if name=='wrong_conclusion' else 'sdt')
        model['zbc']=lambda node,author,first,second,scope,ctx:name!='missing_contrast' and common(node,author,scope,ctx) and (
            symbol(first),symbol(second))==(('sdw','sdv') if name=='reversed_contrast' else ('sdv','sdw'))
        actual=values(doc,model,('node','author','scope','other'))
        common_bad={'wrong_author','wrong_scope','wrong_context','wrong_node'}
        expected=[name not in common_bad|{'wrong_premise','wrong_conclusion'},name not in common_bad|{'reversed_contrast','missing_contrast'}]
        if actual!=expected:raise ValueError('Hypothetical judgment attribution differs: '+name)
        rows[name]=actual
    return rows


def alignment():
    artifact=json.loads((ROOT/'artifacts/written-units-v1/einstein-1905.json').read_text(encoding='utf-8'))
    unit=next(u for u in artifact['units'] if u['id']=='einstein-1905:u0040')
    digest='7e75b87effaf07397f5bd678f7aab178e644c2e48aca3ae656e991b7032d6e6f'
    if hashlib.sha256(unit['text'].encode('utf-8')).hexdigest()!=digest:raise ValueError('Observer judgment source changed')
    start=unit['text'].index('Mit dem bewegten Stabe')
    return {'segments':[{'unit':unit['id'],'unit_sha256':digest,'start':start,'end':len(unit['text']),
        'source':unit['text'][start:],'definitions':['sdo','sdp','sdq','sdr','sdt','sdu','sdv','sdw'],
        'status':'partial_explicit_reading','full_semantic_equivalence':False}],
        'verified_full_units':0,'facsimile_checked':False}


def build_report():
    documents={}
    for compose in (generic_composed,source_composed):
        text,basis=compose();doc=parse(text)
        if (ROOT/basis['document']).read_text(encoding='utf-8')!=text:raise ValueError('Stored judgment differs')
        for notation in ('compact','full'):
            form=format_graph(doc,notation)
            if parse(form)!=doc or parse(decode(encode(form,'v2')))!=doc:raise ValueError('Judgment roundtrip differs')
        documents[basis['document']]=audit_basis(doc,basis)
    paths=[*documents,'data/observer-judgments-basis-v1.json','data/einstein-observer-judgments-basis-v1.json',
        'examples/v014/einstein-moving-light-trip.noema','scripts/compose_observer_judgments.py','scripts/check_observer_judgments.py',
        'noema/discourse.py','noema/finite_semantics.py']
    current=source_composed()[0];previous=(ROOT/'examples/v014/einstein-moving-light-trip.noema').read_text(encoding='utf-8')
    return {'status':'partial_observer_judgment_contrast_with_distinct_criteria','documents':documents,
        'judgments':judgment_checks(),'source_adapter':source_checks(),'criterion_adapter':criterion_checks(),
        'attribution':attribution_checks(),'alignment':alignment(),'roundtrips':True,
        'verified_full_units':{'einstein-1905':0,'kant-1784':0},
        'notation_size':{'canonical_source_document_characters':len(current),'added_declarations_and_statements_characters':len(current)-len(previous)},
        'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in paths}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    report=build_report()
    if args.verify_only:
        if report!=json.loads(REPORT.read_text(encoding='utf-8')):raise ValueError('Observer judgment report differs')
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print('Signed judgments, criterion distinction, observer scope and hypothetical attribution checked')


if __name__=='__main__':main()
