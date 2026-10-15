from copy import deepcopy
from hashlib import sha256
import json
import pytest
from noema.constructed import parse
from noema.manuscript_obligations import audit
from scripts.check_kant_manuscript_obligations import ROOT, MANIFEST


def fixture():
    doc = parse('''p:
d aa[x a] c[e[v x][v x]].
d ab[x a] c[k aa[v x]].
d ac[x a] c[k aa[v x]].
r ad[i[h[a] c]] c.
s[k ad[r[p ab]]].
s[k ad[r[p ac]]].
''')
    unit = {'id': 'test:u1', 'text': 'A B', 'text_sha256': sha256(b'A B').hexdigest()}
    review = {'unit': unit['id'], 'source_sha256': unit['text_sha256'], 'passage_range': [0,3],
        'statement_indices': [0], 'semantic_completion': False, 'counts_as_translated_coverage': False,
        'obligations': [
            {'id':'first', 'range':[0,2], 'source':'A ', 'candidate_roots':['aa','ab','ac'], 'decision':'open', 'remaining':'Review meaning.'},
            {'id':'second', 'range':[2,3], 'source':'B', 'candidate_roots':[], 'decision':'open', 'remaining':'No construction yet.'}],
        'templates': [{'symbol':'ab', 'parameter_roles':['individual']}]}
    return doc, unit, review


def test_quotes_are_dependencies_and_other_statements_do_not_complete_selected_statement():
    doc, unit, review = fixture(); before = deepcopy((doc,unit,review))
    result = audit(doc,unit,review)
    assert (doc,unit,review) == before
    first, second = result['obligations']
    assert first['unconnected_candidate_roots'] == ['ac']
    aa, ab, ac = first['structural_evidence']
    assert aa['selected_statement_path'] == {'statement_index':0, 'symbols':['ab','aa']}
    assert ab['selected_statement_path']['symbols'] == ['ab']
    assert ac['selected_statement_path'] is None
    assert ac['any_statement_path'] == {'statement_index':1, 'symbols':['ac']}
    assert second['has_recorded_candidate'] is False
    template = result['templates'][0]
    assert template['literal_function_quote_sites'] == [{'owner':'statement:0', 'path':'/body/arguments/0', 'rank':0}]
    assert template['parameters'] == [{'index':0, 'role':'individual', 'sort':'individual'}]
    assert audit(doc,unit,review) == result


@pytest.mark.parametrize('case', ('source_hash','unit','completion','coverage','gap','overlap','excerpt',
    'truncated','empty','unknown_root','duplicate_root','duplicate_id','missing_reason','closed',
    'statement_range','statement_bool','statement_duplicate','statement_empty','template_root','template_roles'))
def test_invalid_or_overclaimed_reviews_are_refused(case):
    doc,unit,review = fixture()
    if case == 'source_hash': unit['text'] = 'X B'
    elif case == 'unit': review['unit'] = 'other'
    elif case == 'completion': review['semantic_completion'] = True
    elif case == 'coverage': review['counts_as_translated_coverage'] = True
    elif case == 'gap': review['obligations'][0]['range'] = [1,2]
    elif case == 'overlap': review['obligations'][1]['range'] = [1,3]
    elif case == 'excerpt': review['obligations'][0]['source'] = 'A'
    elif case == 'truncated': review['obligations'].pop()
    elif case == 'empty': review['obligations'] = []
    elif case == 'unknown_root': review['obligations'][0]['candidate_roots'] = ['zz']
    elif case == 'duplicate_root': review['obligations'][0]['candidate_roots'] = ['aa','aa']
    elif case == 'duplicate_id': review['obligations'][1]['id'] = 'first'
    elif case == 'missing_reason': review['obligations'][0]['remaining'] = ' '
    elif case == 'closed': review['obligations'][0]['decision'] = 'complete'
    elif case == 'statement_range': review['statement_indices'] = [2]
    elif case == 'statement_bool': review['statement_indices'] = [True]
    elif case == 'statement_duplicate': review['statement_indices'] = [0,0]
    elif case == 'statement_empty': review['statement_indices'] = []
    elif case == 'template_root': review['templates'][0]['symbol'] = 'ad'
    elif case == 'template_roles': review['templates'][0]['parameter_roles'] = []
    with pytest.raises(ValueError): audit(doc,unit,review)


def test_unknown_ast_dependencies_are_refused_even_outside_the_selection():
    doc,unit,review = fixture()
    doc['declarations'][2]['body']['symbol'] = 'zz'
    with pytest.raises(ValueError,match='Unknown declaration dependency'): audit(doc,unit,review)


def test_current_manuscript_keeps_the_new_claim_outside_the_attributed_template():
    review = json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))
    units = json.loads((ROOT/review['source_units']).read_text(encoding='utf-8'))['units']
    unit = next(u for u in units if u['id'] == review['unit'])
    doc = parse((ROOT/review['document']).read_text(encoding='utf-8'))
    result = audit(doc,unit,review)
    assert len(result['obligations']) == 14
    assert ''.join(row['source'] for row in result['obligations']) == unit['text'][716:1174]
    rows = {r['id']:r for r in result['obligations']}
    assert rows['self_benefit']['unconnected_candidate_roots'] == []
    assert rows['growing_agency']['unconnected_candidate_roots'] == []
    assert rows['dignified_treatment']['unconnected_candidate_roots'] == ['iaustanding','iautreatment','iavclaim','iavtreatment']
    assert all(r['any_statement_path'] is None for r in rows['dignified_treatment']['structural_evidence'])
    assert {r['id'] for r in result['obligations'] if not r['has_recorded_candidate']} == {'tender_care','more_than_machine','author_note'}
    template = result['templates'][0]
    assert [p['role'] for p in template['parameters']] == ['reading','source','actor','office','first','second','probes','remaining']
    assert template['literal_function_quote_sites'] == [{'owner':'iatattribution','path':'/body/arguments/2','rank':2}]
    assert not result['semantic_completion'] and not result['counts_as_translated_coverage']
