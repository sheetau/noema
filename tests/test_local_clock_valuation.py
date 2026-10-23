from scripts.check_local_clock_valuation import local_checks,record_checks,method_checks,modal_checks,presentation_checks,structure_checks

def test_local_indications_and_finding():assert local_checks()['native_indication_and_event_readings_bound']
def test_same_candidate_fields():assert record_checks()['two_fields_same_event_clock_context']
def test_all_events_one_execution():assert method_checks()['native_two_event_method_executed']
def test_conditional_possibility():assert modal_checks()['native_conditional_content_executed']
def test_attributed_presentation():assert presentation_checks()['existing_forward_reference_begin_reused']
def test_source_and_preserved_meanings():assert structure_checks()['three_A_symbols_same_place']
