"""Check unrestricted choice pairs, guided fulfillment and faithful ranked quotation."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_free_choice_obedience import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, PRIMITIVES, IMPORTED, LIMITS,
    parent, build, closure, choice, obedience)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v150.json'
REPORT = 'reports/free-choice-obedience-v1.json'
AUDIT = 'data/free-choice-obedience-reading-v1.json'
DOC = 'docs/free-choice-obedience-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
PRIOR = 'reports/role-commands-v1.json'
SENTENCES = 'data/role-commands-reading-v1.json'
FIRST = 'data/heard-prohibition-reading-v1.json'
EXTRA = 'r zp[] a.r zs[] a.r zr[] d.r zt[] d.'
SCENES = ('reference', 'later')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def finite_descriptions(doc):
    """Diagnostic only: instantiate the full description quantifier at three quotes."""
    root = next(d for d in doc['declarations'] if d['name'] == 'rtx')
    node = root['body']['body']['body']
    assert node['kind'] == 'forall' and node['sort']['kind'] == 'description'
    instances = [dict(kind='apply', function=dict(kind='lambda',
                     parameters=[dict(name=node['variable'], sort=deepcopy(node['sort']))],
                     body=deepcopy(node['body'])),
                     arguments=[dict(kind='quote', body=dict(kind='function_ref', symbol=name))])
                 for name in ('zzq', 'zother', 'zalias')]
    node.clear()
    node.update(kind='and', arguments=[instances[0], dict(kind='and', arguments=instances[1:])])


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    query = ''
    if kind.startswith('obedience'):
        replacement = parse('p:r ztruth[a a d] c.' +
            'r cg[a a d] c.d zzq[person a activity a] e[b point[k cg[v person v activity v point]]].' +
            'd h233z[item a] i[h[a a] e][r[p zzq]].' +
            'd zother[person a activity a] e[b point[k ztruth[v person v activity v point]]].' +
            'd zalias[person a activity a] e[b point[k cg[v person v activity v point]]].')
        new = {d['name']: d for d in replacement['declarations']}
        assert new['zzq'] == catalog().entries['zzq']['declaration']
        doc['declarations'] = list(new.values()) + [d for d in doc['declarations'] if d['name'] not in new]
        if kind == 'obedience_finite':
            finite_descriptions(doc)
        roots = ['r2ud', 'zother', 'zalias']
        query = 'q[t[k r2ud[k zs[] k zp[] k zr[]]][k zt[]]].'
    elif kind == 'permission':
        roots = ['r2ub']
        query = 'q[t[k r2ub[k zs[] k zp[] k zr[]]][k zt[]]].'
    elif kind == 'groups':
        replacement = parse('p:r zpermit[a a d d] c.r zobey[a a d d] c.' +
            'd r2ub[source a person a reference d] e[b point[k zpermit[v source v person v reference v point]]].' +
            'd r2ud[source a person a reference d] e[b point[k zobey[v source v person v reference v point]]].')
        new = {d['name']: d for d in replacement['declarations']}
        doc['declarations'] = [d for d in replacement['declarations'] if d['kind'] == 'primitive'] + [
            new.get(d['name'], d) for d in doc['declarations']]
        roots = ['r2ug', 'r2uh']
        query = ''.join('q[t[o[c[k ' + n + '[k zr[]]][k zs[]]]][k zt[]]].' for n in roots)
        query += ('q[e[c[k r2ug[k zr[]]][k zs[]]][j s[k r2ue[k zs[] k zr[]]]]].'
                  'q[e[c[k r2uh[k zr[]]][k zs[]]][j m[k r2uf[k zs[] k zr[]]]]].')
    else:
        assert kind == 'quotation'
        roots = ['r2ug', 'r2uh']
        query = 'r zsaid[i b[h[a] f]] c.' + ''.join(
            'q[k zsaid[o a[r b[p ' + n + ']][r[k zr[]]]]].' for n in roots)
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + EXTRA + query)


def base(doc):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(zp=lambda: 'person', zs=lambda: 'source', zr=lambda: 'reference', zt=lambda: 'later')
    return values


def permission_model(doc, variant='baseline'):
    activities = ('as', 'al', 'bs', 'bl') + (
        ('asdup',) if variant == 'extra_candidate_not_permitted' else ())
    topics = dict(zip(activities, ('alpha', 'alpha', 'beta', 'beta', 'alpha')))
    extents = dict(zip(activities, ('small', 'large', 'small', 'large', 'small')))
    v = base(doc)
    v.update(
        h233q=lambda p, topic, ref: (p, ref) == ('person', 'reference') and topic in ('alpha', 'beta')
            and variant != 'no_topic_wanted',
        h233r=lambda p, amount, ref: (p, ref) == ('person', 'reference') and amount in ('small', 'large')
            and variant != 'no_extent_wanted',
        ca=lambda p, act, ref: (p, ref) == ('person', 'reference') and act in activities
            and not (variant == 'missing_cross_pair' and act == 'bl'),
        h232p=lambda act, ref: act in activities and ref == 'reference' and variant != 'nonargument_activity',
        h233s=lambda p, act, ref: topics.get(act, 'alpha'),
        h233t=lambda p, act, ref: 'small' if variant == 'all_candidates_short' else extents.get(act, 'small'),
        h227z=lambda act, topic, ref: ref == 'reference' and act in activities and topic == (
            'beta' if variant == 'wrong_topic_binding' and act == 'as' else topics[act]),
        h233u=lambda p, act, ref: 'office',
        h7a=lambda source, person, role, act, code, sign, point: (
            source, person, role, point) == ('source', 'person', 'office', 'later')
            and symbol(code) == 'zzq' and not sign
            and variant == 'one_pair_prohibited' and act == 'bl',
        h7b=lambda source, person, role, act, code, sign, point: (
            source, person, role, point) == (
                'other' if variant == 'wrong_source' else 'source',
                'other' if variant == 'wrong_person' else 'person',
                'other' if variant == 'wrong_role' else 'office',
                'reference' if variant == 'permission_only_at_reference' else 'later')
            and sign and act in activities and symbol(code) == ('r2ua' if variant == 'wrong_code' else 'zzq')
            and not (variant == 'one_pair_not_permitted' and act == 'bl')
            and act != 'asdup')
    return v


@lru_cache(None)
def permission_checks():
    doc = fixture('permission')
    people = ('person', 'source', 'other', 'office', 'alpha', 'beta', 'small', 'large', 'as', 'al', 'bs', 'bl')
    rows = {}
    for variant in ('baseline', 'missing_cross_pair', 'all_candidates_short', 'nonargument_activity',
                    'wrong_topic_binding', 'wrong_source', 'wrong_person', 'wrong_role', 'wrong_code',
                    'permission_only_at_reference', 'one_pair_not_permitted', 'one_pair_prohibited',
                    'no_topic_wanted', 'no_extent_wanted'):
        actual = evaluate(doc, permission_model(doc, variant), people, SCENES, True)
        assert actual == [variant in ('baseline', 'no_topic_wanted', 'no_extent_wanted')], (variant, actual)
        rows[variant] = actual
    extra = evaluate(doc, permission_model(doc, 'extra_candidate_not_permitted'),
                     (*people, 'asdup'), SCENES, True)
    assert extra == [False]
    rows['extra_candidate_not_permitted'] = extra
    v = permission_model(doc)
    for missing in ('h233q', 'h233r', 'h7a', 'h7b'):
        w = dict(v); w[missing] = unknown
        try:
            evaluate(doc, w, people, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(contrasts=rows, independent_topic_extent_pairs=True, all_candidates_not_only_one_per_pair=True,
                same_source_person_role_code_and_point=True, actual_execution_unknown=True,
                unknown_inputs_refused=4, semantic_boundaries=[])


def obedience_model(doc, variant='baseline', bits=(True, False, True, True)):
    performed, forbidden_performed, followed_first, followed_second = bits
    v = base(doc)
    def requirement(source, person, role, activity, code, sign, point):
        rows = [] if variant == 'no_requirements' else [
            ('source', 'person', 'office', 'first', 'zzq', True, 'reference'),
            ('source', 'person', 'office', 'second', 'zzq', False, 'reference')]
        if variant == 'unlisted_description':
            rows.append(('source', 'person', 'office', 'first', 'zother', True, 'reference'))
        if variant == 'conflicting':
            rows.append(('source', 'person', 'office', 'first', 'zzq', False, 'reference'))
        if variant == 'wrong_requirement_source':
            rows = [('other', *row[1:]) for row in rows]
        return (source, person, role, activity, symbol(code), sign, point) in rows
    def guided(source, person, role, activity, code, sign, ref, point):
        expected = ('other' if variant == 'guidance_wrong_source' else 'source',
                    'other' if variant == 'guidance_wrong_person' else 'person',
                    'office', activity, 'zother' if variant == 'guidance_wrong_content' else 'zzq',
                    activity == 'first',
                    'later' if variant == 'guidance_wrong_reference' else 'reference', 'later')
        return (source, person, role, activity, symbol(code), sign, ref, point) == expected and (
            followed_first if activity == 'first' else followed_second if activity == 'second' else False)
    v.update(
        h233v=lambda source, p, ref, role: (source, p, ref, role) == ('source', 'person', 'reference', 'office'),
        h233w=lambda source, p, ref, item: (source, p, ref) == ('source', 'person', 'reference')
            and item in ('first', 'second') and variant not in ('empty_records', 'no_requirements'),
        h233x=lambda item: 'office', h233y=lambda item: item, h234a=lambda item: item == 'first',
        h7a=requirement, h234b=guided,
        cg=lambda p, act, point: (p, point) == ('person', 'later')
            and (performed if act == 'first' else forbidden_performed if act == 'second' else False),
        ztruth=lambda p, act, point: False)
    return v


@lru_cache(None)
def obedience_checks():
    doc = fixture('obedience_finite')
    people = ('source', 'person', 'office', 'first', 'second', 'other')
    matrix = []
    for bits in product((False, True), repeat=4):
        actual = evaluate(doc, obedience_model(doc, bits=bits), people, SCENES, True)
        assert actual == [bits[0] and not bits[1] and bits[2] and bits[3]], (bits, actual)
        matrix.append(dict(execution_and_guidance=bits, result=actual))
    rows = {}
    for variant in ('baseline', 'empty_records', 'unlisted_description', 'conflicting',
                    'wrong_requirement_source', 'guidance_wrong_source', 'guidance_wrong_person',
                    'guidance_wrong_content', 'guidance_wrong_reference', 'no_requirements'):
        actual = evaluate(doc, obedience_model(doc, variant), people, SCENES, True)
        assert actual == [variant in ('baseline', 'no_requirements')], (variant, actual)
        rows[variant] = actual
    full = fixture('obedience_full')
    try:
        evaluate(full, obedience_model(full), people, SCENES, True)
    except ValueError as error:
        assert 'description domain' in str(error), str(error)
    else:
        raise AssertionError('Finite evaluator accepted the full description universe')
    for missing in ('h7a', 'cg', 'h234b'):
        v = obedience_model(doc); v[missing] = unknown
        try:
            evaluate(doc, v, people, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(missing)
    return dict(matrix=matrix, contrasts=rows, mere_coincidence_is_not_guided_obedience=True,
                missing_or_conflicting_requirements_rejected=True,
                restricted_description_diagnostic=['zzq', 'zother', 'zalias'],
                full_description_domain_verified=False, full_description_domain_refused=True,
                unknown_inputs_refused=3,
                semantic_boundaries=['Only in the diagnostic copy: instantiate rtx description quantifier at three native quotes'])


@lru_cache(None)
def group_checks():
    doc = fixture('groups')
    people = ('source', 'person', 'second', 'other')
    matrix = []
    for flags in product((False, True), repeat=4):
        v = base(doc)
        v.update(h233p=lambda source, ref, p: (source, ref) == ('source', 'reference') and p in ('person', 'second'),
                 zpermit=lambda source, p, ref, point: (source, ref, point) == ('source', 'reference', 'later')
                     and (flags[0] if p == 'person' else flags[1] if p == 'second' else False),
                 zobey=lambda source, p, ref, point: (source, ref, point) == ('source', 'reference', 'later')
                     and (flags[2] if p == 'person' else flags[3] if p == 'second' else False))
        actual = evaluate(doc, v, people, SCENES, True)
        assert actual == [flags[0] and flags[1], flags[2] and flags[3], True, True], (flags, actual)
        matrix.append(dict(each_recipients_permission_and_obedience=flags, result=actual))
    return dict(matrix=matrix, each_fixed_recipient_required=True,
                permission_not_conditioned_on_actual_obedience=True, assertion_and_directive_distinct=True,
                semantic_boundaries=['r2ub/r2ud content bodies: separately tested; here native b point wrappers around diagnostic primitives'])


@lru_cache(None)
def quotation_checks():
    doc = fixture('quotation')
    v = base(doc)
    # The reference itself and every policy/fulfillment input remain unknown.
    v['zr'] = unknown
    seen = []
    def said(desc):
        node = json.loads(desc.syntax)
        assert desc.rank == 1 and node['kind'] == 'apply'
        assert node['function']['symbol'] in ('r2ug', 'r2uh')
        assert node['arguments'] == [dict(kind='call', symbol='zr', arguments=[])]
        seen.append(node['function']['symbol'])
        return True
    v['zsaid'] = said
    assert evaluate(doc, v, ('person', 'source'), SCENES, True) == [True, True]
    # The lower rank must not silently drop the disquotation-bearing body.
    low = format_graph(doc, 'compact').replace('r b[p r2uh]', 'r[p r2uh]')
    try:
        parse(low)
    except ValueError:
        lower_rejected = True
    else:
        # Formatting may alpha-normalize the spacing; inspect the exact quote AST.
        lowdoc = deepcopy(doc)
        def lower(node):
            if isinstance(node, dict):
                if node.get('kind') == 'quote' and node.get('body') == dict(kind='function_ref', symbol='r2uh'):
                    node.pop('rank', None)
                for val in node.values():
                    lower(val)
            elif isinstance(node, list):
                for val in node:
                    lower(val)
        lower(lowdoc['statements'])
        try:
            parse(format_graph(lowdoc, 'compact'))
        except ValueError:
            lower_rejected = True
        else:
            raise AssertionError('Rank-zero obedience quotation accepted')
    return dict(native_ranked_messages=seen, reference_norms_execution_and_guidance_unknown=True,
                lower_rank_rejected=lower_rejected, semantic_boundaries=[])


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    return dict(status='free_choice_and_command_guided_obedience_partial', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'],
                            range=[427, 536], text=unit['text'][427:536]),
                definitions=list(MEANINGS), interpretation=LIMITS,
                whole_sentence_semantically_verified=False, newly_reviewed_sentence_characters=0,
                authored_statements_added=0, preserved_reviewed_sentence_characters=366,
                unresolved=['唯一の統治者の役割・世界の範囲・発話への同定',
                            '同じ話者による段階1の発話記述の提示と複数宛先',
                            'aberの対照・括弧による挿入・前の三者との対照',
                            '著者への帰属と括弧文全体の通読'],
                references=['https://korpora.org/Kant/aa08/037.html',
                            'https://www.duden.de/rechtschreibung/gehorchen'],
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in
                               (FULL, BASIS, DOC, INVENTORY, PRIOR, SENTENCES, FIRST)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert old.document['statements'] == new.document['statements']
    assert len(new.document['statements']) == 68
    assert all(new.entries[n] == e for n, e in old.entries.items())
    for library in (choice.LIBRARY, obedience.LIBRARY):
        original = parse((ROOT / library).read_text(encoding='utf-8'))
        for d in original['declarations']:
            if d['name'] in IMPORTED:
                assert new.entries[d['name']]['declaration'] == d, d['name']
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    assert read(SENTENCES)['selection'] == selection_binding(new, [65, 66, 67])
    first = read(FIRST)
    assert first['selection'] == selection_binding(new, [64])
    assert first['first_sentence_recheck']['selection'] == selection_binding(new, [63])
    for p in (PRIOR, SENTENCES, FIRST):
        validate_hashes(ROOT, read(p)['source_sha256'])
    assert read(AUDIT) == reading()
    for p, body in build().items():
        assert (ROOT / p).read_text(encoding='utf-8') == body
    for p in (FULL, CORE):
        doc = parse((ROOT / p).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_whole_unit_reviews=len(reviews), preserved_statements=68,
                imported_definitions=len(IMPORTED), new_definitions=len(MEANINGS) - len(IMPORTED),
                imported_bodies_unchanged=True, preserved_reviewed_sentence_characters=366, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for p, body in build().items():
        write_exact(ROOT / p, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('permission', permission_checks), ('obedience', obedience_checks),
                     ('groups', group_checks), ('quotation', quotation_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, PRIOR, SENTENCES, FIRST, choice.LIBRARY, choice.BASIS,
        obedience.LIBRARY, obedience.BASIS, 'scripts/compose_choice_permissions.py',
        'scripts/compose_scoped_obedience.py', 'scripts/compose_free_choice_obedience.py',
        'scripts/check_free_choice_obedience.py', 'tests/test_free_choice_obedience.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='free_choice_and_command_guided_obedience_partial', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], definitions=list(MEANINGS),
                               status='partial_quoted_choice_policy_and_guided_obedience_contents'),
                whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
