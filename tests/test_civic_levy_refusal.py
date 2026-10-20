from scripts.check_civic_levy_refusal import (
    payment_checks,civic_checks,case_checks,refusal_checks,binding_checks,norm_checks,unknown_checks,structure_checks)


def test_native_payment_and_exact_four_argument_adapter():
    payment_checks()


def test_civic_standing_does_not_require_delegated_office():
    civic_checks()


def test_same_public_levy_and_nonfactive_payment_requirement():
    case_checks()


def test_refusal_is_a_response_and_negative_practical_stance_not_nonpayment():
    refusal_checks()


def test_every_refusal_binding_position_and_length():
    binding_checks()


def test_prohibition_does_not_execute_the_refusal_or_payment():
    norm_checks()


def test_unknown_inputs_are_rejected():
    unknown_checks()


def test_preserved_meanings_and_notation():
    structure_checks()
