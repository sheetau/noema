from scripts import check_individual_departure as checks


def test_order():
    assert checks.order_checks()['cases'] == 135


def test_native_adapters():
    assert all(row['native_component_executed'] for row in checks.adapter_checks().values())


def test_same_person_scope():
    assert checks.scope_checks()['contrasts']['split_people'] == [False]


def test_attribution_and_consequence():
    assert checks.discourse_checks()['world_contents_unknown']


def test_structure_and_preserved_reviews():
    assert checks.structure_checks()['new_authored_assertions'] == 1
