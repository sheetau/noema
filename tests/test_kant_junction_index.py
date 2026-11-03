import math
import pytest
from scripts.kant_junction_index import JunctionIndex,bounds
from scripts.kant_readable_flow import joins_away_from_ends
from scripts.circle_contact_script import line


@pytest.mark.parametrize('offset,expected',[(0.,True),(.003,True),(.008,False)])
def test_distance_sum_tolerance_is_an_ellipse_not_an_epsilon_box(offset,expected):
    old=[line((0.,0.),(100.,0.))]
    new=[line((50.,offset),(50.,20.))]
    assert joins_away_from_ends(new,old,()) is expected
    assert JunctionIndex(old).joins(new,()) is expected


def test_all_directions_offsets_and_allowed_endpoints_match_the_old_predicate():
    old=[line((0.,0.),(100.,0.)),line((0.,0.),(0.,64.)),line((0.,0.),(64.,64.))]
    index=JunctionIndex(old)
    for x in (-1000.,-1e-7,0.,32.,64.,1000.):
        for y in (-64.,-.003,0.,.003,.008,64.):
            for dx,dy in ((32.,0.),(0.,32.),(32.,32.),(32.,-32.),(0.,0.)):
                new=[line((x,y),(x+dx,y+dy))]
                for ends in ((),((x,y),(x+dx,y+dy)),((0.,0.),)):
                    expected=joins_away_from_ends(new,old,ends)
                    assert index.joins(new,ends)==expected
                    assert JunctionIndex(old).joins(new,ends)==expected


def test_large_and_nonfinite_coordinates_use_the_unmodified_predicate():
    for magnitude in (1e6,1e10,1e16,math.inf,math.nan):
        old=[line((0.,0.),(magnitude,0.))]
        new=[line((32.,.003),(32.,64.))]
        assert JunctionIndex(old).joins(new,())==joins_away_from_ends(new,old,())
        if not math.isfinite(magnitude) or magnitude>1e6:assert bounds(old[0]) is None


def test_shared_endpoints_and_split_ink_keep_their_original_junction_meaning():
    old=[line((0.,0.),(32.,0.)),line((32.,0.),(64.,0.))]
    new=[line((64.,0.),(96.,32.))]
    assert not JunctionIndex(old).joins(new,((64.,0.),(96.,32.)))
    assert JunctionIndex(old).joins(new,())
    fork=[line((32.,0.),(32.,32.))]
    assert JunctionIndex(old).joins(fork,())


def test_far_lines_are_skipped_but_near_lines_still_use_the_old_predicate(monkeypatch):
    old=[line((1000.,0.),(1100.,0.))]
    def unexpected(*args):raise AssertionError('Far pair reached the detailed predicate')
    monkeypatch.setattr('scripts.kant_junction_index._on_segment',unexpected)
    assert not JunctionIndex(old).joins([line((0.,0.),(32.,0.))],())
    with pytest.raises(AssertionError,match='Far pair'):
        JunctionIndex(old).joins([line((1050.,0.),(1050.,32.))],())
