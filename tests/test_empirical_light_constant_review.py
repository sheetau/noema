import pytest
from scripts.review_empirical_light_constant import review_record


@pytest.mark.parametrize('i',[0,1,2])
def test_whole_source_unit_in_connected_sentence(i):
    r=review_record(i);assert r['decision']=='equivalent_under_stated_reading' and not r['unresolved']
