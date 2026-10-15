"""Check nonfactive credit, four-place bindings, plurality and attribution."""
import argparse
from functools import lru_cache
import hashlib,json,subprocess,sys
from noema.grammar import parse,format_graph
from noema.finite_semantics import evaluate_document
from noema.meaning_basis import audit_basis
from noema.script import transcribe
from noema.specialization import specialize_definition
from scripts.compose_intellectual_credit import ROOT,PARENT,JUDGMENT,SOURCE,LIBRARY,CORE,READING,RELATIONS,build,reused_judgment
from scripts.compose_limits import call as k
from scripts.check_described_appraisals import candidate
from scripts.check_rod_setup import callbacks,guarded

REPORT=ROOT/'reports/intellectual-credit-v1.json'
PEOPLE=('input1','input2','recipient','giver','work','event','measure','j1','j2','input3','j3')
SCENES=('actual','belief')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,model,people=PEOPLE):
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=people,situations=SCENES,
        primitives={n:model[n] for n in names},max_steps=20_000_000,memoize_definitions=True,memoize_expressions=True)]


@lru_cache(None)
def fixture(path=CORE):
    extra='r jcreditinput[] a.d jalias[] h[j[a]] e[k sewj[]].'
    fields=[k('rd'),k('zrqperson'),k('jcreditinput'),k('zrqwork'),k('ri')]+[k('zrq'+n) for n,_ in RELATIONS]
    queries=['t[k sewl[]][k ri[]]','t[k sewk[]][k ri[]]']+[k(n,*fields) for n in ('sewc','sewd','sewe')]
    return candidate(text(path),extra+''.join('q['+q+'].' for q in queries))


def model_for(doc,variant='baseline'):
    model=guarded(doc)
    for n,value in dict(rd='recipient',zrqperson='giver',zrqwork='work',ri='actual',jcreditinput='input1').items():
        model[n]=lambda value=value:value
    inputs=('input1','input2','input3') if variant=='three_inputs' else ('input1','input2')
    judges={'j1':'input1','j2':'input1' if variant=='duplicate_input' else 'input2'}
    if variant=='three_inputs':judges['j3']='input3'
    if variant=='one_input':judges={'j1':'input1'}
    def active(context):return not (variant=='misattributed' and context=='actual')
    def occurs(event,context):
        if variant=='unknown_occurrence':raise ValueError('Occurrence interpretation missing')
        return event=='event' and active(context) and variant!='no_event'
    def performs(person,event,context):return (person,event)==('giver','event') and active(context) and variant!='wrong_giver'
    def produces(event,item,context):return event=='event' and item in inputs and active(context) and variant!='different_input'
    def uses(person,item,work,context):
        return (person,work)==('recipient','work') and item in inputs and active(context) and variant not in ('unused','wrong_work','wrong_recipient')
    def standard(person,work,measure,context):return (person,work,measure)==('recipient','work','measure') and variant!='no_standard'
    def meets(item,measure,context):
        return item in inputs and measure=='measure' and not (variant=='bad_second' and item=='input2') and not (variant=='bad_candidate' and context=='actual')
    def linked(judgment,description,bindings,context):
        expected=('recipient','giver',judges.get(judgment),'work')
        if variant=='reordered_bindings':expected=('giver','recipient',judges.get(judgment),'work')
        symbol='jalias' if variant=='different_description' else 'sewj'
        return judgment in judges and json.loads(description.syntax)==dict(kind='call',symbol=symbol,arguments=[]) and bindings.items==expected and context=='actual'
    callbacks(doc,model,{'zrq'+n:f for n,f in dict(occurs=occurs,performs=performs,produces=produces,uses=uses,standard=standard,meets=meets,
        judgments=lambda person,judgment,context:person=='recipient' and judgment in judges and context=='actual',
        matters=lambda judgment,person,context:judgment in judges and person=='giver' and context=='actual' and variant!='wrong_subject',
        linked=linked,candidates=lambda judgment,context,point:judgment in judges and context=='actual' and variant!='empty_candidates' and (point=='belief' or variant=='bad_candidate')).items()})
    return model


@lru_cache(None)
def source_checks():
    cases={
        'baseline':[True,True,True,True,True],
        'three_inputs':[True,True,True,True,True],
        'misattributed':[True,True,False,True,False],
        'duplicate_input':[False,False,True,True,True],
        'one_input':[False,False,True,True,True],
        'bad_second':[False,False,True,True,True],
        'empty_candidates':[False,False,True,True,True],
        'different_description':[False,False,True,True,True],
        'reordered_bindings':[False,False,True,True,True],
        'wrong_subject':[False,False,True,True,True],
        'bad_candidate':[False,False,True,False,False],
        'no_standard':[False,False,True,False,False],
    }
    for n in ('no_event','wrong_giver','different_input','unused','wrong_work','wrong_recipient'):
        cases[n]=[False,False,False,True,False]
    doc=fixture();rows={}
    for name,wanted in cases.items():
        actual=evaluate(doc,model_for(doc,name));assert actual==wanted,(name,actual)
        rows[name]=actual
    full=fixture(SOURCE)
    for name in ('baseline','misattributed','duplicate_input'):
        assert evaluate(full,model_for(full,name))==cases[name],name
    try:evaluate(doc,model_for(doc,'unknown_occurrence'))
    except ValueError as exc:assert 'missing' in str(exc)
    else:raise AssertionError('Unknown occurrence filled in')
    return dict(cases=rows,full_source_cases=['baseline','misattributed','duplicate_input'],unknown_occurrence_refused=True,
        real_history_proved=False,gratitude_emotion_or_repayment_inferred=False)


