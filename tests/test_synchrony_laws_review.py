import pytest
from scripts.review_synchrony_laws import review_record


@pytest.mark.parametrize('i',[0,1])
def test_whole_numbered_law(i):
    r=review_record(i);assert r['decision']=='equivalent_under_stated_reading' and not r['unresolved']
