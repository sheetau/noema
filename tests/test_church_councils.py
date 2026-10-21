from scripts.check_church_councils import (
    deliberation_checks,function_checks,order_checks,district_checks,regional_checks,structure_checks)


def test_same_deliberation_actor_issue_body_and_church():deliberation_checks()


def test_assigned_function_does_not_execute_meeting():function_checks()


def test_same_complete_polity_with_adjacent_institutional_levels():order_checks()


def test_all_constituents_in_same_nearby_district():district_checks()


def test_same_province_upper_council_and_each_local_council():regional_checks()


def test_historical_articles_unchanged_imports_and_roundtrips():structure_checks()
