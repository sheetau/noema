"""Check modal answer candidates and presentation without asserting answers."""
import argparse
import hashlib
from itertools import product
import json
import subprocess
import sys
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from scripts.compose_exploratory_question import ROOT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,PRIMITIVES,MEANINGS,build,closure

REPORT=ROOT/'reports/exploratory-question-v1.json'
DOMAIN=('author','present','prior','trial','extra','partial','full','episode','other_episode','other')
SCENES=('actual','possible','outside','now')


def forbidden(*args):raise ValueError('Unknown interpretation')


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=values,
        max_steps=500000,memoize_definitions=False,memoize_expressions=False)]


def source_document(answer=False):
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'))
    doc['declarations']=closure(doc,['hzld'] if answer else ['hzle'])
    doc['statements']=[] if answer else doc['statements'][-1:]
    if answer:doc=parse(format_graph(doc,'compact')+'r jextent[] a.q[h[k hzld[]][k jextent[]]].')
    return doc


def modal_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+
        'r jbase[] d.r jextent[] a.r jpossible[d d] c.r jtarget[a d] c.'+
        'q[h[k rqrt[k jbase[] p jpossible p jtarget]][k jextent[]]].')
    count=0
    for bits in product((False,True),repeat=6):
        possible=dict(zip(SCENES[:3],bits[:3],strict=True));target=dict(zip(SCENES[:3],bits[3:],strict=True))
        values=dict(jbase=lambda:'actual',jextent=lambda:'partial',
            jpossible=lambda base,case:base=='actual' and possible.get(case,False),
            jtarget=lambda extent,case:extent=='partial' and target.get(case,False))
        expected=[any(possible[w] and target[w] for w in SCENES[:3])]
        assert evaluate(doc,values)==expected,bits;count+=1
    return dict(truth_combinations=count,empty_accessibility_produces_no_candidate=True)


def answer_model(doc,variant='baseline',extent='partial'):
    values={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    values.update(hzik=lambda:'present',hzjn=lambda:'prior',hzjl=lambda:'actual',jextent=lambda:extent)
    world='actual' if variant in ('actual_only','actual_possible') else 'possible'
    extents=('partial','full') if variant=='multiple_extents' else ('partial',)
    def possible(base,candidate):
        if variant=='unknown_possibility':return forbidden()
        return variant!='empty_possible' and (base,candidate)==('actual','actual' if variant=='actual_possible' else 'possible')
    def chance(episode,ctx):
        if variant=='unknown_chance' and ctx==world:return forbidden()
        return variant!='no_chance' and (episode,ctx)==('episode',world)
    def causes(episode,first,second,extent,ctx):
        return variant!='no_cause' and (episode,first,second,ctx)==('other_episode' if variant=='split_episodes' else 'episode',
            'other' if variant=='other_first_document' else 'present','other' if variant=='other_second_document' else 'prior',world) and extent in (
                ('full',) if variant=='other_causal_extent' else extents)
    def agrees(first,second,extent,ctx):
        if variant=='unknown_agreement' and ctx==world:return forbidden()
        return variant!='no_agreement' and (first,second,ctx)==('present','prior','outside' if variant=='split_contexts' else world) and extent in extents
    values.update(hzku=possible,hzkw=chance,hzkx=causes,hzkv=agrees,
        dg=lambda episode,ctx:variant!='no_occurrence' and episode in ('episode','other_episode') and ctx==world)
    return values


def causal_checks():
    doc=source_document(True);count=0
    for bits in product((False,True),repeat=4):
        values=answer_model(doc)
        for name,bit in zip(('dg','hzkw','hzkx','hzkv'),bits,strict=True):
            fn=values[name];values[name]=lambda *args,fn=fn,bit=bit:bit and fn(*args)
        assert evaluate(doc,values)==[all(bits)];count+=1
    variants=('baseline','actual_only','actual_possible','empty_possible','no_occurrence','no_chance','no_cause','no_agreement',
        'split_episodes','other_first_document','other_second_document','other_causal_extent','split_contexts')
    rows={}
    for variant in variants:
        rows[variant]=evaluate(doc,answer_model(doc,variant))
        assert rows[variant]==[variant in ('baseline','actual_possible')],(variant,rows[variant])
    for extent in ('partial','full'):assert evaluate(doc,answer_model(doc,'multiple_extents',extent))==[True]
    for variant in ('unknown_possibility','unknown_chance','unknown_agreement'):
        try:evaluate(doc,answer_model(doc,variant))
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(variant)
    return dict(condition_combinations=count,contrasts=rows,multiple_candidates_without_maximum=True,unknown_answers_refused=True)


def presentation_model(doc,variant='baseline',seen=None):
    # Every primitive used only inside the quoted question stays unknown.
    values={d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
    values.update(wa=lambda:'author',hzik=lambda:'present',hzjm=lambda:'now',hzjl=lambda:'actual',hzla=lambda:'trial')
    def permits(person,document,moment,ctx):
        if variant=='unknown_stance':return forbidden()
        return variant!='no_stance' and (person,document,moment,ctx)==('other' if variant=='other_person' else 'author',
            'other' if variant=='other_document' else 'present','possible' if variant=='other_time' else 'now',
            'outside' if variant=='other_context' else 'actual')
    def assigns(person,document,role,ctx):
        if variant=='unknown_role':return forbidden()
        if variant=='empty_roles':return False
        if (person,document,ctx)==('author','present','actual'):
            return role=='trial' or variant=='extra_role' and role=='extra'
        return variant=='other_person_role' and (person,document,role,ctx)==('other','present','extra','actual') or (
            variant=='other_document_role' and (person,document,role,ctx)==('author','other','extra','actual')) or (
            variant=='other_context_role' and (person,document,role,ctx)==('author','present','extra','outside'))
    def exploratory(role,description,ctx):
        if variant=='unknown_trial':return forbidden()
        syntax=json.loads(description.syntax)
        if seen is not None:seen.append(syntax)
        return (role,ctx)==('extra' if variant=='other_trial_role' else 'trial','actual') and syntax=={
            'kind':'call','symbol':'other' if variant=='other_question' else 'hzld','arguments':[]}
    values.update(hzlb=permits,hzkz=assigns,hzky=exploratory)
    return values


def presentation_checks():
    doc=source_document();rows={};seen=[]
    variants=('baseline','no_stance','other_person','other_document','other_time','other_context','empty_roles','extra_role',
        'other_person_role','other_document_role','other_context_role','other_trial_role','other_question')
    for variant in variants:
        actual=evaluate(doc,presentation_model(doc,variant,seen));rows[variant]=actual
        assert actual==[variant in ('baseline','other_person_role','other_document_role','other_context_role')],(variant,actual)
    assert seen and all(x=={'kind':'call','symbol':'hzld','arguments':[]} for x in seen)
    for variant in ('unknown_stance','unknown_role','unknown_trial'):
        try:evaluate(doc,presentation_model(doc,variant))
        except ValueError as e:assert 'Unknown' in str(e)
        else:raise AssertionError(variant)
    return dict(contrasts=rows,unknown_question_content_not_evaluated=True,question_description_preserved=True,
        unknown_presentational_facts_refused=True,exclusivity_scoped_to_person_document_context=True)


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS);size=len(old.document['declarations'])
    assert new.document['declarations'][:size]==old.document['declarations']
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==23
    added=new.document['declarations'][size:]
    assert {d['name'] for d in added if d['kind']=='primitive'}==set(PRIMITIVES)
    assert {d['name'] for d in added if d['kind']=='definition'}==set(MEANINGS)
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY)
    assert lib.document['declarations']==closure(new.document,['rqrt','rqru','rqrv']) and len(lib.entries)==3
    old_names=load_annotations(ROOT,PARENT_BASIS,'data/counterfactual-withholding-identifiers-v1.json').show()['entries']
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries']==old_names
    return dict(previous_statements_preserved=22,previous_declarations_preserved=size,new_primitives=8,new_definitions=6,new_statements=1)


