"""Check the current nature adapter and individual scope after source recovery."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
from noema.constructed import parse,format_graph
from noema.constructed_semantics import SequenceValue,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_kant_emancipation_content_visible as content
from scripts import check_nature_sentence as nature
from scripts.check_motive_causes import unknown

check=content.check


def fixture(roots,suffix):
    doc=check.backprojection(check.restored()['document'])
    ds={d['name']:d for d in doc['declarations']};seen=set();pending=set(roots)
    while pending:
        name=pending.pop()
        if name not in seen:seen.add(name);pending.update(_references(ds[name].get('body')))
    doc=deepcopy(doc);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen];doc['statements']=[]
    return parse(format_graph(doc,'compact')+suffix)


def evaluate(doc,values,people,scenes):
    return [r['value'] for r in evaluate_document(doc,individuals=people,situations=scenes,
        primitives={d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'},
        max_steps=100000000,memoize_definitions=True,memoize_expressions=True)]


@lru_cache(None)
def nature_adapter_checks():
    doc=fixture(['r2eb'],'r zperson[] a.r zpoint[] d.q[t[k r2eb[k zperson[]]][k zpoint[]]].')
    levels=nature.prior.VALUES
    def model(variant='baseline'):
        values=nature.source_values(doc,variant);original=dict(values)
        values.update(zperson=lambda:'person',zpoint=lambda:'now',hzzo=lambda:'reference',
            hzzj=lambda kind,point:SequenceValue(tuple((*levels,levels[0]) if variant=='duplicate_scale' else levels)
                if (kind,point)==('reference','now') else (), '"individual"'),
            hzzk=lambda kind,degree,point:(kind,point)==('reference','now') and original['znear'](degree),
            hzzl=lambda kind,*args:kind=='reference' and original['zmeasured'](*args))
        if variant=='other_dimension':values['hzzo']=lambda:'process'
        if variant=='missing_measure':values['hzzl']=lambda *args:False
        if variant=='near_is_top':values['hzzk']=lambda kind,degree,point:degree==levels[-1]
        return values
    positive=('baseline','no_guided_activity','no_prior_experience','no_formation_cause',
        'prior_deliberated_contribution','currently_selected','currently_opposed')
    negative=('duplicate_scale','other_dimension','missing_measure','near_is_top','no_process',
        'missing_prior','ambiguous_prior','no_increase','no_internal_cause',
        'other_pattern_owner','other_causal_pattern','selected_successes','all_selected','empty_selection_comparison')
    rows={}
    for variant in (*positive,*negative):
        actual=evaluate(doc,model(variant),nature.prior.SOURCE_PEOPLE,nature.prior.SOURCE_SCENES)
        assert actual==[variant in positive],(variant,actual)
        rows[variant]=actual
    for name in ('hzzj','hzzk','hzzl','ag','hzie','hzzf','hzzg'):
        values=model();values[name]=unknown
        try:evaluate(doc,values,nature.prior.SOURCE_PEOPLE,nature.prior.SOURCE_SCENES)
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(contrasts=rows,unknown_inputs_refused=7,exact_current_adapter='r2eb',
        current_nature_body='r2ea',native_bodies_unchanged=True,origin_not_presupposed=True)


@lru_cache(None)
def individual_scope_checks():
    doc=fixture(['r2ec'],'r zpoint[] d.q[t[k r2ec[]][k zpoint[]]].')
    probes=parse('p:r zhabit[a d] c.r zdifficult[a d] c.d zfirst[person a] e[b point[k zhabit[v person v point]]].d zsecond[person a] e[b point[k zdifficult[v person v point]]].')
    replacements={'r2eb':probes['declarations'][2]['body'],'r2dx':probes['declarations'][3]['body']}
    for d in doc['declarations']:
        if d['name'] in replacements:d['body']=deepcopy(replacements[d['name']])
    doc['declarations']=probes['declarations'][:2]+doc['declarations'];doc=parse(format_graph(doc,'compact'))
    people=('first','second','outsider','node')
    def model(scope,habit,difficult,human=people[:3],variant='baseline'):
        values={d['name']:unknown for d in doc['declarations'] if d['kind']=='primitive'}
        values.update(zpoint=lambda:'now',hzzq=lambda:'node',aa=lambda person:person in human,
            hzzn=lambda node,person,point:(node,point)==('other' if variant=='other_node' else 'node',
                'elsewhere' if variant=='other_context' else 'now') and person in scope,
            zhabit=lambda person,point:person in habit and point=='now',
            zdifficult=lambda person,point:person in difficult and point=='now')
        return values
    rows=[]
    for bits in product((False,True),repeat=4):
        habit={p for p,b in zip(people[:2],bits[:2]) if b};difficult={p for p,b in zip(people[:2],bits[2:]) if b}
        actual=evaluate(doc,model(people[:2],habit,difficult),people,('now','elsewhere'))
        assert actual==[all(bits)],(bits,actual);rows.append(dict(bits=list(bits),values=actual))
    contrasts={}
    for name,scope,habit,difficult,human,expected in [
        ('empty_scope',(),(),(),people,False),
        ('nonhuman_scope_member',('first','node'),people,people,people[:3],False),
        ('unqualified_outsider_not_quantified',('first',),('first',),('first',),people[:3],True),
        ('split_people',people[:2],('first',),('second',),people[:3],False),
        ('one_failing_member',people[:2],people[:2],('first',),people[:3],False),
        ('other_node',people[:2],people[:2],people[:2],people[:3],False),
        ('other_context',people[:2],people[:2],people[:2],people[:3],False)]:
        actual=evaluate(doc,model(scope,habit,difficult,human,name),people,('now','elsewhere'))
        assert actual==[expected],(name,actual);contrasts[name]=actual
    for name in ('hzzn','aa','zhabit','zdifficult'):
        values=model(people[:2],people[:2],people[:2]);values[name]=unknown
        try:evaluate(doc,values,people,('now','elsewhere'))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(name)
    return dict(combinations=rows,contrasts=contrasts,unknown_inputs_refused=4,
        exact_current_scope='r2ec',isolated_component_probes=['r2eb','r2dx'],
        binding_diagnostic_only=True,not_a_native_full_sentence_world_test=True)


def source_pins():
    paths=set(content.source_pins())|{'scripts/check_kant_emancipation_integration_visible.py',
        'tests/test_kant_emancipation_integration_visible.py'}
    return {p:check.digest(p) for p in sorted(paths)}


def build_report():
    return dict(schema='noema-kant-emancipation-integration-check-1',nature_adapter=nature_adapter_checks(),
        individual_scope=individual_scope_checks(),source_sha256=source_pins(),formal_integration_credit=0,
        semantic_equivalence_automatically_proved=False)
