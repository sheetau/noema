"""Check each duty target and diagnose scopes without claiming finite coverage."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_civic_noncontravention import ROOT, LIBRARY, BASIS, PRIMITIVES, MEANINGS, parent, build, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

REPORT = 'reports/civic-noncontravention-v1.json'
DOC = 'docs/civic-noncontravention-v1.md'
PRIOR = ('reports/civic-example-v1.json', 'reports/levy-opinions-v1.json')
DOMAIN = ('source', 'person', 'role', 'activity', 'community', 'other')
SCENES = ('reference', 'outcome', 'other')
EXTRA = ''.join('r z' + n + '[] a.' for n in DOMAIN) + '''
r zref[] d.r zpoint[] d.r ztargetref[] d.
r zcontent[j[a]] e.r zothercontent[j[a]] e.
r zbody[j[a] d] e.r zotherbody[j[a] d] e.
r zaction[a a] e.r zotheraction[a a] e.
d zranked[bindings j[a] reference d] e[c[s[r[p zbody]]][v bindings v reference]].
d zotherranked[bindings j[a] reference d] e[c[s[r[p zotherbody]]][v bindings v reference]].
'''
BINDINGS = 'l[a][k zperson[] k zactivity[]]'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def expression(text):
    return parse('p:' + EXTRA + 'q[e[' + text + '][' + text + ']].')['statements'][0]['body']['arguments'][0]


def restrict_domains(doc, sequences=True):
    """Instantiate the real quantified bodies on explicit test values only."""
    def visit(node):
        if isinstance(node, list):
            return [visit(x) for x in node]
        if not isinstance(node, dict):
            return node
        selected_kinds = ('description', 'sequence') if sequences else ('description',)
        if node.get('kind') == 'forall' and isinstance(node['sort'], dict) and node['sort']['kind'] in selected_kinds:
            sort = node['sort']
            if sort['kind'] == 'sequence':
                terms = (BINDINGS, 'l[a][k zperson[] k zother[]]')
            elif sort.get('rank', 0) == 1:
                terms = ('r b[p zranked]', 'r b[p zotherranked]')
            else:
                # The direct-action description has two individual arguments.
                rendered = json.dumps(sort, sort_keys=True)
                direct = rendered.count('individual') == 2
                terms = ('r[p zaction]', 'r[p zotheraction]') if direct else ('r[p zcontent]', 'r[p zothercontent]')
            body = visit(node['body'])
            return dict(kind='and', arguments=[dict(kind='apply', function=dict(kind='lambda',
                parameters=[dict(name=node['variable'], sort=deepcopy(sort))], body=deepcopy(body)),
                arguments=[expression(term)]) for term in terms])
        return {k: visit(v) for k, v in node.items()}
    return parse(format_graph(visit(doc), 'compact'))


@lru_cache(None)
def fixture(target, finite=False):
    doc = deepcopy(catalog().document)
    doc.update(declarations=closure(doc, [target]), statements=[])
    args = {
        'r35a': 'k zsource[] k zperson[] k zrole[] r[p zcontent] ' + BINDINGS + ' k zpoint[]',
        'r35b': 'k zsource[] k zperson[] k zrole[] r b[p zranked] ' + BINDINGS + ' k ztargetref[] k zpoint[]',
        'r35c': 'k zsource[] k zperson[] k zrole[] k zactivity[] k zref[]',
        'r35d': 'k zsource[] k zperson[] k zrole[] k zactivity[] k zref[]',
        'r35e': 'k zsource[] k zperson[] k zrole[] k zactivity[] k zpoint[]',
        'r35f': 'k zperson[] k zrole[] k zactivity[] k zcommunity[] k zref[]',
    }[target]
    call = 'k ' + target + '[' + args + ']'
    if target in ('r35c', 'r35d', 'r35f'):
        call = 't[' + call + '][k zpoint[]]'
    # Test descriptions must precede the definitions whose quantified bodies
    # are later instantiated with them; stored production definitions stay intact.
    prefix = parse('p:' + EXTRA)
    doc['declarations'] = prefix['declarations'] + doc['declarations']
    doc = parse(format_graph(doc, 'compact') + 'q[' + call + '].')
    return restrict_domains(doc, sequences=finite is True) if finite else doc


def base(doc):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    for n in DOMAIN:
        values['z' + n] = lambda n=n: n
    values.update(zref=lambda: 'reference', zpoint=lambda: 'outcome', ztargetref=lambda: 'other')
    return values


@lru_cache(None)
def target_checks():
    rows = {}
    for target in ('r35a', 'r35b'):
        doc = fixture(target); cases = []
        for positive, negative, truth in product((False, True), repeat=3):
            v = base(doc); calls = []
            def bound_content(bindings, reference=None):
                assert tuple(bindings.items) == ('person', 'activity')
                assert reference == ('other' if target == 'r35b' else None)
                calls.append(('content', reference))
                return Content(SCENES, (not truth, truth, not truth))
            def required(source, person, role, code, bindings, *tail):
                expected = ('source', 'person', 'role', 'zranked' if target == 'r35b' else 'zcontent',
                            1 if target == 'r35b' else 0, ('person', 'activity'))
                assert (source, person, role, symbol(code), code.rank, tuple(bindings.items)) == expected
                if target == 'r35b':
                    reference, sign, point = tail; assert reference == 'other'
                else:
                    sign, point = tail
                assert point == 'outcome'; calls.append(('requirement', sign))
                return positive if sign else negative
            v.update(zcontent=bound_content, zbody=bound_content, h7k=required, h237z=required)
            result = evaluate(doc, v, DOMAIN, SCENES, True)
            assert result == [(not positive or truth) and (not negative or not truth)]
            assert ('requirement', True) in calls and ('requirement', False) in calls
            cases.append(dict(positive=positive, negative=negative, truth=truth, conforms=result[0]))
        rows[target] = cases
    return dict(cases=rows, native_unquotation_both_ranks=True, exact_ordered_bindings_and_target_reference=True,
        positive_negative_conflict_rejected=True, permission_not_consulted=True)


def model(doc, variant='baseline', failing='none'):
    v = base(doc)
    def content(kind, bindings, reference=None):
        selected = tuple(bindings.items) == ('person', 'activity')
        if kind == 'ranked':
            selected = selected and reference == 'other'
        return Content(SCENES, tuple(not (kind == failing and selected and point == 'outcome') for point in SCENES))
    v.update(zcontent=lambda bindings: content('bound', bindings),
        zothercontent=lambda bindings: Content(SCENES, (True,) * len(SCENES)),
        zbody=lambda bindings, reference: content('ranked', bindings, reference),
        zotherbody=lambda bindings, reference: Content(SCENES, (True,) * len(SCENES)),
        zaction=lambda person, act: Content(SCENES, tuple(not (failing == 'direct' and
            (person, act, point) == ('person', 'activity', 'outcome')) for point in SCENES)),
        zotheraction=lambda person, act: Content(SCENES, (True,) * len(SCENES)),
        aa=lambda person: person == 'person',
        h237c=lambda person, community, ref: (person, community, ref) == ('person', 'community', 'reference'),
        hzwn=lambda person, role, ref: (person, role, ref) == ('person', 'role', 'reference'),
        h244g=lambda role, community, ref: variant != 'not_civic_role' and
            (role, community, ref) == ('role', 'community', 'reference'))
    def source(community, reference):
        assert (community, reference) == ('community', 'reference')
        return 'other' if variant == 'different_norm_source' else 'source'
    def scope(person, role, act, code, bindings, *refs):
        fixed = refs[-1]
        expected_act = 'other' if variant == 'different_scope_activity' else 'activity'
        expected_person = 'other' if variant == 'different_scope_person' else 'person'
        expected_role = 'other' if variant == 'different_scope_role' else 'role'
        expected_ref = 'other' if variant == 'different_scope_reference' else 'reference'
        if (person, role, act, fixed) != (expected_person, expected_role, expected_act, expected_ref):
            return False
        # Include all listed targets for this explicit finite diagnostic table.
        # The real h245s/t contract requires the complete relevant scope.
        return variant != 'no_bound_scope'
    def req(source, person, role, code, bindings, *tail):
        ranked = len(tail) == 3
        reference, sign, point = tail if ranked else (None, *tail)
        target = 'zranked' if ranked else 'zcontent'
        wanted_act = 'other' if variant == 'second_binding_violation' else 'activity'
        if variant == 'second_description_violation':
            target = 'zotherranked' if ranked else 'zothercontent'
        return sign and (source, person, role, symbol(code), code.rank, tuple(bindings.items), reference, point) == (
            'source', 'person', 'role', target, int(ranked), ('person', wanted_act), 'other' if ranked else None, 'outcome')
    def direct(source, person, role, act, code, sign, point):
        return sign and (source, person, role, act, symbol(code), code.rank, point) == (
            'other' if variant == 'foreign_direct_source' else 'source', 'person', 'role',
            'other' if variant == 'separate_payment' else 'activity', 'zaction', 0, 'outcome')
    v.update(h245d=source, h245s=scope, h245t=scope, h7k=req, h237z=req, h7a=direct)
    return v


@lru_cache(None)
def finite_scope_checks():
    rows = {}
    for target, bad in (('r35c', 'bound'), ('r35d', 'ranked'), ('r35e', 'direct'), ('r35f', None)):
        doc = fixture(target, True); cases = {}
        for failing in ('none', 'bound', 'ranked', 'direct'):
            actual = evaluate(doc, model(doc, failing=failing), DOMAIN, SCENES, True)
            expected = failing == 'none' if target == 'r35f' else failing != bad
            assert actual == [expected], (target, failing, actual)
            cases[failing] = actual[0]
        rows[target] = cases
    doc = fixture('r35f', True); contrasts = {}
    for variant, failing, expected in (
        ('not_civic_role', 'none', False), ('different_norm_source', 'bound', True),
        ('foreign_direct_source', 'direct', True), ('separate_payment', 'direct', True),
        ('different_scope_activity', 'bound', True), ('different_scope_person', 'bound', True),
        ('different_scope_role', 'bound', True), ('different_scope_reference', 'bound', True),
        ('no_bound_scope', 'ranked', True)):
        actual = evaluate(doc, model(doc, variant, failing), DOMAIN, SCENES, True)
        assert actual == [expected], (variant, actual); contrasts[variant] = actual[0]
    # Verify the second instantiated description and binding are actually
    # visited, so a diagnostic cannot accidentally test only its first item.
    for variant in ('second_description_violation', 'second_binding_violation'):
        for target in ('r35c', 'r35d'):
            doc = fixture(target, True); v = model(doc, variant)
            if variant == 'second_description_violation':
                v['zothercontent'] = lambda bindings: Content(SCENES, (False,) * len(SCENES))
                v['zotherbody'] = lambda bindings, ref: Content(SCENES, (False,) * len(SCENES))
            else:
                v['zcontent'] = lambda bindings: Content(SCENES, (tuple(bindings.items) != ('person', 'other'),) * len(SCENES))
                v['zbody'] = lambda bindings, ref: Content(SCENES, (tuple(bindings.items) != ('person', 'other'),) * len(SCENES))
            actual = evaluate(doc, v, DOMAIN, SCENES, True)
            assert actual == [False], (variant, target, actual)
            contrasts[variant + ':' + target] = False
    return dict(cases=rows, contrasts=contrasts, native_instantiated_quantifier_bodies=True,
        finite_description_and_sequence_diagnostic_only=True, not_a_completeness_proof=True)


@lru_cache(None)
def domain_checks():
    rows = {}
    for target in ('r35c', 'r35d', 'r35e', 'r35f'):
        doc = fixture(target)
        try:
            evaluate(doc, model(doc), DOMAIN, SCENES, True)
        except ValueError as error:
            assert 'Cannot finitely quantify the description domain' in str(error), str(error)
            rows[target] = str(error)
        else:
            raise AssertionError('Full description domain was silently approximated: ' + target)
    for target in ('r35c', 'r35d'):
        doc = fixture(target, 'descriptions_only')
        try:
            evaluate(doc, model(doc), DOMAIN, SCENES, True)
        except ValueError as error:
            assert 'Cannot finitely quantify the unbounded sequence domain' in str(error), str(error)
            rows[target + ':sequences'] = str(error)
        else:
            raise AssertionError('Full binding-list domain was silently approximated: ' + target)
    return dict(full_domain_evaluation_refused=rows, production_quantifiers_unrestricted=True)


@lru_cache(None)
def quotation_checks():
    doc = deepcopy(catalog().document); doc['statements'] = []
    quoted = 'r c[p r35f]'
    doc = parse(format_graph(doc, 'compact') + 'q[e[' + quoted + '][' + quoted + ']].')
    assert evaluate(doc, base(doc), DOMAIN, SCENES, True) == [True]
    try:
        parse(format_graph(catalog().document, 'compact') + 'q[e[r b[p r35f]][r b[p r35f]]].')
    except ValueError as error:
        rejected = str(error)
    else:
        raise AssertionError('Insufficient quotation rank accepted')
    return dict(rank_two_quote_without_evaluating_duties=True, insufficient_rank_rejected=rejected)


@lru_cache(None)
def unknown_checks():
    rows = []
    for target, name in (('r35a', 'h7k'), ('r35a', 'zcontent'), ('r35b', 'h237z'),
                         ('r35b', 'zbody'), ('r35f', 'h245s'), ('r35f', 'h245t'), ('r35f', 'h245d')):
        doc = fixture(target, target == 'r35f'); v = model(doc); v[name] = unknown
        try:
            evaluate(doc, v, DOMAIN, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error), str(error)
        else:
            raise AssertionError(name)
        rows.append(target + ':' + name)
    return dict(unknown_inputs_refused=rows)


@lru_cache(None)
def structure_checks():
    new, old = catalog(), parent()
    assert not new.document['statements']
    for n, entry in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert entry['declaration'] == old.entries[n]['declaration'] and entry['meaning_ja'] == old.entries[n]['meaning_ja']
    for prior in PRIOR:
        validate_hashes(ROOT, read(prior)['source_sha256'])
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for notation in ('compact', 'full'):
        text = format_graph(new.document, notation)
        assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(new_definitions=len(MEANINGS), new_primitives=len(PRIMITIVES), inherited_meanings_preserved=True,
        roundtrips=True, active_manuscript_unchanged=True, new_semantic_reviews=0)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items():
        write_exact(ROOT / path, body)


def build_report():
    results = {}
    for name, fn in [('target', target_checks), ('finite_scope', finite_scope_checks), ('domain', domain_checks),
                     ('quotation', quotation_checks), ('unknown', unknown_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set(parent().source_sha256) | {DOC, *PRIOR,
        'scripts/compose_civic_noncontravention.py', 'scripts/check_civic_noncontravention.py',
        'tests/test_civic_noncontravention.py', 'scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='ranked_action_scoped_civic_noncontravention_candidate', document=LIBRARY, **results,
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