def adapter_checks():
    extra='r jrelation[a a a a] e.r ja[] a.r jb[] a.r jc[] a.r jd[] a.r jpoint[] d.'
    lists=['l[a][k ja[] k jb[] k jc[] k jd[]]','l[a][k jb[] k ja[] k jc[] k jd[]]',
        'l[a][k ja[] k jb[] k jc[]]','l[a][k ja[] k jb[] k jc[] k jd[] k ja[]]',
        'l[a][k ja[] k ja[] k jc[] k jd[]]']
    query=lambda seq:'q[t[c[k sewg[p jrelation]]['+seq+']][k jpoint[]]].'
    doc=candidate(text(LIBRARY),extra+''.join(query(x) for x in lists))
    from noema.finite_semantics import Content
    model=guarded(doc)
    for n in ('a','b','c','d'):model['j'+n]=lambda n=n:n
    model['jpoint']=lambda:'actual'
    model['jrelation']=lambda *xs:Content(SCENES,tuple(xs==('a','b','c','d') for _ in SCENES))
    first=evaluate(doc,model,('a','b','c','d'));assert first==[True,False,False,False,False],first
    model['jrelation']=lambda *xs:Content(SCENES,tuple(xs==('a','a','c','d') for _ in SCENES))
    repeated=evaluate(doc,model,('a','b','c','d'));assert repeated==[False,False,False,False,True],repeated
    return dict(ordered=first,repeated=repeated)


def attribution_check():
    doc=parse(text(CORE));model=guarded(doc);seen=[]
    for n,value in dict(zrqnode='claim',rd='author',zrqscope='scope',ri='actual').items():model[n]=lambda value=value:value
    def claim(node,author,content,scope,context):
        target=json.loads(content.syntax)['symbol'];seen.append(target)
        return (node,author,target,scope,context)==('claim','author','sewl','scope','actual')
    model['uh']=claim
    assert evaluate(doc,model,('claim','author','scope'))==[True]
    return dict(quoted_targets=seen,credit_claim_evaluated=False)


def description_checks():
    base=fixture();base['statements']=[]
    binding='l[a][k rd[] k zrqperson[] k jcreditinput[] k zrqwork[]]'
    doc=candidate(format_graph(base,'compact'),
        'q[e[r[k sewj[]]][r[k jalias[]]]].'+
        'q[e[c[k sewj[]]['+binding+']][c[k jalias[]]['+binding+']]].')
    result=evaluate(doc,model_for(doc));assert result==[False,True],result
    return dict(description_equality=False,content_equality_in_supplied_model=True)


def alignment():
    work=json.loads(text('artifacts/written-units-v1/einstein-1905.json'))
    unit=next(x for x in work['units'] if x['id']=='einstein-1905:u0276')
    excerpt='und daß ich demselben manche wertvolle Anregung verdanke.'
    start=unit['text'].index(excerpt)
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(excerpt)],
        text=excerpt,status='partial_credit_for_several_valuable_inputs',definitions=['sewc','sewd','sewi','sewl'])])


def build_report():
    files=build();audits={}
    for p,body in files.items():assert text(p)==body,p
    old=parse(text(PARENT));doc=parse(text(SOURCE));assert len(old['statements'])==204 and doc['statements'][:-1]==old['statements']
    assert doc['declarations'][:len(old['declarations'])]==old['declarations']
    lookup={d['name']:d for d in doc['declarations']};assert lookup['sewb']==reused_judgment()
    before={**doc,'declarations':[d for d in doc['declarations'] if d['name']!='sewl'],'statements':[]}
    specialized=specialize_definition(before,'sewk','sewl',{})
    assert specialized.document['declarations'][-1]==lookup['sewl']
    for p in (SOURCE,LIBRARY,CORE):
        document=parse(text(p));basis=next(json.loads(x) for q,x in files.items() if q.endswith('.json') and json.loads(x)['document']==p)
        audits[p]={k:v for k,v in audit_basis(document,basis).items() if k!='definition_dependencies'}
        for notation in ('full','compact'):
            output=format_graph(document,notation);assert parse(output)==parse(transcribe(output,alphabet='v2'))==document
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==document
    reading=json.loads(text(READING));assert reading['segments']==alignment()['segments']
    assert hashlib.sha256((ROOT/reading['facsimile_path']).read_bytes()).hexdigest()==reading['facsimile_sha256']
    paths=set(files)|{PARENT,JUDGMENT,READING,reading['facsimile_path'],'data/einstein-law-characterization-basis-v1.json',
        'artifacts/written-units-v1/einstein-1905.json','reports/written-units-v1.json','tests/test_intellectual_credit.py','tests/test_intellectual_credit_description.py','docs/intellectual-credit-v1.md'}
    paths.update('scripts/'+n+'.py' for n in ('compose_intellectual_credit','check_intellectual_credit','compose_personal_criteria',
        'compose_origin_clock','compose_limits','compose_situated_criticism','check_described_appraisals','check_rod_setup'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','finite_semantics','extraction','meaning_basis','script','linking','specialization'))
    return dict(status='partial_credit_for_several_valuable_inputs',document=SOURCE,basis_audits=audits,
        source=source_checks(),adapter=adapter_checks(),attribution=attribution_check(),descriptions=description_checks(),
        reused_judgment_identical=True,disquotations_removed=specialized.disquotations_removed,
        statements_preserved=204,new_author_attributions=1,roundtrips=True,cli_parse=True,alignment=alignment(),
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Intellectual contribution, nonfactive credit and plurality checked',flush=True)


if __name__=='__main__':main()
