"""Retained analytical controls plus recovered source bodies; not SVG evidence."""
import pytest
import test_tenth_energy_physics_visible as adapter

GROUPS = {
    'electron_energy_balance': ('numeric_checks','polynomial_checks','binding_checks','oriented_work_checks','work_integral_refusal'),
    'kinetic_energy_chain': ('numeric_checks','integrand_checks','polynomial_checks','printed_structure'),
    'energy_boundary': ('numeric_checks','polynomial_checks','refusal_checks','physical_checks'),
    'material_energy_extension': ('numerical_checks','polynomial_checks','scope_checks'),
}

@pytest.mark.parametrize('group,name', [(g,n) for g,names in GROUPS.items() for n in names])
def test_retained_physical_diagnostics_with_recovered_bodies(group, name):
    module = adapter.adapted_module('scripts.check_'+group)
    # Both direct CORE inspection and specialization need an explicit original
    # typed-body check. This also makes each parametrized test independent.
    if name == 'printed_structure':
        adapter.checked_extract(module.parse(module.text(module.CORE)), roots=['serg','serh'])
    if group == 'energy_boundary' and name == 'physical_checks':
        adapter.checked_extract(module.parse(module.text(module.CORE)), roots=['setb'])
    result = vars(module)[name]()
    # Original functions assert every expected value, invalid polynomial claim,
    # unknown-input refusal and limit. Several return named rows, not a count.
    assert isinstance(result, dict) and result, (group,name,result)
    if name == 'printed_structure':
        assert result['printed_mass_factor'] is False
        assert result['source_silently_corrected'] is False
        assert 'serg' in adapter.RECOVERED_DEFINITIONS_SEEN
        assert 'serh' in adapter.DIAGNOSTIC_ONLY_SEEN
