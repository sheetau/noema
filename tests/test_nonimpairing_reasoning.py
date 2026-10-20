from scripts.check_nonimpairing_reasoning import (
    causal_checks, method_checks, joint_checks, scholarly_checks, unknown_checks, structure_checks)


def test_same_work_causal_nonimpairment():
    causal_checks()


def test_fixed_method_and_complete_results():
    method_checks()


def test_one_method_for_both_requirements():
    joint_checks()


def test_native_scholarly_office_binding():
    scholarly_checks()


def test_unknown_inputs_refused():
    unknown_checks()


def test_imports_and_roundtrips():
    structure_checks()
