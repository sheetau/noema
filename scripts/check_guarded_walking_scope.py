"""Execute the compound claim and expose unbound confinement-stage witnesses."""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import json

from noema.constructed import parse, format_graph
from noema.constructed_semantics import SequenceValue
from noema.finite_semantics import SequenceValue as LegacySequence
from noema.meaning_catalog import load_catalog, _references
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_insistent_framing import ROOT, FULL, BASIS, closure
from scripts.check_pastoral_roles import evaluate
from scripts.check_prevented_attempt import source_model, DOMAIN, SCENES, ref
from scripts.check_motive_causes import unknown

INDEX = 'data/semantic-review-index-v76.json'
CORE = 'examples/v016/guarded-walking-scope.noema'
AUDIT = 'data/guarded-walking-scope-v1.json'
REPORT = 'reports/guarded-walking-scope-v1.json'
DOC = 'docs/guarded-walking-scope-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
SELECTION = [9, 35, 36, 46, 47, 48, 49]
PEOPLE = DOMAIN + ('supervised', 'detailone', 'detailtwo')
CONFINEMENT_PEOPLE = PEOPLE + ('lock', 'frame', 'closing', 'inside', 'threshold', 'outside')
TIMES = ('conditioning', 'prior', 'closed', 'middle', 'actual', 'belief', 'loss')


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


def fixture(roots, suffix):
    d = deepcopy(catalog().document)
    d.update(declarations=closure(d, roots), statements=[])
    return parse(format_graph(d, 'compact') + suffix)


@lru_cache(None)
def compound():
    return fixture(['hztq', 'hztr', 'rqzw'], '''
r za[] d.r zb[] d.r zc[] d.r jp[] a.
q[k hztq[k db[] k za[] k zb[] k zc[]]].
q[t[k hztr[k db[]]][k za[]]].
q[k rqzw[k jp[] k zc[] k za[]]].
''')


def model(d, variant='baseline'):
    v = source_model(d, variant)
    second = v['zc']()
    def goal(g, bindings):
        return ref(g, 'hztm') and bindings.items in (('person',), ('other',))
    v.update(jp=lambda: 'person', hztd=lambda: 'supervised', h7k=unknown,
        h7l=lambda *args: variant == 'permission_present',
        hztk=lambda group, act, g, b, aspect, s:
            (group, act, s) == ('guards', 'blocking_act', second) and goal(g, b)
            and aspect in ('detailone', 'detailtwo'),
        hztj=lambda actor, act, g, b, aspect, s:
            (actor, act, s) == ('guardone' if aspect == 'detailone' else 'guardtwo', 'blocking_act', second)
            and goal(g, b) and aspect in ('detailone', 'detailtwo')
            and not (variant == 'missing_attention' and aspect == 'detailtwo'),
        hztl=lambda actor, act, g, b, s: variant != 'no_purpose'
            and actor in ('guardone', 'guardtwo') and (act, s) == ('blocking_act', second) and goal(g, b))
    if variant == 'other_person_permission':
        v['h7l'] = lambda source, person, role, goal, bindings, positive, scene: person == 'other'
    return v


def compound_checks():
    rows = {}
    variants = ('baseline', 'simultaneous', 'reverse_prefix', 'late_conditioning', 'late_blocking',
        'blocking_now', 'empty_agents', 'empty_audience', 'no_conditioning_result', 'actually_attempts',
        'no_blocking_cause', 'different_earlier_target', 'split_blocking', 'no_warning', 'split_warning',
        'wrong_warning_subject', 'permission_present', 'missing_attention', 'no_purpose', 'other_person_permission')
    stage_ok = {'baseline', 'simultaneous', 'reverse_prefix', 'no_warning', 'split_warning', 'wrong_warning_subject'}
    local_ok = stage_ok | {'late_conditioning', 'empty_audience', 'no_conditioning_result', 'other_person_permission'}
    for name in variants:
        actual = evaluate(compound(), model(compound(), name), PEOPLE, SCENES, True)
        expected = [name in stage_ok, name in ('baseline', 'simultaneous', 'reverse_prefix'), name in local_ok]
        assert actual == expected, (name, actual, expected)
        rows[name] = actual
        print('compound '+name+' checked', flush=True)
    return dict(contrasts=rows, columns=['shared_stage', 'whole_claim', 'selected_person_stage'],
        actual_current_definitions_executed=True, quoted_warning_risk_left_unknown=True,
        one_person_success_does_not_replace_all_recipients=True,
        relative_order_of_two_prior_stages_not_asserted=True, pure_memoization=True)


