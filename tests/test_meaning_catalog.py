from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
from noema.constructed import parse,format_graph,promote
from noema.grammar import parse as legacy_parse
from noema.meaning_catalog import BasisError,load_catalog

ROOT=Path(__file__).resolve().parents[1]


def write(path,value):
    body=json.dumps(value,ensure_ascii=False,indent=2) if isinstance(value,dict) else value
    path.write_text(body+'\n',encoding='utf-8',newline='\n')


def bundle(root):
    base=legacy_parse('n:r aa[a] c.d ab[x a] c[k aa[v x]].s[f x a[k ab[v x]]].')
    write(root/'base.noema','n:r aa[a] c.d ab[x a] c[k aa[v x]].s[f x a[k ab[v x]]].')
    primitive=base['declarations'][0]
    basis=dict(document='base.noema',primitives=[dict(symbol='aa',parameters=primitive['parameters'],result=primitive['result'],
        arguments=['subject'],meaning_ja='対象に成立する試験用の基本関係。')],definitions={'ab':'基本関係への適用。'},unresolved=['Primitive grounding is not established.'])
    write(root/'base.json',basis)
    old=promote(base);statements=old['statements'];old['statements']=[]
    # The primitive is only reachable under the quotation inside ac. ad has an
    # open higher-order argument but no statically declared primitive.
    current=parse(format_graph(old,'compact')+'d ac[] i[h[a] c][r[p ab]].d ad[test h[a] c person a] c[c[v test][v person]].')
    # Construct the statement through syntax so its canonical AST is validated.
    current['statements']=statements
    current=parse(format_graph(current,'compact')+'q[e[k ac[]][k ac[]]].')
    write(root/'current.noema',format_graph(current,'compact'))
    added=current['declarations'][len(base['declarations']):]
    delta=dict(document='current.noema',parent='base.noema',inherited_meaning_basis='base.json',
        definitions={'ac':'引用した定義への参照。','ad':'引数として渡す条件の適用。'},
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=['No source-language equivalence claim.'])
    write(root/'delta.json',delta)
    return base,basis,current,delta


def test_full_chain_preserves_conventions_provenance_and_unexpanded_inputs(tmp_path):
    base,basis,doc,delta=bundle(tmp_path)
    catalog=load_catalog(tmp_path,'delta.json');result=catalog.explain(['ac','ad'])
    assert result['primitive_count']==1 and result['definition_count']==3
    assert result['statement_count']==2 and len(result['lineage'])==2
    assert result['lineage'][-1]['statement_changes']==dict(added=1,removed=0,same_order_and_contents=False)
    rows={r['symbol']:r for r in result['entries']}
    assert rows['ac']['primitive_dependencies']==['aa'] and rows['ac']['direct_dependencies']==['ab']
    assert rows['aa']['meaning_basis']=='base.json' and rows['ac']['meaning_basis']=='delta.json'
    assert rows['ad']['primitive_dependencies']==[] and rows['ad']['formal_parameters'][0]['sort']['kind']=='function'
    assert not result['primitive_grounding_proven'] and not result['semantic_equivalence_to_source_proven']
    assert result['lineage'][0]['caveats']['unresolved']==basis['unresolved']
    assert result['lineage'][1]['caveats']['limitations']==delta['limitations']
    for path,digest in result['source_sha256'].items():assert hashlib.sha256((tmp_path/path).read_bytes()).hexdigest()==digest


@pytest.mark.parametrize('fault',['missing_definition','extra_definition','empty_meaning','wrong_signature','missing_signature','missing_primitive',
    'primitive_signature','argument_labels','duplicate_primitive','override_inherited'])
def test_incomplete_or_inconsistent_conventions_are_rejected(tmp_path,fault):
    base,basis,doc,delta=bundle(tmp_path)
    if fault=='missing_definition':del delta['definitions']['ac']
    if fault=='extra_definition':delta['definitions']['ae']='余分な説明'
    if fault=='empty_meaning':delta['definitions']['ac']='  '
    if fault=='wrong_signature':delta['new_signatures']['ac']['result']='truth'
    if fault=='missing_signature':del delta['new_signatures']['ad']
    if fault=='missing_primitive':basis['primitives']=[]
    if fault=='primitive_signature':basis['primitives'][0]['result']='individual'
    if fault=='argument_labels':basis['primitives'][0]['arguments']=[]
    if fault=='duplicate_primitive':basis['primitives']*=2
    if fault=='override_inherited':delta['definitions']['ab']='黙って意味を変更'
    write(tmp_path/'base.json',basis);write(tmp_path/'delta.json',delta)
    with pytest.raises(BasisError):load_catalog(tmp_path,'delta.json')


