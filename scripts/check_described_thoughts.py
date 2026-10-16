"""Check typed thought descriptions, scoped bridges and modal question use."""
import argparse
import hashlib
from itertools import product
import json
import subprocess
import sys
from noema.constructed import parse,format_graph
from noema.identifiers import load_annotations
from noema.meaning_catalog import load_catalog
from noema.script import transcribe
from noema.semantic_reviews import selection_binding
from scripts import check_thought_correspondence as previous
from scripts.compose_described_thoughts import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,MEANINGS,build,closure

REPORT=ROOT/'reports/described-thoughts-v1.json'
CLAIMS='r jclaim[a d] c.r jotherclaim[a d] c.r jwho[] a.r jother[] a.'
POS='j s[b at[k jclaim[k jwho[] v at]]]'
NEG='j s[b at[u[k jclaim[k jwho[] v at]]]]'
FORBIDDEN=previous.previous.forbidden


def quote_checks():
    lib=parse((ROOT/LIBRARY).read_text(encoding='utf-8'));lib['declarations']=closure(lib,['rqrz'])
    prefix=format_graph(lib,'compact')+CLAIMS+'r jaspect[] a.r jscene[] d.'
    pairs={
        'same':(POS,POS,True),
        'alpha':(POS,'j s[b renamed[k jclaim[k jwho[] v renamed]]]',True),
        'negative':(POS,NEG,False),
        'question':(POS,POS.replace('j s[','j q[',1),False),
        'directive':(POS,POS.replace('j s[','j m[',1),False),
        'other_subject':(POS,POS.replace('jwho','jother'),False),
        'other_predicate':(POS,POS.replace('jclaim','jotherclaim'),False),
        'universal_existential':('j s[b at[f item a[k jclaim[v item v at]]]]','j s[b at[g item a[k jclaim[v item v at]]]]',False),
        'condition_direction':('j s[b at[y[k jclaim[k jwho[] v at]][k jotherclaim[k jwho[] v at]]]]',
            'j s[b at[y[k jotherclaim[k jwho[] v at]][k jclaim[k jwho[] v at]]]]',False),
        'scope':('j s[b at[u[f item a[k jclaim[v item v at]]]]]','j s[b at[f item a[u[k jclaim[v item v at]]]]]',False),
    }
    rows={}
    for name,(left,right,expected) in pairs.items():
        doc=parse(prefix+'q[k rqrz[r['+left+'] r['+right+'] k jaspect[] k jscene[]]].')
        values={d['name']:FORBIDDEN for d in doc['declarations'] if d['kind']=='primitive'}
        values.update(jaspect=lambda:'topic',jscene=lambda:'actual')
        rows[name]=previous.evaluate(doc,values);assert rows[name]==[expected],name
    # Both contents have identical sampled truth values; the descriptions do not.
    doc=parse(prefix+'q[e['+POS+']['+POS.replace('jclaim','jotherclaim')+']].'+
        'q[k rqrz[r['+POS+'] r['+POS.replace('jclaim','jotherclaim')+'] k jaspect[] k jscene[]]].')
    values=dict(jclaim=lambda *a:True,jotherclaim=lambda *a:True,jwho=lambda:'one',jother=lambda:'two',
        jaspect=lambda:'topic',jscene=lambda:'actual')
    assert previous.evaluate(doc,values)==[True,False]
    for bad in ('k jwho[]','b at[k jclaim[k jwho[] v at]]','j v[i[item a][e[v item][v item]]]'):
        try:parse(prefix+'q[k rqrz[r['+POS+'] r['+bad+'] k jaspect[] k jscene[]]].')
        except ValueError:pass
        else:raise AssertionError('Non-message description accepted: '+bad)
    return dict(contrasts=rows,contents_not_executed=True,sampled_truth_equality_does_not_merge_descriptions=True,
        incompatible_description_sorts_refused=3)


def mapper(right=POS):
    return (CLAIMS+'r jpick[a a d i[f] i[f]] i[f].d jdescribe[item a topic a scene d] i[f]['+
        'k jpick[v item v topic v scene r['+POS+'] r['+right+']]].')


