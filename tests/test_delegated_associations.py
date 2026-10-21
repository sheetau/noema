from scripts.check_delegated_associations import (
    population_checks, delegation_checks, role_checks, source_checks, parties_checks, unknown_checks, structure_checks)


def test_all_members_not_only_qualified_subset(): population_checks()


def test_every_constituent_and_member_has_same_qualified_mandate(): delegation_checks()


def test_same_native_role_appointment_and_service(): role_checks()


def test_clerical_membership_does_not_exclude_elders_from_delegate_group(): source_checks()


def test_parties_fixed_independently_of_oath_time_or_qualification(): parties_checks()


def test_unknown_constituency_and_mandate_are_not_omissions(): unknown_checks()


def test_historical_sources_imports_and_roundtrips(): structure_checks()
