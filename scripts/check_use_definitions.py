"""Check shared role classifications and the two nonfactive definition acts."""
from copy import deepcopy
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.review_registry import load_reviews
from noema.semantic_reviews import digest, selection_binding, validate_hashes
from noema.script import transcribe
from scripts.compose_use_definitions import (
    ROOT, FULL, CORE, BASIS, ANNOTATIONS, MEANINGS, LIMITS, parent, build, closure)
from scripts.check_pastoral_roles import evaluate
from scripts.check_motive_causes import unknown, symbol

INDEX = 'data/semantic-review-index-v161.json'
REPORT = 'reports/use-definitions-v1.json'
AUDIT = 'data/use-definitions-reading-v1.json'
DOC = 'docs/use-definitions-v1.md'
EVIDENCE = 'data/use-definitions-evidence-v1.json'
INVENTORY = 'artifacts/written-units-v1/kant-1784.json'
IMAGE = 'artifacts/answer-discourse-v1/page-485.jpg'
PRIOR = 'reports/answer-discourse-v1.json'
PEOPLE = ('person', 'otherperson', 'activity', 'otheractivity', 'role', 'otherrole', 'audience', 'otheraudience')
SCENES = ('reference', 'other')
NODES = ('author', 'answer', 'publicdef', 'privatedef', 'publicterm', 'privateterm', 'other')
CONTEXTS = ('presentation', 'reference')


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


@lru_cache(None)
def catalog():
    return load_catalog(ROOT, BASIS)


@lru_cache(None)
def fixture(kind):
    doc = deepcopy(catalog().document)
    roots = ['r2zi', 'r2zj', 'zzo', 'zzp', 'r2zm'] if kind == 'classification' else ['r2zk', 'r2zl']
    doc.update(declarations=closure(doc, roots), statements=[])
    if kind == 'classification':
        extra = 'r zp[] a.r za[] a.r zr[] a.r zref[] d.'
        query = ''.join('q[k ' + n + '[k zp[] k za[] k zr[] k zref[]]].' for n in roots)
    else:
        extra, query = '', 'q[k r2zk[]].q[k r2zl[]].'
    return parse(format_graph(doc, 'compact') + extra + query)


def classification_model(doc, flags=(True,) * 7, variant='baseline'):
    human, reason, acting, scholar, directed, world, entrusted = flags
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update(zp=lambda: 'person', za=lambda: 'activity', zr=lambda: 'role', zref=lambda: 'reference',
        aa=lambda person: human and person == 'person',
        ca=lambda person, activity, reference: reason and (person, activity, reference) == (
            'otherperson' if variant == 'other_person_reason' else 'person', 'activity', 'reference'),
        cb=lambda person, activity, role, reference: acting and (person, activity, role, reference) == (
            'person', 'otheractivity' if variant == 'other_activity_role' else 'activity',
            'otherrole' if variant == 'other_role' else 'role',
            'other' if variant == 'other_reference' else 'reference'),
        cd=lambda role, reference: scholar and (role, reference) == (
            'otherrole' if variant == 'scholar_in_another_role' else 'role', 'reference'),
        cc=lambda activity, audience, reference: directed and (activity, audience, reference) == (
            'otheractivity' if variant == 'other_addressed_activity' else 'activity', 'audience', 'reference'),
        ce=lambda audience, reference: world and (audience, reference) == (
            'otheraudience' if variant == 'split_audiences' else 'audience', 'reference'),
        cf=lambda person, role, reference: entrusted and (person, role, reference) == (
            'otherperson' if variant == 'office_entrusted_to_other' else 'person',
            'otherrole' if variant == 'other_entrusted_role' else 'role', 'reference'))
    return v


