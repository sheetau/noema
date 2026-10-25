from copy import deepcopy
import json
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.visible_quantity_vocabulary import QuantityVocabulary,check_quantity_extension,module_records,MODULES,PRIMITIVES
from scripts.visible_scope_vocabulary import ScopeVocabulary
from scripts.visible_compound_vocabulary import CompoundVocabulary
from scripts.visible_defined_vocabulary import DefinedVocabulary
from scripts.visible_syntax_vocabulary import Vocabulary
from scripts.visible_quantity_page import PublicWriter,compile_document,decode_document,compile_page,decode_page,main
from scripts.visible_language_page import decode_page as edition_four_decode
from scripts.visible_word_forms import Word,symbol
from scripts.visible_syntax_geometry import render,from_svg,to_svg
from scripts.visible_page import packet,vertical_bounds
from scripts.visible_lexical_script import _translate
from scripts.shared_reference import truth
from scripts.check_visible_quantity_library import vocabulary,new_names,word_checks,cases,arithmetic_example,container_example,question_example,ROOT,SOURCE


def document(declarations,statements=()):
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=list(statements)))


def test_all_previous_words_and_new_bodies_keep_exact_identity():
    v=vocabulary();data=v.document();parent=ScopeVocabulary()
    assert (len(data['entries']),len(data['compounds']),len(data['definitions']),len(data['primitives']))==(30,141,151,4)
    assert data['edition']==5 and check_quantity_extension(parent,v)
    for name in parent._order:
        assert parent.word(name)==v.word(name)
        assert parent.declaration(name)==v.declaration(name)
    for module in MODULES:
        original=parse((ROOT/module['document']).read_text(encoding='utf-8'))
        for declaration in original['declarations']:
            name=declaration['name'];field='primitives' if name in PRIMITIVES else 'definitions'
            assert data[field][name]==declaration
            restored=v.decode_names(document(v.imports([name])))
            assert next(d for d in restored['declarations'] if d['name']==name)==declaration


def test_all_fifty_one_typed_calls_and_quotes_decode_from_svg():
    rows=word_checks()
    assert len(rows)==51 and {r['name'] for r in rows}==set(new_names())
    assert {r['name'] for r in rows if r['kind']=='primitive'}==PRIMITIVES
    assert max(r['glyphs'] for r in rows)<=768 and max(r['shapes'] for r in rows)<=4096


def test_complete_inventory_and_seven_meaning_examples_decode():
    rows=cases();v=vocabulary()
    assert len(rows)==10
    inventory={d['name'] for row in rows[:3] for d in row['native']['declarations']}
    assert inventory==set(v._order) and len(inventory)==171
    assert [len(row['native']['declarations']) for row in rows[:3]]==[80,40,51]
    assert [r['result'] for r in rows[3:9]]==[[dict(kind='assert',value=True)]]*6
    assert rows[-1]['result']==[dict(kind='ask',answers=[['a'],['b']])]
    for row in rows[3:]:assert decode_page(row['page']['shapes'],v,public_names=True)['document']==row['native']


def test_module_order_preserves_shared_dependencies_and_semantic_records():
    assert module_records()==module_records(list(reversed(MODULES)))
    assert len(module_records())==51
    imports=vocabulary().decode_names(document(vocabulary().imports(new_names())))
    for name in ('memberof','distinctmembers','membercount'):
        assert sum(d['name']==name for d in imports['declarations'])==1


@pytest.mark.parametrize('field',['body','meaning','contract'])
def test_nonidentical_duplicate_dependency_is_rejected(tmp_path,field):
    module=MODULES[1]
    source=parse((ROOT/module['document']).read_text(encoding='utf-8'))
    basis=json.loads((ROOT/module['basis']).read_text(encoding='utf-8'))
    if field=='body':next(d for d in source['declarations'] if d['name']=='memberof')['body']=truth(False)
    elif field=='meaning':basis['definitions']['memberof']='異なる語義'
    else:basis['public_contracts']['memberof']['arguments'][0]['interpretation']='異なる役割規約'
    native=tmp_path/'changed.noema';info=tmp_path/'changed.json'
    native.write_text(format_graph(normalize_document(source)),encoding='utf-8')
    basis['document']=str(native);info.write_text(json.dumps(basis,ensure_ascii=False),encoding='utf-8')
    with pytest.raises(ValueError,match='dependency differs'):
        module_records([MODULES[0],dict(document=str(native),basis=str(info))])


def test_registration_order_changes_neither_imports_nor_geometry():
    data=vocabulary().document()
    for field in ('entries','compounds','definitions','primitives'):data[field]=dict(reversed(list(data[field].items())))
    changed=QuantityVocabulary(data)
    assert changed.imports(list(reversed(new_names())))==vocabulary().imports(new_names())
    assert compile_page(vocabulary().encode(arithmetic_example()),changed,max_width=3200.)==cases()[3]['page']


@pytest.mark.parametrize('change',['old-root','old-compound','old-body','collision','unknown-part','definition-to-primitive',
    'primitive-to-definition','primitive-signature','primitive-missing','dependency','cycle','signature'])
