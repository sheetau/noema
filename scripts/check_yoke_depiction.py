"""Countermodels for a bodily depiction, without asserting its literal truth."""
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
from scripts.compose_yoke_depiction import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,READING,build

REPORT=ROOT/'reports/yoke-depiction-v1.json'
PEOPLE=('person','other','frame','part','foot','load','process','spare')
POINTS=('early','late','anchor')


def unknown(*args):raise ValueError('Unknown bodily depiction interpretation')


@lru_cache(maxsize=2)
def physical_document(kind='release'):
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')
    text+='r zobject[] a.r zperson[] a.r zprocess[] a.r zstart[] d.r zend[] d.r zanchor[] d.'
    query='t[k hzpk[k zobject[] k zperson[]]][k zstart[]]' if kind=='device' else 'k hzpm[k zobject[] k zperson[] k zprocess[] k zstart[] k zend[] k zanchor[]]'
    return parse(text+'q['+query+'].')


def physical_model(variant='baseline',flags=(True,True,True,True)):
    frame,upper,attached,coupling=flags
    def fastens(obj,part,bearer,point):
        if (obj,bearer)!=('frame','person'):return False
        if variant=='already_removed':return False
        if point=='early':return attached and part==('foot' if variant=='different_part' else 'part')
        return part==('foot' if variant=='transferred_to_foot' else 'part') and variant in (
            'transferred_to_foot','lost_classification_only','still_attached')
    return dict(zobject=lambda:'frame',zperson=lambda:'person',zprocess=lambda:'process',
        zstart=lambda:'late' if variant in ('reverse_time','same_time') else 'early',
        zend=lambda:'early' if variant=='reverse_time' else 'late',
        zanchor=lambda:'early' if variant=='future_completion' else 'anchor',
        hzph=lambda obj,point:frame and obj=='frame' and not(variant=='lost_classification_only' and point!='early'),
        hzpg=lambda part,bearer,point:upper and (part,bearer)==('part','other' if variant=='other_body' else 'person'),
        h2e=fastens,
        hzpi=lambda obj,part,bearer,load,point:coupling and (obj,part,bearer,load)==(
            'spare' if variant=='other_device' else 'frame',
            'foot' if variant=='other_coupling_part' else 'part',
            'other' if variant=='other_coupling_bearer' else 'person',
            'person' if variant=='self_load' else 'frame' if variant=='device_load' else 'load'),
        ia=lambda person,anchor,point:person=='person' and anchor in POINTS and point in POINTS and not(variant=='missing_history' and point=='early'),
        ic=lambda a,b,anchor:POINTS.index(a)<POINTS.index(b),
        ag=lambda process,start,end:variant!='no_change' and (process,start,end)==('process','early','late'),
        la=lambda person,process,start,end:(person,process,start,end)==(
            'other' if variant=='other_affected' else 'person','process','early','late'),
        df=lambda person,process,point:(person,process,point)==(
            'other' if variant=='other_agent' else 'person','process','late'),
        dg=lambda process,point:variant!='no_occurrence' and (process,point)==('process','late'),
        hzpj=lambda process,obj,person,start,end:variant!='no_removal_cause' and (process,obj,person,start,end)==(
            'spare' if variant=='other_process' else 'process','spare' if variant=='other_removed_object' else 'frame',
            'other' if variant=='other_removed_bearer' else 'person','early','late'))


def evaluate(doc,values,people=PEOPLE,points=POINTS):
    selected={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}
    return [r['value'] for r in evaluate_document(doc,individuals=people,situations=points,
        primitives=selected,max_steps=3000000,memoize_definitions=False,memoize_expressions=False)]


def physical_checks():
    doc=physical_document('device');count=0;rows={}
    for flags in product((False,True),repeat=4):
        assert evaluate(doc,physical_model(flags=flags))==[all(flags)],flags;count+=1
    for variant in ('baseline','different_part','other_body','other_device','other_coupling_part',
                    'other_coupling_bearer','self_load','device_load'):
        actual=evaluate(doc,physical_model(variant));assert actual==[variant=='baseline'],(variant,actual)
        rows[variant]=actual
    return dict(required_component_combinations=count,role_contrasts=rows,
        frame_body_attachment_and_traction_roles_shared=True,actual_pulling_not_required=True)


def release_checks():
    doc=physical_document();rows={}
    variants=('baseline','already_removed','still_attached','transferred_to_foot','lost_classification_only',
        'reverse_time','same_time','future_completion','missing_history','no_change','other_affected','other_agent',
        'no_occurrence','no_removal_cause','other_process','other_removed_object','other_removed_bearer')
    for variant in variants:
        actual=evaluate(doc,physical_model(variant));assert actual==[variant=='baseline'],(variant,actual)
        rows[variant]=actual
    values=physical_model();old=values['h2e']
    values['h2e']=lambda obj,part,person,point:old(obj,part,person,point) or (obj,part,person)==('spare','foot','person')
    assert evaluate(doc,values)==[True]
    count=0
    for name in ('hzpg','hzph','hzpi','hzpj','h2e','df'):
        values=physical_model();values[name]=unknown
        try:evaluate(doc,values)
        except ValueError as error:assert 'Unknown' in str(error),(name,error)
        else:raise AssertionError(name)
        count+=1
    return dict(contrasts=rows,other_restraints_not_silently_excluded=True,unknown_inputs_refused=count,
        all_checks_eager_and_uncached=True)


