"""Factor the unchanged spacing predicate when only connector lines are added."""
from scripts.balanced_circle_script import spacing_check


def spacing_extension(circles,old_lines,new_lines):
    """Caller has checked circles + old_lines; no circle is added or moved.

    Circle/line exceptions depend on all circle partners, so keep every circle
    in that check. Old/new line pairs depend only on their two segments. The
    old/old pairs were already checked and cannot be repaired by adding lines.
    """
    spacing_check(circles+new_lines)
    for new in new_lines:
        for old in old_lines:spacing_check([old,new])
    return True
