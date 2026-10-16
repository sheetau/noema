"""Check referents, descriptive scope and unknown factual classification."""
import argparse
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_attached_note as previous
from scripts.compose_subject_bound_departure import closure
from scripts.compose_projected_classification import ROOT,PARENT,PARENT_BASIS,FULL,BASIS,ANNOTATIONS,build

REPORT=ROOT/'reports/projected-classification-v1.json'
VARIANTS=('baseline','missing_use','other_author','article_citation_only','other_target_description',
    'other_classification_description','swapped_descriptions','other_context','missing_courtesy')


def document(combined=False):
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'))
    roots=[*previous.previous.previous.SYMBOLS,'hzlt','hzlz','hzmd'] if combined else ['hzmd']
    doc['declarations']=closure(doc,roots)
    doc['statements']=doc['statements'][18:27] if combined else doc['statements'][-1:]
    return doc


def unknown(*args):raise ValueError('Unknown actual classification')


def model(doc,variant='baseline',prior='baseline',seen=None):
    values=previous.model(previous.document(True),variant=prior)
    values.update(aa=unknown,hzma=unknown)
    def designation(author,use,target,classification,context):
        if variant=='unknown_use':return unknown()
        pair=(json.loads(target.syntax),json.loads(classification.syntax))
        if seen is not None:seen.append(pair)
        first='hzmc' if variant=='swapped_descriptions' else 'other' if variant=='other_target_description' else 'hzmb'
        second='hzmb' if variant=='swapped_descriptions' else 'dr' if variant=='other_classification_description' else 'hzmc'
        return variant!='missing_use' and (author,use,context)==(
            'other' if variant=='other_author' else 'author',
            'citation' if variant=='article_citation_only' else 'mention',
            'branch' if variant=='other_context' else 'note') and pair==(
                {'kind':'function_ref','symbol':first},{'kind':'function_ref','symbol':second})
    values['du']=designation
    if variant=='missing_courtesy':values['hzlq']=lambda *args:False
    return {d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=previous.DOMAIN,
        situations=previous.previous.previous.SCENES,primitives=values,max_steps=3000000,
        memoize_definitions=False,memoize_expressions=False)]


def checks():
    doc=document();rows={};seen=[]
    for variant in VARIANTS:
        rows[variant]=evaluate(doc,model(doc,variant,seen=seen))
        assert rows[variant]==[variant=='baseline'],(variant,rows[variant])
    assert seen and all(pair==({'kind':'function_ref','symbol':'hzmb'},{'kind':'function_ref','symbol':'hzmc'}) for pair in seen)
    try:evaluate(doc,model(doc,'unknown_use'))
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown designation use was guessed')
    combined=document(True);joined={}
    for variant,prior,expected in (
        ('baseline','baseline',[True]*9),
        ('missing_use','baseline',[True]*8+[False]),
        ('article_citation_only','baseline',[True]*8+[False]),
        ('other_classification_description','baseline',[True]*8+[False]),
        ('baseline','no_link',[True]*7+[False,True]),
        ('baseline','other_credit_author',[True]*7+[False,True]),
        ('missing_courtesy','baseline',[True]*5+[False,True,True,False]),
    ):
        actual=evaluate(combined,model(combined,variant,prior));assert actual==expected,(variant,prior,actual)
        joined[variant+'/'+prior]=actual
    # Explicitly evaluating the projected description requires the actual
    # classification. Merely using the description must not evaluate it.
    expanded=deepcopy(doc)
    expanded['statements'].append({'kind':'ask','body':{'kind':'evaluate',
        'content':{'kind':'call','symbol':'hzmc','arguments':[{'kind':'call','symbol':'hzjo','arguments':[]}]},
        'situation':{'kind':'call','symbol':'hzjl','arguments':[]}}})
    expanded=parse(format_graph(expanded,'compact'))
    truth_rows={}
    for truth in (False,True):
        values=model(expanded);values['aa']=lambda person:True
        values['hzma']=lambda person,ctx,truth=truth:truth
        actual=evaluate(expanded,values);assert actual==[True,truth]
        truth_rows[str(truth)]=actual
    unknown_values=model(expanded);unknown_values['aa']=lambda person:True
    try:evaluate(expanded,unknown_values)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('Unknown factual membership was silently filled')
    # The referent criterion identifies the same existing individual and does
    # not depend on the projected classification or the person's name string.
    identity=deepcopy(doc);identity['statements']=[]
    for person in ('hzjo','wa'):
        identity['statements'].append({'kind':'ask','body':{'kind':'evaluate',
            'content':{'kind':'call','symbol':'hzmb','arguments':[{'kind':'call','symbol':person,'arguments':[]}]},
            'situation':{'kind':'call','symbol':'hzjl','arguments':[]}}})
    assert evaluate(identity,model(identity))==[True,False]
    return dict(source_contrasts=rows,combined_nine_statement_contrasts=joined,
        actual_membership_independent=truth_rows,actual_membership_unknown_until_queried=True,
        unknown_designation_refused=True,referent_identity_checked=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==27
    assert new.document['declarations'][:-4]==old.document['declarations']
    for n,e in old.entries.items():assert new.entries[n]==e,n
    for index in (16,17):assert selection_binding(old,[index])==selection_binding(new,[index])
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries']==load_annotations(ROOT,PARENT_BASIS,'data/attached-note-identifiers-v1.json').show()['entries']
    gender=new.entries['hzmc']['declaration']['body']
    from noema.meaning_catalog import _references
    assert _references(gender)=={'aa','hzma'}
    return dict(previous_statements_preserved=26,new_primitive_relations=1,new_local_references=0,new_definitions=3,
        female_negation_and_adult_threshold_absent=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')),
        previous_meanings_and_review_bindings_preserved=True)


def build_report():
    for name,text in build().items():assert (ROOT/name).read_text(encoding='utf-8')==text
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'))
    for notation in ('compact','full'):
        text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    prior=json.loads((ROOT/'reports/attached-note-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior['source_sha256'])
    evidence=json.loads((ROOT/'data/courteous-reference-evidence-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,evidence['source_sha256'])
    inventory=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    unit=next(u for u in inventory['units'] if u['id']=='kant-1784:u0020');phrase='des Herrn Mendelssohn';start=unit['text'].index(phrase)
    paths=set(prior['source_sha256'])|set(evidence['source_sha256'])|set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{
        'reports/attached-note-v1.json','data/courteous-reference-evidence-v1.json','scripts/compose_projected_classification.py',
        'scripts/check_projected_classification.py','tests/test_projected_classification.py','docs/projected-classification-v1.md'}
    return dict(status='partial_honorific_classification_in_designation_scope',document=FULL,checks=checks(),structure=structure(),roundtrips=True,
        alignment=dict(segments=[dict(unit=unit['id'],unit_sha256=unit['text_sha256'],range=[start,start+len(phrase)],source=phrase,
            status='partial_descriptive_honorific_classification',definitions=['hzmb','hzmc','hzmd'],remaining=['Social convention grounding and whole footnote semantics remain incomplete.'])]),
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Projected honorific classification kept separate from actual attributes')


if __name__=='__main__':main()
