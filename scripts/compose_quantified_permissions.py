"""Connect per-person obligation catalogues and every eligible action description."""
from copy import deepcopy
import json
from pathlib import Path

from noema.extraction import extract_document
from noema.grammar import parse as old_parse
from noema.ranked import parse, format_graph, promote
from scripts.compose_origin_clock import definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params
from scripts.compose_described_norms import DESCRIPTION, RULE, TRUE

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'examples/v014/kant-unrestricted-others.noema'
SOURCE = 'examples/v015/kant-quantified-permissions.noema'
CORE = 'examples/v015/quantified-permissions-core.noema'
BASIS = 'data/quantified-permissions-basis-v1.json'
CATALOGUE = [('officeroles', 'h[a a d] c'), ('items', 'h[a a d] c'),
    ('issuers', 'h[a a d] a'), ('offices', 'h[a a d] a'), ('actions', 'h[a a d] a'),
    ('descriptions', 'h[a a d] ' + DESCRIPTION), ('signs', 'h[a a d] c'),
    ('cases', 'h[a a ' + DESCRIPTION + ' d d] c')]
POINT = [('person', 'a'), ('activity', 'a'), ('target', DESCRIPTION), ('anchor', 'd')] + CATALOGUE + [('required', RULE)]
CLAIM = [('population', 'h[a d] c'), ('excluded', 'h[a d] c'),
    ('activities', 'h[a a ' + DESCRIPTION + ' d] c'), ('authority', 'a'), ('roles', 'h[a d] a'),
    ('anchor', 'd')] + CATALOGUE + [('required', RULE), ('permitted', RULE)]
FIXED = [(name, type_) for name, type_ in CLAIM if name not in ('anchor', 'required', 'permitted')]
REFERENCES = {name: 'hzj' + chr(ord('a') + index) for index, (name, _) in enumerate(FIXED)}


def definitions():
    entries = ['i[item a][' + app(v(name), v('person'), v('item'), v('anchor')) + ']'
               for name, _ in CATALOGUE[:-1]]
    trigger = app('s[v target]', v('person'), v('activity'))
    candidates = 'i[point d][' + app(v('cases'), v('person'), v('activity'), v('target'), v('anchor'), v('point')) + ']'
    text = definition('rpt', params(POINT), k('rpq', v('person'), v('anchor'), *entries, v('required'), trigger, candidates))
    nonrestriction = k('rpt', *(v(name) for name, _ in POINT))
    eligible = both(app(v('population'), v('person'), v('anchor')),
        op('u', app(v('excluded'), v('person'), v('anchor'))),
        app(v('activities'), v('person'), v('activity'), v('target'), v('anchor')), nonrestriction)
    permission = k('rdm', v('authority'), v('person'), app(v('roles'), v('person'), v('anchor')),
        v('activity'), v('target'), TRUE, v('anchor'), v('required'), v('permitted'))
    body = op('y', eligible, permission)
    for name, type_ in reversed(POINT[:3]):
        body = quant('f', name, type_, body)
    return text + definition('rpu', params(CLAIM), body)


def source_additions():
    text = definitions()
    for name, type_ in FIXED:
        # A fixed interpretation parameter can be a higher-order function value.
        text += 'r ' + REFERENCES[name] + '[] ' + type_ + '.'
    text += 'r hzjn[a a i b[e] a d] c.r hzjo[] a.r hzjp[] a.'
    arguments = {name: k(REFERENCES[name]) for name, _ in FIXED}
    arguments.update(anchor=v('context'), required='p h7a', permitted='p h7b')
    text += definition('hzjq', '', 'b context[' + k('rpu', *(arguments[name] for name, _ in CLAIM)) + ']', 'e')
    text += definition('hzjr', '', k('hzjn', k('hzjo'), k('wa'), 'r b[k hzjq[]]', k('hzjp'), k('wh')))
    return text


def build_documents():
    parent = old_parse((ROOT / PARENT).read_text(encoding='utf-8'))
    additions = source_additions()
    full = promote(parent)
    statements, full['statements'] = full['statements'], []
    full = parse(format_graph(full, 'compact') + additions + 's[k hzjr[]].')
    full['statements'] = statements + full['statements']
    core = extract_document(parent, roots=['rpq', 'rdm', 'h7a', 'h7b', 'wa', 'wh'], statement_indices=[]).document
    core = parse(format_graph(promote(core), 'compact') + additions + 's[k hzjr[]].')
    return {SOURCE: format_graph(full, 'compact') + '\n', CORE: format_graph(core, 'compact') + '\n'}


