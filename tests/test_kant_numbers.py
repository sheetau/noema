from math import gcd
import pytest
from scripts import kant_public_fragment as writing
from scripts.kant_number_grammar import components,number_tokens,read_number,MAX_DIGITS
from scripts.check_kant_numbers import cases,checked,preserved_rows,preserved,number,malformed,raw_numeral_svg
from scripts.visible_syntax_geometry import from_svg


@pytest.mark.parametrize('index',range(len(cases())))
def test_actual_ink_preserves_number_arguments_scope_and_quotation(index):
    checked(index)


@pytest.mark.parametrize('index',range(len(preserved_rows())))
def test_numeric_mode_preserves_saved_nonnumeric_ink(index):
    preserved(index)


@pytest.mark.parametrize('key',list(malformed()))
def test_noncanonical_number_is_rejected_from_ink(key):
    parts,message=malformed()[key]
    with pytest.raises(ValueError,match=message):
        writing.decode(list(reversed(from_svg(raw_numeral_svg(parts)))))


@pytest.mark.parametrize('mode',['branch','seam'])
def test_numeral_cannot_hide_a_dependency_or_word_boundary(mode):
    with pytest.raises(ValueError,match='Numeral cannot carry'):
        writing.decode(from_svg(raw_numeral_svg(number_tokens(number(10)),**{mode:True})))


def test_positional_rule_and_canonical_rational_limits():
    for a in range(-90,91):
        for b in (1,2,7,11):
            if gcd(abs(a),b)!=1:continue
            source=number(a,b);tokens=number_tokens(source)
            assert read_number(tokens[0],iter(tokens[1:]).__next__)==source
    for a,b in [(True,1),(1,False),(1,0),(1,-2),(2,4),(0,2)]:
        with pytest.raises(ValueError,match='canonical rational'):number_tokens(number(a,b))
    largest=number(9**MAX_DIGITS-1)
    tokens=number_tokens(largest)
    assert read_number(tokens[0],iter(tokens[1:]).__next__)==largest
    with pytest.raises(ValueError,match='digit resource limit'):number_tokens(number(9**MAX_DIGITS))
    digits,_=components()
    with pytest.raises(ValueError,match='digit resource limit'):
        read_number('number_positive',iter([digits[1]]*(MAX_DIGITS+1)).__next__)


def test_numeric_shapes_are_intrinsic_and_old_word_table_is_unambiguous():
    digits,_=components()
    for value,token in enumerate(digits):
        glyph=writing.forms(token)[0];g=writing.read_geometry(glyph['shapes'])
        assert len(g['circles'])==1 and g['circles'][0]['size']=='medium'
        assert g['circles'][0]['center_direction']==(None if value==0 else value-1)
    assert writing.table.__wrapped__()==writing.table()
