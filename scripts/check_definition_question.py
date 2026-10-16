"""Check a typed definition question independently of its attributed answer."""
import argparse,hashlib,json,subprocess,sys
from copy import deepcopy
from functools import lru_cache
from itertools import product
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,Content
from noema.diagnostic_short_circuit import lower
from noema.script import transcribe
from scripts.compose_definition_question import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,CODE,QCODE,MEANINGS,PRIMITIVES,build
from scripts.compose_qualified_utterance import closure
from scripts.check_norm_bound_choice import structure as parent_structure
from scripts.check_rod_setup import guarded

REPORT=ROOT/'reports/definition-question-v1.json'
DOMAIN=('question','answer','author','other')
SCENES=('context','other')


@lru_cache(None)
def text(path):return (ROOT/path).read_text(encoding='utf-8')


def evaluate(doc,values,indices=None,*,short=True,memoize=True):
    if indices is not None:
        doc=deepcopy(doc);doc['statements']=[doc['statements'][i] for i in indices]
    names={d['name'] for d in doc['declarations'] if d['kind']=='primitive'};values={n:values[n] for n in names}
    if short:doc,values=lower(doc,values)
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=values,
        max_steps=2_000_000,memoize_definitions=memoize,memoize_expressions=memoize)]


@lru_cache(None)
def fixture(path=LIBRARY):
    doc=parse(text(path));doc['statements']=[]
    extra='''r jdqreference[a] e.r jdqcandidate[a] e.r jdqalias[a] e.
r jdqquestion[] a.r jdqanswer[] a.r jdqauthor[] a.r jdqcontext[] d.'''
    extra+='r jdqpresents[a a '+QCODE+' d] c.r jdqdefines[a a '+CODE+' d] c.r jdqbefore[a a d] c.r jdqresponds[a a a d] c.'
    ref='r[p jdqreference]';candidate='r[p jdqcandidate]'
    pair='k rqqs[k jdqquestion[] k jdqanswer[] k jdqauthor[] k jdqcontext[] '+ref+' '+candidate+' p jdqpresents p jdqdefines p jdqbefore p jdqresponds]'
    questions=['h[k rqqq['+ref+']]['+candidate+']','k rqqp['+ref+' '+candidate+']',
        'e[k rqqr['+ref+']][r b[c[p rqqq]['+ref+']]]',pair,
        'u[e[k rqqr['+ref+']][k rqqr[r[p jdqalias]]]]',
        'h[s[k rqqr['+ref+']]]['+candidate+']']
    return parse(format_graph(doc,'compact')+extra+''.join('q['+q+'].' for q in questions))


def query_syntax(reference='jdqreference'):
    return dict(kind='apply',function=dict(kind='function_ref',symbol='rqqq'),
        arguments=[dict(kind='quote',body=dict(kind='function_ref',symbol=reference))])


def model(doc,reference=3,candidate=3,bits=(True,True,True,True,True),unknown=False):
    distinct,presented,defined,before,responded=bits
    def content(mask,person):
        if unknown:raise ValueError('unknown property interpretation')
        index=0 if person in ('question','author') else 1
        return Content(SCENES,tuple(bool(mask&(1<<(2*index+i))) for i in range(2)))
    values=guarded(doc)
    values.update(jdqreference=lambda p:content(reference,p),jdqcandidate=lambda p:content(candidate,p),jdqalias=lambda p:content(reference,p),
        jdqquestion=lambda:'question',jdqanswer=lambda:'answer' if distinct else 'question',jdqauthor=lambda:'author',jdqcontext=lambda:'context',
        jdqpresents=lambda node,author,code,scene:presented and (node,author,scene)==('question','author','context') and code.rank==1 and json.loads(code.syntax)==query_syntax(),
        jdqdefines=lambda node,author,code,scene:defined and (node,author,scene)==('answer','author','context') and code.rank==0 and json.loads(code.syntax)==dict(kind='function_ref',symbol='jdqcandidate'),
        jdqbefore=lambda first,last,scene:before and (first,last,scene)==('question','answer','context'),
        jdqresponds=lambda author,first,last,scene:responded and (author,first,last,scene)==('author','question','answer','context'))
    return values