def attribution_checks():
    rows={}
    for full in (False,True):
        doc=parse((ROOT/(FULL if full else CORE)).read_text(encoding='utf-8'));doc['statements']=doc['statements'][-1:]
        for variant in ('baseline','wrong_node','wrong_author','wrong_context','reversed_descriptions','missing_attribution'):
            values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
            def presents(node,author,target,depiction,context):
                pair=[json.loads(x.syntax) for x in (target,depiction)]
                expected=['hzpn','h4q'] if variant=='reversed_descriptions' else ['h4q','hzpn']
                return variant!='missing_attribution' and (node,author,context)==(
                    'other' if variant=='wrong_node' else 'frame','other' if variant=='wrong_author' else 'person',
                    'early' if variant=='wrong_context' else 'anchor') and pair==[dict(kind='function_ref',symbol=n) for n in expected]
            values.update(qa=presents,hzpo=lambda:'frame',wa=lambda:'person',hzp3=lambda:'anchor')
            actual=evaluate(doc,values);assert actual==[variant=='baseline'],(full,variant,actual)
            rows[('full:' if full else 'core:')+variant]=actual
        values['qa']=unknown
        try:evaluate(doc,values)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError('Unknown depiction relation accepted')
    return dict(contrasts=rows,all_world_primitives_unknown_without_execution=True,
        source_and_depiction_direction_preserved=True,unknown_attribution_refused=True)


def source_checks():
    reading=json.loads((ROOT/READING).read_text(encoding='utf-8'))
    source=json.loads((ROOT/reading['source_inventory']).read_text(encoding='utf-8'))
    unit=next(u for u in source['units'] if u['id']==reading['source_unit'])
    assert unit['text_sha256']==reading['unit_sha256']==digest(unit['text'].encode('utf-8'))
    start,end=reading['range'];assert unit['text'][start:end]==reading['text']
    for key in ('facsimile','lexical_evidence'):
        item=reading[key];assert digest((ROOT/item['artifact']).read_bytes())==item['sha256']
    assert reading['mapping']==dict(node='hzpo',author='wa',context='hzp3',target='h4q',depiction='hzpn',
        attribution='hzpp',shared_role='the same individual in the unary property position',
        not_inferred=reading['mapping']['not_inferred'])
    return dict(source_unit=unit['id'],source_sha256=unit['text_sha256'],range=[start,end],
        source=reading['text'],facsimile_and_lexical_snapshot_pinned=True,
        visual_collation_is_assistant_judgment_not_independent_human_review=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['declarations'][:-9]==old.document['declarations']
    assert new.document['statements'][:-1]==old.document['statements'] and len(new.document['statements'])==34
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    return dict(new_compositions=4,new_semantic_relation_primitives=4,new_local_references=1,
        existing_statements_preserved=33,total_statements=34,seven_review_bindings_preserved=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for name,body in outputs.items():assert (ROOT/name).read_text(encoding='utf-8')==body,name
    for name in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    previous=json.loads((ROOT/'reports/existential-dissemination-v1.json').read_text(encoding='utf-8'))
    for path,sha in previous['source_sha256'].items():assert digest((ROOT/path).read_bytes())==sha,path
    reading=json.loads((ROOT/READING).read_text(encoding='utf-8'));source=source_checks()
    paths=set(load_catalog(ROOT,BASIS).source_sha256)|set(outputs)|set(previous['source_sha256'])|{
        READING,reading['source_inventory'],reading['facsimile']['artifact'],reading['lexical_evidence']['artifact'],
        'reports/existential-dissemination-v1.json','scripts/compose_yoke_depiction.py',
        'scripts/check_yoke_depiction.py','tests/test_yoke_depiction.py','docs/yoke-depiction-v1.md'}
    results={}
    for name,check in [('physical',physical_checks),('release',release_checks),('attribution',attribution_checks),('structure',structure)]:
        results[name]=check();print(name+' checked',flush=True)
    return dict(status='source_anchored_self_release_metaphor_candidate',document=FULL,**results,source=source,
        roundtrips=True,new_source_assertions=1,alignment=dict(unit=source['source_unit'],unit_sha256=source['source_sha256'],
            start=source['range'][0],end=source['range'][1],source=source['source'],definitions=['hzpk','hzpm','hzpn','hzpp'],
            status='partial_self_release_depiction',full_semantic_equivalence=False,
            remaining=['full figurative implications and source-appropriate target reading',
                       'event alignment inside the conditional dissemination content','whole paragraph meaning review']),
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Source-anchored depiction checked without asserting physical restraints',flush=True)


if __name__=='__main__':main()
