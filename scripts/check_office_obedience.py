"""Check job restriction without weakening quantified obedience or modality."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import FunctionValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_office_obedience import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts import check_free_choice_obedience as guided

INDEX = 'data/semantic-review-index-v164.json'
REPORT = 'reports/office-obedience-v1.json'
AUDIT = 'data/office-obedience-reading-v1.json'
DOC = 'docs/office-obedience-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGE = 'artifacts/answer-discourse-v1/page-485.jpg'
PRIOR = ('reports/public-purpose-mechanism-v1.json', 'reports/free-choice-obedience-v1.json')
DOMAIN = ('source', 'person', 'office', 'work', 'first', 'second', 'other')
SCENES = ('reference', 'later')
EXTRA = guided.EXTRA + 'r zrole[] a.r zwork[] a.'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    if kind.startswith('obedience'):
        replacement = parse('p:r ztruth[a a d] c.r cg[a a d] c.' +
            'd zzq[person a activity a] e[b point[k cg[v person v activity v point]]].' +
            'd h233z[item a] i[h[a a] e][r[p zzq]].' +
            'd zother[person a activity a] e[b point[k ztruth[v person v activity v point]]].' +
            'd zalias[person a activity a] e[b point[k cg[v person v activity v point]]].')
        new = {d['name']: d for d in replacement['declarations']}
        assert new['zzq'] == catalog().entries['zzq']['declaration']
        doc['declarations'] = list(new.values()) + [d for d in doc['declarations'] if d['name'] not in new]
        if kind == 'obedience_finite':
            guided.finite_descriptions(doc)
        roots = ['r3i', 'zother', 'zalias']
        query = 'q[t[k r3i[k zs[] k zp[] k zrole[] k zwork[] k zr[]]][k zt[]]].'
    elif kind == 'permission':
        roots = ['r3j']
        query = 'q[t[k r3j[k zp[] k zrole[] k zwork[] k zr[]]][k zt[]]].'
    elif kind == 'requirement':
        roots = ['r3l']
        query = 'q[t[k r3l[k zp[] k zrole[] k zwork[] k zr[]]][k zt[]]].'
    elif kind == 'scope':
        roots = ['r3m', 'r3n']
        for d in doc['declarations']:
            if d['name'] in ('r3c',):
                d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
                d.pop('body')
        query = ('q[k r3m[k zp[] k zrole[] k zwork[] k zr[]]].'
                 'q[t[k r3n[]][k zt[]]].')
    else:
        assert kind == 'discourse'
        roots, query = ['r3o'], 'q[k r3o[]].'
    doc.update(declarations=closure(doc, roots), statements=[])
    return parse(format_graph(doc, 'compact') + ('' if kind == 'discourse' else EXTRA) + query)


def base(doc):
    values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    values.update(zs=lambda: 'source', zp=lambda: 'person', zrole=lambda: 'office',
                  zwork=lambda: 'work', zr=lambda: 'reference', zt=lambda: 'later',
                  h237h=lambda w, r: 'work', h237g=lambda m, w, r: 'source')
    return values


@lru_cache(None)
def obedience_checks():
    doc = fixture('obedience_finite')
    def model(document, variant='baseline', bits=(True, False, True, True), scope=('first', 'second')):
        values = guided.obedience_model(document, variant, bits)
        values.update(zrole=lambda: 'office', zwork=lambda: 'work',
            h237x=lambda person, role, work, activity, reference: (
                person, role, work, reference) == ('person', 'office', 'work', 'reference') and activity in scope)
        return values
    rows = []
    for bits in product((False, True), repeat=4):
        actual = evaluate(doc, model(doc, bits=bits), DOMAIN, SCENES, True)
        assert actual == [bits[0] and not bits[1] and bits[2] and bits[3]], (bits, actual)
        rows.append(dict(flags=list(bits), value=actual[0]))
    contrasts = {}
    for variant in ('empty_records', 'unlisted_description', 'conflicting', 'guidance_wrong_source',
                    'guidance_wrong_content', 'guidance_wrong_reference', 'no_requirements'):
        actual = evaluate(doc, model(doc, variant), DOMAIN, SCENES, True)
        assert actual == [variant == 'no_requirements'], (variant, actual)
        contrasts[variant] = actual[0]
    assert evaluate(doc, model(doc, bits=(True, True, True, False), scope=('first',)), DOMAIN, SCENES, True) == [True]
    full = fixture('obedience_full')
    try:
        evaluate(full, model(full), DOMAIN, SCENES, True)
    except ValueError as error:
        assert 'description domain' in str(error), str(error)
    else:
        raise AssertionError('Full description universe was evaluated as finite')
    return dict(combinations=rows, contrasts=contrasts, other_work_requirements_excluded=True,
                scoped_missing_requirements_not_deleted=True, full_description_domain_refused=True,
                full_description_domain_verified=False,
                semantic_boundaries=['Diagnostic copy only: rtx description quantifier instantiated at zzq, zother, zalias.'])


def permission_model(doc, variant='baseline'):
    values = base(doc)
    values.update(
        ca=lambda p, act, ref: (p, ref) == ('person', 'reference') and act in ('first', 'second'),
        h232p=lambda act, ref: act in ('first', 'second') and ref == 'reference',
        cb=lambda p, act, role, ref: (p, role, ref) == ('person', 'office', 'reference'),
        h237x=lambda p, role, work, act, ref: (p, role, work, ref) == (
            'person', 'office', 'work', 'reference') and act == 'first',
        h7b=lambda source, p, role, act, code, sign, point: (source, p, role, act, symbol(code), sign, point) == (
            'other' if variant == 'permission_other_source' else 'source', 'person',
            'other' if variant == 'permission_other_role' else 'office',
            'second' if variant == 'permission_outside_work' else 'first', 'zzq', True,
            'reference' if variant == 'permission_at_reference_only' else 'later') and variant != 'baseline')
    return values


@lru_cache(None)
def permission_checks():
    doc, rows = fixture('permission'), {}
    for variant in ('baseline', 'permission_in_work', 'permission_other_source',
                    'permission_other_role', 'permission_outside_work', 'permission_at_reference_only'):
        actual = evaluate(doc, permission_model(doc, variant), DOMAIN, SCENES, True)
        assert actual == [variant != 'permission_in_work'], (variant, actual)
        rows[variant] = actual[0]
    values = permission_model(doc); values['h7b'] = unknown
    try:
        evaluate(doc, values, DOMAIN, SCENES, True)
    except ValueError as error:
        assert 'Unknown' in str(error)
    else:
        raise AssertionError('Unknown permission became denial')
    assert permission_model(doc)['cg'] is unknown
    return dict(contrasts=rows, execution_not_evaluated=True, unknown_permission_refused=True)


def require_model(doc, variant='baseline'):
    values = base(doc)
    values['h237z'] = lambda source, person, role, target, bindings, reference, sign, point: (
        source, person, role, symbol(target), target.rank, tuple(bindings.items), reference, sign, point) == (
        'other' if variant == 'other_source' else 'source', 'person', 'office',
        'r2zv' if variant == 'passivity_instead_of_obedience' else 'r3k', 1,
        ('person', 'work', 'office') if variant == 'wrong_bindings' else ('person', 'office', 'work'),
        'later' if variant == 'other_reference' else 'reference',
        False if variant == 'negative_requirement' else True, 'later')
    return values


@lru_cache(None)
def requirement_checks():
    doc, rows = fixture('requirement'), {}
    for variant in ('baseline', 'other_source', 'passivity_instead_of_obedience',
                    'wrong_bindings', 'other_reference', 'negative_requirement'):
        actual = evaluate(doc, require_model(doc, variant), DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual[0]
    assert require_model(doc)['h7a'] is unknown
    return dict(contrasts=rows, rank_one_full_obedience_quote_not_executed=True,
                reference_passed_into_target=True)


@lru_cache(None)
def adapter_checks():
    doc = deepcopy(catalog().document)
    replacement = parse('p:r zfulfilled[a a a a d d] c.' +
        'd r3i[source a person a role a work a reference d] e[b point[' +
        'k zfulfilled[v source v person v role v work v reference v point]]].')
    new = {d['name']: d for d in replacement['declarations']}
    doc['declarations'] = [new['zfulfilled']] + [
        new.get(d['name'], d) for d in doc['declarations']]
    doc.update(declarations=closure(doc, ['r3k']), statements=[])
    prefix = format_graph(doc, 'compact') + EXTRA
    rows = {}
    for seq in ((), ('zp',), ('zp', 'zrole'), ('zp', 'zrole', 'zwork'),
                ('zrole', 'zp', 'zwork'), ('zp', 'zrole', 'zwork', 'zp')):
        query = ('q[t[k r3k[l[a][' + ' '.join('k ' + n + '[]' for n in seq) +
                 '] k zr[]]][k zt[]]].')
        current = parse(prefix + query)
        for ref in ('reference', 'other'):
            values = base(current)
            values.update(zr=lambda: ref,
                h237g=lambda m, w, r: 'source' if r == 'reference' else 'other',
                zfulfilled=lambda source, person, role, work, reference, point: (
                    source, person, role, work, reference, point) == (
                    'source' if ref == 'reference' else 'other',
                    'person', 'office', 'work', ref, 'later'))
            actual = evaluate(current, values, DOMAIN, (*SCENES, 'other'), True)
            assert actual == [seq == ('zp', 'zrole', 'zwork')], (seq, ref, actual)
            rows[','.join(seq) + '@' + ref] = actual[0]
    return dict(contrasts=rows, explicit_reference_not_replaced_by_global_constant=True,
                semantic_boundaries=['r3i content replaced only here by a typed binding diagnostic; native obedience checked separately.'])


@lru_cache(None)
def scope_checks():
    doc, rows = fixture('scope'), {}
    for variant in ('baseline', 'empty_work_scope', 'other_office', 'other_member', 'missing_background',
                    'permission_present', 'requirement_absent'):
        values = permission_model(doc, 'permission_in_work' if variant == 'permission_present' else 'baseline')
        values.update(require_model(doc))
        # Restore the permission callbacks after adding the requirement interpretation.
        permissions = permission_model(doc, 'permission_in_work' if variant == 'permission_present' else 'baseline')
        for name in ('ca', 'h232p', 'cb', 'h237x', 'h7b'):
            values[name] = permissions[name]
        values.update(h232v=lambda: 'reference',
            h237y=lambda w, r: variant != 'empty_work_scope' and (w, r) == ('work', 'reference'),
            aa=lambda p: p == 'person',
            h237d=lambda m, w, r: FunctionValue(('individual',), 'truth',
                lambda p: p == ('other' if variant == 'other_member' else 'person')),
            h237i=lambda w, r: 'work',
            h237c=lambda p, community, r: (p, community, r) == ('person', 'work', 'reference'),
            h237e=lambda p, m, w, r: 'other' if variant == 'other_office' else 'office',
            h237f=lambda p, role, m, w, r: (p, role, m, w, r) == ('person', 'office', 'work', 'work', 'reference'),
            r3c=lambda w, r: variant != 'missing_background' and (w, r) == ('work', 'reference'))
        if variant == 'requirement_absent':
            values['h237z'] = lambda *args: False
        actual = evaluate(doc, values, DOMAIN, SCENES, True)
        # Invalid scope fixtures are rejected by the native scope; background is
        # a fixture boundary whose membership/assignment consistency is pinned separately.
        expected = {'baseline': [True, True], 'empty_work_scope': [False, False],
                    'other_office': [False, True], 'other_member': [False, True],
                    'missing_background': [True, False], 'permission_present': [True, False],
                    'requirement_absent': [True, False]}[variant]
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, scope_precedes_permissions_and_compliance=True,
                semantic_boundaries=['r3c is a typed boundary; its nonempty members and assignment conditions were checked previously.',
                                     'Inconsistent scope plus background fixtures do not claim source-model validity.'])


@lru_cache(None)
def discourse_checks():
    doc, rows = fixture('discourse'), {}
    for variant in ('baseline', 'missing_correction', 'wrong_replacement', 'missing_acknowledgment',
                    'wrong_scope', 'wrong_explanation'):
        values = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
        values.update(wa=lambda: 'author', h242c=lambda: 'sentence', h237w=lambda: 'prior',
            h232o=lambda: 'presentation',
            h236i=lambda n, a, code, ctx: (n, a, symbol(code), code.rank, ctx) == (
                'sentence', 'author', 'r3n', 3, 'presentation'),
            h242a=lambda n, a, scope, neg, pos, ctx: variant != 'missing_correction' and (
                n, a, symbol(scope), symbol(neg), neg.rank, symbol(pos), pos.rank, ctx) == (
                'sentence', 'author', 'r3c' if variant == 'wrong_scope' else 'r3m',
                'r3j', 1, 'r3k' if variant == 'wrong_replacement' else 'r3l', 2, 'presentation'),
            h242b=lambda n, a, code, ctx: variant != 'missing_acknowledgment' and (
                n, a, symbol(code), code.rank, ctx) == ('sentence', 'author', 'r3n', 3, 'presentation'),
            uf=lambda a, first, second, ctx: (a, first, second, ctx) == (
                'author', 'sentence' if variant == 'wrong_explanation' else 'prior', 'sentence', 'presentation'),
            ue=lambda first, second, ctx: (first, second, ctx) == ('prior', 'sentence', 'presentation'))
        actual = evaluate(doc, values, DOMAIN + ('author', 'sentence', 'prior'), SCENES + ('presentation',), True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual[0]
    return dict(contrasts=rows, content_not_executed=True, modality_ranks_preserved=True)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    parts = [
        ('Hier ', ['h237y', 'r3m', 'r3n'], '直前の事務・機構・成員・割当て職務を受ける。'),
        ('ist es nun ', ['uf', 'ue', 'r3o'], '直前の受動的役割の説明を許可と要求の面で具体化する。'),
        ('freilich ', ['h242b', 'r3o'], 'この限定された場面では確かに認めるという承認的な取り立て。'),
        ('nicht erlaubt, zu räsonniren; ', ['r3j', 'ca', 'h232p', 'h7b'], '同じ職務の事務内の言語的検討について実行許可を否定する。'),
        ('sondern ', ['h242a', 'r3o'], '否定した選択に代わる肯定的要求の提示。'),
        ('man muß gehorchen.', ['r3h', 'r3i', 'r3k', 'r3l', 'r3n'], '同じ範囲の各本人に同じ出所の事務上の要求を網羅して従うよう求める。'),
    ]
    cursor, clauses = 1661, []
    for text, names, meaning in parts:
        assert unit['text'][cursor:cursor + len(text)] == text, (cursor, text)
        clauses.append(dict(range=[cursor, cursor + len(text)], text=text, definitions=names, reading=meaning))
        cursor += len(text)
    assert cursor == 1742
    text = unit['text'][1661:1742]
    count = sum(not c.isspace() for c in text)
    return dict(status='office_obedience_sentence_reviewed_under_explicit_reading',
                reviewer='assistant_review', document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[1661, 1742], text=text),
                selection=selection_binding(catalog(), [80]), clauses=clauses, interpretation=LIMITS,
                unresolved=[], decision='equivalent_under_stated_reading_for_the_office_obedience_sentence',
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                newly_reviewed_sentence_characters=count, preserved_reviewed_sentence_characters=1422,
                paragraph_reviewed_sentence_characters=1422 + count,
                semantic_equivalence_automatically_proved=False,
                holistic_review=[
                    'Hierの事務・成員・職務を先行の同じ機構へ接続し、同じ人の職務外まで量化していない。',
                    '議論の許可否定、服従への要求、実際の履行の三つを分け、許可と要求の出所を共有する。',
                    '服従には全記述域の網羅と履行、指示に従う調整を保持し、受動性だけに縮めていない。',
                    'sondernの対置、nunの説明への継続、freilichの限定的な承認を保持した。',
                    '原刊485頁の同文と直後の学識者としての留保を照合し、この読みの職務範囲と整合することを確認した。'],
                original_page=dict(path=IMAGE, page=485, visually_inspected=True),
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in (
                    FULL, BASIS, ANNOTATIONS, DOC, INVENTORY, IMAGE, *PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:80] == old.document['statements']
    assert len(new.document['statements']) == 81
    assert all(new.entries[n] == e for n, e in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path in PRIOR:
        validate_hashes(ROOT, read(path)['source_sha256'])
    prior = read('data/public-purpose-mechanism-reading-v1.json')
    assert prior['selection'] == selection_binding(new, [79])
    validate_hashes(ROOT, prior['source_sha256'])
    assert read(AUDIT) == reading()
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_statements=80, added_statements=1,
                preserved_whole_unit_reviews=len(reviews), old_meanings_unchanged=True,
                new_reviewed_sentence_characters=read(AUDIT)['newly_reviewed_sentence_characters'],
                roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('obedience', obedience_checks), ('permission', permission_checks),
                     ('requirement', requirement_checks), ('adapter', adapter_checks), ('scope', scope_checks),
                     ('discourse', discourse_checks), ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, INVENTORY, IMAGE, *PRIOR, 'data/public-purpose-mechanism-reading-v1.json',
        'scripts/compose_office_obedience.py', 'scripts/check_office_obedience.py',
        'tests/test_office_obedience.py', 'scripts/check_free_choice_obedience.py',
        'scripts/compose_scoped_obedience.py', 'scripts/compose_situated_criticism.py',
        'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='office_argument_permission_denial_and_obedience_requirement', document=FULL,
                **results, alignment=dict(**read(AUDIT)['source'], statements=[80],
                    definitions=list(MEANINGS), status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
