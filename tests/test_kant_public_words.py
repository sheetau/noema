import pytest

from scripts.check_kant_public_words import checked, identities, application_checked, application_cases, named
from scripts.kant_public_lexicon import read_word, parts_for, words, spellings, mark_boundaries
from scripts.kant_public_fragment import decode
from scripts.kant_geometry_reader import read_geometry
from scripts.balanced_circle_script import MEDIUM
from scripts.kant_readable_flow import route


@pytest.mark.parametrize('index', range(len(identities())))
def test_all_public_reference_identities_from_actual_svg(index):
    assert checked(index)['token'] == identities()[index]


@pytest.mark.parametrize('index', range(len(application_cases())))
def test_compound_application_and_word_boundaries(index):
    assert application_checked(index)['source']


def test_root_sequence_and_compound_are_separated_by_a_public_boundary():
    tokens = [named('book'), named('home')]
    assert read_word(tokens, 0) == (named('speechreceived'), 2)
    assert read_word(tokens, 0, stops={1}) == (named('book'), 1)
    assert read_word(tokens, 1, stops={1}) == (named('home'), 2)
    assert application_checked(2)['seams'] == 1


def test_joining_a_needed_boundary_does_not_preserve_the_old_syntax():
    row = application_checked(2)
    compiled = row['compiled'];a,b=compiled['groups'][1:]
    circles = [s for s in compiled['shapes'] if s['kind']=='circle']
    joined = route(dict(x=a['center'][0],y=a['center'][1],radius=MEDIUM),
                   dict(x=b['center'][0],y=b['center'][1],radius=MEDIUM), circles)
    assert joined is not None
    shapes = compiled['shapes']+joined[1]
    read_geometry(shapes)  # The mutation is legal geometry; its parse changed.
    with pytest.raises(ValueError):
        decode(shapes)


def test_each_word_needs_no_fixed_start_or_end_marker():
    for token, parts in parts_for().items():
        stream = [dict(token=p,side=None,**({'word':token} if i==0 else {})) for i,p in enumerate(parts)]
        assert mark_boundaries(stream) == stream
        assert not any(event.get('lexical_seam') for event in stream)
        assert read_word([e['token'] for e in stream], 0) == (token, len(parts))


def test_existing_spelling_prefixes_do_not_require_ast_search():
    count = 0
    for parts, word in spellings().items():
        for shorter in range(1,len(parts)):
            if parts[:shorter] not in spellings():
                continue
            count += 1
            assert read_word(parts,0,stops={shorter}) == (spellings()[parts[:shorter]],shorter)
    assert count > 30


def test_cold_hot_references_and_boundary_cases_match():
    for index in (0,len(identities())-1):
        assert checked.__wrapped__(index) == checked(index)
    assert application_checked.__wrapped__(2) == application_checked(2)
