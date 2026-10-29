"""Current finite population bindings retain independent quantity and concession."""
from scripts import check_kant_self_development_count_visible as check

def test_current_population_count_and_concession():check.count_checks()
def test_unknowns_and_nonfactive_quantity():check.unknown_checks()
def test_unbounded_population_quantifiers_are_preserved():check.unbounded_checks()