def adapter_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8'));doc['declarations']=closure(doc,['rqsa'])
    text=format_graph(doc,'compact')+mapper(NEG)+('r jleft[] a.r jright[] a.r jtopic[] a.r jscene[] d.'
        'r jcriterion[i[f] i[f] a d] c.')
    probe=parse(text+'q[e[r['+POS+']][r['+NEG+']]].')
    expected=[node['body'] for node in probe['statements'][0]['body']['arguments']]
    doc=parse(text+'q[k rqsa[k jleft[] k jright[] k jtopic[] k jscene[] p jdescribe p jcriterion]].'+
        'q[k rqsa[k jright[] k jleft[] k jtopic[] k jscene[] p jdescribe p jcriterion]].')
    seen=[]
    def criterion(left,right,topic,scene):
        seen.append((topic,scene))
        return [json.loads(left.syntax),json.loads(right.syntax)]==expected and (topic,scene)==('topic','actual')
    values=dict(jleft=lambda:'one',jright=lambda:'two',jtopic=lambda:'topic',jscene=lambda:'actual',
        jpick=lambda item,topic,scene,a,b:a if item=='one' else b,jcriterion=criterion,
        jclaim=FORBIDDEN,jotherclaim=FORBIDDEN,jwho=FORBIDDEN,jother=FORBIDDEN)
    assert previous.evaluate(doc,values)==[True,False]
    assert seen==[('topic','actual'),('topic','actual')]
    for name,value in (('jtopic','other_topic'),('jscene','elsewhere')):
        modified=dict(values);modified[name]=lambda:value
        assert previous.evaluate(doc,modified)==[False,False]
    values['jcriterion']=FORBIDDEN
    try:previous.evaluate(doc,values)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Unknown criterion was bypassed')
    return dict(asymmetric_criterion_preserved=True,topic_and_context_forwarded=True,unknown_criterion_refused=True)


def generic_document(right=POS):
    text=(ROOT/LIBRARY).read_text(encoding='utf-8')+mapper(right)
    text+='r jfirst[] a.r jsecond[] a.r jextent[] a.r jscene[] d.r jdomain[a d] c.r jinclude[a a d] c.r jattr[a a a d] c.r jmatch[a a a d] c.'
    text+='q[k rqsb[k jfirst[] k jsecond[] k jscene[] p jdomain p jattr p jmatch p jdescribe p rqrz]].'
    text+='q[k rqry[k jfirst[] k jsecond[] k jextent[] k jscene[] p jdomain p jinclude p jattr p jmatch]].'
    text+='q[k rqsc[k jfirst[] k jsecond[] k jextent[] k jscene[] p jdomain p jinclude p jattr p jdescribe p rqrz]].'
    return parse(text)


def bridge_checks():
    docs={same:generic_document(POS if same else NEG) for same in (False,True)}
    items=('one','two');pairs=list(product(items,repeat=2));count=0;bridged=0
    for same in (False,True):
        for bits in product((False,True),repeat=8):
            left={a for a,b in zip(items,bits[:2]) if b};right={a for a,b in zip(items,bits[2:4]) if b}
            match={p for p,b in zip(pairs,bits[4:]) if b};used=left|right
            values=dict(jfirst=lambda:'first',jsecond=lambda:'second',jextent=lambda:'topic',jscene=lambda:'actual',
                jdomain=lambda a,c:(a,c)==('topic','actual'),jinclude=lambda e,a,c:(e,a,c)==('topic','topic','actual'),
                jattr=lambda d,a,i,c:(a,c)==('topic','actual') and i in (left if d=='first' else right if d=='second' else set()),
                jmatch=lambda a,b,t,c:(t,c)==('topic','actual') and (a,b) in match,
                jpick=lambda item,topic,scene,a,b:a if item=='one' else b if item=='two' else FORBIDDEN(),
                jclaim=FORBIDDEN,jotherclaim=FORBIDDEN,jwho=FORBIDDEN,jother=FORBIDDEN)
            bridge=all(((a,b) in match)==(same or a==b) for a in used for b in used)
            expected=[bridge,previous.covered(left,right,match),previous.covered(left,right,{p for p in pairs if same or p[0]==p[1]})]
            actual=previous.evaluate(docs[same],values,True)
            assert actual==expected,(same,bits,actual,expected)
            if bridge:assert actual[1]==actual[2];bridged+=1
            count+=1
    # With total descriptions, the saved graph also evaluates eagerly.
    values.update(jpick=lambda item,topic,scene,a,b:a if item=='one' else b)
    assert previous.evaluate(docs[True],values)==previous.evaluate(docs[True],values,True)
    return dict(combinations=count,models_satisfying_bridge=bridged,bridge_implies_extent_agreement=True,
        unused_descriptions_diagnostic_skipped=True,eager_complete_model_checked=True)


def source_document(right=POS):
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'));doc['declarations']=closure(doc,['hzld','hzlj','hzll','rqrz']);doc['statements']=[]
    return parse(format_graph(doc,'compact')+mapper(right)+'r jextent[] a.r jscene[] d.'+
        'q[k hzlj[k jscene[] p jdescribe p rqrz]].'+
        'q[h[k hzll[p jdescribe p rqrz]][k jextent[]]].q[h[k hzld[]][k jextent[]]].')