@lru_cache(None)
def combined():
    return fixture(['hztq', 'hztr', 'rqzw', 'zbe', 'zbb'], '''
r za[] d.r zb[] d.r zc[] d.r jp[] a.r jf[] a.r jl[] a.r jm[] d.
q[t[k hztr[k db[]]][k za[]]].
q[k rqzw[k jp[] k zc[] k za[]]].
q[k zbe[k jp[] k jf[] k jl[] k za[]]].
q[t[k zbb[k jp[] k jf[] k jl[]]][k zc[]]].
q[t[k zbb[k jp[] k jf[] k jl[]]][k jm[]]].
''')


def combined_model(d, earlier=False):
    # Adapt primitive values only, keeping every current Noema definition.
    from scripts.check_confinement_onset import source_model as confinement_model
    v = model(d)
    old = confinement_model(d)
    rename = {'being': 'person', 'guard': 'guardone', 'before': 'conditioning' if earlier else 'prior',
        'closed': 'prior' if earlier else 'closed', 'middle': 'middle', 'now': 'actual'}
    inverse = {b: a for a, b in rename.items()}
    def adapted(fn):
        def call(*args):
            result = fn(*(inverse.get(a, a) if isinstance(a, str) else a for a in args))
            if isinstance(result, LegacySequence):
                return SequenceValue(tuple(rename.get(a, a) for a in result.items), result.element_type)
            return rename.get(result, result) if isinstance(result, str) else result
        return call
    for name in ('ag', 'la', 'zba', 'qw', 'qz', 'qt', 'qu', 'qv', 'q7', 'qx', 'qy'):
        v[name] = adapted(old[name])
    for name in ('df', 'dg'):
        a, b = v[name], adapted(old[name])
        v[name] = lambda *args, a=a, b=b: a(*args) or b(*args)
    v.update(dd=lambda a, b: TIMES.index(a) < TIMES.index(b),
        ha=lambda a, b: a+b, hc=lambda a, b: a < b, hd=lambda truth: Fraction(int(truth)),
        jf=lambda: 'frame', jl=lambda: 'lock', jm=lambda: 'middle')
    return v


def confinement_checks():
    rows = {}
    for name, earlier in (('confinement_after_prevention', False), ('confinement_by_prevention', True)):
        actual = evaluate(combined(), combined_model(combined(), earlier), CONFINEMENT_PEOPLE, TIMES, True)
        expected = [True, True, True, earlier, True]
        assert actual == expected, (name, actual, expected)
        rows[name] = actual
        print(name+' checked', flush=True)
    return dict(contrasts=rows,
        columns=['whole_claim', 'same_person_prior_stage', 'confinement_until_anchor', 'confined_at_prior', 'confined_at_middle'],
        independent_past_witnesses_do_not_establish_overlap=True,
        actual_causal_attention_permission_and_graph_confinement_definitions_executed=True,
        countermodel_does_not_assert_humans_are_livestock=True,
        limit='This exposes an unentailed temporal condition, not an automatic proof of the intended historical reading.')


def unknown_checks():
    for name in ('g3', 'hztj', 'h7l', 'dd', 'f2'):
        v = model(compound()); v[name] = unknown
        try:
            evaluate(compound(), v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error), error
        else:
            raise AssertionError(name)
    return dict(unknown_inputs_refused=5)


