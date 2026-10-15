"""Check bounded predictions, record provenance and jointly possible comparisons."""
import argparse
from fractions import Fraction as F
from functools import lru_cache
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.polynomial_proofs import verify_universal
from noema.script import transcribe
from scripts.compose_experimental_comparison import ROOT,PARENT,SOURCE,LIBRARY,CORE,READING,NUMERIC,BASE,SPEC,RELATIONS,FIELDS,DIRECT,build
from scripts.compose_limits import call as k,both,op,v
from scripts.check_coordinate_correspondence import abstract
from scripts.check_described_appraisals import candidate
from scripts.check_plane_waveforms import setup,OPS
from scripts.check_rod_setup import callbacks,guarded
from scripts.check_phi_normalization import number
from scripts.check_quantities import ARITHMETIC
from scripts.check_real_products import MEANINGS,assertion

REPORT=ROOT/'reports/experimental-comparison-v1.json'
PEOPLE=('subject','frame','comparison','theory','ratiomethod','directmethod','other',
        'erecord','mrecord','drecord','eevent','mevent','devent','ekind','mkind','dkind','eunit','munit','dunit')
SCENES=('actual','ratio','direct','joint')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model):
    return [r['value'] for r in evaluate_document(doc,individuals=PEOPLE,situations=SCENES,
        primitives={d['name']:model[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},max_steps=4_000_000,
        memoize_definitions=True,memoize_expressions=True)]


def numeric_checks():
    cases={
        'exact_match':((5,2,2,F(6,5),F(6,5),3,3,3,3),[True,True,False]),
        'overlap_without_equal_centers':((5,F(19,10),F(21,10),F(11,10),F(13,10),F(55,21),F(65,19),F(33,10),F(7,2)),[True,True,False]),
        'disjoint':((5,2,2,F(6,5),F(6,5),3,3,4,5),[True,False,True]),
        'touching_boundary':((5,2,2,1,F(6,5),F(5,2),3,3,4),[True,True,False]),
        'only_light_speed_common':((5,2,2,2,2,5,5,5,6),[True,False,True]),
        'partly_above_light':((5,2,2,F(6,5),F(12,5),3,6,4,7),[True,True,False]),
        'negative_direct_lower':((5,2,2,0,F(2,5),0,1,-1,F(1,2)),[True,True,False]),
        'entirely_negative_direct':((5,2,2,0,F(2,5),0,1,-2,-1),[True,False,True]),
        'zero_in_denominator_interval':((5,0,2,1,2,F(5,2),0,0,5),[False,False,False]),
        'reversed_direct_interval':((5,2,2,F(6,5),F(6,5),3,3,4,2),[False,False,False]),
        'wrong_prediction_bounds':((5,2,2,F(6,5),F(6,5),2,4,3,3),[False,False,False]),
    };rows={}
    rational=format_graph(extract_document(parse(text(LIBRARY)),roots=['seub'],statement_indices=[]).document,'compact')
    for label,(numbers,expected) in cases.items():
        direct=evaluate(parse(rational+'q['+k('seub',*map(number,numbers))+'].'),ARITHMETIC)
        assert direct==[expected[1]],label
        output=[]
        for path in (LIBRARY,CORE):
            query=''.join('q['+k(n,*(k('bb',number(x)) for x in numbers))+'].' for n in ('seud','seuc','seue'))
            doc=abstract(candidate(text(path),query),OPS);_,model=setup(doc);model.update(ARITHMETIC)
            result=evaluate(doc,model);assert result==expected,(label,path,result);output+=result
        rows[label]=output
    return rows


def polynomial_checks():
    base=format_graph(extract_document(parse(text(LIBRARY)),roots=['seub'],statement_indices=[]).document,'compact')
    terms=list(map(v,NUMERIC.split()));V,el,eh,ml,mh,pl,ph,dl,dh=terms
    e,m,s=map(v,('electric','magnetic','speed'))
    le=lambda a,b:op('u',k('aa',b,a));mul=lambda a,b:k('ad',a,b);eq=lambda a,b:op('e',a,b);zero=number(0)
    interval=k('setz',*terms[:7]);compatible=k('seub',*terms)
    within=lambda x:both(le(pl,x),le(x,ph),le(dl,x),le(x,dh),le(zero,x),k('aa',x,V))
    claims={
        'ratio_prediction_encloses_all_values_in_reported_bounds':assertion(NUMERIC+' electric magnetic speed',op('y',both(
            interval,le(el,e),le(e,eh),le(ml,m),le(m,mh),eq(mul(e,s),mul(V,m))),both(le(pl,s),le(s,ph)))),
        'a_shared_sublight_value_implies_compatibility':assertion(NUMERIC+' speed',op('y',both(interval,le(dl,dh),within(s)),compatible)),
        'compatibility_has_a_maximum_lower_bound_witness':assertion(NUMERIC,op('y',compatible,op('x',
            both(le(dl,pl),within(pl)),both(k('aa',pl,dl),within(dl))))),
        'overlap_requires_same_interval_centers':assertion('',op('y',k('seub',*map(number,(5,2,2,1,F(6,5),F(5,2),3,3,4))),eq(number(F(11,4)),number(F(7,2))))),
    };rows={}
    for name,claim in claims.items():
        result=verify_universal(parse(base+claim),{n:MEANINGS[n] for n in ('aa','ad')},timeout_ms=20000)[0]
        assert result['status']==('invalid' if name.startswith('overlap_') else 'valid'),(name,result);rows[name]=result
    return rows


def fixture(path,source=False):
    declarations=''.join('r jexp'+n+'[] '+sort+'.' for n,sort in FIELDS)
    if source:
        queries=''.join('q[t[k '+n+'[]][k jexpcontext[]]].' for n in ('seuk','seuo','seup','seum'))
        queries+='q[t[k seun[]][k ri[]]].q[t[k seul[]][k ri[]]].q[t[k seuk[]][k ri[]]].'
    else:
        queries=''.join('q['+k(n,*[k('jexp'+name) for name,_ in FIELDS])+'].' for n in ('seuf','seug','seuh'))
        queries+='q['+k('seui',*[k('jexp'+name) for name,_ in DIRECT])+'].'
    return abstract(candidate(text(path),declarations+queries),OPS)


class ComparisonModel:
    def __init__(self,doc,variant='baseline'):
        self.doc=doc;self.cuts,self.model=setup(doc);self.model.update(ARITHMETIC);make=self.cuts.make;read=self.cuts.read
        raw={'electric':(F(2),F(2)),'magnetic':(F(6,5),F(6,5)),'direct':(F(29,10),F(31,10))}
        if variant=='disjoint':raw['direct']=(F(4),F(41,10))
        if variant=='zero_denominator':raw['electric']=(F(0),F(2))
        scales={p:F(2 if variant==p+'_unit_rescaled' else 1) for p in raw}
        raw={p:tuple(x/scales[p] for x in pair) for p,pair in raw.items()}
        labels={n:n for n,_ in BASE if n!='context'}
        labels['context']='joint';labels['light']=make(5)
        for p in raw:
            for suffix in ('record','event','kind','unit'):labels[p+suffix]=p[0]+suffix
            labels[p+'scale']=scales[p]
            for suffix,value in zip(('low','high'),raw[p]):labels[p+suffix]=make(value)
        if variant=='same_record':labels['directrecord']='erecord'
        if variant=='same_method':labels['directmethod']='ratiomethod'
        if variant=='wrong_subject':labels['subject']='other'
        if variant=='wrong_frame':labels['frame']='other'
        if variant=='wrong_comparison':labels['comparison']='other'
        if variant=='wrong_theory':labels['theory']='other'
        if variant=='wrong_direct_kind':labels['directkind']='ekind'
        if variant=='wrong_direct_unit':labels['directunit']='eunit'
        if variant=='wrong_response_kind':labels['magnetickind']='ekind'
        for name,_ in FIELDS:
            if name in labels:self.model['jexp'+name]=lambda value=labels[name]:value
        def present(prefix,context):
            if variant=='only_direct':return prefix=='direct' and context in ('direct','joint')
            if variant=='no_joint' and context=='joint':return False
            if context=='actual':return variant=='actual_records'
            return context=='joint' or context==('direct' if prefix=='direct' else 'ratio')
        def recorded(record,subject,kind,frame,event,unit,lo,hi,context):
            return any(present(p,context) and (record,subject,kind,frame,event,unit)==(
                p[0]+'record','subject',p[0]+'kind','frame',p[0]+'event',p[0]+'unit') and (read(lo),read(hi))==raw[p] for p in raw)
        def calibrated(unit,kind,scale,context):
            return any((unit,kind,scale)==(p[0]+'unit',p[0]+'kind',scales[p]) for p in raw) and variant!='missing_calibration'
        def methodof(record,method,context):
            return (record,method) in [('erecord','ratiomethod'),('mrecord','ratiomethod'),('drecord','directmethod')]
        def independent(direct,ratio,theory,context):
            if variant=='unknown_independence':raise ValueError('Method independence missing')
            return variant!='circular_method' and (direct,ratio,theory)==('directmethod','ratiomethod','theory')
        def matched(subject,frame,comparison,event,context):
            return (subject,frame,comparison)==('subject','frame','comparison') and event in ('eevent','mevent','devent') and not (variant=='unmatched_direct_event' and event=='devent')
        entries=dict(recorded=recorded,calibrated=calibrated,methodof=methodof,independent=independent,matched=matched)
        callbacks(doc,self.model,{'jexp'+n:fn for n,fn in entries.items()});self.model['va']=lambda frame:frame in ('frame','other')
        # Source records can have values in alternative situations without any
        # assertion that they already exist in the actual situation.
        declared={d['name'] for d in doc['declarations']}
        if 'seul' in declared:
            for n,_ in FIELDS:
                if n in ('subject','frame','theory','context','light','calibrated'):continue
                if n in entries:self.model['zrm'+n]=self.model['jexp'+n]
                elif n.endswith(('low','high')):
                    callbacks(doc,self.model,{'zrm'+n:lambda c,n=n:labels[n]})
                else:self.model['zrm'+n]=self.model['jexp'+n]
            for source,n in [('zramatter','subject'),('ra','frame'),('zrlrationode','theory'),('tc','light')]:self.model[source]=self.model['jexp'+n]
            self.model['zof']=calibrated;self.model['ri']=lambda:'actual'
            def accessible(origin,outcome):
                allowed=() if variant=='no_possible_situation' else ('ratio','direct') if variant=='no_joint' else ('ratio','direct','joint','actual')
                return origin=='actual' and outcome in allowed
            callbacks(doc,self.model,{'zrjaccessible':accessible})

    def evaluate(self):return evaluate(self.doc,self.model)


EXPECTED={
    'baseline':[True,True,False,True], 'disjoint':[True,False,True,True],
    'electric_unit_rescaled':[True,True,False,True],'magnetic_unit_rescaled':[True,True,False,True],'direct_unit_rescaled':[True,True,False,True],
    'zero_denominator':[False,False,False,True],'only_direct':[False,False,False,True],
    'no_joint':[False,False,False,False],'actual_records':[True,True,False,True],
    **{n:[False]*4 for n in ('same_method','wrong_subject','wrong_frame','wrong_comparison','wrong_theory','missing_calibration','circular_method','unmatched_direct_event','wrong_direct_kind','wrong_direct_unit')},
    'wrong_response_kind':[False,False,False,True],
    'same_record':[False,False,False,False],
}


def binding_checks():
    rows={}
    for path,source in ((LIBRARY,False),(CORE,True),(SOURCE,True)):
        doc=fixture(path,source);cases={}
        for variant,wanted in EXPECTED.items():
            expected=list(wanted)
            if source:
                direct=wanted[3] or variant=='no_joint'
                joint=wanted[0]
                expected += [direct,joint,variant=='actual_records']
            actual=ComparisonModel(doc,variant).evaluate();assert actual==expected,(path,variant,actual,expected)
            cases[variant]=actual
        if source:
            actual=ComparisonModel(doc,'no_possible_situation').evaluate();assert actual==[True,True,False,True,False,False,False]
            cases['no_possible_situation']=actual
        rows[path]=cases
    try:ComparisonModel(fixture(LIBRARY),'unknown_independence').evaluate()
    except ValueError as exc:assert 'missing' in str(exc)
    else:raise AssertionError('Independence invented from method names')
    return dict(cases=rows,unknown_independence_refused=True,successful_test_inferred_from_testability=False)


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc);seen=[]
    for n,value in {'zrmclaimnode':'claim','zrmdirectnode':'direct','zrmreasonnode':'reason','rd':'author','zrmscope':'scope','ri':'actual'}.items():model[n]=lambda value=value:value
    symbol=lambda x:json.loads(x.syntax)['symbol']
    def claim(node,author,content,scope,context):
        seen.append(['claim',symbol(content)])
        return (node,symbol(content)) in [('claim','seul'),('direct','seun')] and (author,scope,context)==('author','scope','actual')
    def reason(node,author,premise,conclusion,scope,context):
        seen.append(['reason',symbol(premise),symbol(conclusion)])
        return (node,author,scope,context)==('reason','author','scope','actual') and (symbol(premise),symbol(conclusion))==('seun','seul')
    model.update(uh=claim,zc=reason)
    result=evaluate_document(doc,individuals=('claim','direct','reason','author','scope'),situations=('actual',),primitives=model)
    assert [r['value'] for r in result]==[True]*3
    return dict(quoted_targets=seen,measurements_or_capability_executed=False,agreement_or_disagreement_attributed=False)


