"""Check conditional scope, prospective writing, source bindings and discourse."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.constructed_semantics import Content, FunctionValue, SequenceValue
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_scholarly_compatibility import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, LIMITS, NAMES, parent, dependency, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol
from scripts.check_nonimpairing_reasoning import scholarly_model, SCENES as MODEL_SCENES, POINTS, STATES, key
from scripts.check_scholarly_self_ascription import EXTRA, DOMAIN as CIVIC_DOMAIN

INDEX = 'data/semantic-review-index-v165.json'
REPORT = 'reports/scholarly-compatibility-v1.json'
AUDIT = 'data/scholarly-compatibility-reading-v1.json'
DOC = 'docs/scholarly-compatibility-v1.md'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGE = 'artifacts/answer-discourse-v1/page-485.jpg'
PRIOR = ('reports/office-obedience-v1.json', 'reports/scholarly-self-ascription-v1.json', 'reports/nonimpairing-reasoning-v1.json')
SCENES = (*MODEL_SCENES, 'start', 'presentation')
DOMAIN = ('person', 'activity', 'work', 'writing', 'method', 'othermethod', 'factor', 'result', 'record', 'carrier', 'other')
CARGS = ' '.join('k z' + n + '[]' for n in NAMES) + ' k zref[]'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    roots = {'premise': ['r32b'], 'result': ['r32a'], 'bindings': ['r32a'],
             'quantifier': ['r32f'], 'discourse': ['r32g'], 'focus': ['r32h', 'r32i']}[kind]
    boundaries = {'bindings': ('r3u', 'r3v', 'r3y'), 'quantifier': ('r32b', 'r32a')}.get(kind, ())
    doc = deepcopy(catalog().document)
    for d in doc['declarations']:
        if d['name'] in boundaries:
            d.update(kind='primitive', parameters=[p['sort'] for p in d['parameters']])
            d.pop('body')
    doc.update(declarations=closure(doc, roots), statements=[])
    if kind == 'premise':
        query = 'q[k r32b[' + CARGS + ']].'
    elif kind in ('result', 'bindings'):
        query = 'q[t[k r32a[k zperson[] k zactivity[] k zwork[] k zwriting[] k zref[]]][k zstart[]]].'
    elif kind == 'quantifier':
        query = 'q[t[k r32f[]][k zstart[]]].'
    elif kind == 'focus':
        query = ''.join('q[k ' + n + '[k zperson[] k zcommunity[] k zworld[] k zref[]]].' for n in roots)
    else:
        query = 'q[k r32g[]].'
    return parse(format_graph(doc, 'compact') + EXTRA + 'r zstart[] d.' + query)


def base(doc):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    for n in (*NAMES, 'other'):
        v['z' + n] = lambda n=n: n
    v.update(zref=lambda: 'reference', zstart=lambda: 'start', h232v=lambda: 'reference')
    return v


@lru_cache(None)
def premise_checks():
    doc, rows = fixture('premise'), {}
    for variant in ('baseline', 'not_reasoned_discussion', 'other_public_actor', 'wrong_community'):
        v = scholarly_model(doc, variant)
        v.update(zstart=lambda: 'start')
        if variant == 'wrong_community':
            v['h237i'] = lambda w, r: 'other'
        # Every record predicate is unknown. The premise classifies a prospective
        # written activity, and must not demand a book already published now.
        for n in ('sc', 'hzwr', 'hzws', 'hzwt', 'h242e', 'h242f'):
            v[n] = unknown
        actual = evaluate(doc, v, CIVIC_DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual[0]
    return dict(contrasts=rows, no_existing_record_or_cosmopolitan_truth_in_antecedent=True,
                native_office_self_ascription_and_public_classification=True)


def result_model(doc, variant='baseline', log=None):
    v = base(doc)
    def prefix(args):
        if log is not None:
            log.add(tuple(args[:6]))
        p, a, w, ref, start, method = args[:6]
        return (p, a, w, ref, start) == ('person', 'activity', 'work', 'reference', 'start')
    v.update(
        h242j=lambda *args: (prefix(args), SequenceValue(('factor', 'result'), '"individual"'))[1],
        h242k=lambda *args: (prefix(args), False)[1],
        h242l=lambda *args: (prefix(args), 'factor')[1],
        h242m=lambda *args: (prefix(args), POINTS[STATES.index(key(args[-1]))])[1],
        h242n=lambda w, ref, s: (w, ref) == ('work', 'reference') and s in POINTS,
        h242o=lambda w, ref, left, right: (w, ref) == ('work', 'reference') and (
            variant != 'harmful' or left not in ('on_a', 'on_b') or right in ('on_a', 'on_b')),
        h242p=lambda *args: prefix(args) and args[5] == 'method' and variant != 'unavailable',
        h242q=lambda *args: prefix(args) and args[5:] == ('method', 'on_a'),
        h242r=lambda *args: prefix(args) and args[5:] == ('method', 'on_a'),
        cg=lambda p, a, s: (p, a) == ('person', 'activity') and s in ('on_a', 'on_b'),
        sc=lambda w, s: (w, s) == ('writing', 'on_a'),
        hzwr=lambda record, w, s: (record, w, s) == ('record', 'writing', 'on_a'),
        hzws=lambda record, carrier, s: (record, carrier, s) == (
            'other' if variant == 'split_record' else 'record', 'carrier', 'on_a'),
        hzwt=lambda record, s: variant != 'unreadable' and (record, s) == ('record', 'on_a'))
    return v


@lru_cache(None)
def result_checks():
    doc, rows = fixture('result'), {}
    for variant in ('baseline', 'split_record', 'unreadable', 'harmful', 'unavailable'):
        log = set()
        v = result_model(doc, variant, log)
        actual = evaluate(doc, v, DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual[0]
        assert log and all(row[:4] == ('person', 'activity', 'work', 'reference') and row[4] in SCENES for row in log)
        assert any(row[4:] == ('start', 'method') for row in log)
        assert not v['sc']('writing', 'reference') and not v['sc']('writing', 'start')
    return dict(contrasts=rows, native_ability_causal_comparison_and_records=True,
                written_record_required_only_in_possible_execution_results=True,
                baseline_distinct_from_start=True)


@lru_cache(None)
def binding_checks():
    doc, rows = fixture('bindings'), {}
    for variant in ('baseline', 'different_methods', 'record_in_different_method'):
        v, calls = result_model(doc), []
        def causal(person, activity, work, start, variables, equations, factor, view, checked, atleast):
            assert (person, activity, work, start, variables.items, factor) == ('person', 'activity', 'work', 'start', ('factor', 'result'), 'factor')
            state = FunctionValue(('individual',), 'truth', lambda item: item == 'factor')
            assert not equations('result', state)
            assert view(state) == 'on_a'
            assert checked('work', 'start', 'on_a') and not checked('other', 'start', 'on_a')
            assert atleast('work', 'start', 'on_a', 'off_a')
            calls.append('causal')
            return True
        def capable(person, activity, method, start, variables, equations, factor, view, available, outcomes, selected):
            if start != 'start':
                return False
            assert (person, activity, start) == ('person', 'activity', 'start')
            assert available('person', 'method', 'start') and not available('other', 'method', 'start')
            assert outcomes('person', 'method', 'start', 'on_a') and not outcomes('person', 'method', 'reference', 'on_a')
            assert selected('person', 'method', 'start', 'on_a') and not selected('person', 'method', 'start', 'off_a')
            calls.append(('method', method))
            return method == 'method'
        def written(writing, variables, equations, factor, view):
            assert writing == 'writing'
            state = FunctionValue(('individual',), 'truth', lambda item: item == 'factor')
            calls.append('written')
            return view(state) == ('on_b' if variant == 'record_in_different_method' else 'on_a')
        # Expose the selected method in the model's view, so split-method checks
        # inspect actual capture rather than trusting three independent flags.
        v['h242m'] = lambda p, a, w, ref, start, m, s: 'on_a' if m == 'method' else 'on_b'
        def causal_bound(*args):
            if args[3] != 'start':
                return False
            state = FunctionValue(('individual',), 'truth', lambda item: item == 'factor')
            view = args[7]
            if view(state) == 'on_a':
                causal(*args)
            return view(state) == ('on_b' if variant == 'different_methods' else 'on_a')
        v.update(r3u=causal_bound, r3v=capable, r3y=written)
        actual = evaluate(doc, v, DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        assert calls
        rows[variant] = actual[0]
    return dict(contrasts=rows, inspected_provider_and_callback_arguments=True,
                boundaries=['r3u/r3v/r3y are typed boundaries here; separate result checks execute all three natively.'])


@lru_cache(None)
def quantifier_checks():
    doc, rows = fixture('quantifier'), {}
    # Two values independently range over every one of the nine argument slots.
    first = ('x',) * 9
    second = ('y',) * 9
    mixed = ('x', 'y', 'y', 'x', 'y', 'y', 'x', 'x', 'y')
    for variant in ('empty_antecedent', 'one_success', 'one_failure', 'second_failure', 'wrong_baseline', 'wrong_evaluation', 'mixed_match', 'mixed_wrong_activity', 'mixed_wrong_work', 'mixed_wrong_writing'):
        v = base(doc)
        selected = set() if variant == 'empty_antecedent' else {first, second} if variant == 'second_failure' else {first}
        if variant.startswith('mixed_'):
            selected = {mixed}
        v['r32b'] = lambda *args: args[:-1] in selected and args[-1] == ('other' if variant == 'wrong_baseline' else 'reference')
        seen = set()
        def consequence(p, a, w, writing, ref):
            seen.add((p, a, w, writing, ref))
            good = variant not in ('one_failure',) and not (variant == 'second_failure' and p == 'y')
            if variant.startswith('mixed_'):
                wanted = [mixed[i] for i in (0,5,2,7)]
                if variant != 'mixed_match':
                    i = {'mixed_wrong_activity': 1, 'mixed_wrong_work': 2, 'mixed_wrong_writing': 3}[variant]
                    wanted[i] = 'x' if wanted[i] == 'y' else 'y'
                good = (p,a,w,writing) == tuple(wanted)
            return Content(SCENES, tuple(good and s == ('other' if variant == 'wrong_evaluation' else 'start') for s in SCENES))
        v['r32a'] = consequence
        actual = evaluate(doc, v, ('x', 'y'), SCENES, True)
        expected = variant in ('empty_antecedent', 'one_success', 'wrong_baseline', 'mixed_match')
        assert actual == [expected], (variant, actual)
        assert seen and all(ref == 'reference' for p, a, w, writing, ref in seen)
        rows[variant] = actual[0]
    return dict(contrasts=rows, independent_nine_argument_quantification=True,
                no_assertion_of_antecedent_existence=True,
                boundaries=['r32b and r32a are typed boundaries for quantifier composition; they are checked separately.'])


@lru_cache(None)
def focus_checks():
    from scripts.check_scholarly_self_ascription import self_model
    doc, rows = fixture('focus'), {}
    for variant in ('baseline', 'negative_ascription', 'other_ascribed_person', 'third_person_identification'):
        v = self_model(doc, variant=variant); v['zstart'] = lambda: 'start'
        actual = evaluate(doc, v, CIVIC_DOMAIN, SCENES, True)
        assert actual == [variant == 'baseline'] * 2, (variant, actual)
        rows[variant] = actual
    return dict(contrasts=rows, nonfactive_focus_content=True)


@lru_cache(None)
def discourse_checks():
    doc, rows = fixture('discourse'), {}
    for variant in ('baseline', 'wrong_prior', 'missing_acknowledgment', 'reversed_escalation', 'wrong_explanation', 'missing_partial_aspect', 'wrong_presentation'):
        v = base(doc)
        v.update(h242i=lambda: 'sentence', h242c=lambda: 'prior', wa=lambda: 'author', h232o=lambda: 'presentation')
        def header(n, a, code, ctx):
            return (n, a, symbol(code), code.rank, ctx) == ('sentence', 'author', 'r32f', 3,
                'other' if variant == 'wrong_presentation' else 'presentation')
        v.update(h236i=header,
            h242b=lambda *args: variant != 'missing_acknowledgment' and header(*args),
            h236k=lambda n,a,prior,old,current,new,dimension,ctx: header(n,a,new,ctx) and (
                prior, symbol(old), old.rank, current, symbol(dimension)) == (
                'other' if variant == 'wrong_prior' else 'prior', 'r3n', 3, 'sentence', 'r2zg'),
            h242s=lambda n,a,outer,scope,first,second,ctx: header(n,a,outer,ctx) and (
                symbol(scope), symbol(first), symbol(second)) == ('r3r',
                'r32i' if variant == 'reversed_escalation' else 'r32h', 'r32i'),
            h242t=lambda n,a,outer,scope,first,second,ctx: header(n,a,outer,ctx) and (
                symbol(scope), symbol(first), symbol(second)) == ('r32b', 'r32c',
                'r32e' if variant == 'wrong_explanation' else 'r32d'),
            h242u=lambda n,a,outer,scope,part,ctx: variant != 'missing_partial_aspect' and header(n,a,outer,ctx) and (
                symbol(scope), symbol(part)) == ('r32b', 'r32e'),
            ue=lambda a,b,ctx: (a,b,ctx) == ('prior','sentence','presentation'))
        actual = evaluate(doc, v, DOMAIN + ('author','sentence','prior'), SCENES, True)
        assert actual == [variant == 'baseline'], (variant, actual)
        rows[variant] = actual[0]
    for name in ('h242s','h242t','h242u'):
        # Reuse the otherwise total presentation model; unknown is not false.
        test = dict(v); test[name] = unknown
        try:
            evaluate(doc, test, DOMAIN + ('author','sentence','prior'), SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, content_and_models_not_executed=True, rank_three_content_preserved=True,
                unknown_discourse_inputs_refused=3)


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    parts = [
        ('So fern sich ', ['r32b', 'r32f'], '自己理解と学識者としての活動の立場にある限りという条件。'),
        ('aber ', ['h236k', 'r32g'], '前文の職務内の制約と、同じ人の別の立場を対照する。'),
        ('dieser Theil der Maschine ', ['r3m', 'h237h', 'r32e'], '先行する同じ機構の担当成員への照応。'),
        ('zugleich ', ['r32b', 'r32c', 'r32e'], '同じ本人・基準で職務上の位置付けと自己理解を併存させる。'),
        ('als Glied eines ganzen gemeinen Wesens, ', ['r3p', 'r32h', 'h237i'], '同じ事務の共同体全体の成員としての内容。'),
        ('ja sogar der Weltbürgergesellschaft ', ['r3q', 'r32i', 'h242s'], '国家を越える市民社会への成員性まで進める取り立て。'),
        ('ansieht, ', ['r3r', 'fa', 'h242d', 'h242h'], '本人が一人称として自分を捉えて肯定する。真理は実行しない。'),
        ('mithin ', ['h242t', 'r32c', 'r32d'], '同じ自己理解を学識者としての活動の立場で説明する。'),
        ('in der Qualität eines Gelehrten, ', ['r3z', 'r2zi', 'cb', 'cd'], '職業免許ではなく、同じ本人が学識者の立場で理性を使用する活動候補。'),
        ('der sich an ein Publikum im eigentlichen Verstande ', ['r3z', 'cc', 'ce'], '同じ活動が向かう、本来の全読者世界としての公衆。'),
        ('durch Schriften wendet; ', ['h242g', 'r3y', 'r3z', 'sc', 'sd'], '同じ作品を介して向ける活動構成と、可能な実行結果での記録。'),
        ('kann er ', ['r32a', 'r3v', 'xd'], '同じ本人の同じ活動を一つの方法で実行できるという可能性。'),
        ('allerdings ', ['h242b', 'r32g'], 'この限定された可能性を確かに認める取り立て。'),
        ('räsonniren, ', ['h232p', 'r32d', 'zzq'], '同じ理性による言語的検討の活動の実行。'),
        ('ohne daß dadurch die Geschäfte leiden, ', ['r32a', 'r3u', 'hze', 'r2vh'], '同じ方法の実行によって、同じ事務の遂行が悪化しない因果的留保。'),
        ('zu denen er ', ['r3m', 'h237f', 'r32e'], '同じ人が割り当てられた同じ事務への照応。'),
        ('zum Theile ', ['h242u', 'r32e'], '職務をその人のある側面へ限定する。'),
        ('als passives Glied angesetzt ist.', ['h237d', 'h237e', 'h237f', 'r3m', 'r32e'], '先行する受動的遂行の役割への割当てを受ける。実際の服従は断言しない。'),
    ]
    cursor, clauses = 1743, []
    for text, names, meaning in parts:
        assert unit['text'][cursor:cursor + len(text)] == text, (cursor, text)
        clauses.append(dict(range=[cursor, cursor + len(text)], text=text, definitions=names, reading=meaning))
        cursor += len(text)
    assert cursor == 2122
    text = unit['text'][1743:2122]
    count = sum(not c.isspace() for c in text)
    return dict(status='scholarly_compatibility_sentence_reviewed_under_explicit_reading', reviewer='assistant_review',
        document=FULL, meaning_basis=BASIS,
        source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[1743,2122], text=text),
        selection=selection_binding(catalog(), [81]), clauses=clauses, interpretation=LIMITS, unresolved=[],
        decision='equivalent_under_stated_reading_for_the_conditional_scholarly_compatibility_sentence',
        whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
        newly_reviewed_sentence_characters=count, preserved_reviewed_sentence_characters=1491,
        paragraph_reviewed_sentence_characters=1491 + count, semantic_equivalence_automatically_proved=False,
        holistic_review=[
            '原刊485頁で前文の禁止からSo fernの条件、末尾の受動的成員への照応まで再読した。条件の範囲、同じ本人・共同体・職務・活動・作品を通して確認した。',
            '自己理解を事実的な成員性へ、世界市民社会を世界政府へ、学識者を免許の保有へ置き換えていない。',
            '活動候補の書面への経路と、その実行結果内での作品・記録を分け、刊行済み作品を前件へ追加する過剰条件を避けた。',
            'kannを実践的な両立可能性と読むことを明示し、前文の禁止と先行する公的自由の規範的主張は保持した。職務内の禁止を個別許可へ撤回していない。',
            '実行・非実行の比較、事務の評価、利用可能性と結果の全解との一致、書面の存在は一つの方法に束縛した。安全な方法と実行可能な方法の取り違えを許さない。',
            'ja sogar、mithin、aber、allerdingsを同じ引用内容の中で提示し、zugleichとzum Theileを同じ人の役割の併存と部分的な側面への限定として保持した。',
            '全解の非悪化と活動類型の条件的一般化は採用した明示解釈であり、因果の現実的な正しさや原文の唯一の読解を証明したとはしない。'],
        original_page=dict(path=IMAGE,page=485,visually_inspected=True),
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in (FULL,BASIS,ANNOTATIONS,DOC,INVENTORY,IMAGE,*PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new, lib = parent(), catalog(), dependency()
    assert new.document['statements'][:81] == old.document['statements']
    assert len(new.document['statements']) == 82
    assert all(new.entries[n] == e for n,e in old.entries.items())
    for n,e in lib.entries.items():
        assert new.entries[n]['declaration'] == e['declaration']
        assert new.entries[n]['meaning_ja'] == e['meaning_ja']
    reviews = load_reviews(ROOT,INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new,[s['index'] for s in row['selection']['statements']])
    for path in PRIOR:
        validate_hashes(ROOT,read(path)['source_sha256'])
    prior = read('data/office-obedience-reading-v1.json')
    assert prior['selection'] == selection_binding(new,[80])
    validate_hashes(ROOT,prior['source_sha256'])
    assert read(AUDIT) == reading()
    for path,body in build().items():
        assert (ROOT/path).read_text(encoding='utf-8') == body
    for path in (FULL,CORE):
        doc=parse((ROOT/path).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation)
            assert parse(text) == parse(transcribe(text,alphabet='v2')) == doc
    return dict(preserved_statements=81,added_statements=1,preserved_whole_unit_reviews=len(reviews),
                old_meanings_unchanged=True, new_reviewed_sentence_characters=323,roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path,body in build().items():
        write_exact(ROOT/path,body)
    write_exact(ROOT/AUDIT,encoded(reading()))


def build_report():
    results={}
    for name,fn in [('premise',premise_checks),('result',result_checks),('bindings',binding_checks),
                    ('quantifier',quantifier_checks),('focus',focus_checks),('discourse',discourse_checks),('structure',structure_checks)]:
        results[name]=fn(); print(name+' checked',flush=True)
    paths=set(build()) | set(catalog().source_sha256) | {
        INDEX,AUDIT,DOC,INVENTORY,IMAGE,*PRIOR,'data/office-obedience-reading-v1.json',
        'scripts/compose_scholarly_compatibility.py','scripts/check_scholarly_compatibility.py','tests/test_scholarly_compatibility.py',
        'scripts/compose_nonimpairing_reasoning.py','scripts/check_nonimpairing_reasoning.py',
        'scripts/check_scholarly_self_ascription.py','scripts/compose_grounded_step.py',
        'scripts/compose_qualitative_influence.py','scripts/check_pastoral_roles.py','scripts/check_motive_causes.py'}
    return dict(status='conditional_scholarly_reasoning_without_work_impairment',document=FULL,**results,
        alignment=dict(**read(AUDIT)['source'],statements=[81],definitions=list(MEANINGS),status='explicit_interpretive_annotation'),
        whole_sentence_semantically_verified=True,whole_unit_semantically_verified=False,
        verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})
