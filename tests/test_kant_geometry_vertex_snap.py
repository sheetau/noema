import pytest

from scripts.balanced_circle_script import EPS,line
from scripts.kant_geometry_reader import stroke_graph,canonical_vertices


@pytest.mark.parametrize('x',[1009.057430250,1009.057430250-1e-9,1009.057430250+1e-9])
def test_bend_endpoint_and_computed_intersection_do_not_create_a_free_spur(x):
    # Regression from statement 9: the same bend rounded to adjacent 1e-7 cells.
    lines=[line((979.763346585,32),(x,32)),line((x,32),(x+16,16))]
    vertices,edges=stroke_graph([],lines)
    assert len(vertices)==3
    assert sorted(v['degree'] for v in vertices)==[1,1,2]
    assert len(edges)==2
    assert stroke_graph([],list(reversed(lines)))==(vertices,edges)


def test_distinct_points_outside_tolerance_are_not_joined():
    a,b=(0.,0.),(2*EPS,0.)
    assert canonical_vertices({a,b})=={a:a,b:b}


def test_nearby_chains_cannot_collapse_distant_endpoints():
    a,b,c=(0.,0.),(.75*EPS,0.),(1.5*EPS,0.)
    result=canonical_vertices({a,b,c})
    assert result[a]==result[b]
    assert result[a]!=result[c]


def test_a_point_near_two_distinct_representatives_is_rejected():
    points={(0.,0.),(0.,1.5*EPS),(.1*EPS,.75*EPS)}
    with pytest.raises(ValueError,match='Ambiguous geometric vertex'):
        canonical_vertices(points)
