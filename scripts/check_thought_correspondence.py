"""Check bilateral coverage, exact extents and the source question connection."""
import argparse
import hashlib
from itertools import product
import json
import subprocess
import sys
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.diagnostic_short_circuit import lower
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from noema.semantic_reviews import selection_binding
from scripts import check_exploratory_question as previous
from scripts.check_class_restricted_roles import semantic_entry
from scripts.compose_thought_correspondence import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,PRIMITIVES,build,closure

REPORT=ROOT/'reports/thought-correspondence-v1.json'
DOMAIN=('first','second','topic','other_topic','one','two')
SCENES=('actual','elsewhere')


def evaluate(doc,values,diagnostic=False,individuals=DOMAIN,situations=SCENES):
    if diagnostic:doc,values=lower(doc,values)
    return [r['value'] for r in evaluate_document(doc,individuals=individuals,situations=situations,
        primitives=values,max_steps=5000000,memoize_definitions=False,memoize_expressions=False)]


def generic_document(extent=False):
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    doc['declarations']=closure(doc,['rqry' if extent else 'rqrx'])
    text=format_graph(doc,'compact')+'r jfirst[] a.r jsecond[] a.r jaspect[] a.r jctx[] d.r jattr[a a a d] c.r jmatch[a a a d] c.'
    if extent:
        text+='r jdomain[a d] c.r jinclude[a a d] c.q[k rqry[k jfirst[] k jsecond[] k jaspect[] k jctx[] p jdomain p jinclude p jattr p jmatch]].'
    else:text+='q[k rqrx[k jfirst[] k jsecond[] k jaspect[] k jctx[] p jattr p jmatch]].'
    return parse(text)


def constants():return dict(jfirst=lambda:'first',jsecond=lambda:'second',jaspect=lambda:'topic',jctx=lambda:'actual')


def covered(left,right,matches):
    return bool(left and right and all(any((a,b) in matches and (b,a) in matches for b in right) for a in left)
        and all(any((a,b) in matches and (b,a) in matches for a in left) for b in right))


def coverage_checks():
    doc=generic_document();count=0;items=('one','two');pairs=list(product(items,repeat=2))
    for bits in product((False,True),repeat=8):
        left={a for a,b in zip(items,bits[:2]) if b};right={a for a,b in zip(items,bits[2:4]) if b}
        matches={p for p,b in zip(pairs,bits[4:]) if b};values=constants()
        values.update(jattr=lambda d,a,i,c:a=='topic' and c=='actual' and i in (left if d=='first' else right if d=='second' else set()),
            jmatch=lambda a,b,t,c:t=='topic' and c=='actual' and (a,b) in matches)
        expected=[covered(left,right,matches)]
        assert evaluate(doc,values)==expected,bits
        assert evaluate(doc,values,True)==expected,bits
        count+=1
    return dict(combinations=count,ordinary_and_diagnostic_agree=True,
        bilateral_coverage_not_intersection=True,empty_and_one_sided_profiles_refused=True)


def extent_checks():
    doc=generic_document(True);topics=('topic','other_topic');count=0;zero=0
    for bits in product((False,True),repeat=6):
        domain={a for a,b in zip(topics,bits[:2]) if b};agreed={a for a,b in zip(topics,bits[2:4]) if b}
        included={a for a,b in zip(topics,bits[4:]) if b};values=constants()
        values.update(jdomain=lambda a,c:c=='actual' and a in domain,
            jinclude=lambda e,a,c:e=='topic' and c=='actual' and a in included,
            jattr=lambda d,a,i,c:c=='actual' and a in topics and (d,i) in (('first','one'),('second','two')),
            jmatch=lambda a,b,t,c:c=='actual' and t in agreed and (a,b) in (('one','two'),('two','one')))
        expected=[bool(domain) and included==agreed&domain]
        assert evaluate(doc,values,True)==expected,bits
        # A representative complete model also checks the saved, eager graph.
        if bits in ((True,True,True,False,True,False),(True,False,False,False,False,False),(False,)*6):
            assert evaluate(doc,values)==expected
        if expected[0] and not included:zero+=1
        count+=1
    assert zero>0
    return dict(combinations=count,empty_agreement_extent_allowed=zero,empty_comparison_domain_refused=True,
        omitted_matching_topics_and_extra_topics_refused=True,eager_examples=3)


def contrasts():
    doc=generic_document();rows={}
    for variant in ('baseline','same_item','many_to_one','unmatched_right','missing_first','missing_second','empty_both',
        'one_way','wrong_topic','wrong_scene','wrong_document','split_match_context'):
        values=constants();left={'one'};right={'two'}
        if variant=='same_item':right={'one'}
        if variant=='many_to_one':left={'one','two'}
        if variant=='unmatched_right':right={'one','two'}
        if variant in ('missing_first','empty_both'):left=set()
        if variant in ('missing_second','empty_both'):right=set()
        def attributed(d,a,i,c):
            topic='other_topic' if variant=='wrong_topic' and d=='second' else 'topic'
            scene='elsewhere' if variant=='wrong_scene' and d=='second' else 'actual'
            second='other_topic' if variant=='wrong_document' else 'second'
            return a==topic and c==scene and i in (left if d=='first' else right if d==second else set())
        match={('one','two'),('two','one')}
        if variant=='same_item':match={('one','one')}
        if variant=='many_to_one':match.add(('two','two'))
        if variant=='one_way':match={('one','two')}
        values.update(jattr=attributed,jmatch=lambda a,b,t,c:t=='topic' and (a,b) in match and c==(
            'elsewhere' if variant=='split_match_context' and (a,b)==('two','one') else 'actual'))
        result=evaluate(doc,values);assert result==[variant in ('baseline','same_item','many_to_one')],(variant,result)
        rows[variant]=result
    for name in ('jattr','jmatch'):
        values=constants();values.update(jattr=lambda d,a,i,c:a=='topic' and c=='actual' and (d,i) in (('first','one'),('second','two')),
            jmatch=lambda *a:True);values[name]=previous.forbidden
        for diagnostic in (False,True):
            try:evaluate(doc,values,diagnostic)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError((name,diagnostic))
    return dict(cases=rows,unknown_inputs_refused=True,different_content_objects_may_correspond=True,
        no_content_truth_evaluation=True)


