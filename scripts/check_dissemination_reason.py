"""Check source anchoring and nonfactive authorial reason presentation."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts.compose_dissemination_reason import ROOT,PARENT,PARENT_BASIS,FULL,CORE,BASIS,READING,build

REPORT=ROOT/'reports/dissemination-reason-v1.json'
PEOPLE=('author','conclusion','reason','other')
SCENES=('paragraph','prior_paragraph','future')


def unknown(*args):raise ValueError('Unknown authorial reason relation')


@lru_cache(maxsize=2)
def document(full=False):
    doc=parse((ROOT/(FULL if full else CORE)).read_text(encoding='utf-8'))
    doc['statements']=doc['statements'][-1:]
    return doc


def model(doc,variant='baseline'):
    values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
    def grounds(author,premises,conclusion,context):
        expected={'reason'}
        if variant=='extra_premise':expected.add('other')
        if variant=='reversed_argument':expected={'conclusion'}
        return variant!='missing_reason' and (author,conclusion,context)==(
            'other' if variant=='wrong_author' else 'author',
            'reason' if variant=='reversed_argument' else 'conclusion',
            'prior_paragraph' if variant=='wrong_context' else 'paragraph') and {
                person for person in PEOPLE if premises(person)}==expected
    values.update(wa=lambda:'author',hzp3=lambda:'paragraph',hzp4=lambda:'conclusion',
        hzp5=lambda:'conclusion' if variant=='same_nodes' else 'reason',ud=grounds,
        ue=lambda first,last,context:(first,last,context)==(
            ('reason','conclusion','paragraph') if variant=='reversed_text_order' else
            ('conclusion','reason','future') if variant=='event_time_instead_of_text' else
            ('conclusion','reason','paragraph')))
    return values


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=PEOPLE,situations=SCENES,
        primitives=values,max_steps=3000000,memoize_definitions=False,memoize_expressions=False)]


def relation_checks():
    rows={};doc=document()
    for variant in ('baseline','missing_reason','wrong_author','wrong_context','reversed_argument',
                    'extra_premise','same_nodes','reversed_text_order','event_time_instead_of_text'):
        actual=evaluate(doc,model(doc,variant));assert actual==[variant=='baseline'],(variant,actual);rows[variant]=actual
    full=document(True)
    assert evaluate(full,model(full))==[True]
    for name in ('ud','ue'):
        values=model(doc);values[name]=unknown
        try:evaluate(doc,values)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,unknown_relations_refused=2,
        full_manuscript_last_statement_evaluated_with_all_content_primitives_unknown=True,
        no_new_semantic_relation_primitive=True,all_checks_eager=True)


def nonfactivity_checks():
    doc=deepcopy(document());doc['statements']=[]
    names=('zpremisetruth','zconclusiontruth','zvalidinference','zactualfreedom')
    text=''.join('r '+name+'[] c.' for name in names)
    text+='s[k hzp6[]].'+''.join('q[k '+name+'[]].' for name in names)
    doc=parse(format_graph(doc,'compact')+text);count=0
    for truths in product((False,True),repeat=4):
        values=model(doc)
        values.update({name:(lambda truth=truth:truth) for name,truth in zip(names,truths)})
        actual=evaluate(doc,values);assert actual==[True,*truths],actual;count+=1
    return dict(independent_truth_validity_and_actual_freedom_combinations=count,
        reason_presentation_does_not_assert_content_truth_or_actual_freedom=True)


def source_checks():
    reading=json.loads((ROOT/READING).read_text(encoding='utf-8'))
    unit=next(u for u in json.loads((ROOT/reading['source_inventory']).read_text(encoding='utf-8'))['units']
              if u['id']==reading['source_unit'])
    assert digest(unit['text'].encode('utf-8'))==reading['unit_sha256']
    anchors=reading['anchors'];text=unit['text']
    assert text[anchors['connective']['start']:anchors['connective']['end']]=='Denn'
    assert text[0:128].startswith('Daß aber ein Publikum') and text[0:128].endswith('unausbleiblich.')
    assert text[129:448].startswith('Denn da werden') and text[129:448].endswith('verbreiten werden.')
    assert anchors['conclusion']==dict(symbol='hzp4',start=0,end=128)
    assert anchors['reason']==dict(symbol='hzp5',start=129,end=448)
    scan=reading['facsimile'];assert digest((ROOT/scan['artifact']).read_bytes())==scan['sha256']
    assert scan['visually_checked'] is True and scan['reviewer']=='assistant'
    return dict(source_unit=unit['id'],source_sha256=reading['unit_sha256'],
        exact_connective_range=[129,133],connective='Denn',
        sentence_anchors_locate_content_but_do_not_count_as_content_representation=True,
        original_page=483,visual_collation_is_assistant_judgment_not_independent_human_review=True,
        primary_image_hash_verified=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['declarations'][:-4]==old.document['declarations']
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==33
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    return dict(new_local_references=3,new_semantic_relation_primitives=0,new_compositions=1,
        existing_statements_preserved=32,total_statements=33,seven_review_bindings_preserved=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for name,body in outputs.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/focused-dissemination-v1.json').read_text(encoding='utf-8'))
    for path,sha in previous['source_sha256'].items():assert digest((ROOT/path).read_bytes())==sha,path
    source=source_checks()
    paths=set(load_catalog(ROOT,BASIS).source_sha256)|set(outputs)|set(previous['source_sha256'])|{
        READING,'artifacts/written-units-v1/kant-1784.json','artifacts/future-dissemination-reading-v1/page-483.jpg',
        'reports/focused-dissemination-v1.json','scripts/compose_dissemination_reason.py','scripts/check_dissemination_reason.py',
        'tests/test_dissemination_reason.py','docs/dissemination-reason-v1.md'}
    result={}
    for name,check in [('relations',relation_checks),('nonfactivity',nonfactivity_checks),('structure',structure)]:
        result[name]=check();print(name+' checked',flush=True)
    return dict(status='source_anchored_discourse_assertion_not_whole_unit_completion',document=FULL,**result,source=source,
        roundtrips=True,alignment=dict(unit=source['source_unit'],unit_sha256=source['source_sha256'],
            start=129,end=133,source='Denn',definitions=['hzp6'],status='partial_author_reason_presentation',
            full_semantic_equivalence=False,remaining=['closed contents for both same nodes','conditional scope, comparison and metaphor','whole paragraph meaning']),
        new_source_assertions=1,verified_full_units={'kant-1784':0,'einstein-1905':0},
        active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Source-anchored authorial reason relation checked',flush=True)


if __name__=='__main__':main()
