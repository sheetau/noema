from scripts.check_policy_integration import fixture,checks,model,CONTRASTS,input_paths,benefit,political,collective
from scripts.compose_policy_constraints import ROOT,CORE
from noema.constructed import parse
from noema.extraction import _references


def test_actual_source_definitions_are_preserved_including_every_parent():
    source=parse((ROOT/CORE).read_text(encoding='utf-8'))
    actual={d['name']:d for d in fixture()['declarations']}
    assert all(actual[d['name']]==d for d in source['declarations'])
    for name in ('iayschema','iaxschema','iawiatschema','iawiasschema','iatappraisal','iaxbeneficiaries','iaymeaning'):
        assert actual[name]['kind']=='definition'


def test_fixture_policy_uses_concrete_treatment_without_boolean_shortcut():
    policy=next(d for d in fixture()['declarations'] if d['name']=='jpnew')
    assert 'iavtreatment' in _references(policy['body'])
    assert 'jppolicy' not in _references(policy['body'])


def test_comparison_worlds_preserve_original_human_population():
    p,domain,scenes=model()
    assert p['aa']('person') and p['aa']('other')
    assert all(x in scenes for x in ('left','right','political','normbase','normchanged','normkept'))
    assert p['iaxcases']('person','topicone','political','left')
    assert not p['iaxcases']('person','topicone','end','left')


def test_actual_schema_and_all_independent_failure_layers():
    result=checks()
    assert result['baseline']==dict(schema=True,premise_witness=True,appraisal=True,
        actual_benefit=False,beneficiaries=True,policy_inclusion=True,political_cause=True)
    assert set(result['contrasts'])==set(CONTRASTS)
    assert all(row==[False] for row in result['contrasts'].values())


def test_evidence_pins_inherited_document_inputs_as_well_as_python():
    assert {CORE,benefit.SOURCE,benefit.CORE,political.SOURCE,political.CORE,
        collective.SOURCE,collective.CORE}<=input_paths()