def source_document(answer=True):
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'))
    doc['declarations']=closure(doc,['hzld' if answer else 'hzle'])
    doc['statements']=[] if answer else doc['statements'][-1:]
    if answer:doc=parse(format_graph(doc,'compact')+'r jextent[] a.q[h[k hzld[]][k jextent[]]].')
    return doc


def source_model(doc,variant='baseline'):
    values=previous.answer_model(doc,variant);values.pop('hzkv',None)
    values.update(hzlf=lambda aspect,ctx:aspect=='full' and ctx=='possible',
        hzlg=lambda extent,aspect,ctx:variant!='zero_agreement' and (extent,aspect,ctx)==('partial','full','possible'),
        hzlh=lambda document,aspect,item,ctx:aspect=='full' and ctx=='possible' and (
            (document,item)==('present','author') or variant!='missing_second' and (document,item)==('prior','other') or
            variant=='unmatched_right' and (document,item)==('prior','extra')),
        hzli=lambda left,right,aspect,ctx:variant!='zero_agreement' and aspect=='full' and ctx=='possible' and
            (left,right) in ({('author','other')} if variant=='one_way' else {('author','other'),('other','author')}))
    if variant=='unknown_match':values['hzli']=previous.forbidden
    return values


def source_checks():
    doc=source_document();rows={}
    for variant in ('baseline','zero_agreement','missing_second','unmatched_right','one_way','no_occurrence','no_chance',
        'no_cause','split_episodes','other_first_document','other_second_document','other_causal_extent','empty_possible'):
        rows[variant]=evaluate(doc,source_model(doc,variant),True,previous.DOMAIN,previous.SCENES)
        assert rows[variant]==[variant in ('baseline','zero_agreement')],(variant,rows[variant])
    try:evaluate(doc,source_model(doc,'unknown_match'),True,previous.DOMAIN,previous.SCENES)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown comparison was guessed')
    presentation=source_document(False);seen=[]
    assert evaluate(presentation,previous.presentation_model(presentation,seen=seen),False,previous.DOMAIN,previous.SCENES)==[True]
    assert seen and all(x=={'kind':'call','symbol':'hzld','arguments':[]} for x in seen)
    return dict(contrasts=rows,source_diagnostic=True,unknown_comparison_refused=True,
        presentation_without_evaluating_comparison=True,question_description_preserved=True)


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    before={d['name']:d for d in old.document['declarations']};after={d['name']:d for d in new.document['declarations']}
    assert set(after)-set(before)==set(PRIMITIVES)|{'rqrx','rqry'} and not set(before)-set(after)
    assert [n for n in before if before[n]!=after[n]]==['hzkv']
    assert before['hzkv']['kind']=='primitive' and after['hzkv']['kind']=='definition'
    assert before['hzkv']['parameters']==[p['sort'] for p in after['hzkv']['parameters']]
    assert before['hzkv']['result']==after['hzkv']['result']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==23
    for n in before:
        if n!='hzkv':assert semantic_entry(old.entries[n])==semantic_entry(new.entries[n]),n
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries']==load_annotations(
        ROOT,PARENT_BASIS,'data/class-restricted-roles-identifiers-v1.json').show()['entries']
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY);assert len(lib.entries)==2
    signature_before=selection_binding(old,[16]);signature_after=selection_binding(new,[16])
    assert signature_before['statements']==signature_after['statements']
    assert signature_before['dependencies']==signature_after['dependencies']
    return dict(replaced_primitive='hzkv',new_local_primitives=4,new_generic_definitions=2,
        previous_statements_preserved=23,other_meanings_preserved=True,signature_before=signature_before,signature_after=signature_after)


def alignment():
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0020')
    text=unit['text'];start=text.index('wiefern')
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,len(text)],source=text[start:],
        status='partial_explicit_topic_correspondence_reading',definitions=['rqrx','rqry','hzkv','hzlc','hzld'],
        remaining=['Topic selection, attribution completeness, content correspondence criteria, contingency and full source review.'])])


def build_report():
    files=build()
    for name,body in files.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    coverage=coverage_checks();extent=extent_checks();contrast=contrasts();source=source_checks();structural=structure()
    for p in (FULL,LIBRARY):
        doc=parse(files[p])
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    previous_report=json.loads((ROOT/'reports/class-restricted-roles-v1.json').read_text(encoding='utf-8'))
    paths=set(previous_report['source_sha256'])|set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|{
        'reports/class-restricted-roles-v1.json','scripts/compose_thought_correspondence.py','scripts/check_thought_correspondence.py',
        'tests/test_thought_correspondence.py','docs/thought-correspondence-v1.md'}
    for p,h in previous_report['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    return dict(status='partial_topic_correspondence_checked',document=FULL,coverage=coverage,extent=extent,contrasts=contrast,
        source=source,structure=structural,alignment=alignment(),roundtrips=True,cli_parse=True,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        size_accounting=dict(manuscript_characters=len(files[FULL]),
            additional_manuscript_characters=len(files[FULL])-len((ROOT/PARENT).read_text(encoding='utf-8')),
            generic_library_characters=len(files[LIBRARY]),note='Counts shared definitions; not a compression claim.'),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Bilateral topic correspondence and exact agreement extents checked')


if __name__=='__main__':main()