def alignment():
    work=json.loads(text('artifacts/written-units-v1/einstein-1905.json'));unit=next(u for u in work['units'] if u['id']=='einstein-1905:u0268');body=unit['text']
    ranges=[(0,body.index(', z. B.')),(body.index('gemessen werden kann'),len(body))]
    common=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],status='partial_experimental_comparison_and_direct_measurement_possibility')
    return {'segments':[dict(common,range=[a,b],text=body[a:b],definitions=['seuk','seul','seum','seun']) for a,b in ranges]}


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));current=parse(text(SOURCE));assert current['statements'][:-3]==old['statements'] and len(old['statements'])==194
    assert current['declarations'][:len(old['declarations'])]==old['declarations']
    for p in (SOURCE,LIBRARY,CORE):
        doc=parse(text(p));basis=next(json.loads(body) for q,body in files.items() if q.endswith('.json') and json.loads(body)['document']==p)
        audits[p]={k:v for k,v in audit_basis(doc,basis).items() if k!='definition_dependencies'}
        for notation in ('full','compact'):
            output=format_graph(doc,notation);assert parse(output)==parse(transcribe(output,alphabet='v2'))==doc
        cli=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8');assert json.loads(cli.stdout)==doc
    reading=json.loads(text(READING));assert reading['segments']==alignment()['segments']
    assert hashlib.sha256((ROOT/reading['facsimile_path']).read_bytes()).hexdigest()==reading['facsimile_sha256']
    paths=set(files)|{PARENT,READING,reading['facsimile_path'],'data/einstein-deflection-ratio-basis-v1.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json',
        'scripts/compose_experimental_comparison.py','scripts/check_experimental_comparison.py','tests/test_experimental_comparison.py','docs/experimental-comparison-v1.md',
        'scripts/compose_convention_comparison.py','scripts/compose_origin_clock.py','scripts/compose_limits.py','scripts/compose_situated_criticism.py',
        'scripts/check_coordinate_correspondence.py','scripts/check_described_appraisals.py','scripts/check_plane_waveforms.py','scripts/check_rod_setup.py',
        'scripts/check_phi_normalization.py','scripts/check_quantities.py','scripts/check_real_products.py','scripts/check_tau_differential.py','scripts/check_angle_composition.py'}
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','polynomial_proofs'))
    return dict(status='partial_bounded_experimental_comparison_and_joint_possibility',document=SOURCE,basis_audits=audits,
        numeric=numeric_checks(),polynomial=polynomial_checks(),bindings=binding_checks(),attribution=attribution_check(),
        statements_preserved=194,new_author_attributions=3,roundtrips=True,cli_parse=True,alignment=alignment(),
        oscillating_field_measurement_constructed=False,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Bounded comparisons and jointly possible records checked; testability does not assert agreement',flush=True)


if __name__=='__main__':main()
