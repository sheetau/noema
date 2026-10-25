from copy import deepcopy
import json
import pytest

from noema.constructed_discourse import normalize_document
from scripts.visible_defined_vocabulary import DefinedVocabulary,check_defined_extension
from scripts.visible_library import LibraryWriter,compile_page,decode_page,decode_document,compile_document
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_lexical_script import check_extension,_shape_set
from scripts.visible_word_forms import Word,symbol
from scripts.visible_sharing import SharedReader
from scripts.visible_syntax_geometry import recognize,render
from scripts.check_visible_library import vocabulary,specimens,candidate_examples,boolean


def test_every_published_definition_retains_its_body_and_kind():
    v=vocabulary()
    check_extension(Vocabulary(),v)
    for row in specimens():
        recovered=decode_page(row['page']['shapes'])['document']
        assert recovered==row['encoded']
        assert all(d['kind']=='definition' for d in recovered['declarations'])
        assert v.decode_names(recovered)==row['native']
    assert len(v.document()['definitions'])==14 and len(v.document()['entries'])==30


def test_order_of_dictionary_registration_does_not_change_appearance_or_import_order():
    data=vocabulary().document()
    for field in ('entries','definitions'):data[field]=dict(reversed(list(data[field].items())))
    other=DefinedVocabulary(data)
    names=list(data['definitions'])
    assert other.imports(names)==vocabulary().imports(list(reversed(names)))
    encoded=vocabulary().encode(candidate_examples())
    assert compile_page(encoded,other,max_width=3000.)==specimens()[1]['page']


@pytest.mark.parametrize('name',list(DefinedVocabulary().document()['definitions']))
def test_every_shared_word_can_be_called_and_referenced(name):
    v=vocabulary(); declaration=v.declaration(name)
    args=[dict(kind='variable',name='arg'+chr(97+i)) for i in range(len(declaration['parameters']))]
    call=dict(kind='call',symbol=declaration['name'],arguments=args)
    body=dict(kind='iff',arguments=[call,call])
    for arg,param in reversed(list(zip(args,declaration['parameters']))):
        body=dict(kind='forall',variable=arg['name'],sort=param['sort'],body=body)
    ref=dict(kind='function_ref',symbol=declaration['name'])
    quoted=dict(kind='quote',body=ref)
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=v.imports([name]),
        statements=[dict(kind='assert',body=body),dict(kind='assert',body=dict(kind='equal',arguments=[quoted,quoted]))]))
    w=LibraryWriter(v);w.document(doc)
    shapes=render(w.glyphs)['shapes']
    assert decode_document(shapes)==doc


def test_local_definition_can_use_new_public_words_in_its_spelling_and_body():
    v=vocabulary(); name=symbol(Word('compound',('candidatepossible','rain')),v)
    shared=v.declaration('candidatepossible')
    params=deepcopy(shared['parameters'])
    body=dict(kind='call',symbol=shared['name'],arguments=[dict(kind='variable',name=p['name']) for p in params])
    local=dict(kind='definition',name=name,parameters=params,result='truth',body=body)
    doc=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=v.imports(['candidatepossible'])+[local],statements=[]))
    assert decode_document(compile_document(doc)['shapes'])==doc


def test_public_definition_cannot_be_replaced_by_a_primitive_or_a_different_body():
    v=vocabulary(); d=v.declaration('candidateexists')
    primitive=dict(kind='primitive',name=d['name'],parameters=[p['sort'] for p in d['parameters']],result='truth')
    for changed in (primitive,{**d,'body':boolean(False)}):
        doc=dict(schema_version='0.16',lexicon_version='0.16',declarations=[changed],statements=[])
        with pytest.raises(ValueError,match='public meaning'): compile_document(doc)


def test_missing_imported_dependency_is_rejected_without_implicit_insertion():
    v=vocabulary(); w=LibraryWriter(v)
    w.keyword('document');w.natural(16);w.natural(2)
    w.keyword('import');w.name(v.declaration('necessaryactual')['name']);w.end();w.end()
    with pytest.raises(ValueError,match='Unknown'):decode_document(render(w.glyphs)['shapes'])


@pytest.mark.parametrize('change',['cycle','unknown','primitive','signature','old-meaning','shape-collision'])
def test_invalid_shared_dictionary_is_rejected(change):
    data=vocabulary().document()
    d=data['definitions']['candidateexists']
    if change in ('cycle','unknown'):
        d['body']=dict(kind='call',symbol='candidateexists' if change=='cycle' else 'unregistered',arguments=[])
    elif change=='primitive':d['kind']='primitive'
    elif change=='signature':data['entries']['candidateexists']['parameters']=[];data['entries']['candidateexists']['roles']=[]
    elif change=='old-meaning':data['entries']['rain']['meaning']='別の意味'
    else:data['entries']['candidateexists']['form']=data['entries']['rain']['form']
    with pytest.raises(ValueError): DefinedVocabulary(data)


def test_extension_rejects_changed_definition_even_with_same_signature():
    data=vocabulary().document();data['definitions']['candidateexists']['body']=boolean(False)
    changed=DefinedVocabulary(data)
    with pytest.raises(ValueError,match='definition'):check_defined_extension(vocabulary(),changed)


def test_vocabulary_edition_is_read_from_visible_header():
    from scripts.check_visible_page import specimens as old_specimens
    from scripts.check_visible_syntax import integrated_document
    for row in old_specimens():
        assert decode_page(row['page']['shapes'])['document']==integrated_document()
    v=vocabulary();w=LibraryWriter(v)
    w.keyword('document');w.natural(16);w.natural(3);w.end();w.end()
    with pytest.raises(ValueError,match='edition'):decode_document(render(w.glyphs)['shapes'])


def test_cli_imports_public_names_and_restores_same_native_text(tmp_path,capsys):
    from noema.constructed import parse
    from scripts.check_visible_library import ROOT,SOURCE
    from scripts.visible_library import main
    target=tmp_path/'library.svg'
    assert main(['render',str(ROOT/SOURCE),str(target),'--width','3000','--public-names'])==0
    assert json.loads(capsys.readouterr().out)['rows']>1
    assert main(['decode',str(target),'--native','--public-names'])==0
    assert parse(capsys.readouterr().out)==candidate_examples()