def basis(documents):
    parent = old_parse((ROOT / PARENT).read_text(encoding='utf-8'))
    doc = parse(documents[SOURCE])
    prior = {d['name'] for d in parent['declarations']}
    meanings = {
        'population': '基準文脈における対象人口。実際の人々を同定する解釈は未確定。',
        'excluded': '同じ文脈で既に論じた対象群。単に話者本人を除く条件ではない。',
        'activities': '本人・活動・閉じた実行記述・基準文脈に対する、対象の公的提示の資格条件。現在は指定範囲であり、hzgyの一般化した内容との一致は未接続。',
        'authority': '当該許可の権限側を指す。原文の君主への照応の確定は未了。',
        'roles': '本人と基準文脈ごとの公的役割。学者の社会的意味の説明は未了。',
        'officeroles': '本人・役割・基準文脈について職務と数える範囲。実際の全職務を尽くすかは未確認。',
        'items': '本人・項目・基準文脈ごとの選択義務一覧。空を未知情報の代用にしない。',
        'issuers': '本人・一覧項目・基準文脈に対応する要求の出所。',
        'offices': '本人・一覧項目・基準文脈に対応する職務の役割。',
        'actions': '本人・一覧項目・基準文脈に対応する要求対象の活動。',
        'descriptions': '本人・一覧項目・基準文脈に対応する閉じた要求内容の記述。人ごとに異なる記述を許す。',
        'signs': '本人・一覧項目・基準文脈に対応する要求の肯否。',
        'cases': '本人・対象活動・同じ対象記述・基準文脈ごとの比較候補。全可能状況であるとは仮定しない。',
    }
    explanations = {REFERENCES[name]: text for name, text in meanings.items()}
    explanations.update(hzjn='発話箇所・著者・層1の内容記述・原文範囲・文脈に対する主張の帰属。内容の真理を含意しない。旧uhと型の異なる帰属規約で、両者の同一性は未証明。',
        hzjo='今回の部分的な一般許可の読みを対応させる発話箇所。', hzjp='カントu0015の他の対象者への許可に関する範囲。なおさらの論証は含まない。',
        rpt='同じ本人・活動・対象記述から実行内容を評価し、本人と基準文脈に応じた全義務の網羅性と候補排除の不在へ接続する。',
        rpu='本人・活動・対象記述の全組を量化し、対象範囲と無制約条件を満たす組について、同じ記述への積極的許可と反対要求の不在を要求する。',
        hzjq='rpuの要求と許可を既存h7a・h7bへ結び、文脈に依存する一般許可内容とする。',
        hzjr='hzjqの層1の引用を、既存の著者waと文脈wh、新しい発話箇所・原文範囲へ帰属する部分草案。')
    added = [deepcopy(d) for d in doc['declarations'] if d['name'] not in prior]
    if {d['name'] for d in added} != set(explanations):
        raise ValueError('Added declaration explanations differ')
    return dict(status='partial_parameterized_author_attribution_not_completed_translation',
        document=SOURCE, core_document=CORE, parent_document=PARENT,
        parent_basis='data/kant-unrestricted-others-basis-v1.json',
        additions=[dict(declaration=d, meaning_ja=explanations[d['name']]) for d in added],
        unresolved=['公的な提示の資格範囲activitiesと、判断・主張・吟味目的を結ぶhzgyの一般内容との一致は未接続。',
            '対象人口・既出の聖職者・学者の役割・君主への照応・基礎概念を指定値だけで説明したとは扱わない。',
            '義務記述と対象記述を全域量化する。有限検査は明示した四記述への具体化であり全域の意味確認ではない。',
            '層0の実行記述を対象とする型付きの読み。任意の引用層の義務を網羅したとの主張ではない。',
            'なおさらの論証と、前文の聖職者への許可全体は未接続。',
            '標準版に未採用の0.15の部分草案。新しい著者帰属文は原文との同義性を確認した文ではない。'])


def main():
    documents = build_documents()
    files = documents | {BASIS: json.dumps(basis(documents), ensure_ascii=False, indent=2) + '\n'}
    for name, text in files.items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != text:
                raise ValueError('Existing quantified permission artifact differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
        print(name, len(text), 'characters')


if __name__ == '__main__':
    main()
