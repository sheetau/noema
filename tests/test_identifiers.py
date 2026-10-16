from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest
from noema.constructed import parse
from noema.identifiers import load_annotations
from noema.meaning_catalog import BasisError

ROOT=Path(__file__).resolve().parents[1]


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n' if isinstance(value,dict) else value,encoding='utf-8',newline='\n')


def bundle(root):
    text='p:r aa[] a.r ab[] a.r ac[a] a.r ad[] c.d ae[] a[k aa[]].'
    write(root/'names.noema',text);doc=parse(text)
    basis=dict(document='names.noema',primitives=[dict(symbol=d['name'],parameters=d['parameters'],result=d['result'],
        arguments=['argument'] if d['parameters'] else [],meaning_ja='試験用の名称または関係。') for d in doc['declarations'] if d['kind']=='primitive'],
        definitions={'ae':'名称への参照。'})
    write(root/'basis.json',basis)
    form=lambda text,language='de':dict(text=text,language=language,role='identifying_form')
    data=dict(schema_version='noema-identifiers-1',document='names.noema',document_sha256=hashlib.sha256(text.encode()).hexdigest(),
        entries=[dict(symbol='aa',role='designation',forms=[form('Kant'),form('カント','ja'),form('José')]),
            dict(symbol='ab',role='designation',forms=[form('Kant'),form('Jose\u0301'),form('اسم','ar'),form('🪷','und')])])
    write(root/'names.json',data)
    return data


def test_homonyms_and_alternative_forms_do_not_choose_or_merge_referents(tmp_path):
    bundle(tmp_path);names=load_annotations(tmp_path,'basis.json','names.json')
    assert [r['symbol'] for r in names.find('Kant')['matches']]==['aa','ab']
    assert names.find('カント','ja')['matches'][0]['symbol']=='aa'
    assert not names.find('カント','de')['matches']
    assert not names.show()['referent_identity_inferred'] and not names.show()['conceptual_meaning_certified']


def test_scalar_sequences_case_and_whitespace_are_preserved_exactly(tmp_path):
    data=bundle(tmp_path);names=load_annotations(tmp_path,'basis.json','names.json')
    assert names.show()['entries']==data['entries']
    assert names.find('José')['matches'][0]['symbol']=='aa'
    assert names.find('Jose\u0301')['matches'][0]['symbol']=='ab'
    assert names.find('اسم')['matches'] and names.find('🪷')['matches']
    assert not names.find('kant')['matches'] and not names.find(' Kant')['matches']
    result=names.show();result['entries'][0]['forms'][0]['text']='changed'
    assert len(names.find('Kant')['matches'])==2


@pytest.mark.parametrize('fault',['digest','document','unknown_symbol','open_function','truth_sort','duplicate_symbol','duplicate_form',
    'empty_form','empty_language','wrong_role','no_entries','no_forms','extra_field'])
def test_invalid_or_stale_designation_annotations_are_rejected(tmp_path,fault):
    data=bundle(tmp_path);entry=data['entries'][0]
    if fault=='digest':data['document_sha256']='0'*64
    if fault=='document':data['document']='other.noema'
    if fault=='unknown_symbol':entry['symbol']='missing'
    if fault=='open_function':entry['symbol']='ac'
    if fault=='truth_sort':entry['symbol']='ad'
    if fault=='duplicate_symbol':data['entries'].append(deepcopy(entry))
    if fault=='duplicate_form':entry['forms'].append(deepcopy(entry['forms'][0]))
    if fault=='empty_form':entry['forms'][0]['text']='  '
    if fault=='empty_language':entry['forms'][0]['language']=''
    if fault=='wrong_role':entry['role']='referent'
    if fault=='no_entries':data['entries']=[]
    if fault=='no_forms':entry['forms']=[]
    if fault=='extra_field':entry['referent']='aa'
    write(tmp_path/'names.json',data)
    with pytest.raises(BasisError):load_annotations(tmp_path,'basis.json','names.json')


def test_duplicate_keys_non_scalar_unicode_and_changed_document_are_rejected(tmp_path):
    data=bundle(tmp_path)
    raw=json.dumps(data,ensure_ascii=True)
    write(tmp_path/'names.json',raw.replace('"text": "Kant"','"text": "Kant", "text": "other"',1))
    with pytest.raises(BasisError,match='Duplicate JSON key'):load_annotations(tmp_path,'basis.json','names.json')
    write(tmp_path/'names.json',raw.replace('Kant','\\ud800',1))
    with pytest.raises(BasisError,match='Non-scalar Unicode'):load_annotations(tmp_path,'basis.json','names.json')
    write(tmp_path/'names.json',data)
    with (tmp_path/'names.noema').open('a',encoding='utf-8') as stream:stream.write('\n')
    with pytest.raises(BasisError,match='digest'):load_annotations(tmp_path,'basis.json','names.json')


def test_cli_outputs_annotations_without_rewriting_the_core_or_overwriting_files(tmp_path):
    bundle(tmp_path);original=(tmp_path/'names.noema').read_bytes();output=tmp_path/'out.json'
    cmd=[sys.executable,'-X','utf8','-m','noema.identifiers','find','--root',str(tmp_path),'--basis','basis.json','--annotations','names.json','--text','Kant','--output',str(output)]
    result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8');assert result.returncode==0,result.stderr
    raw=output.read_bytes();assert len(json.loads(raw)['matches'])==2
    result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8');assert result.returncode==2
    assert output.read_bytes()==raw and (tmp_path/'names.noema').read_bytes()==original


def test_current_signature_annotations_bind_the_name_object_not_the_author():
    names=load_annotations(ROOT,'data/author-signature-basis-v1.json','data/author-signature-identifiers-v1.json')
    assert names.find('Immanuel Kant')['matches'][0]['symbol']=='hzif'
    assert names.catalog.entries['wa']['declaration']['result']=='individual'
    assert [r['symbol'] for r in names.show()['entries']]==['hzif']
