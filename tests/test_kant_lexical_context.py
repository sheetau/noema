from copy import deepcopy

import pytest

from scripts.kant_lexical_context import LexicalContext, use_context, abbreviate
from scripts.kant_public_lexicon import vocabulary, words, declarations_for, parts_for
from scripts.kant_public_fragment import compile_statement, decode, table, forms
from scripts.check_kant_public_fragment import canonical
from scripts.check_kant_public_fragment import cases
from scripts.check_visible_syntax import call, logic, variable, quote, quant
from scripts.visible_word_forms import Word, symbol
from scripts.visible_syntax_geometry import to_svg, from_svg


def extension(place='town'):
    name = symbol(Word('compound', ('red', 'book', 'treeone')), vocabulary())
    declaration = dict(kind='definition',name=name,parameters=[],result='truth',
                       body=call('rain',call(place)))
    return name,dict(schema_version='0.16',lexicon_version='0.16',
                     declarations=[declaration],statements=[])


def test_explicit_definition_roundtrip_and_context_restored_after_failure():
    name, document = extension()
    context = LexicalContext(document)
    assert name not in words()
    with use_context(context):
        source=canonical(dict(kind='call',symbol=name,arguments=[]))
    drawing=compile_statement(source,lexicon=context)
    document['statements']=[source]
    public=LexicalContext(document).published()
    assert public['native']['statements']==[]
    reader_context=LexicalContext.from_published(public)
    assert decode(from_svg(to_svg(drawing['shapes'])),lexicon=reader_context)==source
    corrupt=deepcopy(public)
    corrupt['aliases'][0]['symbol']='unknown'
    with pytest.raises(ValueError,match='dictionary spelling'):
        LexicalContext.from_published(corrupt)
    assert name not in words()
    with pytest.raises(ValueError):
        compile_statement(source)
    with pytest.raises(ValueError):
        decode([],lexicon=context)
    assert name not in words()


def test_context_import_cache_does_not_transfer_a_changed_definition():
    name, a=extension('town')
    _, b=extension('home')
    ca,cb=LexicalContext(a),LexicalContext(b)
    assert ca.fingerprint != cb.fingerprint
    imports=[]
    for context in (ca,cb,ca):
        with use_context(context):
            imports.append(deepcopy(declarations_for((name,))))
    assert imports[0]==imports[2] and imports[0]!=imports[1]


def test_existing_public_definition_cannot_be_shadowed():
    _, document=extension()
    definition=deepcopy(declarations_for((call('rain',call('town'))['symbol'],))[-1])
    definition['result']='number'
    document['declarations']=[definition]
    with pytest.raises(ValueError,match='changes an existing public definition'):
        LexicalContext(document)


def test_abbreviations_reserve_names_and_ignore_declaration_order():
    full={('a','b'):'short',('a','x','b','c'):'first',('a','y','b','c'):'second'}
    selected, aliases=abbreviate(full)
    assert abbreviate(dict(reversed(list(full.items()))))==(selected,aliases)
    assert aliases[('a','b')]=='short'
    assert aliases[selected['first']]=='first'
    assert aliases[selected['second']]=='second'
    assert selected['first'] != selected['second']


@pytest.mark.parametrize('rank',[0,1,3])
def test_ranked_quotes_remain_distinct_from_nested_quotes(rank):
    term=dict(quote(call('book')),**({'rank':rank} if rank else {}))
    source=canonical(logic('equal',term,term))
    drawing=compile_statement(source)
    assert decode(from_svg(to_svg(drawing['shapes'])))==source
    if rank:
        nested=quote(quote(call('book')))
        other=compile_statement(canonical(logic('equal',nested,nested)))
        assert to_svg(drawing['shapes']) != to_svg(other['shapes'])


@pytest.mark.parametrize('reference',['x','y'])
def test_lambda_preserves_inner_and_outer_bindings(reference):
    term=dict(kind='lambda',parameters=[dict(name='y',sort='individual')],body=variable(reference))
    source=canonical(quant('forall','x',logic('equal',term,term)))
    drawing=compile_statement(source)
    assert decode(from_svg(to_svg(drawing['shapes'])))==source


def test_rank_marker_cannot_modify_a_nonquotation():
    with pytest.raises(ValueError,match='rank marker'):
        decode(forms('quote_raise')[0]['shapes']+[
            dict(s, x=s['x']+150) for s in forms(call('town')['symbol'])[0]['shapes']])


def test_new_forms_are_disjoint_from_all_reserved_words():
    assert len(table())==53


@pytest.mark.parametrize('index',[0,7,18,22])
def test_local_candidate_checks_preserve_complete_prefix_layout(index):
    source=cases()[index][2]
    whole=compile_statement(source,local_checks=False)
    local=compile_statement(source,local_checks=True)
    assert to_svg(whole['shapes'])==to_svg(local['shapes'])
    assert decode(from_svg(to_svg(local['shapes'])))==source
