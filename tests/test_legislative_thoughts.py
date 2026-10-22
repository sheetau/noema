from scripts import check_legislative_thoughts as check


def test_strict_improvement_keeps_same_legal_comparison():check.comparison_checks()
def test_own_public_views_do_not_require_actual_improvement():check.own_public_checks()
def test_all_items_are_presented_in_one_activity():check.plural_checks()
def test_direct_and_quoted_ten_object_binding():check.binding_checks()
def test_existing_meanings_and_ranked_roundtrips():check.structure_checks()
