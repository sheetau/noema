"""Check scoped attribution without executing the attributed contents."""
import argparse
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog,_references
from noema.semantic_reviews import digest,selection_binding
from noema.script import transcribe
from scripts import check_expected_focus as previous
from scripts.compose_attributed_focus import ROOT,PARENT,PARENT_BASIS,FULL,CORE,LIBRARY,BASIS,REUSED,IMPORTED,PAIR,build

REPORT=ROOT/'reports/attributed-focus-v1.json'
UNKNOWN=previous.UNKNOWN


def evaluate(doc,values):return previous.evaluate(doc,values)


def unwrap(description):
    assert description.rank==3
    body=json.loads(description.syntax)
    assert body['kind']=='apply' and len(body['arguments'])==1
    identity=body['function'];assert identity['kind']=='lambda' and len(identity['parameters'])==1
    assert identity['body']==dict(kind='variable',name=identity['parameters'][0]['name'])
    assert identity['parameters'][0]['sort']=='content'
    return body['arguments'][0]


@lru_cache(maxsize=1)
def generic_document():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8'))
    text='r zfg[d] c.r zbg[d] c.r znode[] a.r zauthor[] a.r zfs[] a.r zbs[] a.r zcontext[] d.'
    text+='d zforeground[] e[b point[k zfg[v point]]].d zbackground[] e[b point[k zbg[v point]]].'
    text+='d zpackage[] '+PAIR+'[k rst[r c[k zforeground[]] r c[k zbackground[]]]].'
    for package in ('k zpackage[]','k rsw[k zpackage[]]'):
        text+='q[k rqtv[k znode[] k zauthor[] '+package+' k zfs[] k zbs[] k zcontext[]]].'
    for symbol in ('rsx','rsy'):
        text+='q[k '+symbol+'[k zpackage[] k zcontext[]]].'
    text+='q[t[s[k rqtu[k rsu[k zpackage[]]]]][k zcontext[]]].'
    text+='q[t[s[k rqtu[k rsv[k zpackage[]]]]][k zcontext[]]].'
    return parse(format_graph(doc,'compact')+text)


def metadata(doc):
    values=previous.unknown_values(doc)
    values.update(znode=lambda:'person',zauthor=lambda:'authority',zfs=lambda:'person',zbs=lambda:'authority',zcontext=lambda:'outside')
    return values


def relation_values(reported=True,backgrounded=True,seen=None):
    def report(node,author,content,scope,context):
        code=unwrap(content)
        if seen is not None:seen.append(('claim',node,author,code,scope,context))
        return reported and (node,author,scope,context)==('person','authority','person','outside')
    def background(node,author,foreground,background,fs,bs,context):
        fg,bg=unwrap(foreground),unwrap(background)
        if seen is not None:seen.append(('background',node,author,fg,bg,fs,bs,context))
        return backgrounded and (node,author,fs,bs,context)==('person','authority','person','authority','outside')
    return dict(hznreport=report,hzrbgreport=background)


def generic_checks():
    doc=generic_document();count=0
    for reported,backgrounded,fg,bg in product((False,True),repeat=4):
        seen=[];values=metadata(doc);values.update(relation_values(reported,backgrounded,seen),zfg=lambda p:fg,zbg=lambda p:bg)
        actual=evaluate(doc,values);assert actual==[reported and backgrounded]*2+[fg,bg,fg,bg],actual
        assert [r[0] for r in seen]==['claim','background','claim','background']
        first,marked,negated,negmarked=seen
        assert first[3]==marked[3] and negated[3]==negmarked[3]
        assert marked[4]==negmarked[4]==dict(kind='call',symbol='zbackground',arguments=[])
        assert first[3]==dict(kind='call',symbol='zforeground',arguments=[])
        assert first[3]!=negated[3] and _references(negated[3])=={'zforeground'}
        count+=1
    return dict(attribution_and_world_truth_combinations=count,rank_adapter_preserves_evaluated_content=True,
        same_foreground_passed_to_both_relations=True,negation_changes_only_foreground=True,all_checks_eager=True)


def contrast_checks():
    doc=generic_document();selected=dict(doc,statements=doc['statements'][:1]);rows={}
    for name,other in [('znode','authority'),('zauthor','person'),('zfs','authority'),('zbs','person'),('zcontext','other')]:
        values=metadata(doc);values.update(relation_values());values[name]=lambda:other
        assert evaluate(selected,values)==[False];rows[name]=False
    # A relation requiring the two roles in reverse must not accept the package.
    values=metadata(doc);values.update(relation_values())
    values['hzrbgreport']=lambda n,a,f,b,fs,bs,c:unwrap(f)==dict(kind='call',symbol='zbackground',arguments=[]) and unwrap(b)==dict(kind='call',symbol='zforeground',arguments=[])
    assert evaluate(selected,values)==[False]
    unknowns=0
    for name in ('znode','zauthor','zfs','zbs','zcontext','hznreport','hzrbgreport'):
        values=metadata(doc);values.update(relation_values());values[name]=UNKNOWN
        try:evaluate(selected,values)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
        unknowns+=1
    values=metadata(doc);values.update(relation_values())
    assert evaluate(selected,values)==[True] # zfg and zbg remain unknown.
    values['hznreport']=lambda *args:False;values['hzrbgreport']=UNKNOWN
    try:evaluate(selected,values)
    except ValueError as error:assert 'Unknown' in str(error)
    else:raise AssertionError('A false claim report concealed unknown background attribution')
    return dict(metadata_contrasts=rows,swapped_content_roles_rejected=True,required_unknowns_refused=unknowns,
        attributed_truth_not_evaluated=True,false_report_does_not_hide_unknown_background=True)


