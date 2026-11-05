import pytest
from scripts.concept2_assembly_reader import AssemblyCodec
from tests import test_concept2_trunk as prior


@pytest.fixture(scope='module')
def codec():return AssemblyCodec(prior.codec.__wrapped__().dictionary)


@pytest.mark.parametrize('check',[
    prior.test_svg_roundtrip_preserves_argument_order_and_prefix_word_boundary,
    prior.test_scope_dot_alias_and_hole_controls_read_from_svg,
    prior.test_merge_composes_repeated_arguments_results_quotes_and_binders,
    prior.test_extended_native_corpus_individual_and_folded_svg,
    prior.test_malformed_type_headers_and_typed_application_fail_from_svg,
    prior.test_quotation_checks_referenced_definition_evaluation_depth,
    prior.test_unpaired_dots_and_out_of_scope_values_are_rejected,
])
def test_existing_syntax_and_rejections_are_preserved(codec,check):check(codec)
