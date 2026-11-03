import math
import pytest

from scripts.kant_geometry_rules import geometry_check
from scripts.kant_geometry_reader import read_geometry
from scripts.kant_public_fragment import forms,table
from scripts.check_kant_circle_pair_correction import forbidden_shapes
from scripts.check_kant_geometry_reader import allowed_pairs
from scripts.check_kant_shared_argument import checked
from scripts.balanced_circle_script import SMALL,MEDIUM,LARGE,circle,nucleus


@pytest.mark.parametrize('key',list(forbidden_shapes()))
def test_eccentric_pair_rejected_by_both_drawing_and_reading(key):
    shapes=forbidden_shapes()[key]
    with pytest.raises(ValueError,match='smaller center on the larger rim'):
        geometry_check(shapes,[])
    with pytest.raises(ValueError,match='smaller center on the larger rim'):
        read_geometry(shapes)


@pytest.mark.parametrize('token',['and','or','implies','and_shared'])
def test_replacement_uses_medium_circumference_not_small_radius(token):
    glyph=forms(token)[0]
    rings=[s for s in glyph['shapes'] if s['kind']=='circle']
    a,b=sorted(rings,key=lambda s:s['r'])
    assert math.isclose(math.dist((a['x'],a['y']),(b['x'],b['y'])),MEDIUM)
    assert a['r']==SMALL and b['r']==MEDIUM
    assert a['x']<b['x']
    geometry_check(glyph['shapes'],glyph['paths'])


def test_concentric_pairs_and_small_centers_on_large_rims_still_allowed():
    for small,large in ((SMALL,MEDIUM),(SMALL,LARGE),(MEDIUM,LARGE)):
        if large==LARGE:
            base=nucleus(0,32,large,None,1,mode='outer')['shapes']
        else:
            base=[circle(0,32,large)]
        read_geometry(base+[circle(0,32,small)])
        for sign in (-1,1):
            away=nucleus(0,32,large,None,4 if sign==1 else 0)['shapes'] if large==LARGE else base
            read_geometry(away+[circle(sign*large,32,small)])


def test_inventory_no_longer_counts_reverse_center_on_rim():
    pairs=allowed_pairs()
    assert len(pairs)==31
    for row in pairs:
        if row['kind']=='center_on_rim':
            a,b=[s for s in row['shapes'] if s['kind']=='circle']
            assert math.isclose(math.dist((a['x'],a['y']),(b['x'],b['y'])),max(a['r'],b['r']))


def test_cold_and_hot_lookup_and_shared_svg_agree_after_rule_change():
    assert table.__wrapped__()==table()
    for index in (0,3,10):
        assert checked.__wrapped__(index)==checked(index)
