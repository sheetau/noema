"""Check anchored notes without inferring topical or logical explanation."""
import argparse
from copy import deepcopy
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_current_answer as previous
from scripts.compose_subject_bound_departure import closure
from scripts.compose_attached_note import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,build

REPORT=ROOT/'reports/attached-note-v1.json'
DOMAIN=previous.DOMAIN+('note_section','anchor','attachment')
VARIANTS=('baseline','no_occurrence','no_note_membership','no_anchor_membership','other_note_document',
    'other_anchor_document','other_part_context','no_link','other_link_display','other_link_note',
    'other_link_anchor','other_link_document','other_link_context','no_credit','other_credit_note',
    'other_credit_author','other_credit_display','other_credit_context','note_is_anchor','note_is_document','anchor_is_document')


def document(combined=False):
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'))
    roots=[*previous.previous.SYMBOLS,'hzlt','hzlz'] if combined else ['hzlz']
    doc['declarations']=closure(doc,roots)
    doc['statements']=doc['statements'][18:26] if combined else doc['statements'][-1:]
    return doc


def model(doc,variant='baseline',prior='baseline'):
    values=previous.model(previous.document(True),prior_variant=prior)
    note='anchor' if variant=='note_is_anchor' else 'document' if variant=='note_is_document' else 'note_section'
    anchor='document' if variant=='anchor_is_document' else 'anchor'
    values.update(hzlu=lambda:note,hzlv=lambda:anchor,hzlw=lambda:'attachment')
    occurs,credit=values['dg'],values['hzij']
    values['dg']=lambda act,ctx:occurs(act,ctx) or variant!='no_occurrence' and (act,ctx)==('attachment','note')
    def part(section,work,ctx):
        if variant=='unknown_part':return previous.previous.unknown()
        if ctx!=('branch' if variant=='other_part_context' else 'note'):return False
        return (variant!='no_note_membership' and (section,work)==(note,'other' if variant=='other_note_document' else 'document')) or (
            variant!='no_anchor_membership' and (section,work)==(anchor,'other' if variant=='other_anchor_document' else 'document'))
    def links(act,section,position,work,ctx):
        if variant=='unknown_link':return previous.previous.unknown()
        return variant!='no_link' and (act,section,position,work,ctx)==(
            'other' if variant=='other_link_display' else 'attachment',
            'other' if variant=='other_link_note' else note,
            'other' if variant=='other_link_anchor' else anchor,
            'other' if variant=='other_link_document' else 'document',
            'branch' if variant=='other_link_context' else 'note')
    def author(act,section,person,ctx):
        if variant=='unknown_credit' and act=='attachment':return previous.previous.unknown()
        return credit(act,section,person,ctx) or variant!='no_credit' and (act,section,person,ctx)==(
            'other' if variant=='other_credit_display' else 'attachment',
            'other' if variant=='other_credit_note' else note,
            'other' if variant=='other_credit_author' else 'author',
            'branch' if variant=='other_credit_context' else 'note')
    values.update(hzlx=part,hzly=links,hzij=author)
    return {d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=previous.previous.SCENES,
        primitives=values,max_steps=3000000,memoize_definitions=False,memoize_expressions=False)]


def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+
        'r jdisplay[] a.r jauthor[] a.r jnote[] a.r janchor[] a.r jdoc[] a.r jctx[] d.'+
        'r joccurs[a d] c.r jpart[a a d] c.r jlinks[a a a a d] c.r jcredit[a a a d] c.'+
        'q[k rqsm[k jdisplay[] k jauthor[] k jnote[] k janchor[] k jdoc[] k jctx[] p joccurs p jpart p jlinks p jcredit]].')
    for bits in product((False,True),repeat=5):
        values={n:lambda v=v:v for n,v in dict(jdisplay='attachment',jauthor='author',jnote='note_section',janchor='anchor',jdoc='document',jctx='note').items()}
        values.update(joccurs=lambda *args:bits[0],jpart=lambda section,work,ctx:bits[1] if section=='note_section' else bits[2],
            jlinks=lambda *args:bits[3],jcredit=lambda *args:bits[4])
        assert evaluate(doc,values)==[all(bits)],bits
    return 32


