"""Check explanatory candidates and preserve a nonfactive title question."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts.compose_explanatory_question import ROOT,FULL,CORE,LIBRARY,BASIS,ANNOTATIONS,CODE,CRITERION,QCODE,MEANINGS,LIMITS,parent,closure,build

REPORT='reports/explanatory-question-v1.json'
READING='data/explanatory-question-reading-v1.json'
INVENTORY='artifacts/written-units-v1/kant-1784.json'
DOMAIN=('question','answer','author','other')
SCENES=('context','other')


def unknown(*args):raise ValueError('Unknown explanatory-question input')


def ref(code,name):return json.loads(code.syntax)==dict(kind='function_ref',symbol=name)


def query_syntax(reference='za',context='zd',criterion='ze'):
    quote=lambda body:dict(kind='quote',body=body)
    return dict(kind='apply',function=dict(kind='function_ref',symbol='rqwd'),arguments=[
        quote(dict(kind='function_ref',symbol=reference)),quote(dict(kind='call',symbol=context,arguments=[])),
        quote(dict(kind='function_ref',symbol=criterion))])


def evaluate(doc,values,indices=None):
    if indices is not None:
        doc=deepcopy(doc);doc['statements']=[doc['statements'][i] for i in indices]
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=1000000,memoize_definitions=False,memoize_expressions=False)]


@lru_cache(None)
def fixture():
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+'r za[a] e.r zb[a] e.r zc[a] e.r zd[] d.r ze['+CODE+' '+CODE+' d] c.'
    text+='r zf[] a.r zg[] a.r zh[] a.r zi[a a '+QCODE+' d] c.r zj[a a '+CODE+' d] c.r zk[a a d] c.r zl[a a a d] c.'
    args='r[p za] r[k zd[]] r[p ze]'
    bodies=['h[k rqwd['+args+']][r[p zb]]','k rqqp[r[p za] r[p zb]]',
        'h[s[k rqwe['+args+']]][r[p zb]]',
        'e[k rqwe['+args+']][r b[c[p rqwd]['+args+']]]',
        'k rqwf[k zf[] k zg[] k zh[] '+args+' r[p zb] p zi p zj p zk p zl]']
    return parse(text+''.join('q['+b+'].' for b in bodies))


def model(reference=3,candidate=3,explains=True,variant='baseline',bits=(True,)*5):
    distinct,presents,defines,before,responds=bits
    def content(mask,p):
        offset=0 if p in ('question','author') else 2
        return Content(SCENES,tuple(bool(mask&(1<<(offset+i))) for i in range(2)))
    return dict(za=lambda p:content(reference,p),zb=lambda p:content(candidate,p),zc=lambda p:content(reference,p),
        zd=lambda:'context',
        ze=lambda r,c,s:explains and ref(r,'zb' if variant=='reversed_reference' else 'za') and ref(c,'za' if variant=='reversed_reference' else 'zc' if variant=='other_candidate' else 'zb') and s==('other' if variant=='other_context' else 'context'),
        zf=lambda:'question',zg=lambda:'answer' if distinct else 'question',zh=lambda:'author',
        zi=lambda n,a,q,s:presents and (n,a,s)==('question','author','context') and q.rank==1 and json.loads(q.syntax)==query_syntax(),
        zj=lambda n,a,c,s:defines and (n,a,s)==('answer','author','context') and ref(c,'zb'),
        zk=lambda n,a,s:before and (n,a,s)==('question','answer','context'),
        zl=lambda a,n,r,s:responds and (a,n,r,s)==('author','question','answer','context'))


def candidate_checks():
    doc=fixture();count=0
    for reference,candidate,explains in product(range(16),range(16),(False,True)):
        result=evaluate(doc,model(reference,candidate,explains),[0,1,2])
        assert result==[reference==candidate and explains,reference==candidate,reference==candidate and explains],(reference,candidate,explains,result);count+=1
    isolated=0
    for p,s in product(DOMAIN,SCENES):
        m=model(0,0);m['zb']=lambda person,p=p,s=s:Content(SCENES,tuple(person==p and scene==s for scene in SCENES))
        assert evaluate(doc,m,[0,1,2])==[False]*3;isolated+=1
    contrasts={}
    for variant in ('baseline','reversed_reference','other_candidate','other_context'):
        result=evaluate(doc,model(variant=variant),[0,1,2]);assert result==[variant=='baseline',True,variant=='baseline'];contrasts[variant]=result
    for name in ('za','zb','zd','ze'):
        m=model();m[name]=unknown
        try:evaluate(doc,m,[0])
        except ValueError as e:assert 'Unknown explanatory' in str(e)
        else:raise AssertionError(name)
    # Equal descriptions do not entail explanatory adequacy; an expanded
    # defined description may nevertheless count as an explanation.
    same=deepcopy(doc);same['statements']=[]
    same=parse(format_graph(same,'compact')+'q[h[k rqwd[r[p za] r[k zd[]] r[p ze]]][r[p za]]].')
    for allowed in (False,True):
        m=model();m['ze']=lambda r,c,s:allowed and ref(r,'za') and ref(c,'za') and s=='context'
        assert evaluate(same,m)==[allowed]
    return dict(profile_and_explanation_combinations=count,isolated_person_scene_differences=isolated,
        binding_contrasts=contrasts,unknown_inputs_refused=4,same_syntax_not_automatically_circular_or_adequate=True,uncached=True)


def presentation_checks():
    doc=fixture();count=0
    for bits in product((False,True),repeat=5):
        # A presented answer can be wrong and explanatorily inadequate.
        assert evaluate(doc,model(3,12,False,bits=bits),[4])==[all(bits)];count+=1
    m=model()
    for n in ('za','zb','zc','ze'):m[n]=unknown
    assert evaluate(doc,m,[3,4])==[True,True]
    assert evaluate(doc,{n:unknown for n in model()},[3])==[True]
    for name in ('zd','zi','zj','zk','zl'):
        m=model();m[name]=unknown
        try:evaluate(doc,m,[4])
        except ValueError as e:assert 'Unknown explanatory' in str(e)
        else:raise AssertionError(name)
    d=deepcopy(doc);d['statements']=[];text=format_graph(d,'compact')
    enumeration=parse(text+'q[k rqwd[r[p za] r[k zd[]] r[p ze]]].')
    try:evaluate(enumeration,model())
    except ValueError as e:assert 'description' in str(e).lower()
    else:raise AssertionError('Unbounded answer descriptions enumerated')
    try:parse(text+'q[h[k rqwd[r[p za] r[k zd[]] r[p ze]]][r b[p zb]]].')
    except ValueError:pass
    else:raise AssertionError('Wrong-rank candidate accepted')
    return dict(combinations=count,unknown_presentation_inputs_refused=5,description_construction_runs_no_inputs=True,
        wrong_or_unknown_answer_can_be_presented=True,unbounded_enumeration_and_wrong_rank_refused=True,uncached=True)


@lru_cache(None)
def catalog():return load_catalog(ROOT,BASIS)


def source_model(doc,variant='baseline'):
    m={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    expected=query_syntax('bf' if variant=='other_concept' else 'bi','hzjl' if variant=='other_quoted_context' else 'wh',
        'ze' if variant=='other_criterion' else 'hzv6')
    m.update(hzia=lambda:'question',wb=lambda:'question' if variant=='same_node' else 'answer',wa=lambda:'author',wh=lambda:'context',
        hzib=lambda n,a,q,s:variant!='no_question' and (n,a,s)==('other' if variant=='other_node' else 'question',
            'other' if variant=='other_author' else 'author','other' if variant=='other_context' else 'context') and q.rank==1 and json.loads(q.syntax)==expected,
        ua=lambda n,a,c,s:variant!='no_definition' and (n,a,s)==('answer','author','context') and ref(c,'bf' if variant=='other_answer' else 'bi'),
        ue=lambda a,b,s:(a,b,s)==(('answer','question','context') if variant=='reverse_order' else ('question','answer','context')),
        hzcs=lambda a,q,r,s:(a,q,r,s)==(('author','answer','question','context') if variant=='reverse_response' else ('author','question','answer','context')))
    return m


def source_checks():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));rows={}
    question_variants=('baseline','no_definition','other_answer','same_node','reverse_order','reverse_response')
    for variant in ('baseline','no_question','other_node','other_author','other_context','other_concept','other_quoted_context','other_criterion',
        'no_definition','other_answer','same_node','reverse_order','reverse_response'):
        result=evaluate(doc,source_model(doc,variant));assert result==[variant in question_variants,variant=='baseline'],(variant,result);rows[variant]=result
    for name in ('hzib','wh'):
        m=source_model(doc);m[name]=unknown
        try:evaluate(doc,m)
        except ValueError as e:assert 'Unknown explanatory' in str(e)
        else:raise AssertionError(name)
    return dict(cases=rows,all_concept_truth_and_explanation_facts_unknown=True,unknown_presentation_refused=2,uncached=True)


def structure():
    old=parent();new=catalog();assert new.document['declarations'][:-8]==old.document['declarations']
    assert new.document['statements'][1:40]==old.document['statements'][1:] and len(new.document['statements'])==41
    assert all(new.entries[n]==entry for n,entry in old.entries.items())
    idx=json.loads((ROOT/'data/semantic-review-index-v34.json').read_text(encoding='utf-8'))
    for path in idx['works']['kant-1784']['reviews']:
        review=json.loads((ROOT/path).read_text(encoding='utf-8'));indices=[s['index'] for s in review['selection']['statements']]
        assert selection_binding(old,indices)==review['selection']==selection_binding(new,indices)
    opening=next(p for p in idx['works']['kant-1784']['reviews'] if 'u0008' in p)
    review=json.loads((ROOT/opening).read_text(encoding='utf-8'))
    assert 'bi' in review['selection']['dependencies'] and 'bi' in selection_binding(new,[0])['dependencies']
    for name,text in build().items():assert (ROOT/name).read_text(encoding='utf-8')==text,name
    for name in (FULL,CORE,LIBRARY):
        d=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('full','compact'):
            text=format_graph(d,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==d
    assert all(d['kind']=='definition' for d in parse((ROOT/LIBRARY).read_text(encoding='utf-8'))['declarations'])
    return dict(new_definitions=7,new_general_explanation_relation=1,changed_statement_indices=[0],appended_statement_indices=[40],
        other_statements_preserved=39,nine_review_bindings_preserved=True,opening_concept_and_conventions_preserved=True,roundtrips=True)


def reading():
    unit=next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0006')
    scan='artifacts/publication-header-v1/page-481.jpg'
    return dict(status='facsimile_collated_explanatory_title_question',reviewer='assistant_review',document=FULL,meaning_basis=BASIS,
        source=dict(unit=unit['id'],unit_sha256=unit['text_sha256'],text=unit['text'],range=[0,len(unit['text'])]),
        facsimile=dict(path=scan,page=481,visually_inspected=True,url='https://api.digitale-sammlungen.de/iiif/image/v2/bsb10926843_00521/full/full/0/default.jpg'),
        references=['https://korpora.org/Kant/aa08/035.html'],
        observations=['原刊の独立した表題行Was ist Aufklärung?と疑問符を視認した。直前のBeantwortung der Frage:と、参照指示の後にある冒頭の説明を区別した。',
            'was istを、啓蒙という概念の内容・構成を説明する記述を求める問いと読む。個別の啓蒙事例の列挙や別名だけを求める読みではない。',
            '参照する概念biは第一段落で確認した本人の未成熟から自立的能力への移行と同じ内容である。表題の質問は説明を求める提示であり、カントの答えの真実性・十分性を認定する文ではない。'],
        binding=selection_binding(catalog(),[0]),limitations=LIMITS,
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (INVENTORY,scan)})


def build_report():
    results={}
    for name,fn in [('candidate',candidate_checks),('presentation',presentation_checks),('source',source_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    note=reading();assert json.loads((ROOT/READING).read_text(encoding='utf-8'))==note;s=note['source']
    prior='reports/bodily-acquisition-v1.json';old=json.loads((ROOT/prior).read_text(encoding='utf-8'));validate_hashes(ROOT,old['source_sha256'])
    paths=set(build())|set(catalog().source_sha256)|set(old['source_sha256'])|set(note['source_sha256'])|{READING,prior,
        'scripts/compose_explanatory_question.py','scripts/check_explanatory_question.py','tests/test_explanatory_question.py',
        'docs/explanatory-question-v1.md','docs/title-question-review-v1.md','data/semantic-review-index-v34.json'}
    return dict(status='explanatory_title_question_with_separate_answer_presentation',document=FULL,**results,
        alignment=dict(unit=s['unit'],unit_sha256=s['unit_sha256'],range=s['range'],source=s['text'],definitions=list(MEANINGS),
            status='partial_explanatory_title_question',full_semantic_equivalence=False),
        new_covered_characters=0,verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args()
    from scripts.audit_opening_scope import write_exact,encoded
    write_exact(ROOT/READING,encoded(reading()));report=build_report()
    if args.verify_only:assert json.loads((ROOT/REPORT).read_text(encoding='utf-8'))==report
    else:write_exact(ROOT/REPORT,encoded(report))
    print('Explanatory candidates, source question and independent answer presentation checked',flush=True)


if __name__=='__main__':main()