def source_model(doc,variant='baseline'):
    values=guarded(doc)
    values.update(wa=lambda:'author',wh=lambda:'context',wb=lambda:'answer',hzia=lambda:'answer' if variant=='same_node' else 'question')
    expected_query=query_syntax('bf' if variant=='different_reference' else 'bi')
    def presented(node,author,code,scene):
        return variant!='missing_presentation' and (node,author,scene)==('other' if variant=='other_question_node' else 'question',
            'other' if variant=='other_author' else 'author','other' if variant=='other_context' else 'context') and code.rank==1 and json.loads(code.syntax)==expected_query
    def defined(node,author,code,scene):
        return variant!='missing_definition' and (node,author,scene)==('other' if variant=='other_answer_node' else 'answer','author','context') and code.rank==0 and (
            json.loads(code.syntax)==dict(kind='function_ref',symbol='bf' if variant=='different_answer' else 'bi'))
    values.update(hzib=presented,ua=defined,
        ue=lambda a,b,c:(a,b,c)==(('answer','question','context') if variant=='reverse_order' else ('question','answer','context')),
        hzcs=lambda author,a,b,c:(author,a,b,c)==(('author','answer','question','context') if variant=='reverse_response' else ('author','question','answer','context')))
    return values


@lru_cache(None)
def checks():
    doc=fixture();count=0
    for reference,candidate in product(range(16),repeat=2):
        actual=evaluate(doc,model(doc,reference,candidate),indices=(0,1,5))
        assert actual==[reference==candidate]*3,(reference,candidate,actual);count+=1
    isolated=0
    for changed_person,changed_scene in product(DOMAIN,SCENES):
        values=model(doc,0,0)
        values['jdqcandidate']=lambda person,p=changed_person,s=changed_scene:Content(SCENES,tuple(person==p and scene==s for scene in SCENES))
        assert evaluate(doc,values,indices=(0,1,5))==[False]*3
        isolated+=1
    records=0
    for bits in product((False,True),repeat=5):
        actual=evaluate(doc,model(doc,3,12,bits),indices=(3,))
        assert actual==[all(bits)],(bits,actual);records+=1
    comparison={}
    for path in (LIBRARY,FULL):
        doc=fixture(path)
        correct=evaluate(doc,model(doc,3,3));wrong=evaluate(doc,model(doc,3,12))
        assert correct==[True]*6 and wrong==[False,False,True,True,True,False]
        comparison[path]=dict(correct=correct,attributed_wrong_answer=wrong)
        def forbidden(*args):raise AssertionError('Question description construction executed its content')
        assert evaluate(doc,{n:forbidden for n in model(doc)},indices=(2,4))==[True,True]
        # Presentation of a wrong or unknown answer does not run its candidate test.
        assert evaluate(doc,model(doc,unknown=True),indices=(3,))==[True]
    unknown_refused=False
    try:evaluate(doc,model(doc,unknown=True),indices=(0,))
    except ValueError as exc:assert 'unknown property' in str(exc);unknown_refused=True
    else:raise AssertionError('Unknown content accepted as an answer')
    body=deepcopy(doc);body['statements']=[]
    enumeration=parse(format_graph(body,'compact')+'q[k rqqq[r[p jdqreference]]].')
    try:evaluate(enumeration,model(enumeration))
    except ValueError as exc:
        assert 'description' in str(exc).lower();enumeration_error=str(exc)
    else:raise AssertionError('Unbounded description answers were finitely enumerated')
    try:parse(format_graph(body,'compact')+'q[k rqqp[r[p jdqreference] r b[p jdqcandidate]]].')
    except ValueError:rank_refused=True
    else:raise AssertionError('A rank-one candidate was accepted as rank zero')
    doc=fixture()
    for candidate in (3,12):
        assert evaluate(doc,model(doc,3,candidate),short=False,memoize=False)==comparison[LIBRARY]['correct' if candidate==3 else 'attributed_wrong_answer']
    full=parse(text(FULL));source={}
    for variant in ('baseline','missing_presentation','missing_definition','other_question_node','other_answer_node','other_author',
        'other_context','different_reference','different_answer','reverse_order','reverse_response','same_node'):
        actual=evaluate(full,source_model(full,variant),indices=(0,));assert actual==[variant=='baseline'],(variant,actual)
        source[variant]=actual
    return dict(property_profile_pairs=count,isolated_person_scene_differences=isolated,presentation_combinations=records,question_answer_checks=comparison,
        source_contrasts=source,unknown_answer_refused=unknown_refused,unbounded_answer_enumeration_refused=enumeration_error,
        wrong_candidate_rank_refused=rank_refused,nonfactive_question_and_answer_presentation=True,unlowered_uncached_cases=2)