def checks():
    doc=document();rows={}
    for variant in VARIANTS:
        rows[variant]=evaluate(doc,model(doc,variant))
        assert rows[variant]==[variant=='baseline'],(variant,rows[variant])
    for variant in ('unknown_part','unknown_link','unknown_credit'):
        try:evaluate(doc,model(doc,variant))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(variant)
    combined=document(True);joined={}
    for prior in ('baseline','actual_receipt','other_withheld_work','no_trial_role','no_courtesy','no_citation'):
        expected=[i not in previous.previous.EXPECTED_FALSE[prior] for i in range(6)]+[True,True]
        actual=evaluate(combined,model(combined,prior=prior));assert actual==expected,(prior,actual)
        joined[prior]=actual
    for variant in ('no_anchor_membership','other_link_document','other_credit_author'):
        actual=evaluate(combined,model(combined,variant));assert actual==[True]*7+[False],(variant,actual)
        joined[variant]=actual
    extra=deepcopy(doc);extra['statements']=[]
    extra=parse(format_graph(extra,'compact')+'r jexplains[] c.s[k hzlz[]].q[k jexplains[]].')
    for truth in (False,True):
        values=model(doc);values['jexplains']=lambda truth=truth:truth
        assert evaluate(extra,values)==[True,truth]
    return dict(source_contrasts=rows,combined_eight_statement_contrasts=joined,
        unknown_inputs_refused=3,logical_explanation_not_entailed=True,generic_combinations=generic_checks())


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==26
    assert new.document['declarations'][:-7]==old.document['declarations']
    for n,e in old.entries.items():assert new.entries[n]==e,n
    for index in (16,17):assert selection_binding(old,[index])==selection_binding(new,[index])
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries']==load_annotations(ROOT,PARENT_BASIS,'data/current-answer-identifiers-v1.json').show()['entries']
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY);assert set(lib.entries)=={'rqsm'}
    return dict(previous_statements_preserved=25,new_primitive_relations=2,new_local_references=3,new_definitions=2,
        generic_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')),
        previous_meanings_and_review_bindings_preserved=True)


def alignment():
    inventory=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    segments=[]
    for unit_id in ('kant-1784:u0017','kant-1784:u0020'):
        u=next(u for u in inventory['units'] if u['id']==unit_id)
        start=u['text'].rfind('*)') if unit_id.endswith('17') else 0
        assert start>=0 and u['text'][start:start+2]=='*)'
        segments.append(dict(unit=unit_id,unit_sha256=u['text_sha256'],range=[start,start+2],source='*)',
            status='partial_structural_note_attachment',definitions=['hzlz'],
            remaining=['Only note attachment; no completion claim for surrounding prose or full note.']))
    return dict(segments=segments)


def build_report():
    for name,text in build().items():assert (ROOT/name).read_text(encoding='utf-8')==text
    for name in (FULL,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    prior=json.loads((ROOT/'reports/current-answer-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    paths=set(prior['source_sha256'])|set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{
        'reports/current-answer-v1.json','scripts/compose_attached_note.py','scripts/check_attached_note.py',
        'tests/test_attached_note.py','docs/attached-note-v1.md','artifacts/author-signature-facsimile-v1/page-494.jpg'}
    return dict(status='partial_document_attachment_with_author_credit',document=FULL,
        checks=checks(),structure=structure(),alignment=alignment(),roundtrips=True,
        source_reading='Original p.494 inspected: matching markers at the main-text ending and note beginning. Attachment does not fix exclusive topical scope. Author-note attribution follows the source classification and first-person continuity.',
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Note membership, anchor, author credit and independent content scope checked')


if __name__=='__main__':main()
