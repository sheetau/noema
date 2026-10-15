"""Check cautious comparison, normative identity and inference attribution."""
import argparse
from fractions import Fraction as F
from functools import lru_cache
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph,number_word
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from scripts.compose_theory_comparison_caution import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,ASSESS,POLICY,METADATA,build
from scripts.compose_limits import call as k
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks,guarded

REPORT=ROOT/'reports/theory-comparison-caution-v1.json'
SYMBOLS={n:'jqt'+number_word(i) for i,(n,_) in enumerate(METADATA+POLICY)}
PEOPLE=('person','other','activity','left','right','subject','othersubject','case','outside','first','second','authority','role')
SCENES=('actual','other')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def fixture(path,source=False,norm_only=False):
    declarations=''.join('r '+SYMBOLS[n]+'[] '+sort+'.' for n,sort in METADATA+POLICY)
    declarations+='r jqtperson[] a.r jqtactivity[] a.r jqtsubject[] a.r jqtcase[] a.r jqtcontext[] d.'
    args=lambda fields:[k(SYMBOLS[n]) for n,_ in fields]
    prefix=[k('jqtactivity'),k('jqtcase'),k('jqtcontext')]
    queries='q['+k('seqk',*prefix,*args(ASSESS))+'].q['+k('seql',prefix[0],prefix[2],*args(POLICY))+'].'
    queries+='q['+k('seqm',k('jqtperson'),prefix[0],k('jqtsubject'),prefix[2],*args(METADATA+POLICY))+'].'
    if source:
        queries='q[t[k seqp[]][k jqtcontext[]]].'
        if not norm_only:queries+='q[t[k seqn[k jqtperson[] k jqtactivity[]]][k jqtcontext[]]].'
    return abstract(candidate(text(path),declarations+queries),OPS)


class ComparisonModel:
    def __init__(self,doc,variant='baseline'):
        self.doc=doc;self.variant=variant;self.cuts,self.model=setup(doc)
        self.assessment_calls=[];self.required_calls=[]
        make=self.cuts.make
        def interpretation(activity,value,context):
            candidates=() if variant=='empty_candidates' else ('first',) if variant=='unselected_equal' else ('first','second')
            return activity=='activity' and context=='actual' and value in candidates
        def meaning(activity,value,context):
            self.assessment_calls.append('meaning')
            if variant=='unknown_assessment':raise ValueError('Comparison assessment missing')
            return (activity,context)==('activity','actual') and not (variant=='different_meaning' and value=='second')
        def units(activity,value,context):return (activity,context)==('activity','actual') and not (variant=='different_units' and value=='second')
        def corresponds(activity,value,case,context):return (activity,case,context)==('activity','case','actual') and not (variant=='different_case' and value=='second')
        def concludes(activity,case,context):
            wanted='outside' if variant=='outside_conclusion' else 'case'
            return variant!='abstains' and (activity,case,context)==('activity',wanted,'actual')
        def rightvalue(activity,value,case,context):
            return make(1 if variant=='equal_values' or (variant in ('ambiguous_difference','unselected_equal') and value=='second') else 2)
        entries={'actor':lambda activity:'person','left':lambda activity:'left',
            'right':lambda activity:'left' if variant=='same_theory' else 'right',
            'topic':lambda activity:'othersubject' if variant=='other_topic' else 'subject',
            'cases':lambda activity,case,context:(activity,case,context)==('activity','case','actual'),
            'concludes':concludes,'interpretations':interpretation,'meanings':meaning,'units':units,'corresponds':corresponds,
            'leftvalue':lambda *a:make(1),'rightvalue':rightvalue}
        callbacks(doc,self.model,{SYMBOLS[n]:fn for n,fn in entries.items()})
        for name in SYMBOLS:self.model['zrc'+name]=self.model[SYMBOLS[name]]
        self.model.update(jqtperson=lambda:'other' if variant=='other_person' else 'person',jqtactivity=lambda:'activity',
            jqtsubject=lambda:'subject',jqtcase=lambda:'case',jqtcontext=lambda:'actual',
            zrcsubject=lambda:'subject',zrcrole=lambda:'role',rd=lambda:'authority')
        self.model['zrccomparisons']=lambda activity,context:variant!='no_comparisons' and (activity,context)==('activity','actual')
        def required(authority,person,role,activity,description,polarity,context):
            symbol=json.loads(description.syntax)['symbol'];actual=(authority,person,role,activity,symbol,polarity,context)
            self.required_calls.append(actual)
            expected=['authority','person','role','activity','seqn',True,'actual']
            for index,name in enumerate(('authority','person','role','activity','description','polarity','context')):
                if variant=='wrong_required_'+name:expected[index]=False if name=='polarity' else 'other'
            if variant=='unknown_requirement':raise ValueError('Methodological requirement missing')
            return variant!='no_requirement' and actual==tuple(expected)
        self.model['zrcmust']=required

    def evaluate(self):
        return [r['value'] for r in evaluate_document(self.doc,individuals=PEOPLE,situations=SCENES,
            primitives={d['name']:self.model[d['name']] for d in self.doc['declarations'] if d['kind']=='primitive'},max_steps=5_000_000)]


