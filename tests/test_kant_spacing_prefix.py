from copy import deepcopy
import pytest
from scripts.balanced_circle_script import spacing_check,circle,line,MEDIUM,SMALL
from scripts.kant_spacing_extension import spacing_extension
from scripts.check_kant_spacing_prefix import cases,checked
from scripts.visible_syntax_geometry import from_svg


@pytest.mark.parametrize('index',range(len(cases())))
def test_old_and_new_route_and_layout_produce_identical_svg(index):
    row=checked(index)
    assert row['identical_svg'] and row['new_checks']<row['old_checks']


def accepts(action):
    try:action();return True
    except ValueError:return False


def composed(circles,old,new):
    spacing_check(circles+old)
    return spacing_extension(circles,old,new)


@pytest.mark.parametrize('index',range(len(cases())))
def test_spacing_partition_keeps_all_old_conditions(index):
    shapes=from_svg(checked(index)['svg'])
    circles=[s for s in shapes if s['kind']=='circle'];lines=[s for s in shapes if s['kind']=='line']
    for at in (0,len(lines)//2,len(lines)-1):
        for dy in (0.,1.,5.):
            new=deepcopy(lines[at:])
            for s in new:s['y1']+=dy;s['y2']+=dy
            assert accepts(lambda:spacing_check(circles+lines[:at]+new))==accepts(lambda:composed(circles,lines[:at],new))


def test_companion_exception_needs_all_circles_and_is_preserved():
    rings=[circle(0,32,MEDIUM),circle(MEDIUM,32,SMALL)]
    new=[line((MEDIUM+SMALL,32),(MEDIUM+SMALL+32,32))]
    assert accepts(lambda:spacing_check(rings+new))
    assert composed(rings,[],new)
    assert not accepts(lambda:spacing_check(rings[:1]+new))


def test_new_line_cannot_repair_invalid_existing_spacing():
    old=[line((0,0),(40,0)),line((0,2),(40,2))];new=[line((60,0),(100,0))]
    assert not accepts(lambda:spacing_check(old+new))
    assert not accepts(lambda:composed([],old,new))