@lru_cache(maxsize=1)
def native_document():
    doc=parse((ROOT/CORE).read_text(encoding='utf-8'));old=previous.prior.native_document('conditional')
    existing={d['name']:d for d in doc['declarations']}
    for d in old['declarations']:
        if d['name']=='zpackage':continue
        if d['name'] in existing:assert d==existing[d['name']]
        else:doc['declarations'].append(deepcopy(d))
    frame='r b[k rqtp['+previous.prior.CONDITION_ARGS+' k znativefamily[]]]'
    args=frame+' r[k zgoverned[]] r[p zappointed] r[p zguardian]'
    text='q[k hzpy['+args+']].'
    return parse(format_graph(doc,'compact')+text)


def native_checks():
    doc=native_document();rows={}
    for reported,backgrounded in product((False,True),repeat=2):
        seen=[];values=previous.unknown_values(doc)
        values.update(hzp5=lambda:'person',wa=lambda:'authority',hzpz=lambda:'person',hzq2=lambda:'authority',hzp3=lambda:'outside')
        relations=relation_values(reported,backgrounded,seen);values.update(relations)
        actual=evaluate(doc,values);assert actual==[reported and backgrounded]
        claim,marked=seen;assert claim[3]==marked[3]
        assert {'rqtp','znativefamily','hzhb','zgoverned','zappointed','zguardian'}<=_references(claim[3])
        assert {'rqts','hzpt','rqtp','hzhb','wa','hzp3'}<=_references(marked[4])
        assert claim[3]!=marked[4]
        rows[str((reported,backgrounded))]=actual
    return dict(native_shared_permission_and_existential_frame=rows,
        guardian_predicate_constructed_from_closed_arguments=True,all_world_and_expectation_primitives_unknown=True,
        all_checks_eager=True,full_source_interpretation_not_claimed=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['declarations'][:-9]==old.document['declarations']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==34
    reused={d['name']:d for d in parse((ROOT/REUSED).read_text(encoding='utf-8'))['declarations']}
    for name in IMPORTED:assert new.entries[name]['declaration']==reused[name]
    for name,entry in old.entries.items():assert new.entries[name]==entry,name
    for index in (16,17,27,28,29,30,31):assert selection_binding(old,[index])==selection_binding(new,[index])
    return dict(reused_declarations=list(IMPORTED),new_compositions=4,new_local_references=2,new_semantic_relations=0,
        existing_statements=34,seven_review_bindings_preserved=True,
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')))


def build_report():
    outputs=build()
    for p,body in outputs.items():assert (ROOT/p).read_text(encoding='utf-8')==body
    for p in (FULL,CORE,LIBRARY):
        doc=parse((ROOT/p).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    paths=set(outputs)|set(load_catalog(ROOT,BASIS).source_sha256)
    for name in ('reports/expected-focus-v1.json','reports/focused-permission-v1.json'):
        previous_report=json.loads((ROOT/name).read_text(encoding='utf-8'));paths.add(name)
        for p,sha in previous_report['source_sha256'].items():assert digest((ROOT/p).read_bytes())==sha,p
        paths.update(previous_report['source_sha256'])
    paths.update({REUSED,'scripts/compose_attributed_focus.py','scripts/check_attributed_focus.py','tests/test_attributed_focus.py',
        'docs/attributed-focus-v1.md','scripts/compose_policy_recognition.py','scripts/compose_focused_permission.py'})
    results={}
    for name,fn in [('generic',generic_checks),('contrasts',contrast_checks),('native',native_checks),('structure',structure)]:
        results[name]=fn();print(name+' checked',flush=True)
    source=previous.source_checks()
    return dict(status='scoped_foreground_and_background_attribution_connected',document=FULL,**results,roundtrips=True,
        source_scope_references={'foreground':[137,448],'background':[178,217]},new_source_assertions=0,new_covered_characters=0,
        alignment=dict(unit=source['source_unit'],unit_sha256=source['source_sha256'],start=178,end=183,source='sogar',
            definitions=['hzpy'],status='partial_attribution_connection',full_semantic_equivalence=False),
        verified_full_units={'kant-1784':0,'einstein-1905':0},active_review_index_unchanged='data/semantic-review-index-v22.json',
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();result=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==result
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Scoped claim/background attribution checked',flush=True)


if __name__=='__main__':main()