def alignment():
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0020')
    text=unit['text'];start=text.index('die jetzt')
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,len(text)],source=text[start:],
        status='partial_exploratory_modal_question',definitions=['rqrt','rqru','rqrv','hzlc','hzld','hzle'],
        remaining=['Agreement criteria, contingency, modal range, mag/nur reading and full footnote review remain unresolved.'])])


def build_report():
    files=build()
    for name,body in files.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    modal=modal_checks();causal=causal_checks();presentation=presentation_checks();structural=structure()
    for p in (FULL,LIBRARY):
        doc=parse(files[p])
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    facsimile=json.loads((ROOT/'data/author-signature-facsimile-v1.json').read_text(encoding='utf-8'))
    for p,h in facsimile['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    paths=set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|set(facsimile['source_sha256'])|{
        'data/author-signature-facsimile-v1.json','data/counterfactual-withholding-identifiers-v1.json',
        'scripts/compose_exploratory_question.py','scripts/check_exploratory_question.py','scripts/compose_subject_bound_departure.py',
        'scripts/compose_calendar_dateline.py','docs/exploratory-question-v1.md','tests/test_exploratory_question.py',
        'noema/__init__.py','noema/resources/lexicon.json','noema/resources/alphabet-v1.json','noema/resources/alphabet-v2.json'}
    paths.update('noema/'+n+'.py' for n in ('constructed','constructed_discourse','constructed_semantics','discourse','extraction',
        'grammar','guarded_ranked_semantics','identifiers','meaning_basis','meaning_catalog','ranked','ranked_discourse','script','semantics'))
    parent=(ROOT/load_catalog(ROOT,PARENT_BASIS).document_path).read_text(encoding='utf-8')
    return dict(status='partial_exploratory_question_checked',document=FULL,modal=modal,causal=causal,presentation=presentation,
        structure=structural,alignment=alignment(),roundtrips=True,cli_parse=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        size_accounting=dict(manuscript_characters=len(files[FULL]),additional_manuscript_characters=len(files[FULL])-len(parent),
            generic_library_characters=len(files[LIBRARY]),annotation_bytes=len(files[ANNOTATIONS].encode('utf-8')),
            note='Includes declarations and references; not a source compression ratio.'),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Modal extent question and provisional presentation checked')


if __name__=='__main__':main()
