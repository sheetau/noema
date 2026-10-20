"""Check task coverage, real presentations, and quantified teaching policy."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest, validate_hashes
from noema.script import transcribe
from scripts.compose_teaching_policy import ROOT, LIBRARY, BASIS, NAMES, MESSAGE, PRIMITIVES, MEANINGS, parents, build, closure
from scripts.check_confessional_teaching import EXTRA, PROVIDERS, model as teaching_model, DOMAIN, SCENES
from scripts.check_ranked_appointment import model as appointment_model, SCENES as PAST_SCENES
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

REPORT = 'reports/teaching-policy-v1.json'
DOC = 'docs/teaching-policy-v1.md'
PRIOR = ('reports/confessional-teaching-v1.json', 'reports/ranked-appointment-v1.json')
MORE = ('occasion', 'secondoccasion', 'secondactivity', 'event')
EXTRA_LOCAL = EXTRA + ''.join('r z' + n + '[] a.' for n in MORE) + 'r zpast[] d.'
EXTRA_LOCAL += 'd zbadmessage[subject a] f[j s[k zmeaning[v subject]]].'
SMALL = (*DOMAIN, *MORE)
TIMES = ('reference', 'early', 'one', 'two', 'last')


def read(path): return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog(): return load_catalog(ROOT, BASIS)


def substitute(node, name, value):
    if node == dict(kind='variable', name=name): return deepcopy(value)
    if isinstance(node, dict): return {k: substitute(v, name, value) for k, v in node.items()}
    if isinstance(node, list): return [substitute(x, name, value) for x in node]
    return node


def two_messages(node):
    # Diagnostic fixture only; production keeps the complete description domain.
    if isinstance(node, dict):
        if node.get('kind') in ('forall', 'exists') and isinstance(node.get('sort'), dict) and node['sort'].get('kind') == 'description':
            assert node['sort'] == parse('p:r zz[' + MESSAGE + '] c.')['declarations'][0]['parameters'][0]
            return dict(kind='and' if node['kind'] == 'forall' else 'or', arguments=[
                two_messages(substitute(node['body'], node['variable'], dict(kind='quote', body=dict(kind='function_ref', symbol=n))))
                for n in ('zmessage', 'zbadmessage')])
        return {k: two_messages(v) for k, v in node.items()}
    if isinstance(node, list): return [two_messages(x) for x in node]
    return node


@lru_cache(None)
def fixture(target, boundaries=(), finite=False, bindings=()):
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']]); d.pop('body')
    doc.update(declarations=closure(doc, [target]), statements=[])
    prefix = parse('p:' + EXTRA_LOCAL + PROVIDERS)
    providers = {d['name']: d for d in prefix['declarations'] if d['name'] in ('h246e', 'h246j')}
    doc['declarations'] = [d for d in prefix['declarations'] if d['name'] not in providers] + [
        deepcopy(providers.get(d['name'], d)) for d in doc['declarations']]
    args = ' '.join('k z' + n + '[]' for n in NAMES) + ' k zref[]'
    if target in ('r355', 'r356', 'r357', 'r36b', 'r36c'): args += ' k zoccasion[]'
    if target in ('r356', 'r357', 'r36a'): args += ' k zactivity[] r[p zmessage]'
    if target == 'r36e': args = 'l[a][' + ' '.join('k z' + n + '[]' for n in bindings) + '] k zref[]'
    call = 'k ' + target + '[' + args + ']'
    if target != 'r355': call = 't[' + call + '][k zpoint[]]'
    doc = parse(format_graph(doc, 'compact') + 'q[' + call + '].')
    return parse(format_graph(two_messages(doc), 'compact')) if finite else doc


def base(doc, point='outcome'):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    for n in (*DOMAIN, *MORE): v['z' + n] = lambda n=n: n
    v.update(zref=lambda: 'reference', zpoint=lambda: point, zpast=lambda: 'past')
    return v


def local_model(doc, variant='baseline'):
    v = teaching_model(doc, variant); v.update({n: f for n, f in base(doc).items() if f is not unknown})
    wanted = ('person', 'role', 'church', 'subject', 'occasion', 'reference')
    fields = ('person', 'role', 'church', 'subject', 'occasion', 'reference')
    v['h246n'] = lambda *args: args == tuple('other' if variant == 'scope_' + n else value for n, value in zip(fields, wanted))
    recipients = () if variant == 'empty_allocation' else ('other',) if variant == 'foreign_recipient' else (
        'member', 'overlap') if variant == 'congregation_task' else ('learner', 'overlap')
    v['h246o'] = lambda occasion, recipient, ref: (occasion, ref) == ('occasion', 'reference') and recipient in recipients
    v['h246p'] = lambda occasion, activity, ref: (occasion, activity, ref) == (
        'secondoccasion' if variant == 'other_task_activity' else 'occasion', 'activity', 'reference')
    conveys = v.get('f2', unknown)
    v['f2'] = lambda activity, recipient, subject, code, point: recipient in recipients and variant != 'no_recipient_reached' and conveys(
        activity, recipient, subject, code, point)
    return v


@lru_cache(None)
def local_checks():
    rows = {}
    variants = {
        'r355': ('baseline', 'congregation_task', 'empty_allocation', 'foreign_recipient', 'scope_person', 'scope_role',
            'scope_church', 'scope_subject', 'scope_occasion', 'scope_reference'),
        'r356': ('baseline', 'congregation_task', 'other_task_activity', 'criterion_failed', 'no_event',
            'other_presenter', 'not_entrusted', 'no_current_adoption', 'no_current_service', 'no_recipient_reached'),
        'r357': ('baseline', 'congregation_task', 'criterion_failed', 'other_task_activity', 'no_event',
            'other_presenter', 'not_exposition', 'no_recipient_reached'),
        'r36a': ('baseline', 'criterion_failed', 'criterion_subject', 'criterion_message', 'not_entrusted',
            'no_current_adoption', 'no_current_service', 'equivalent_alias', 'position_role'),
    }
    for target, names in variants.items():
        doc = fixture(target); rows[target] = {}
        for variant in names:
            v = local_model(doc, variant)
            expected = variant in ('baseline', 'congregation_task') or target == 'r357' and variant == 'criterion_failed'
            if target == 'r357': v['zjudge'] = unknown
            actual = evaluate(doc, v, (*DOMAIN, *MORE), SCENES, True)
            assert actual == [expected], (target, variant, actual); rows[target][variant] = actual[0]
    return dict(contrasts=rows, native_r35t_rfw_rfv_rfu_rfo_used=True,
        pupils_and_congregation_may_have_separate_tasks=True, actual_exposition_not_filtered_by_conformity=True)


def period_model(doc, variant='baseline'):
    v = base(doc, 'last')
    fixed = (*NAMES, 'reference', 'occasion')
    v['r355'] = lambda *args: variant != 'invalid_task' and args == fixed
    def presentation(*args):
        prefix, activity, code = args[:-2], args[-2], args[-1]
        truth = []
        for point in TIMES:
            actual = prefix == fixed and activity == 'activity' and symbol(code) == 'zmessage' and point == 'one'
            if variant == 'no_execution': actual = False
            if variant == 'different_method': actual = prefix == fixed and activity == 'secondactivity' and symbol(code) == 'zmessage' and point == 'two'
            if variant == 'outside_window': actual = prefix == fixed and activity == 'activity' and symbol(code) == 'zmessage' and point == 'early'
            truth.append(actual)
        return Content(TIMES, tuple(truth))
    def actual_exposition(*args):
        values = list(presentation(*args).values)
        if variant in ('extra_bad_message', 'extra_bad_activity', 'extra_bad_later') and args[:-2] == fixed:
            act = 'secondactivity' if variant == 'extra_bad_activity' else 'activity'
            at = 'two' if variant == 'extra_bad_later' else 'one'
            if args[-2] == act and symbol(args[-1]) == 'zbadmessage': values[TIMES.index(at)] = True
        return Content(TIMES, tuple(values))
    v.update(r356=presentation, r357=actual_exposition,
        r36a=lambda *args: Content(TIMES, tuple(args[:-2] == (*NAMES, 'reference') and symbol(args[-1]) == 'zmessage' for _ in TIMES)),
        h7q=lambda occasion, candidate, at: (occasion, candidate) == ('occasion', 'last') and at in TIMES,
        h7r=lambda occasion, candidate, at: (occasion, candidate) == ('occasion', 'last') and at in (
            () if variant == 'empty_window' else ('early', 'two') if variant == 'gapped_window' else ('one', 'two')),
        ic=lambda first, last, candidate: candidate == 'last' and first in TIMES and last in TIMES and TIMES.index(first) < TIMES.index(last))
    return v


@lru_cache(None)
def period_checks():
    boundaries = ('r355', 'r356', 'r357', 'r36a')
    doc, rows = fixture('r36c', boundaries, True), {}
    for variant in ('baseline', 'different_method', 'no_execution', 'outside_window', 'extra_bad_message',
        'extra_bad_activity', 'extra_bad_later', 'invalid_task', 'empty_window', 'gapped_window'):
        actual = evaluate(doc, period_model(doc, variant), SMALL, TIMES, True)
        assert actual == [variant in ('baseline', 'different_method')], (variant, actual); rows[variant] = actual[0]
    complete = fixture('r36c', boundaries)
    try: evaluate(complete, period_model(complete), SMALL, TIMES, True)
    except ValueError as error:
        assert 'Cannot finitely quantify the description domain' in str(error), str(error); refusal = str(error)
    else: raise AssertionError('Production policy reduced the message domain')
    return dict(contrasts=rows, native_tb_and_period_quantification=True, unchosen_alternatives_not_required=True,
        extra_nonconforming_exposition_not_hidden=True, full_domain_refused=refusal,
        boundaries=['Task and concrete exposition predicates are typed boundaries; local checks evaluate their native definitions.',
            'Only this diagnostic fixture expands message quantifiers over zmessage/zbadmessage; production retains the full domain.'])


@lru_cache(None)
def coverage_checks():
    doc, rows = fixture('r36d', ('r35t', 'r36c')), {}
    for variant in ('baseline', 'no_tasks', 'unassigned_member', 'failed_second_task', 'shared_recipient'):
        v = base(doc, 'last'); v['r35t'] = lambda *args: args == (*NAMES, 'reference')
        v['h246n'] = lambda *args: variant != 'no_tasks' and args[:4] == ('person', 'role', 'church', 'subject') and args[4] in ('occasion', 'secondoccasion') and args[5] == 'reference'
        v['h6t'] = lambda group, recipient, ref: ref == 'reference' and (group, recipient) in (('students', 'learner'), ('members', 'member'))
        v['h246o'] = lambda occasion, recipient, ref: ref == 'reference' and ((occasion, recipient) == ('occasion', 'learner') or
            variant != 'unassigned_member' and (occasion, recipient) == ('secondoccasion', 'member') or
            variant == 'shared_recipient' and (occasion, recipient) == ('secondoccasion', 'learner'))
        v['r36c'] = lambda *args: Content(TIMES, tuple(args[:-1] == (*NAMES, 'reference') and
            not (variant == 'failed_second_task' and args[-1] == 'secondoccasion') for _ in TIMES))
        actual = evaluate(doc, v, SMALL, TIMES, True)
        assert actual == [variant in ('baseline', 'shared_recipient')], (variant, actual); rows[variant] = actual[0]
    return dict(contrasts=rows, all_recipients_assigned_and_all_tasks_required=True,
        boundaries=['r35t and r36c are typed boundaries here; native context and task policy have separate checks.'])


@lru_cache(None)
def binding_norm_checks():
    for position in range(len(NAMES)):
        names = tuple('person' if i == position else 'other' for i in range(len(NAMES)))
        expected = tuple('x' if i == position else 'y' for i in range(len(NAMES))) + ('reference',)
        doc = fixture('r36e', ('r36d',), bindings=names); v = base(doc)
        v.update(zperson=lambda: 'x', zother=lambda: 'y', r36d=lambda *args: Content(SCENES, tuple(args == expected for _ in SCENES)))
        assert evaluate(doc, v, ('x', 'y'), SCENES, True) == [True]
    for length in (0, 8, 10):
        doc = fixture('r36e', ('r36d',), bindings=('person',) * length); v = base(doc)
        v.update(zperson=lambda: 'x', r36d=lambda *args: Content(SCENES, (True,) * len(SCENES)))
        assert evaluate(doc, v, ('x', 'y'), SCENES, True) == [False]
    rows = {}
    for target in ('r36f', 'r36g', 'r36h'):
        doc = fixture(target); rows[target] = {}
        for variant in ('baseline', 'absent_duty', 'absent_terms', 'other_target', 'other_bindings', 'other_reference', 'opposite_sign'):
            v = appointment_model(doc); v.update({n: f for n, f in base(doc, 'now').items() if f is not unknown})
            def content(code, bindings, ref, sign):
                return (symbol(code), code.rank, tuple(bindings.items), ref, sign) == (
                    'r35w' if variant == 'other_target' else 'r36e', 1, (*NAMES, 'activity') if variant == 'other_bindings' else NAMES,
                    'past' if variant == 'other_reference' else 'reference', variant != 'opposite_sign')
            v['h237z'] = lambda source, person, role, code, bindings, ref, sign, at: variant != 'absent_duty' and (
                source, person, role, at) == ('church', 'person', 'role', 'now') and content(code, bindings, ref, sign)
            v['h246m'] = lambda event, code, bindings, ref, sign, at: variant != 'absent_terms' and (event, at) == ('event', 'past') and content(code, bindings, ref, sign)
            actual = evaluate(doc, v, (*DOMAIN, *MORE), PAST_SCENES, True)
            expected = variant == 'baseline' or target == 'r36f' and variant == 'absent_terms' or target == 'r36g' and variant == 'absent_duty'
            assert actual == [expected], (target, variant, actual); rows[target][variant] = actual[0]
    return dict(independently_checked_binding_positions=len(NAMES), invalid_lengths_refused=[0, 8, 10],
        norm_and_appointment_contrasts=rows, same_whole_policy_not_one_chosen_activity=True,
        boundaries=['r36d is a typed boundary only in binding checks; norm and past appointment records retain the actual closed policy without executing it.'])


@lru_cache(None)
def unknown_quote_checks():
    rows = []
    for name in ('h246n', 'h246o', 'h246p'):
        doc = fixture('r356'); v = local_model(doc); v[name] = unknown
        try: evaluate(doc, v, (*DOMAIN, *MORE), SCENES, True)
        except ValueError as error: assert 'Unknown' in str(error), str(error)
        else: raise AssertionError(name)
        rows.append(name)
    doc = deepcopy(catalog().document); doc['statements'] = []
    quoted = parse(format_graph(doc, 'compact') + 'q[e[r b[p r36e]][r b[p r36e]]].')
    assert evaluate(quoted, base(quoted), DOMAIN, SCENES, True) == [True]
    try: parse(format_graph(doc, 'compact') + 'q[e[r[p r36e]][r[p r36e]]].')
    except ValueError as error: rank_error = str(error)
    else: raise AssertionError('Insufficient policy quote rank accepted')
    return dict(unknown_scope_inputs_refused=rows, rank_one_policy_quote_without_execution=True, insufficient_rank_rejected=rank_error)


@lru_cache(None)
def structure_checks():
    new = catalog(); old = {n: e for p in parents() for n, e in p.entries.items()}
    assert not new.document['statements']
    for n, e in new.entries.items():
        if n not in PRIMITIVES and n not in MEANINGS:
            assert e['declaration'] == old[n]['declaration'] and e['meaning_ja'] == old[n]['meaning_ja'], n
    for prior in PRIOR: validate_hashes(ROOT, read(prior)['source_sha256'])
    for path, body in build().items(): assert (ROOT / path).read_text(encoding='utf-8') == body, path
    for notation in ('compact', 'full'):
        text = format_graph(new.document, notation); assert parse(text) == parse(transcribe(text, alphabet='v2')) == new.document
    return dict(new_primitives=len(PRIMITIVES), new_definitions=len(MEANINGS), inherited_meanings_preserved=True,
        roundtrips=True, new_semantic_reviews=0, active_manuscript_unchanged=True)


def prepare():
    from scripts.audit_opening_scope import write_exact
    for path, body in build().items(): write_exact(ROOT / path, body)


def build_report():
    results = {}
    for name, fn in [('local', local_checks), ('period', period_checks), ('coverage', coverage_checks),
        ('bindings_norm', binding_norm_checks), ('unknown_quote', unknown_quote_checks), ('structure', structure_checks)]:
        results[name] = fn(); print(name + ' checked', flush=True)
    paths = set(build()) | set().union(*(set(p.source_sha256) for p in parents())) | {DOC, *PRIOR,
        'scripts/compose_teaching_policy.py', 'scripts/check_teaching_policy.py', 'tests/test_teaching_policy.py',
        'scripts/compose_confessional_teaching.py', 'scripts/check_confessional_teaching.py', 'scripts/check_ranked_appointment.py',
        'scripts/compose_protected_remarks.py', 'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py'}
    return dict(status='standing_teaching_policy_with_tasks_and_all_actual_expositions', document=LIBRARY, **results,
        whole_sentence_semantically_verified=False, whole_unit_semantically_verified=False,
        source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
