import pytest
from scripts.check_kant_sequence_definitions import checked,ORIGINALS,KINDS


@pytest.mark.parametrize('index',range(len(ORIGINALS)))
def test_saved_sequence_definition_keeps_its_exact_body_and_scope(index):checked(index)


def test_saved_definitions_connect_every_sequence_constructor():
    assert set().union(*(set(checked(i)['sequence_constructors']) for i in range(len(ORIGINALS))))==KINDS