EXPECTED={
    'baseline':[True,True,True],'different_meaning':[False,False,False],
    'different_units':[False,False,False],'different_case':[False,False,False],
    'empty_candidates':[False,False,False],'ambiguous_difference':[False,False,False],
    'unselected_equal':[True,True,True],'equal_values':[False,False,False],
    'outside_conclusion':[True,False,False],'abstains':[True,True,True],
    'other_person':[True,True,False],'same_theory':[True,True,False],'other_topic':[True,True,False],
}


def procedure_checks():
    doc=fixture(LIBRARY);rows={}
    for variant,expected in EXPECTED.items():
        actual=ComparisonModel(doc,variant).evaluate();assert actual==expected,(variant,actual)
        rows[variant]=actual
    return {'cases':rows,'same_meaning_units_and_case_required':True,
        'abstention_permitted':True,'no_general_theory_consistency_decision':True}


def norm_checks():
    rows={}
    variants=list(EXPECTED)+['no_comparisons','no_requirement']+[
        'wrong_required_'+n for n in ('authority','person','role','activity','description','polarity','context')]
    for path in (CORE,SOURCE):
        doc=fixture(path,True);results={}
        for variant in variants:
            model=ComparisonModel(doc,variant);actual=model.evaluate()
            wanted=[not (variant=='no_requirement' or variant.startswith('wrong_required_')),EXPECTED.get(variant,[True]*3)[-1]]
            assert actual==wanted,(path,variant,actual,wanted)
            assert all(call[4]=='seqn' and call[5] is True for call in model.required_calls)
            results[variant]=actual
        if rows:assert results==next(iter(rows.values()))
        rows[path]=results
    # Norms can be stated even when assessing actual adherence is unavailable.
    doc=fixture(CORE,True,norm_only=True);model=ComparisonModel(doc,'unknown_assessment')
    assert model.evaluate()==[True] and model.assessment_calls==[]
    for source,variant in ((False,'unknown_assessment'),(True,'unknown_requirement')):
        try:ComparisonModel(fixture(CORE,source),variant).evaluate()
        except ValueError as exc:assert 'missing' in str(exc)
        else:raise AssertionError('Missing interpretation invented')
    return {'cases':rows,'actual_adherence_not_inferred_from_requirement':True,
        'norm_does_not_execute_quoted_procedure':True,'unknown_interpretations_refused':True}


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc)
    for name,value in {'zrcnode':'node','rd':'author','zrcscope':'scope','ri':'actual'}.items():model[name]=lambda value=value:value
    def reports(node,author,premise,conclusion,scope,context):
        return (node,author,scope,context)==('node','author','scope','actual') and [json.loads(x.syntax)['symbol'] for x in (premise,conclusion)]==['seqj','seqp']
    model['zc']=reports
    assert evaluate_document(doc,individuals=('node','author','scope'),situations=('actual',),primitives=model)[0]['value'] is True
    return {'premise':'seqj','conclusion':'seqp','norm_or_actual_procedure_executed':False,
        'logical_entailment_of_norm_from_numbers_proved':False}


def alignment():
    source=json.loads(text('artifacts/written-units-v1/einstein-1905.json'))
    unit=next(u for u in source['units'] if u['id']=='einstein-1905:u0259');body=unit['text']
    spans=((body.index('man ersieht daraus'),body.index('sehr')),(body.index('vorsichtig'),len(body)))
    return {'segments':[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],text=body[start:end],
        status='explicit_interpretive_annotation',definitions=['seqk','seql','seqm','seqn','seqo','seqp']) for start,end in spans]}


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));current=parse(text(SOURCE))
    assert current['statements'][:-1]==old['statements'] and len(old['statements'])==177
    assert current['declarations'][:len(old['declarations'])]==old['declarations']
    for p in (SOURCE,LIBRARY,CORE):
        doc=parse(text(p))
        for notation in ('full','compact'):
            rendered=format_graph(doc,notation);assert parse(rendered)==parse(transcribe(rendered,alphabet='v2'))==doc
        basis=next(json.loads(body) for q,body in files.items() if q.endswith('.json') and json.loads(body)['document']==p)
        audits[p]={k:v for k,v in audit_basis(doc,basis).items() if k!='definition_dependencies'}
        output=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(output.stdout)==doc
    reading=json.loads(text(READING));assert reading['segments']==alignment()['segments']
    assert hashlib.sha256((ROOT/reading['facsimile_path']).read_bytes()).hexdigest()==reading['facsimile_sha256']
    paths=set(files)|{PARENT,READING,reading['facsimile_path'],'data/einstein-convention-comparison-basis-v1.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'scripts/compose_theory_comparison_caution.py','scripts/check_theory_comparison_caution.py','tests/test_theory_comparison_caution.py','docs/theory-comparison-caution-v1.md',
        'scripts/compose_convention_comparison.py','scripts/compose_origin_clock.py','scripts/compose_limits.py','scripts/compose_situated_criticism.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'scripts/check_angle_composition.py','scripts/check_tau_differential.py','scripts/check_transverse_time.py'}
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script'))
    return dict(status='partial_methodological_caution_and_inference',document=SOURCE,basis_audits=audits,
        procedure=procedure_checks(),norm=norm_checks(),attribution=attribution_check(),
        statements_preserved=177,new_author_inferences=1,roundtrips=True,cli_parse=True,alignment=alignment(),
        caution_degree_completed=False,theory_ontology_completed=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args()
    report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Comparison caution, normative targets and author inference checked; full source meaning remains partial',flush=True)


if __name__=='__main__':main()
