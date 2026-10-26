from copy import deepcopy
from dataclasses import replace
from functools import lru_cache
import pytest

from scripts.visible_collection import *
from scripts.check_visible_collection import vocabulary, source, saved, compiled, interpret, LABEL
from scripts.visible_senses_book import compile_book
from scripts.visible_syntax_geometry import from_svg, to_svg
from scripts.visible_lexical_script import _shape_set
from scripts.shared_modality import call, v, op
from scripts.shared_reference import I, T, definition
from scripts.shared_time import q
from scripts.shared_focus import quote, eq


@lru_cache(maxsize=1)
def small():
    vocab = vocabulary()
    doc = vocab.decode_names(normalize_document(dict(schema_version='0.16', lexicon_version='0.16',
        declarations=vocab.imports({'red','aki','above'}), statements=[])))
    a = symbol(Word('compound', ('rain','book','home')), vocab)
    b = symbol(Word('compound', ('rain','book','town')), vocab)
    doc['declarations'].extend(definition(n, [], T, call('red', call('aki'))) for n in (a,b))
    common = op('and', call('above',v('x'),v('y')), call('red',v('x')))
    doc['statements'] = [dict(kind='ask',body=eq(quote(call(a)),quote(call(b)))),
        dict(kind='ask',body=q('forall','x',I,q('exists','y',I,op('and',common,op('and',common,common)))))]
    return vocab.encode(normalize_document(doc))


@lru_cache(maxsize=1)
def stream():
    return body_stream(small(), vocabulary())


def streams(cuts, *, header_change=None):
    tokens = stream()[0]; positions = [0, *cuts, len(tokens)]; result = []
    for i,(a,b) in enumerate(zip(positions,positions[1:])):
        h = Header(LABEL, i, len(positions)-1, len(tokens), a, b-a,
                   len(small()['declarations']), len(small()['statements']))
        if header_change:
            h = header_change(i,h)
        head = header_stream(h,vocabulary())[0]
        result.append((head+tokens[a:b], [], 1, 1))
    return result


def test_every_legal_two_volume_cut_preserves_names_binding_and_quotes():
    tokens,_,bounds,doc = stream()
    for cut in sorted(bounds-{0,len(tokens)}):
        assert assemble(streams([cut]),vocabulary())['document']==doc


def test_illegal_cut_inside_word_keyword_or_numeral_is_rejected():
    tokens,_,bounds,_=stream()
    illegal=sorted(set(range(1,len(tokens)))-bounds)
    assert illegal
    for cut in illegal:
        with pytest.raises(ValueError,match='indivisible'):
            assemble(streams([cut]),vocabulary())


@pytest.mark.parametrize('field,value', [('ordinal',0),('offset',0),('volumes',3),
    ('total',10000),('declarations',99),('statements',99),
    ('label',Word('proper',('book','rain')))])
def test_inconsistent_volume_headers_rejected(field,value):
    cut=sorted(stream()[2])[10]
    inputs=streams([cut],header_change=lambda i,h:replace(h,**{field:value}) if i else h)
    with pytest.raises(ValueError):
        assemble(inputs,vocabulary())


def test_consistently_wrong_record_count_is_rejected():
    inputs=streams([],header_change=lambda i,h:replace(h,statements=h.statements+1))
    with pytest.raises(ValueError,match='record counts'):
        assemble(inputs,vocabulary())


def test_truncated_repeated_reordered_and_extra_streams_rejected():
    cut=sorted(stream()[2])[10]; inputs=streams([cut])
    for bad in (inputs[:-1],inputs[1:],inputs[::-1],inputs+[inputs[-1]],inputs+[inputs[0]]):
        with pytest.raises(ValueError):
            assemble(bad,vocabulary())


@lru_cache(maxsize=1)
def little_pages():
    result=compile_collection(small(),LABEL,vocabulary(),payload=64)
    return [from_svg(to_svg(p['shapes'])) for p in result['pages']]


