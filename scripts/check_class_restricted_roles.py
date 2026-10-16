"""Check category restriction, witness adoption and preserved question scope."""
import argparse
import hashlib
from itertools import product
import json
import subprocess
import sys
from noema.constructed import parse,format_graph
from noema.diagnostic_short_circuit import lower
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from noema.semantic_reviews import selection_binding
from scripts import check_exploratory_question as previous
from scripts.compose_class_restricted_roles import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,MEANINGS,build,closure

REPORT=ROOT/'reports/class-restricted-roles-v1.json'
ROLES=('trial','extra','other')


def evaluate(doc,values,diagnostic=False):
    if diagnostic:doc,values=lower(doc,values)
    return previous.evaluate(doc,values)


def generic_document():
    return parse((ROOT/LIBRARY).read_text(encoding='utf-8')+
        'r jperson[] a.r jdoc[] a.r jrole[] a.r jctx[] d.r jassign[a a a d] c.r jqual[a] c.'+
        'q[k rqrw[k jperson[] k jdoc[] k jrole[] k jctx[] p jassign p jqual]].'+
        'q[w[k rqrv[k jperson[] k jdoc[] k jrole[] k jctx[] p jassign]][k jqual[k jrole[]]]].')


def generic_checks():
    doc=generic_document();count=0;differences=[]
    for bits in product((False,True),repeat=6):
        adopted={r for r,b in zip(ROLES,bits[:3],strict=True) if b}
        qualified={r for r,b in zip(ROLES,bits[3:],strict=True) if b}
        values=dict(jperson=lambda:'author',jdoc=lambda:'present',jrole=lambda:'trial',jctx=lambda:'actual',
            jassign=lambda person,document,role,ctx:(person,document,ctx)==('author','present','actual') and role in adopted,
            jqual=lambda role:role in qualified)
        expected=['trial' in adopted and adopted<=qualified,adopted=={'trial'} and 'trial' in qualified]
        actual=evaluate(doc,values);assert actual==expected,bits
        assert evaluate(doc,values,True)==actual
        if actual[0]!=actual[1]:differences.append(dict(adopted=sorted(adopted),qualified=sorted(qualified),new=actual[0],old=actual[1]))
        count+=1
    assert len(differences)==5 and all(r['new'] and not r['old'] for r in differences)
    return dict(combinations=count,accepted_class_cases_rejected_by_singleton= differences)


def source_document(path=FULL):
    doc=parse((ROOT/path).read_text(encoding='utf-8'))
    doc['declarations']=closure(doc,['hzle']);doc['statements']=doc['statements'][-1:]
    return doc


def model_for(doc,variant='baseline',seen=None):
    values=previous.presentation_model(doc,variant,seen)
    assigned={'trial'}
    if variant in ('two_trials','second_not_trial','second_other_question','unknown_second_trial'):assigned.add('extra')
    if variant=='three_trials':assigned.update(('extra','other'))
    if variant=='witness_missing':assigned={'extra'}
    if variant in ('two_trials','three_trials','second_not_trial','second_other_question','unknown_second_trial','witness_missing'):
        values['hzkz']=lambda person,document,role,ctx:(person,document,ctx)==('author','present','actual') and role in assigned
        def trial(role,description,ctx):
            syntax=json.loads(description.syntax)
            if seen is not None:seen.append(syntax)
            if variant=='unknown_second_trial' and role=='extra':return previous.forbidden()
            permitted=assigned-{'extra'} if variant=='second_not_trial' else assigned
            expected='other' if variant=='second_other_question' and role=='extra' else 'hzld'
            return role in permitted and ctx=='actual' and syntax=={'kind':'call','symbol':expected,'arguments':[]}
        values['hzky']=trial
    return values


def source_checks():
    new=source_document();old=source_document(PARENT);rows={};seen=[]
    variants=('baseline','two_trials','three_trials','second_not_trial','second_other_question','witness_missing',
        'no_stance','other_person','other_document','other_time','other_context','empty_roles','extra_role',
        'other_person_role','other_document_role','other_context_role','other_trial_role','other_question')
    positives={'baseline','two_trials','three_trials','other_person_role','other_document_role','other_context_role'}
    for variant in variants:
        actual=evaluate(new,model_for(new,variant,seen));prior=evaluate(old,model_for(old,variant))
        assert actual==[variant in positives],(variant,actual)
        assert prior==[variant in positives-{'two_trials','three_trials'}],(variant,prior)
        rows[variant]=dict(old=prior,new=actual)
    assert seen and all(x=={'kind':'call','symbol':'hzld','arguments':[]} for x in seen)
    for variant in ('unknown_stance','unknown_role','unknown_trial','unknown_second_trial'):
        for diagnostic in (False,True):
            try:evaluate(new,model_for(new,variant),diagnostic)
            except ValueError as e:assert 'Unknown' in str(e)
            else:raise AssertionError((variant,diagnostic))
    values=model_for(new)
    known=values['hzky']
    values['hzky']=lambda role,desc,ctx:known(role,desc,ctx) if role=='trial' else previous.forbidden()
    assert evaluate(new,values,True)==[True]
    try:evaluate(new,values)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Eager evaluation should expose the unspecified unused qualification')
    return dict(contrasts=rows,question_description_preserved=True,unknown_adopted_qualification_refused=True,
        unused_unknown_qualification_diagnostic_skipped=True,unused_unknown_qualification_eager_refused=True,
        question_content_not_evaluated=True)