def test_an_inherited_body_change_is_detected_even_when_its_signature_matches(tmp_path):
    base,basis,doc,delta=bundle(tmp_path)
    text=(tmp_path/'current.noema').read_text(encoding='utf-8')
    original=format_graph(promote(base),'compact').splitlines()[2]
    changed=original.replace('c[','c[u[',1).replace(']].',']]].',1)
    assert original in text and original!=changed
    write(tmp_path/'current.noema',text.replace(original,changed,1))
    with pytest.raises(BasisError,match='Inherited declarations changed'):load_catalog(tmp_path,'delta.json')


@pytest.mark.parametrize('fault',['wrong_parent','cycle','outside_root','duplicate_key','incomplete_parent_metadata'])
def test_invalid_inheritance_and_provenance_are_rejected(tmp_path,fault):
    base,basis,doc,delta=bundle(tmp_path)
    if fault=='wrong_parent':delta['parent']='different.noema'
    if fault=='cycle':delta['inherited_meaning_basis']='delta.json'
    if fault=='outside_root':delta['inherited_meaning_basis']='../escape.json'
    if fault=='incomplete_parent_metadata':del delta['inherited_meaning_basis']
    write(tmp_path/'delta.json',delta)
    if fault=='duplicate_key':
        raw=(tmp_path/'delta.json').read_text(encoding='utf-8')
        write(tmp_path/'delta.json',raw.replace('{','{"document":"base.noema",',1))
    with pytest.raises(BasisError):load_catalog(tmp_path,'delta.json')


def test_projection_is_exact_and_keeps_statement_changes_explicit(tmp_path):
    base,basis,doc,delta=bundle(tmp_path)
    projected=deepcopy(doc);projected['declarations']=projected['declarations'][:3];projected['statements']=[]
    write(tmp_path/'library.noema',format_graph(projected,'compact'))
    result=load_catalog(tmp_path,'delta.json',document_path='library.noema').audit()
    assert result['definition_count']==2 and result['projection']['omitted_declarations']==1
    assert result['projection']['statement_comparison']['removed']==2
    projected['declarations']=projected['declarations'][:2]
    projected=parse(format_graph(projected,'compact')+'d ac[] c[e[n p a b][n p a b]].')
    write(tmp_path/'library.noema',format_graph(projected,'compact'))
    with pytest.raises(BasisError,match='Projection adds, changes'):load_catalog(tmp_path,'delta.json',document_path='library.noema')


def test_ranked_and_constructed_types_are_not_lowered_to_legacy_types(tmp_path):
    base,basis,doc,delta=bundle(tmp_path)
    # A second complete, explicitly edition-0.15 basis is audited as written.
    from noema.ranked import parse as ranked_parse,format_graph as ranked_format
    ranked=ranked_parse('o:d aa[] i b[c][r b[e[n p a b][n p a b]]].')
    write(tmp_path/'ranked.noema',ranked_format(ranked,'compact'))
    write(tmp_path/'ranked.json',dict(document='ranked.noema',primitives=[],definitions={'aa':'層1の記述。'}))
    result=load_catalog(tmp_path,'ranked.json').explain(['aa'])
    assert result['edition']=='0.15' and result['entries'][0]['declaration']['result']['rank']==1


def test_cli_audits_and_explains_without_overwriting_an_existing_artifact(tmp_path):
    bundle(tmp_path);out=tmp_path/'explanation.json'
    cmd=[sys.executable,'-X','utf8','-m','noema.meaning_catalog','explain','--root',str(tmp_path),'--basis','delta.json','--symbol','ac','--output',str(out)]
    first=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    assert first.returncode==0,first.stderr
    raw=out.read_bytes();result=json.loads(raw);assert result['requested_symbols']==['ac']
    second=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    assert second.returncode==2 and out.read_bytes()==raw
    bad=subprocess.run(cmd[:-4]+['--symbol','unknown'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    assert bad.returncode==2 and 'Unknown requested symbol' in bad.stderr
    audit=cmd[:];audit[5]='audit';audit=audit[:-4]
    checked=subprocess.run(audit,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    assert checked.returncode==0,checked.stderr
    assert json.loads(checked.stdout)['definition_count']==3
    invalid=subprocess.run(audit+['--symbol','ac'],cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
    assert invalid.returncode==2 and '--symbol is only valid with explain' in invalid.stderr


def test_current_kant_catalog_and_library_share_the_same_meanings():
    catalog=load_catalog(ROOT,'data/definition-question-basis-v1.json')
    result=catalog.explain(['hzic']);assert len(result['lineage'])==7
    assert (result['primitive_count'],result['definition_count'],result['statement_count'])==(258,1116,16)
    assert result['retained_symbols'][-1]=='hzic' and len(result['entries'])==40
    projected=load_catalog(ROOT,'data/definition-question-basis-v1.json',document_path='examples/v016/definition-question.noema')
    assert projected.audit()['primitive_count']==0
    assert projected.explain(['rqqs'])['entries'][-1]['meaning_ja']==catalog.entries['rqqs']['meaning_ja']