def test_invalid_dictionary_cannot_reinterpret_or_disguise_arithmetic(change):
    data=vocabulary().document()
    if change=='old-root':data['entries']['home']['meaning']='別の意味'
    elif change=='old-compound':data['compounds']['referentat']['parts']=['rain','treeone']
    elif change=='old-body':data['definitions']['referentat']['body']=truth(False)
    elif change=='collision':data['compounds']['memberof']['parts']=data['compounds']['referentat']['parts']
    elif change=='unknown-part':data['compounds']['memberof']['parts']=['fruit','unknown']
    elif change=='definition-to-primitive':data['definitions']['memberof']['kind']='primitive'
    elif change=='primitive-to-definition':
        data['definitions']['rationaladd']=data['primitives'].pop('rationaladd')
    elif change=='primitive-signature':data['primitives']['rationaladd']['result']='truth'
    elif change=='primitive-missing':data['primitives'].pop('rationaladd')
    elif change in ('dependency','cycle'):
        data['definitions']['memberof']['body']=dict(kind='call',symbol='unknown' if change=='dependency' else 'memberof',arguments=[])
    else:data['compounds']['memberof']['result']='individual'
    with pytest.raises(ValueError):QuantityVocabulary(data)


def test_changed_new_body_or_arithmetic_meaning_is_not_compatible():
    for field in ('body','meaning'):
        data=vocabulary().document()
        if field=='body':data['definitions']['memberof']['body']=truth(False)
        else:data['compounds']['rationaladd']['meaning']='二つの値の別の演算'
        fork=QuantityVocabulary(data)
        with pytest.raises(ValueError):check_quantity_extension(vocabulary(),fork)


def test_public_primitive_stays_primitive_and_cannot_be_replaced_with_a_local_definition():
    v=vocabulary();d=v.declaration('rationaladd')
    assert d['kind']=='primitive'
    from scripts.shared_readings import num
    replacement=dict(kind='definition',name=d['name'],parameters=[dict(name='left',sort='number'),dict(name='right',sort='number')],
        result='number',body=num(0))
    with pytest.raises(ValueError,match='public meaning'):compile_document(document([replacement]))


def test_reader_rejects_shadow_and_missing_arithmetic_dependency():
    v=vocabulary();d=v.declaration('rationaladd');w=PublicWriter(v)
    w.keyword('document');w.natural(16);w.natural(5);w.keyword('definition');w.name(d['name'])
    w.parameters([]);w.type('truth');w.expr(truth(True),());w.end();w.end()
    with pytest.raises(ValueError,match='shadows'):decode_document(render(w.glyphs)['shapes'])
    w=PublicWriter(v);w.keyword('document');w.natural(16);w.natural(5)
    w.keyword('import');w.name(v.declaration('quantityequal')['name']);w.end();w.end()
    with pytest.raises(ValueError,match='Unknown'):decode_document(render(w.glyphs)['shapes'])


@pytest.mark.parametrize('constructor',[Vocabulary,DefinedVocabulary,CompoundVocabulary,ScopeVocabulary])
def test_old_local_spelling_collision_retains_its_old_interpretation(constructor):
    old=constructor();name=symbol(Word('compound',('round','give')),old)
    d=document([dict(kind='definition',name=name,parameters=[],result='truth',body=truth(True))])
    page=compile_page(d,old,max_width=1800.)
    assert decode_page(page['shapes'])['document']==d
    assert decode_page(page['shapes'],public_names=True)['document']==d
    with pytest.raises(ValueError,match='public meaning'):compile_page(d)


def test_old_public_headers_and_new_header_select_their_exact_dictionaries():
    for vocab,names in ((Vocabulary(),['home']),(DefinedVocabulary(),['candidateexists']),
        (CompoundVocabulary(),['chronology']),(ScopeVocabulary(),['referentat']),(vocabulary(),['rationaladd'])):
        declarations=vocab.imports(names) if hasattr(vocab,'imports') else [vocab.declaration(n) for n in names]
        d=document(declarations)
        assert decode_page(compile_page(d,vocab,max_width=1800.)['shapes'])['document']==d


def test_unknown_edition_and_explicit_wrong_dictionary_rejected():
    w=PublicWriter(vocabulary());w.keyword('document');w.natural(16);w.natural(6);w.end();w.end()
    with pytest.raises(ValueError,match='edition'):decode_document(render(w.glyphs)['shapes'])
    page=cases()[3]['page']
    with pytest.raises(ValueError,match='edition'):decode_page(page['shapes'],ScopeVocabulary())
    with pytest.raises(ValueError,match='edition'):edition_four_decode(page['shapes'])


def test_split_header_preserves_row_and_atomic_boundary_checks():
    d=document([],[dict(kind='assert',body=truth(True))]);v=vocabulary();w=PublicWriter(v);w.document(d)
    first=render(packet(w.glyphs[:2],0,final=False,vocabulary=v))['shapes']
    second=render(packet(w.glyphs[2:],1,final=True,vocabulary=v))['shapes']
    shift=vertical_bounds(first)[1]+64-vertical_bounds(second)[0]
    assert decode_page(first+_translate(second,0,shift))['document']==d
    with pytest.raises(ValueError,match='row'):decode_page(_translate(second,0,shift))


def test_scrambled_svg_elements_and_paragraphs_preserve_question():
    v=vocabulary();d=v.encode(question_example());page=compile_page(d,v,max_width=1800.,paragraph_starts=[0])
    assert decode_page(from_svg(to_svg(list(reversed(page['shapes'])))))==dict(document=d,paragraph_starts=[0])


def test_cli_roundtrip_of_explicit_content_and_measurement_functions(tmp_path,capsys):
    target=tmp_path/'contents.svg'
    assert main(['render',str(ROOT/SOURCE),str(target),'--width','3200','--public-names'])==0
    assert json.loads(capsys.readouterr().out)['rows']>1
    assert main(['decode',str(target),'--native','--public-names'])==0
    assert parse(capsys.readouterr().out)==container_example()
