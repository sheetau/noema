from copy import deepcopy
import pytest

from scripts.check_kant_shared_argument import cases,checked
from scripts.kant_public_fragment import compile_statement,decode,events,table,feature,forms
from scripts.kant_geometry_reader import read_geometry
from scripts.check_kant_public_words import checked as word_checked,identities


@pytest.mark.parametrize('index',range(len(cases())))
@pytest.mark.parametrize('sharing',[True,False])
def test_shared_and_explicit_svg_restore_identical_native_syntax(index,sharing):
    assert checked(index,sharing)['source']==cases()[index][2]


@pytest.mark.parametrize('index',[i for i,c in enumerate(cases()) if c[3]])
def test_sharing_removes_occurrences_without_a_new_header(index):
    a,b=checked(index),checked(index,False)
    assert a['circles']<b['circles']
    from scripts.kant_public_fragment import event_count
    assert event_count(events(a['source']))<event_count(events(a['source'],sharing=False))


def test_association_remains_visible():
    assert checked(8)['svg']!=checked(9)['svg']
    assert checked(8)['source']!=checked(9)['source']


def test_quote_scope_does_not_capture_the_ambient_binder():
    # Both quoted binders normalize to va independently, not the outer frame.
    source=checked(11)['source']
    assert source['body']['arguments'][0]['body']['variable']=='va'
    assert source['body']['arguments'][1]['body']['variable']=='va'
    assert decode(checked(11)['compiled']['shapes'])==source


def test_malformed_shared_head_without_argument_is_rejected():
    shapes=forms('and_shared')[0]['shapes']
    with pytest.raises(ValueError,match='requires one visible terminal'):
        decode(shapes)


def test_sharing_is_not_semantic_deduplication():
    # Equal sorts or related referents are insufficient: exact terminal syntax
    # and the existing public unary signature must both agree.
    for index in (5,6,7):
        assert checked(index)['fused']==0


def test_shared_glyph_is_distinct_from_every_published_root():
    g=read_geometry(forms('and_shared')[0]['shapes'])
    assert table()[feature(g,range(len(g['circles'])))]=='and_shared'


@pytest.mark.parametrize('index',[0,47,188,len(identities())-1])
def test_unchanged_public_reference_paths(index):
    assert word_checked(index)['token']==identities()[index]


def test_cold_and_hot_shared_decoding_agree():
    assert checked.__wrapped__(0)==checked(0)
    assert checked.__wrapped__(11)==checked(11)