@lru_cache(None)
def classification_checks():
    doc, cases = fixture('classification'), []
    for flags in product((False, True), repeat=7):
        human, reason, acting, scholar, directed, world, entrusted = flags
        public = reason and acting and scholar and directed and world
        private = reason and acting and entrusted
        actual = evaluate(doc, classification_model(doc, flags), PEOPLE, SCENES, True)
        assert actual == [human and public, human and private, public, private, acting and scholar]
        cases.append(dict(flags=list(flags), new_public_private_old_public_private_focus=actual))
    rows = {}
    public_only_fail = {'scholar_in_another_role', 'other_addressed_activity', 'split_audiences'}
    private_only_fail = {'office_entrusted_to_other', 'other_entrusted_role'}
    for variant in ('baseline', 'other_person_reason', 'other_activity_role', 'other_role', 'other_reference',
                    *sorted(public_only_fail), *sorted(private_only_fail)):
        actual = evaluate(doc, classification_model(doc, variant=variant), PEOPLE, SCENES, True)
        expected = [True, True] if variant == 'baseline' else [False, True] if variant in public_only_fail else (
            [True, False] if variant in private_only_fail else [False, False])
        assert actual[:4] == expected * 2, (variant, actual)
        rows[variant] = actual[:2]
    for name in ('aa', 'ca', 'cb', 'cc', 'cd', 'ce', 'cf'):
        v = classification_model(doc); v[name] = unknown
        try:
            evaluate(doc, v, PEOPLE, SCENES, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    assert not {'h7a', 'h7b', 'de'} & {d['name'] for d in doc['declarations']}
    return dict(combinations=cases, contrasts=rows, unknown_inputs_refused=7,
                no_exclusive_or_exhaustive_partition=True,
                actual_execution_and_token_permission_not_classification_conditions=True,
                semantic_boundaries=[])


def discourse_model(doc, variant='baseline'):
    v = {d['name']: unknown for d in doc['declarations'] if d['kind'] == 'primitive'}
    v.update(wa=lambda: 'author', h232o=lambda: 'presentation', h235p=lambda: 'answer',
             h236p=lambda: 'publicterm', h236q=lambda: 'publicterm' if variant == 'collapsed_terms' else 'privateterm',
             h236r=lambda: 'publicdef', h236s=lambda: 'publicdef' if variant == 'collapsed_definition_nodes' else 'privatedef')
    def definition(node, author, term, code, context):
        expected = {'publicdef': ('publicterm', 'r2zi'), 'privatedef': ('privateterm', 'r2zj')}
        if node not in expected:
            return False
        wanted_term, wanted_code = expected[node]
        if variant == 'public_uses_private_class' and node == 'publicdef':
            wanted_code = 'r2zj'
        if variant == 'private_uses_public_class' and node == 'privatedef':
            wanted_code = 'r2zi'
        return (variant != 'missing_public_self_definition' or node != 'publicdef') and (
            variant != 'missing_private_self_definition' or node != 'privatedef') and (
            author, term, symbol(code), code.rank, context) == (
            'other' if variant == 'wrong_author' else 'author', wanted_term, wanted_code, 0,
            'reference' if variant == 'wrong_context' else 'presentation')
    def remit(node, author, classification, basis, context):
        return variant != 'missing_normative_remit' and (
            node, author, symbol(classification), classification.rank, symbol(basis), basis.rank, context) == (
            'privatedef', 'author', 'r2zi' if variant == 'wrong_remit_class' else 'r2zj', 0,
            'cd' if variant == 'wrong_remit_basis' else 'cf', 0, 'presentation')
    def clarification(node, author, prior, content, term, classification, context):
        return variant != 'missing_clarification' and (
            node, author, prior, symbol(content), content.rank, term, symbol(classification), classification.rank, context) == (
            'publicdef', 'author', 'other' if variant == 'wrong_antecedent' else 'answer',
            'r2z5' if variant == 'partial_antecedent' else 'r2zf', 3, 'publicterm', 'r2zi', 0, 'presentation')
    def order(first, last, context):
        pairs = {('answer', 'publicdef'), ('publicdef', 'privatedef')}
        if variant == 'wrong_order':
            pairs.remove(('publicdef', 'privatedef'))
        return context == 'presentation' and (first, last) in pairs
    def focus(node, author, classification, condition, context):
        return variant != 'missing_scholar_focus' and (
            node, author, symbol(classification), classification.rank, symbol(condition), condition.rank, context) == (
            'publicdef', 'author', 'r2zi', 0, 'r2zj' if variant == 'wrong_focus' else 'r2zm', 0, 'presentation')
    v.update(h236o=definition, h236t=remit, h236u=clarification, h236v=focus, ue=order)
    return v


@lru_cache(None)
def discourse_checks():
    doc, rows = fixture('discourse'), {}
    first = {'missing_public_self_definition', 'public_uses_private_class', 'missing_clarification',
             'wrong_antecedent', 'partial_antecedent', 'missing_scholar_focus', 'wrong_focus'}
    second = {'missing_private_self_definition', 'private_uses_public_class', 'missing_normative_remit',
              'wrong_remit_class', 'wrong_remit_basis', 'wrong_order', 'collapsed_terms', 'collapsed_definition_nodes'}
    for variant in ('baseline', *sorted(first), *sorted(second), 'wrong_author', 'wrong_context'):
        actual = evaluate(doc, discourse_model(doc, variant), NODES, CONTEXTS, True)
        expected = [True, True] if variant == 'baseline' else [False, True] if variant in first else (
            [True, False] if variant in second else [False, False])
        assert actual == expected, (variant, actual)
        rows[variant] = actual
    for name in ('h236o', 'h236t', 'h236u', 'h236v', 'ue'):
        v = discourse_model(doc); v[name] = unknown
        try:
            evaluate(doc, v, NODES, CONTEXTS, True)
        except ValueError as error:
            assert 'Unknown' in str(error)
        else:
            raise AssertionError(name)
    return dict(contrasts=rows, unknown_discourse_inputs_refused=5,
                classification_and_answer_unknown_and_unexecuted=True,
                normative_remit_separate_from_current_token_permissions=True, semantic_boundaries=[])


def reading():
    unit = next(u for u in read(INVENTORY)['units'] if u['id'] == 'kant-1784:u0012')
    groups = [
        (981, [
            ('Ich verstehe ', ['h236o', 'r2zk'], '著者自身がこの論説での理解・用語の使い方として明示する。'),
            ('aber ', ['h236u', 'r2zk'], '先行回答を受け、使った語を明確にする説明への転換。'),
            ('unter dem öffentlichen Gebrauche ', ['h236p', 'r2zi'], '定義対象の語と合成された公的使用分類を結ぶ。'),
            ('seiner eigenen Vernunft ', ['ca', 'r2zi'], '各本人自身の理性の使用。別人の理性への照応にしない。'),
            ('denjenigen, den jemand ', ['aa', 'r2zi'], 'ある特定者の実例ではなく、人を引数とする活動類型の定義。'),
            ('als Gelehrter ', ['cb', 'cd', 'zzo', 'r2zm', 'h236v'], 'この活動で学識者として振る舞う立場を強調する。職業の資格だけでは足りず、この条件だけで公的使用に十分とはしない。'),
            ('von ihr ', ['ca', 'r2zi'], '同じ本人の理性を受ける。'),
            ('vor dem ganzen Publikum der Leserwelt ', ['cc', 'ce', 'zzo'], '活動を全読者世界へ向ける。全員による受領は要求しない。'),
            ('macht.', ['ca', 'cb', 'r2zi'], '定義で取り上げる理性使用の活動類型。現実の特定の実行例の存在を主張しない。'),
        ]),
        (1146, [
            ('Den Privatgebrauch ', ['h236q', 'r2zj'], '定義対象の私的使用という語を合成分類へ結ぶ。'),
            ('nenne ich ', ['h236o', 'r2zl'], '著者自身がそう呼ぶと明示する定義の提示。'),
            ('denjenigen, den er ', ['aa', 'ca', 'r2zj'], '同じ本人の理性使用を活動引数で受ける。'),
            ('in einem gewissen ihm anvertrauten bürgerlichen Posten, oder Amte, ', ['cb', 'cf', 'zzp'], '同じ本人に委ねられた特定の市民的な立場・職務での使用。両職の同時所有や排他的選言ではない。'),
            ('von seiner Vernunft ', ['ca', 'r2zj'], '同じ本人自身の理性への照応を保持する。'),
            ('machen darf.', ['h236t', 'cf', 'r2zl'], '委任に伴って与えられる職務上の使用の範囲という規範的限定。個々の指示への適合や無条件の現時点の実行許可に置き換えない。'),
        ]),
    ]
    clauses = []
    for start, parts in groups:
        cursor = start
        for text, names, interpretation in parts:
            assert unit['text'][cursor:cursor + len(text)] == text, (cursor, text)
            assert all(n in catalog().entries for n in names)
            clauses.append(dict(range=[cursor, cursor + len(text)], text=text, definitions=names, reading=interpretation))
            cursor += len(text)
        assert cursor == (1145 if start == 981 else 1293)
    text = unit['text'][981:1293]
    assert sum(not c.isspace() for c in text) == 268
    validate_hashes(ROOT, read(EVIDENCE)['source_sha256'])
    return dict(status='use_definition_pair_reviewed_under_explicit_reading', reviewer='assistant_review',
                document=FULL, meaning_basis=BASIS,
                source=dict(unit=unit['id'], unit_sha256=unit['text_sha256'], range=[981, 1293], text=text),
                sentence_ranges=[[981, 1145], [1146, 1293]], clauses=clauses,
                selection=selection_binding(catalog(), [76, 77]), interpretation=LIMITS, unresolved=[],
                decision='equivalent_under_stated_reading_for_the_definition_pair',
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                source_nonblank_characters=268, newly_reviewed_sentence_characters=268,
                preserved_reviewed_sentence_characters=838, paragraph_reviewed_sentence_characters=1106,
                semantic_equivalence_automatically_proved=False,
                holistic_review=[
                    '両文は用語についての著者自身の定義の提示であり、一般的な人・活動・立場・基準の分類を引用する。現実の使用者の存在へ交換していない。',
                    '同じ本人・理性・活動・立場の照応を保ち、学識者として全読者世界へ向ける使用と、委ねられた市民的職務での使用を対比可能な分類として構成した。',
                    '公的と私的が排他的または全活動を尽くすとはしていない。公衆全体という宛先と全員による実際の受領、学識者という立場と職業名を区別した。',
                    'darfを委任に伴う職務上の権限の範囲として明示し、当該語を省かず、個々の指示・禁止が分類を出入りさせる循環を避けた。別の読みとの相違は限界欄へ記した。',
                    'aber、verstehe、nenne ichの働きを、先行回答と同じ著者・提示文脈へ結んだ。定義から先行する規範主張の正しさを導いていない。',
                ],
                original_page=dict(path=IMAGE, page=485, visually_inspected=True),
                references=[read(EVIDENCE)['source']['url'], read(EVIDENCE)['facsimile']['url']],
                source_sha256={p: digest((ROOT / p).read_bytes())
                               for p in (FULL, BASIS, ANNOTATIONS, DOC, EVIDENCE, INVENTORY, IMAGE, PRIOR)})


@lru_cache(None)
def structure_checks():
    old, new = parent(), catalog()
    assert new.document['statements'][:76] == old.document['statements']
    assert len(new.document['statements']) == 78
    assert all(new.entries[n] == entry for n, entry in old.entries.items())
    reviews = load_reviews(ROOT, INDEX)['works']['kant-1784']
    for row in reviews:
        assert row['selection'] == selection_binding(new, [s['index'] for s in row['selection']['statements']])
    for path, indices in (('data/question-discourse-reading-v1.json', [70, 71]),
                          ('data/answer-discourse-reading-v1.json', [72, 73, 74, 75])):
        record = read(path)
        assert record['selection'] == selection_binding(new, indices)
        validate_hashes(ROOT, record['source_sha256'])
    validate_hashes(ROOT, read(PRIOR)['source_sha256'])
    assert read(AUDIT) == reading()
    for path, body in build().items():
        assert (ROOT / path).read_text(encoding='utf-8') == body
    for path in (FULL, CORE):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        for notation in ('compact', 'full'):
            text = format_graph(doc, notation)
            assert parse(text) == parse(transcribe(text, alphabet='v2')) == doc
    return dict(preserved_statements=76, added_statements=2, preserved_whole_unit_reviews=len(reviews),
                preserved_reviewed_sentence_characters=838, new_reviewed_sentence_characters=268,
                old_meanings_unchanged=True, roundtrips=True)


def prepare():
    from scripts.audit_opening_scope import write_exact, encoded
    for path, body in build().items():
        write_exact(ROOT / path, body)
    write_exact(ROOT / AUDIT, encoded(reading()))


def build_report():
    results = {}
    for name, fn in [('classifications', classification_checks), ('discourse', discourse_checks),
                     ('structure', structure_checks)]:
        results[name] = fn()
        print(name + ' checked', flush=True)
    paths = set(build()) | set(catalog().source_sha256) | {
        INDEX, AUDIT, DOC, EVIDENCE, INVENTORY, IMAGE, PRIOR, 'scripts/compose_use_definitions.py',
        'scripts/check_use_definitions.py', 'scripts/compose_grounded_step.py', 'scripts/compose_qualitative_influence.py',
        'scripts/check_pastoral_roles.py', 'scripts/check_motive_causes.py', 'tests/test_use_definitions.py',
        'data/question-discourse-reading-v1.json', 'data/answer-discourse-reading-v1.json'}
    return dict(status='public_private_use_definitions_under_explicit_reading', document=FULL, **results,
                alignment=dict(**read(AUDIT)['source'], statements=[76, 77], status='explicit_interpretive_annotation'),
                whole_sentence_semantically_verified=True, whole_unit_semantically_verified=False,
                verified_full_units={'kant-1784': 0, 'einstein-1905': 0},
                source_sha256={p: digest((ROOT / p).read_bytes()) for p in sorted(paths)})
