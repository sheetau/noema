from scripts.check_kant_number_definitions import checked


def test_saved_definitions_keep_distinct_numbers_and_parameter_scope():
    a,b=checked(0),checked(1)
    assert a['numeric_argument']==dict(kind='number',numerator=1,denominator=1)
    assert b['numeric_argument']==dict(kind='number',numerator=4,denominator=1)
    assert a['body_sha256']!=b['body_sha256'] and a['svg']!=b['svg']