def semantic_entry(entry):
    return {k:v for k,v in entry.items() if k not in ('meaning_basis','declaration_document')}


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS)
    before={d['name']:d for d in old.document['declarations']};after={d['name']:d for d in new.document['declarations']}
    assert set(after)-set(before)=={'rqrw'} and not set(before)-set(after)
    assert [n for n in before if before[n]!=after[n]]==['hzle']
    assert [d['name'] for d in new.document['declarations'] if d['name']!='rqrw']==list(before)
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==23
    for n in before:
        if n!='hzle':assert semantic_entry(new.entries[n])==semantic_entry(old.entries[n]),n
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY)
    assert lib.document['declarations']==closure(new.document,['rqrv','rqrw']) and len(lib.entries)==2
    old_names=load_annotations(ROOT,PARENT_BASIS,'data/exploratory-question-identifiers-v1.json').show()['entries']
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries']==old_names
    binding_before=selection_binding(old,[16]);binding_after=selection_binding(new,[16])
    assert binding_before['statements']==binding_after['statements']
    assert binding_before['dependencies']==binding_after['dependencies']
    for n in binding_before['dependencies']:assert semantic_entry(old.entries[n])==semantic_entry(new.entries[n]),n
    return dict(changed_definition='hzle',new_definitions=1,new_primitives=0,previous_statements_preserved=23,
        other_semantic_entries_preserved=True,signature_comparison=dict(before=binding_before,after=binding_after,
            note='Dependency digest changes with basis/document provenance; the declarations, arguments and meanings are unchanged.'))


def alignment():
    unit=next(u for u in json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))['units'] if u['id']=='kant-1784:u0020')
    text=unit['text'];start=text.index('die jetzt');end=text.index('wiefern')
    return dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,end],source=text[start:end],
        status='partial_class_restriction_revision',definitions=['rqrw','hzle'],
        remaining=['Scope of nur and mag reading, thought agreement, contingency and whole footnote review remain unresolved.'])])


def build_report():
    files=build()
    for name,body in files.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    generic=generic_checks();source=source_checks();structural=structure()
    for p in (FULL,LIBRARY):
        doc=parse(files[p])
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    facsimile=json.loads((ROOT/'data/author-signature-facsimile-v1.json').read_text(encoding='utf-8'))
    for p,h in facsimile['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    paths=set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|set(load_catalog(ROOT,PARENT_BASIS).source_sha256)|set(facsimile['source_sha256'])|{
        'data/author-signature-facsimile-v1.json','data/exploratory-question-identifiers-v1.json',
        'scripts/compose_class_restricted_roles.py','scripts/check_class_restricted_roles.py','scripts/compose_subject_bound_departure.py',
        'scripts/compose_calendar_dateline.py','scripts/check_exploratory_question.py','scripts/compose_exploratory_question.py',
        'docs/class-restricted-roles-v1.md','tests/test_class_restricted_roles.py',
        'noema/__init__.py','noema/resources/lexicon.json','noema/resources/alphabet-v1.json','noema/resources/alphabet-v2.json'}
    paths.update('noema/'+n+'.py' for n in ('constructed','constructed_discourse','constructed_semantics','discourse','extraction',
        'grammar','guarded_ranked_semantics','identifiers','meaning_basis','meaning_catalog','ranked','ranked_discourse','script','semantics',
        'semantic_reviews','diagnostic_short_circuit'))
    parent=(ROOT/PARENT).read_text(encoding='utf-8')
    return dict(status='partial_role_class_restriction_checked',document=FULL,generic=generic,source=source,structure=structural,
        alignment=alignment(),roundtrips=True,cli_parse=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        size_accounting=dict(manuscript_characters=len(files[FULL]),additional_manuscript_characters=len(files[FULL])-len(parent),
            generic_library_characters=len(files[LIBRARY]),annotation_bytes=len(files[ANNOTATIONS].encode('utf-8')),
            note='Shared definitions are counted; no claim of source compression.'),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Role class restriction checked against the prior singleton condition')


if __name__=='__main__':main()
