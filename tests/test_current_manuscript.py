from noema.constructed import parse
from noema.extraction import _references
from scripts.check_current_manuscript import ROOT,CORE,fixture,schema,model,checks,binding_audit,input_paths,CONTRASTS,RESPONSE_PRIMITIVES
import pytest


def test_current_source_and_every_referenced_definition_are_preserved():
    source=parse((ROOT/CORE).read_text(encoding='utf-8'))
    lookup={d['name']:d for d in fixture()['declarations']}
    assert all(lookup[d['name']]==d for d in source['declarations'])
    assert fixture()['statements'][0]['body']['symbol']==schema()
    for name in (schema(),'ibcfamily','ibcdepiction','ibcresistant','ryu','ibbapposition','ibbbundle'):
        assert lookup[name]['kind']=='definition'


def test_diagnostic_policy_is_composed_and_not_a_replacement_for_source_meaning():
    policy=next(d for d in fixture()['declarations'] if d['name']=='jpnew')
    assert 'iavtreatment' in _references(policy['body'])
    assert 'jppolicy' not in _references(policy['body'])
    audit=binding_audit()
    assert [p['role'] for p in audit['parameters']]==['reading','source','actor','office','first','second','probes','remaining']
    assert audit['parameters'][-1]['referenced_declarations']=={'jpremaining':'primitive'}
    assert audit['source_claim_is_still_template_attribution']
    assert audit['remaining_is_still_external_relation']
    assert all(p['binding_status']=='diagnostic_interpretation_only' for p in audit['parameters'])


def test_model_does_not_replace_human_and_policy_layers_with_nominal_fixture():
    p,domain,scenes=model()
    assert p['aa']('person') and p['aa']('other')
    assert p['iaxcases']('person','topicone','political','left')
    assert {'germ','detail','cover','prior','prior_scope'}<=set(domain)
    assert {'low','high','left','right','political'}<=set(scenes)
    for name in RESPONSE_PRIMITIVES:
        with pytest.raises(AssertionError,match='Attributed response executed'):p[name]()


def test_whole_current_schema_and_contrasts():
    result=checks()
    assert result['baseline']==dict(schema=True,premise_witness=True,appraisal=True,actual_benefit=False,
        beneficiaries=True,policy_inclusion=True,political_cause=True,current_family=True,apposition=True)
    assert set(result['contrasts'])==set(CONTRASTS)
    assert all(v==[False] for v in result['contrasts'].values())
    assert not result['response_conditions_executed']


def test_report_pins_the_current_source_and_inherited_integration():
    assert {CORE,'scripts/check_policy_integration.py','scripts/check_property_apposition.py',
        'scripts/check_cover_reference.py','data/kant-manuscript-obligations-v8.json'}<=input_paths()
