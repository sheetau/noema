"""Distinguish plural qualified people from plural qualified subgroup members."""
from copy import deepcopy
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT, closure
from scripts.compose_thinking_disseminators import QUALIFIED, call, apply, conjunction, variable
from scripts.compose_described_dissemination import declaration

PARENT = 'examples/v016/kant-described-dissemination.noema'
PARENT_BASIS = 'data/described-dissemination-basis-v1.json'
FULL = 'examples/v016/kant-subgroup-dissemination.noema'
CORE = 'examples/v016/subgroup-dissemination-core.noema'
LIBRARY = 'examples/v016/qualified-subgroup.noema'
BASIS = 'data/subgroup-dissemination-basis-v1.json'
RENAMES = {'hzoh': 'hzos', 'hzoi': 'hzot', 'hzoj': 'hzou',
           'hzop': 'hzov', 'hzoq': 'hzow', 'hzor': 'hzox'}
MEANINGS = {
    'rqti': '同じ評価点で、母集団に属して指定条件を満たす異なる対象が二つ以上あり、その同じ該当範囲に部分集団の条件を満たす対象が一つ以上ある。部分集団外の該当対象の存在や、部分集団の該当対象が二つ以上あることは要求しない。対象を人に限定する条件は呼出側で別に与える。',
    'hzos': '母集団が人の範囲であることを検査し、rqtiの部分集団条件へ同じ人・同じ点での任用された後見役hzhbを渡す。全体の複数性と、後見役を含むことを分ける読解候補。',
    'hzot': 'hzoiと同じ非空の将来機会・履歴・順序の条件を保ち、各点の人数条件だけをhzosにする。点ごとの人物交替を許す。',
    'hzou': 'hzojと同じ全将来機会を内部で選び、hzotへ渡す。不成立の機会を除外せず、将来機会が空なら偽になる。',
    'hzov': 'hzopと同じ人・機会に独立判断、自己離脱、経路、受け手の性向取得を結ぶ内容。全将来機会の人数条件だけをhzouにする。',
    'hzow': 'hzoqと同じ閉じた33引数と階数1を保ち、hzovの内容記述を構成する。旧候補hzopとは別の内容記述として保持する。',
    'hzox': 'hzorと同じ非事実含意の帰属関係hzonへ、hzowの閉じた内容を渡す。旧候補への帰属や、内容の真偽から自動的に成立させない。',
}
LIMITS = [
    '旧版の「後見役の中に複数」という読解候補を変更・否定せず、「全体に複数、後見役にも一人以上」という別候補を明示する。原文の唯一の読みを決定したとはしない。',
    '部分集団の範囲は同じ母集団・同じ複合条件との交差で決める。無関係な後見役を加えて条件を満たしたことにしない。',
    'sogarの尺度・比較背景は、この存在条件だけでは表していない。二人という下限の適切さ、immerの機会範囲、自由の仮定への従属、Denn、比喩の読解は残る。',
    '既存32文と七単位の確認を保持する。新しい著者主張・原文対応範囲・意味確認済み単位は加算しない。',
]


def rename_calls(node):
    if isinstance(node, dict):
        return {k: RENAMES.get(v, v) if k == 'symbol' and isinstance(v, str)
                else rename_calls(v) for k, v in node.items()}
    if isinstance(node, list):
        return [rename_calls(v) for v in node]
    return node


def build():
    old = load_catalog(ROOT, PARENT_BASIS)
    doc = deepcopy(old.document)
    assert not set(MEANINGS) & set(old.entries)
    fields = [('point', 'd'), ('members', 'h[a d] c'), ('subgroup', 'h[a d] c'), ('qualified', 'h[a d] c')]
    # rpw requires two distinct witnesses to all three predicates. Here the
    # subgroup in that first count is unrestricted; its overlap is tested once.
    plural = call('rpw', 'v point', 'v members', 'i[person a context d][e[v person][v person]]', 'v qualified')
    overlap = 'g person a[' + conjunction(*(apply(n, 'v person', 'v point') for n in ('members', 'subgroup', 'qualified'))) + ']'
    text = declaration('rqti', fields, 'c', conjunction(plural, overlap))
    human = 'f person a[y[' + apply('members', 'v person', 'v point') + '][' + call('aa', 'v person') + ']]'
    status = 'i[person a context d][' + call('hzhb', 'v person', 'v governed', 'v context', 'v appoints', 'v guardianrole') + ']'
    text += declaration('hzos', [('point', 'd')] + QUALIFIED, 'c', conjunction(human,
        call('rqti', 'v point', 'v members', status, 'v qualified')))
    statements = doc['statements']; doc['statements'] = []
    size = len(doc['declarations'])
    doc = parse(format_graph(doc, 'compact') + text)
    lookup = {d['name']: d for d in old.document['declarations']}
    for source in ('hzoi', 'hzoj', 'hzop', 'hzoq', 'hzor'):
        row = rename_calls(deepcopy(lookup[source])); row['name'] = RENAMES[source]
        doc['declarations'].append(row)
    doc['statements'] = statements
    doc = parse(format_graph(doc, 'compact'))
    core = deepcopy(doc); core['statements'] = []
    core['declarations'] = closure(doc, ['hzox', 'hzor', 'hzny', 'rqsx'])
    library = deepcopy(core); library['declarations'] = closure(doc, ['hzou', 'hzoj'])
    basis = dict(status='explicit_plural_population_and_subgroup_overlap_candidate', document=FULL,
        parent=PARENT, inherited_meaning_basis=PARENT_BASIS, primitives={}, definitions=MEANINGS,
        new_signatures={d['name']: {k: d[k] for k in ('parameters', 'result')}
                        for d in doc['declarations'][size:]}, limitations=LIMITS)
    return {FULL: format_graph(doc, 'compact') + '\n', CORE: format_graph(core, 'compact') + '\n',
            LIBRARY: format_graph(library, 'compact') + '\n', BASIS: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}


def main():
    for name, body in build().items():
        path = ROOT / name
        if path.exists():
            assert path.read_text(encoding='utf-8') == body, name
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Plural population distinguished from qualified subgroup overlap', flush=True)


if __name__ == '__main__':
    main()