def structure():
    inherited=parent_structure();old=parse(text(PARENT));doc=parse(text(FULL));basis=json.loads(text(BASIS))
    assert doc['declarations'][:len(old['declarations'])]==old['declarations'] and doc['statements'][1:]==old['statements']
    assert doc['statements'][0]==dict(kind='assert',body=dict(kind='call',symbol='hzic',arguments=[]))
    added=doc['declarations'][len(old['declarations']):]
    definitions={d['name'] for d in added if d['kind']=='definition'};primitives={d['name'] for d in added if d['kind']=='primitive'}
    assert definitions==set(MEANINGS)==set(basis['definitions']) and primitives==set(PRIMITIVES)==set(basis['primitives'])
    assert {d['name']:{k:d[k] for k in ('parameters','result')} for d in added}==basis['new_signatures']
    assert parse(text(LIBRARY))['declarations']==closure(doc,['rqqs'])
    return dict(inherited_basis_checked=inherited['inherited_basis_checked'],previous_statements_preserved=len(old['statements']),
        previous_declarations_preserved=True,new_definitions=len(definitions),new_primitives=len(primitives),new_attribution_statements=1)


def alignment():
    units=json.loads(text('artifacts/written-units-v1/kant-1784.json'))['units'];lookup={u['id']:u for u in units}
    rows=[]
    for key,end in (('u0005',None),('u0006',None),('u0008',85)):
        unit=lookup['kant-1784:'+key];end=len(unit['text']) if end is None else end
        rows.append(dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[0,end],source=unit['text'][:end],
            status='partial_definition_question_response_framing',definitions=['rqqq','rqqr','rqqs','hzic'],
            remaining=['adequacy of extensional criterion as a definition question','inherited interpretation of bi and its foundational concepts','complete semantic unit review']))
    return dict(segments=rows)


def build_report():
    files=build()
    for name,body in files.items():assert text(name)==body,name
    for path in (FULL,LIBRARY):
        doc=parse(text(path))
        for notation in ('full','compact'):
            body=format_graph(doc,notation);assert parse(body)==parse(transcribe(body,alphabet='v2'))==doc
        result=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/path)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(result.stdout)==doc
    paths=set(files)|{PARENT,PARENT_BASIS,'reports/norm-bound-choice-v1.json','artifacts/written-units-v1/kant-1784.json',
        'docs/definition-question-v1.md','tests/test_definition_question.py'}
    paths.update('scripts/'+n+'.py' for n in ('compose_definition_question','check_definition_question','check_norm_bound_choice','check_outcome_choice',
        'check_unilateral_decision','check_relational_departure','check_quoted_outcomes','compose_origin_clock','compose_limits',
        'compose_situated_criticism','compose_qualified_utterance','check_rod_setup'))
    paths.update('noema/'+n+'.py' for n in ('grammar','language','discourse','semantics','meaning_basis','script','constructed',
        'constructed_discourse','constructed_semantics','guarded_ranked_semantics','diagnostic_short_circuit'))
    return dict(status='partial_title_question_and_opening_definition_response',document=FULL,
        finite=checks(),structure=structure(),alignment=alignment(),roundtrips=True,cli_parse=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');options=cli.parse_args();report=build_report()
    if options.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Definition question, candidate checks and source attribution checked',flush=True)


if __name__=='__main__':main()