def test_saved_geometry_drives_order_and_scope():
    pages=little_pages(); result=decode_collection(iter(pages),vocabulary())
    assert result['document']==small() and result['volumes']>1
    for bad in (pages[:-1],pages[1:],pages[::-1],pages+[pages[-1]]):
        with pytest.raises(ValueError):
            decode_collection(bad,vocabulary())


def test_broken_geometry_is_rejected():
    pages=deepcopy(little_pages()); pages[0]=pages[0][1:]
    with pytest.raises(ValueError):
        decode_collection(pages,vocabulary())


def test_old_book_limit_stays_enforced_and_new_saved_collection_is_complete():
    doc=vocabulary().encode(source())
    with pytest.raises(ValueError,match='node budget'):
        compile_book(doc,vocabulary())
    result=saved()
    assert result['document']==source()
    assert len(result['document']['declarations'])==392
    assert result['pages']>8 and result['volumes']>1 and nodes(doc)>8192
    for volume in compiled()['volumes']:
        assert volume['pages']<=8
    for page in compiled()['pages']:
        assert page['glyphs']<=768 and len(page['shapes'])<=4096


def test_all_finite_two_individual_relations_keep_senses_and_alias_identity():
    doc=saved()['document']
    for mask in range(16):
        answers=interpret(doc,mask)
        assert answers[-3:-1]==[False,True]
    assert interpret(doc,0)[-1] is False
    assert interpret(doc,15)[-1] is True


def test_forward_reference_duplicate_shadow_and_wrong_type_are_rejected():
    for mode in ('forward','duplicate','shadow','type'):
        doc=deepcopy(small())
        if mode=='forward':
            doc['declarations'][-2]['body']=call(doc['declarations'][-1]['name'])
        elif mode=='duplicate':
            doc['declarations'].append(deepcopy(doc['declarations'][-1]))
        elif mode=='shadow':
            doc['declarations'][-1]['name']=vocabulary().declaration('red')['name']
        else:
            doc['declarations'][-1]['result']='individual'
        with pytest.raises(ValueError):
            body_stream(doc,vocabulary())


def test_single_logical_record_limit_is_not_replaced_by_collection_limit():
    doc=deepcopy(small())
    row=dict(kind='ask',body=dict(kind='sequence',element='individual',
        items=[call(vocabulary().declaration('aki')['name']) for _ in range(8193)]))
    # Resource checking precedes any assertion that this is a well-typed ask.
    doc['statements']=[row]
    with pytest.raises(ValueError,match='logical record'):
        check_document(doc)


def test_unknown_format_edition_and_header_atomicity_are_rejected():
    h=Header(LABEL,0,1,len(stream()[0]),0,len(stream()[0]),len(small()['declarations']),2)
    head,_,bounds=header_stream(h,vocabulary())
    bad=[i for i in range(1,len(head)) if i not in bounds]
    assert bad
    for cut in bad:
        with pytest.raises(ValueError,match='header field'):
            assemble([(head+stream()[0],[cut],1,2)],vocabulary())
    changed=head[:]
    changed[0]=_shape_set(family_glyph('logic')['shapes'])
    with pytest.raises(ValueError):
        HeaderReader(changed,vocabulary()).header()


def test_collection_limits_and_payload_targets_reject_invalid_values():
    tokens,_,bounds,_=stream()
    for payload in (0,True,31,6144):
        with pytest.raises(ValueError):
            partition(tokens,bounds,payload)
    for change in (dict(volumes=MAX_VOLUMES+1),dict(total=MAX_COLLECTION_GLYPHS+1),
                   dict(declarations=MAX_DECLARATIONS+1),dict(statements=MAX_STATEMENTS+1)):
        h=Header(LABEL,0,1,len(tokens),0,len(tokens),5,2)
        with pytest.raises(ValueError):
            header_stream(replace(h,**change),vocabulary())