def source_checks():
    rows={}
    for variant in ('same','different_unbridged','different_bridged','zero','no_chance','no_cause','empty_possible'):
        different=variant in ('different_unbridged','different_bridged','zero')
        doc=source_document(NEG if different else POS)
        values=previous.source_model(doc,variant)
        values.update(jscene=lambda:'possible',jpick=lambda item,topic,scene,a,b:a if item=='author' else b if item=='other' else FORBIDDEN(),
            jclaim=FORBIDDEN,jotherclaim=FORBIDDEN,jwho=FORBIDDEN,jother=FORBIDDEN)
        # For complete correspondence use reflexive pairs too; the old model
        # only specified cross-document pairs needed by rqrx.
        values['hzli']=lambda a,b,t,c:t=='full' and c=='possible' and a in ('author','other') and b in ('author','other') and (
            a==b or variant not in ('different_bridged','zero'))
        if variant=='zero':values['hzlg']=lambda *a:False
        rows[variant]=previous.evaluate(doc,values,True,previous.previous.DOMAIN,previous.previous.SCENES)
        expected={'same':[True,True,True],'different_unbridged':[False,False,True],
            'different_bridged':[True,False,False],'zero':[True,True,True],
            'no_chance':[True,False,False],'no_cause':[True,False,False],'empty_possible':[True,False,False]}[variant]
        assert rows[variant]==expected,(variant,rows[variant])
    doc=source_document();values=previous.source_model(doc);values.update(jscene=lambda:'possible',jpick=FORBIDDEN,
        jclaim=FORBIDDEN,jotherclaim=FORBIDDEN,jwho=FORBIDDEN,jother=FORBIDDEN)
    try:previous.evaluate(doc,values,True,previous.previous.DOMAIN,previous.previous.SCENES)
    except ValueError as e:assert 'Unknown' in str(e)
    else:raise AssertionError('Missing thought description was guessed')
    return dict(contrasts=rows,unknown_description_refused=True,source_uses_diagnostic=True,
        original_question_not_unconditionally_replaced=True,described_contents_not_executed=True)


def structure():
    old=load_catalog(ROOT,PARENT_BASIS);new=load_catalog(ROOT,BASIS);size=len(old.document['declarations'])
    assert new.document['declarations'][:size]==old.document['declarations']
    assert new.document['statements']==old.document['statements'] and len(new.document['statements'])==23
    assert {d['name'] for d in new.document['declarations'][size:]}==set(MEANINGS)
    assert all(d['kind']=='definition' for d in new.document['declarations'][size:])
    for name in old.entries:assert new.entries[name]==old.entries[name],name
    assert load_annotations(ROOT,BASIS,ANNOTATIONS).show()['entries']==load_annotations(
        ROOT,PARENT_BASIS,'data/thought-correspondence-identifiers-v1.json').show()['entries']
    assert selection_binding(old,[16])==selection_binding(new,[16])
    lib=load_catalog(ROOT,BASIS,document_path=LIBRARY);assert len(lib.entries)==6
    return dict(previous_statements_preserved=23,new_primitives=0,new_definitions=7,
        inherited_meanings_and_signature_binding_unchanged=True)


def alignment():
    old=previous.alignment()['segments'][0]
    return dict(segments=[dict(old,status='partial_explicit_typed_comparison_interface',definitions=['rqrz','rqsa','rqsb','rqsc','hzlj','hzlk','hzll'],
        remaining=['Actual item descriptions, faithful attribution, nonstructural comparison criteria, other question types and full source review.'])])


def build_report():
    files=build()
    for p,b in files.items():assert (ROOT/p).read_text(encoding='utf-8')==b,p
    quotes=quote_checks();adapter=adapter_checks();bridges=bridge_checks();source=source_checks();structural=structure()
    for p in (FULL,LIBRARY):
        doc=parse(files[p])
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
        run=subprocess.run([sys.executable,'-X','utf8','-m','noema.constructed','parse','-i',str(ROOT/p)],check=True,capture_output=True,encoding='utf-8')
        assert json.loads(run.stdout)==doc
    old=json.loads((ROOT/'reports/thought-correspondence-v1.json').read_text(encoding='utf-8'))
    paths=set(old['source_sha256'])|set(files)|set(load_catalog(ROOT,BASIS).source_sha256)|{
        'reports/thought-correspondence-v1.json','scripts/compose_described_thoughts.py','scripts/check_described_thoughts.py',
        'tests/test_described_thoughts.py','docs/described-thoughts-v1.md'}
    for p,h in old['source_sha256'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
    return dict(status='partial_typed_thought_descriptions_checked',document=FULL,quotes=quotes,adapter=adapter,bridges=bridges,source=source,
        structure=structural,alignment=alignment(),roundtrips=True,cli_parse=True,verified_full_units={'kant-1784':0,'einstein-1905':0},
        size_accounting=dict(manuscript_characters=len(files[FULL]),additional_manuscript_characters=len(files[FULL])-len((ROOT/PARENT).read_text(encoding='utf-8')),
            generic_library_characters=len(files[LIBRARY]),note='Includes reusable definitions, not a compression ratio.'),
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Typed message descriptions and scoped comparison bridges checked')


if __name__=='__main__':main()
