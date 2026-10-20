"""Check source bindings, existential target scope and nonfactive permission."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content, FunctionValue, SequenceValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_private_policy_permission import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, PRIMITIVES, MEANINGS, LIMITS, parent, policy, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v159.json'
REPORT = 'reports/private-policy-permission-v1.json'
AUDIT = 'data/private-policy-permission-reading-v1.json'
DOC = 'docs/private-policy-permission-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = ('reports/qualified-private-influence-v1.json', 'reports/private-choice-frequency-v1.json',
         'reports/public-enlightenment-route-v1.json')
SCENES = ('reference', 'presentation', 'on', 'off', 'point')
PEOPLE = ('public', 'otherpublic', 'person', 'otherperson', 'role', 'otherrole',
          'source', 'othersource', 'office', 'author', 'activity', 'frame', 'caseone', 'casetwo')
EXTRA = 'r zpublic[] a.r zperson[] a.r zrole[] a.r zcase[] a.r zevaluation[] d.'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind, bindings=('public', 'person', 'role')):
    doc = deepcopy(catalog().document)
    roots = {'bindings': ['r2yz'], 'scope': ['r2z2'], 'adapter': ['r2z3'],
             'norm': ['r2z5'], 'attribution': ['r2z6']}[kind]
    boundaries = {'bindings': ('r2yy',), 'scope': ('r2yz',), 'adapter': ('r2yz',),
                  'norm': (), 'attribution': ()}[kind]
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    if kind == 'bindings':
        # The model supplies an actual Noema quotation, not fabricated syntax.
        empty = deepcopy(doc)
        empty.update(declarations=doc['declarations'][:1], statements=[])
        new = parse(format_graph(empty, 'compact') +
                    'r ztruth[a a d] c.d zperform[person a act a] e[b point[k ztruth[v person v act v point]]].'
                    'r zselect[d a a i b[h[a a] e]] i b[h[a a] e].'
                    'd h235a[context d case a record a] i b[h[a a] e]'
                    '[k zselect[v context v case v record r b[p zperform]]].')['declarations'][1:]
        at = next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'h235a')
        doc['declarations'][at:at + 1] = new
    doc.update(declarations=closure(doc, roots), statements=[])
    if kind == 'bindings':
        query = 'q[t[k r2yz[k zpublic[] k zperson[] k zrole[] k zcase[]]][k zevaluation[]]].'
    elif kind == 'scope':
        query = 'q[t[k r2z2[k zpublic[] k zperson[] k zrole[]]][k zevaluation[]]].'
    elif kind == 'adapter':
        query = 'q[t[k r2z3[l[a][' + ' '.join('k z' + n + '[]' for n in bindings) + ']]][k zevaluation[]]].'
    elif kind == 'norm':
        query = 'q[t[k r2z5[]][k zevaluation[]]].'
    else:
        query = 'q[k r2z6[]].'
    return parse(format_graph(doc, 'compact') + EXTRA + query)


def base(doc):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(zpublic=lambda: 'public', zperson=lambda: 'person', zrole=lambda: 'role',
                  zcase=lambda: 'caseone', zevaluation=lambda: 'on',
                  h232v=lambda: 'reference', h232o=lambda: 'presentation', wa=lambda: 'author')
    return values


@lru_cache(None)
def binding_checks():
    doc = fixture('bindings')
    names = ('source person role reference records sources people roles activities codes polarities '
             'required choices scope choiceweight frame degrees degreecriterion points timeweight frequencies '
             'frequencycriterion variables equations factor worlds matches public tolerance').split()
    rows = []
    for case in ('caseone', 'casetwo'):
        v, seen = base(doc), []
        sign = case == 'caseone'
        def key(ctx, which, value):
            assert (ctx, which) == ('presentation', case)
            seen.append((ctx, which))
            return value
        def criteria(public, reference, threshold):
            assert (public, reference) == ('public', 'reference')
            return FunctionValue(('number',), 'truth', lambda ratio: ratio >= threshold)
        def inspect(*args):
            a = dict(zip(names, args, strict=True))
            assert (a['source'], a['person'], a['role'], a['reference'], a['frame'],
                    a['public'], a['tolerance']) == (
                        'source', 'person', 'role', 'reference', 'frame', 'public', Fraction(1, 4))
            assert a['records']('activity') and not a['records']('person')
            assert (a['sources']('activity'), a['people']('activity'), a['roles']('activity'),
                    a['activities']('activity'), a['polarities']('activity')) == (
                        'source', 'person', 'role', 'activity', sign)
            code = a['codes']('activity')
            assert (symbol(code), code.rank) == ('zperform', 1)
            assert a['required']('source', 'person', 'role', 'activity', code, sign, 'point')
            assert a['choices'].items == ('on', 'off')
            assert a['scope']('on') and not a['scope']('point')
            assert a['choiceweight']('on') == 2
            assert a['variables'].items == ('source', 'person')
            on = FunctionValue(('individual',), 'truth', lambda var: var == 'source')
            off = FunctionValue(('individual',), 'truth', lambda var: False)
            assert a['equations']('person', on) and not a['equations']('person', off)
            assert a['factor'] == 'source'
            assert (a['worlds'](on), a['worlds'](off)) == ('on', 'off')
            assert a['matches'](on, off) and not a['matches'](off, on)
            for branch in ('on', 'off'):
                assert a['degrees'](branch, 'point') == (Fraction(3, 4) if branch == 'on' else 0)
                assert a['points'](branch).items == (branch, 'point')
                assert a['timeweight'](branch, 'point') == (2 if branch == 'on' else 1)
                assert a['frequencies'](branch) == (Fraction(1, 2) if branch == 'on' else 0)
            assert a['degreecriterion'](Fraction(3, 4)) and not a['degreecriterion'](Fraction(1, 2))
            assert a['frequencycriterion'](Fraction(1, 2)) and not a['frequencycriterion'](Fraction(1, 4))
            return Content(SCENES, tuple(s == 'on' for s in SCENES))
        v.update(zcase=lambda: case, r2yy=inspect,
            h222f=lambda public, ref: 'source' if (public, ref) == ('public', 'reference') else 'othersource',
            h222g=lambda public, ref: 'frame' if (public, ref) == ('public', 'reference') else 'role',
            h234v=lambda ctx, c, row: key(ctx, c, row == 'activity'),
            h234w=lambda ctx, c, row: key(ctx, c, 'source'),
            h234x=lambda ctx, c, row: key(ctx, c, 'person'),
            h234y=lambda ctx, c, row: key(ctx, c, 'role'),
            h234z=lambda ctx, c, row: key(ctx, c, 'activity'),
            zselect=lambda ctx, c, row, code: key(ctx, c, code),
            h235b=lambda ctx, c, row: key(ctx, c, sign),
            h234s=lambda source, person, role, act, code, polarity, point:
                (source, person, role, act, symbol(code), polarity, point) ==
                ('source', 'person', 'role', 'activity', 'zperform', sign, 'point'),
            h235w=lambda ctx, c: key(ctx, c, SequenceValue(('on', 'off'), '"situation"')),
            h235x=lambda ctx, c, choice: key(ctx, c, choice in ('on', 'off')),
            h235y=lambda ctx, c, choice: key(ctx, c, Fraction(2)),
            h235z=lambda ctx, c, branch, point: key(ctx, c, Fraction(3, 4) if branch == 'on' else Fraction(0)),
            h236a=lambda public, ref: criteria(public, ref, Fraction(3, 4)),
            h236b=lambda public, ref: criteria(public, ref, Fraction(1, 2)),
            h236c=lambda ctx, c, branch: key(ctx, c, SequenceValue((branch, 'point'), '"situation"')),
            h236d=lambda ctx, c, branch, point: key(ctx, c, Fraction(2 if branch == 'on' else 1)),
            h236e=lambda ctx, c, branch: key(ctx, c, Fraction(1, 2) if branch == 'on' else Fraction(0)),
            h236f=lambda ctx, c: key(ctx, c, 'source'),
            h236g=lambda public, ref: Fraction(1, 4) if (public, ref) == ('public', 'reference') else Fraction(1),
            h235d=lambda ctx, c: key(ctx, c, SequenceValue(('source', 'person'), '"individual"')),
            h235e=lambda ctx, c, var, state: key(ctx, c, var == 'person' and state('source')),
            h235g=lambda ctx, c, state: key(ctx, c, 'on' if state('source') else 'off'),
            h235h=lambda ctx, c, on, off: key(ctx, c, on('source') and not off('source')))
        assert evaluate(doc, v, PEOPLE, SCENES, True) == [True]
        assert seen and set(seen) == {('presentation', case)}
        rows.append(dict(case=case, all_arguments_inspected=True, code_rank=1))
    return dict(cases=rows, semantic_boundaries=['r2yy inspects every input; its native policy, release and bound are pinned by qualified-private-influence-v1'])


@lru_cache(None)
def scope_checks():
    doc = fixture('scope')
    rows = []
    def model(document, included, holds):
        v = base(document)
        v.update(h235v=lambda public, person, role, ref, case:
                 (public, person, role, ref) == ('public', 'person', 'role', 'reference') and case in included,
                 r2yz=lambda public, person, role, case: Content(SCENES, tuple(
                     (public, person, role) == ('public', 'person', 'role') and case in holds and s == 'on' for s in SCENES)))
        return v
    for bits in product((False, True), repeat=4):
        included = {c for c, yes in zip(('caseone', 'casetwo'), bits[:2]) if yes}
        holds = {c for c, yes in zip(('caseone', 'casetwo'), bits[2:]) if yes}
        actual = evaluate(doc, model(doc, included, holds), PEOPLE, SCENES, True)[0]
        assert actual == bool(included & holds)
        rows.append(dict(bits=list(bits), result=actual))
    bindings_rows = {}
    # Smaller individual domain suffices for native three-position extraction.
    domain = ('public', 'person', 'role', 'caseone', 'casetwo')
    for bindings in (('public', 'person', 'role'), ('person', 'public', 'role'),
                     ('public', 'role', 'person'), (), ('public', 'person'),
                     ('public', 'person', 'role', 'public')):
        d = fixture('adapter', bindings)
        actual = evaluate(d, model(d, {'casetwo'}, {'casetwo'}), domain, SCENES, True)[0]
        assert actual == (bindings == ('public', 'person', 'role'))
        bindings_rows[','.join(bindings)] = actual
    for name in ('h235v', 'r2yz'):
        v = model(doc, {'caseone'}, {'caseone'}); v[name] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(candidate_combinations=rows, adapter_bindings=bindings_rows, unknown_inputs_refused=2,
                semantic_boundaries=['r2yz truth by candidate; native existential and adapter execute'])


def norm_model(doc, variant='baseline'):
    v = base(doc)
    pairs = (('person', 'role'), ('person', 'otherrole'), ('otherperson', 'role'))
    def source(public, ref):
        return 'source' if public == 'public' else 'othersource'
    def permission(author, recipient, office, code, bindings, sign, context):
        public, person, role = bindings.items
        return (variant != 'missing_permission'
                and not (variant == 'second_public_missing' and public == 'otherpublic')
                and not (variant == 'second_person_missing' and person == 'otherperson')
                and not (variant == 'second_role_missing' and role == 'otherrole')
                and (author, recipient, office, symbol(code), code.rank, sign, context) == (
                    'source' if variant == 'wrong_author' else 'author',
                    'author' if variant == 'wrong_addressee' else source(public, 'reference'),
                    'role' if variant == 'wrong_office' else 'office',
                    'r2yf' if variant == 'wrong_target' else 'r2z3', 2,
                    variant != 'wrong_polarity', 'reference' if variant == 'wrong_context' else 'on')
                and (person, role) in pairs)
    v.update(h222e=lambda public, ref: variant != 'empty_publics' and ref == 'reference' and public in ('public', 'otherpublic'),
             h236h=lambda public, ref, person, role: ref == 'reference' and
                 public in ('public', 'otherpublic') and (person, role) in pairs and
                 not (variant == 'empty_private_scope' and public == 'otherpublic'),
             aa=lambda person: variant != 'nonhuman' and person in ('person', 'otherperson'),
             ca=lambda person, act, ref: act == 'activity' and person in ('person', 'otherperson') and ref == 'reference',
             cb=lambda person, act, role, ref: act == 'activity' and (person, role) in pairs and ref == 'reference',
             cf=lambda person, role, ref: variant != 'not_entrusted' and (person, role) in pairs and ref == 'reference',
             h222f=source, h235r=lambda source, ref: 'office' if ref == 'reference' else 'role', h235u=permission)
    return v


@lru_cache(None)
def norm_checks():
    doc, rows = fixture('norm'), {}
    for variant in ('baseline', 'missing_permission', 'second_public_missing', 'second_person_missing',
                    'second_role_missing', 'wrong_author', 'wrong_addressee', 'wrong_office',
                    'wrong_target', 'wrong_polarity', 'wrong_context', 'empty_publics',
                    'empty_private_scope', 'nonhuman', 'not_entrusted'):
        actual = evaluate(doc, norm_model(doc, variant), PEOPLE, SCENES, True)[0]
        assert actual == (variant == 'baseline'), (variant, actual)
        rows[variant] = actual
    for name in ('h235u', 'h236h', 'cf'):
        v = norm_model(doc); v[name] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    text = format_graph(doc, 'compact')
    try:
        parse(text.replace('r c[p r2z3]', 'r b[p r2z3]'))
    except ValueError:
        pass
    else:
        raise AssertionError('rank-one policy quote accepted')
    return dict(contrasts=rows, unknown_inputs_refused=3, rank_lowering_refused=True,
                all_policy_inputs_unknown_and_unexecuted=True, semantic_boundaries=[])


@lru_cache(None)
def attribution_checks():
    doc, rows = fixture('attribution'), {}
    for variant in ('baseline', 'wrong_node', 'wrong_author', 'wrong_content', 'wrong_context', 'wrong_order'):
        v = base(doc)
        v.update(h236j=lambda: 'caseone', h235t=lambda: 'casetwo',
            h236i=lambda node, author, code, context:
                (node, author, symbol(code), code.rank, context) == (
                    'casetwo' if variant == 'wrong_node' else 'caseone',
                    'source' if variant == 'wrong_author' else 'author',
                    'r2ym' if variant == 'wrong_content' else 'r2z5', 3,
                    'reference' if variant == 'wrong_context' else 'presentation'),
            ue=lambda first, last, context: variant != 'wrong_order' and
                (first, last, context) == ('casetwo', 'caseone', 'presentation'))
        actual = evaluate(doc, v, PEOPLE, SCENES, True)[0]
        assert actual == (variant == 'baseline')
        rows[variant] = actual
    try:
        parse(format_graph(doc, 'compact').replace('r d[k r2z5[]]', 'r c[k r2z5[]]'))
    except ValueError:
        pass
    else:
        raise AssertionError('rank-two attribution quote accepted')
    return dict(contrasts=rows, permission_and_policy_inputs_unknown_and_unexecuted=True,
                rank_lowering_refused=True, semantic_boundaries=[])


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    text = unit['text'][833:980]
    assert text == '; der Privatgebrauch derselben aber darf öfters sehr enge eingeschränkt sein, ohne doch darum den Fortschritt der Aufklärung sonderlich zu hindern.'
    return dict(status='private_policy_permission_clause_partial_answer', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[833, 980], text=text),
                definitions=list(MEANINGS), selection=selection_binding(catalog(), [74]), interpretation=LIMITS,
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                newly_reviewed_sentence_characters=0, preserved_reviewed_sentence_characters=588,
                unresolved=['Ich antworteの自己提示', 'aber/ohne doch darumの対照と期待の取り消し',
                            '回答文全体の原刊照合と通読'],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, prior, new = parent(), policy(), catalog()
    assert new.document['statements'][:74] == old.document['statements']
    assert len(new.document['statements']) == 75
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    for n, entry in prior.entries.items():
        assert new.entries[n]['declaration'] == entry['declaration']
        assert new.entries[n]['meaning_ja'] == entry['meaning_ja']
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in (('data/question-discourse-reading-v1.json', [70, 71]),
                          ('data/public-freedom-duty-reading-v1.json', [72]),
                          ('data/public-enlightenment-route-reading-v1.json', [73])):
        record = read(path)
        assert record['selection'] == selection_binding(new, indices)
        validate_hashes(ROOT, record['source_sha256'])
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    validate_hashes(ROOT, read(BASIS)['import_source_sha256'])
    assert read(AUDIT) == reading()
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_statements=74, added_statements=1, imported_definitions=11,
                added_definitions=len(MEANINGS), added_primitives=len(PRIMITIVES),
                preserved_whole_unit_reviews=len(reviews), new_reviewed_sentence_characters=0,
                old_meanings_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('bindings', binding_checks), ('scope', scope_checks), ('norm', norm_checks),
                     ('attribution', attribution_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | set(read(BASIS)['import_source_sha256']) | {
        INDEX, AUDIT, DOC, INVENTORY, *PRIOR, 'scripts/compose_private_policy_permission.py',
        'scripts/check_private_policy_permission.py', 'scripts/compose_restriction_questions.py',
        'scripts/compose_grounded_step.py', 'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py',
        'tests/test_private_policy_permission.py', 'data/question-discourse-reading-v1.json',
        'data/public-freedom-duty-reading-v1.json', 'data/public-enlightenment-route-reading-v1.json'}
    return dict(status='private_policy_permission_clause_partial_answer', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], statements=[74], definitions=list(MEANINGS),
                               status='partial_private_policy_permission'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