def reading():
    prior = json.loads((ROOT/'data/insistent-framing-reading-v1.json').read_text(encoding='utf-8'))
    validate_hashes(ROOT, prior['source_sha256'])
    return dict(status='compound_scope_audited_confinement_overlap_unresolved', reviewer='assistant_review',
        document=FULL, meaning_basis=BASIS, source=prior['source'],
        selection=selection_binding(catalog(), SELECTION),
        established=['同じ対象者全員への先行する原因行為・注意・許容欠如と、後の提示行為を現行定義で一緒に評価した。',
            '一人だけの成立、別の対象への警告、別の行為の参加、別時点の条件は全体の成立に代用できない。',
            '後の提示は危険内容の真理を要求しない。先行二局面相互の厳密な順序も要求しない。'],
        unresolved=[dict(id='confinement_overlap',
            issue='警告まで続く閉じ込めの開始が、先行する阻止・不許容より後でも現行の条件は両立する。',
            next_step='同じ本人・装置・先行時点へ閉じ込めを結ぶ候補を構成し、原文の時間的含意と照合する。単に二つの過去の存在量化を並べても解消しない。'),
            dict(id='walking_reading', issue='補助なしの脚の移動という既存の身体描写と、この文のgehenの範囲の照合が残る。'),
            dict(id='whole_reading', issue='家畜像・局面上の落ち着き・強調を含む採用読解の通し判断は、この検査だけでは確定しない。')],
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        new_verified_sentence_characters=0, semantic_equivalence_automatically_proved=False)


def structure():
    idx = json.loads((ROOT/INDEX).read_text(encoding='utf-8'))
    assert idx['works']['kant-1784']['document'] == FULL
    assert idx['works']['kant-1784']['meaning_basis'] == BASIS
    for path in idx['works']['kant-1784']['reviews']:
        r = json.loads((ROOT/path).read_text(encoding='utf-8'))
        assert r['selection'] == selection_binding(catalog(), [s['index'] for s in r['selection']['statements']])
    d = combined()
    assert (ROOT/CORE).read_text(encoding='utf-8') == format_graph(d, 'compact')+'\n'
    for notation in ('compact', 'full'):
        s = format_graph(d, notation)
        assert parse(s) == parse(transcribe(s, alphabet='v2')) == d
    assert json.loads((ROOT/AUDIT).read_text(encoding='utf-8')) == reading()
    return dict(manuscript_statements_unchanged=50, preserved_review_selections=11,
        diagnostic_definitions_not_added_to_manuscript=True, current_selection_bound=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    write_exact(ROOT/CORE, format_graph(combined(), 'compact')+'\n')
    write_exact(ROOT/AUDIT, encoded(reading()))


def build_report(results=None):
    if results is None:
        results = {}
        for name, fn in [('compound', compound_checks), ('confinement', confinement_checks), ('unknowns', unknown_checks), ('structure', structure)]:
            results[name] = fn(); print(name+' checked', flush=True)
    prior = json.loads((ROOT/'reports/insistent-framing-v1.json').read_text(encoding='utf-8'))
    validate_hashes(ROOT, prior['source_sha256'])
    unit = next(u for u in json.loads((ROOT/INVENTORY).read_text(encoding='utf-8'))['units']
        if u['id'] == reading()['source']['unit'])
    span = [1073, 1101]
    assert unit['text'][span[0]:span[1]] == 'darin sie sie einsperreten, '
    paths = set(catalog().source_sha256) | set(prior['source_sha256']) | {
        INDEX, CORE, AUDIT, DOC, INVENTORY, 'reports/insistent-framing-v1.json',
        'data/insistent-framing-reading-v1.json', 'scripts/check_guarded_walking_scope.py',
        'scripts/register_guarded_walking_scope.py', 'tests/test_guarded_walking_scope.py',
        'scripts/check_prevented_attempt.py', 'scripts/check_confinement_onset.py',
        'scripts/check_confinement.py', 'scripts/check_described_appraisals.py'}
    return dict(status='compound_scope_checked_with_temporal_countermodel', document=FULL, **results,
        selection=reading()['selection'],
        alignment=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=span,
            text=unit['text'][span[0]:span[1]], definitions=['hztu', 'hztt', 'zbf', 'zbe', 'zbb', 'rqzw', 'hztr', 'hztq'],
            status='partial_compound_scope_check'),
        alignment_usage='Checks the already covered confinement clause; compound context is not additional coverage.',
        whole_sentence_semantically_verified=False, new_verified_sentence_characters=0, new_covered_characters=0,
        verified_full_units={'kant-1784': 0, 'einstein-1905': 0}, semantic_equivalence_automatically_proved=False,
        source_sha256={p: digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    from scripts.audit_opening_scope import write_exact, encoded
    prepare(); write_exact(ROOT/REPORT, encoded(build_report()))


if __name__ == '__main__':
    main()
