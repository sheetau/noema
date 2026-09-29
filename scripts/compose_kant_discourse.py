"""Keep the opening's six textual acts and the author's conclusion distinct."""
import json
from pathlib import Path

from noema.discourse import description_sort, function_sort
from noema.grammar import parse, format_graph
from noema.language import convert
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]


def join(operator, items):
    items = list(items)
    if not items:
        raise ValueError('Empty connective')
    result = items[-1]
    for item in reversed(items[:-1]):
        result = operator + '[' + item + '][' + result + ']'
    return result


def selection(names):
    return 'i[node a][' + join('x', ('e[v node][v ' + name + ']' for name in names)) + ']'


def discourse_basis():
    property_ = function_sort(['individual'], 'content')
    records = [
        ('ua', ['individual', 'individual', description_sort(property_), 'situation'],
         ['node', 'author', 'property_description', 'context'],
         '著者がこの文章箇所で、対象から状況ごとの真偽への性質の記述を、概念の説明として提示する。説明対象の性質はNoemaの定義を参照し、未説明の原語で代用しない。提示したことと現実に該当する対象の存在を分ける。'),
        ('ub', ['individual', 'individual', description_sort('message'), 'situation'],
         ['node', 'author', 'message_description', 'context'],
         '著者がこの文章箇所で指定された発話の記述を引用する。発話の働きも記述に含める。引用内容への賛同、引用された要求の実行や達成は含まない。'),
        ('uc', ['individual', 'individual', description_sort('content'), 'situation'],
         ['node', 'author', 'content_description', 'context'],
         '著者がこの文章箇所で指定された内容を主張する。著者への帰属であり、解釈器がその内容を真と認定する関係ではない。'),
        ('ud', ['individual', function_sort(['individual'], 'truth'), 'individual', 'situation'],
         ['author', 'premise_nodes', 'conclusion_node', 'context'],
         '著者が指定した文章箇所の集合を根拠側として、結論箇所を帰結として提示する。論理的含意、証明の妥当性、因果関係とは区別する。根拠の十分性を判定する関係ではない。'),
        ('ue', ['individual', 'individual', 'situation'], ['earlier_node', 'later_node', 'context'],
         '指定文脈の本文順序で第一箇所が第二箇所より前にある。出来事の時間順序や因果の向きとは別の関係。'),
        ('uf', ['individual', 'individual', 'individual', 'situation'],
         ['author', 'explained_node', 'explanatory_node', 'context'],
         '著者が第二の文章箇所を第三の箇所によって説明・言い換えするという談話関係。二箇所の意味が完全に等しいことを要求しない。')]
    return {
        'version': 'expository-discourse-basis-v1', 'document': 'examples/v013/expository-discourse.noema',
        'primitives': [{'symbol': s, 'parameters': p, 'result': 'truth', 'arguments': a, 'meaning_ja': m}
                       for s, p, a, m in records],
        'definitions': {
            'va': '根拠箇所が空でなく、結論自身を根拠箇所に含めない。',
            'vb': 'vaを満たし、全根拠箇所が結論より本文上で前にあり、著者がその帰結関係を提示する。これを証明検査の代用にはしない。',
            'vc': '選択した箇所内で本文順序が非反射的かつ推移的である。有限集合なら循環を許さない。'},
        'unresolved': [
            '発話・概念説明・本文順序・説明関係を現実の文章から認定する方法と一般的な基礎への還元は未完。',
            '説明の正しさ、主張の真理、推論の妥当性は別に検査する必要がある。']}


def generic_composed():
    text = 'm:\n' + (ROOT / 'examples/fragments/expository-discourse.noema.inc').read_text(encoding='utf-8')
    doc, basis = parse(text), discourse_basis()
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def composed():
    base = convert(parse((ROOT / 'examples/v011/kant-linked-draft.noema').read_text(encoding='utf-8')), '0.13')
    base['statements'] = []
    text = format_graph(base, 'compact') + '\n'
    for name in ('expository-discourse', 'kant-opening-discourse'):
        text += (ROOT / ('examples/fragments/' + name + '.noema.inc')).read_text(encoding='utf-8')
    nodes = ['first', 'second', 'third', 'latin', 'german', 'conclusion']
    selected, premises = selection(nodes), selection(nodes[:-1])
    clauses = ['u[e[v ' + left + '][v ' + right + ']]'
               for i, left in enumerate(nodes) for right in nodes[i + 1:]]
    clauses += ['k ua[v first v author r[p bi] v context]',
                'k ua[v second v author r[p bf] v context]',
                'k ua[v third v author r[p bp] v context]',
                'k ub[v latin v author r[k bl[k ao[]]] v context]',
                'k ub[v german v author r[k bn[k ao[]]] v context]',
                'k uc[v conclusion v author r[k bo[]] v context]',
                'k uf[v author v latin v german v context]']
    clauses += ['k ue[v ' + a + ' v ' + b + ' v context]' for a, b in zip(nodes, nodes[1:])]
    clauses += ['k vc[' + selected + ' v context]', 'k vb[v author ' + premises + ' v conclusion v context]']
    text += 'd cp[author a context d ' + ' '.join(n + ' a' for n in nodes) + '] c[' + join('w', clauses) + '].\n'
    # These are document-local referents, not vocabulary definitions.
    for name in ('wa', 'wb', 'wc', 'wd', 'we', 'wf', 'wg'):
        text += 'r ' + name + '[] a.\n'
    text += 'r wh[] d.\ns[k cp[k wa[] k wh[] k wb[] k wc[] k wd[] k we[] k wf[] k wg[]]].\n'
    doc = parse(text)
    basis = json.loads((ROOT / 'data/kant-linked-basis-v1.json').read_text(encoding='utf-8'))
    additions = discourse_basis()
    basis['version'] = 'kant-opening-discourse-basis-v1'
    basis['document'] = 'examples/v013/kant-opening-discourse.noema'
    basis['primitives'] += additions['primitives']
    for symbol, label in zip(('wa', 'wb', 'wc', 'wd', 'we', 'wf', 'wg'),
                             ('著者', '啓蒙の定義箇所', '未成熟の定義箇所', '自己に責任がある未成熟の説明箇所',
                              'ラテン語の呼びかけの箇所', 'ドイツ語の呼びかけの箇所', '標語として位置付ける結論箇所'), strict=True):
        basis['primitives'].append({'symbol': symbol, 'parameters': [], 'result': 'individual', 'arguments': [],
                                    'meaning_ja': 'この文書の' + label + 'を指す局所参照。内容の意味は本文中のNoemaの定義で記述する。'})
    basis['primitives'].append({'symbol': 'wh', 'parameters': [], 'result': 'situation', 'arguments': [],
                                'meaning_ja': 'この段落を提示する文脈。引用された呼びかけの達成状況とは区別する。'})
    basis['definitions'].update(additions['definitions'])
    basis['definitions'].update({
        'bk': 'この段落で後続のドイツ語の説明を使って採った、ラテン語の呼びかけの目的内容bmへの参照。sapere一般の語義の定義ではない。',
        'bl': 'bkに向けた勇気を持つよう促す発話。ラテン語を後続の説明によって読む文脈的草案であり、独立した逐語訳ではない。',
        'bm': '自分自身の理解能力を使う内容。他者による指導がないという条件はこの式には加えない。',
        'bn': 'bmに向けた勇気を持つよう促す発話。ドイツ語の呼びかけを、先行する自立的使用bbから分けた。',
        'bo': 'bnの呼びかけが先行定義biの事柄の標語であるという内容。現在状況で真と断言せず、主張への帰属の対象にする。',
        'bp': 'bdを対象から命題内容への性質として参照する。',
        'cp': '六つの異なる文章箇所を定義提示・二つの引用・標語の主張として同じ著者と文脈に接続する。本文順序、説明の向き、先行五箇所からの帰結としての提示を保持する。'})
    basis['unresolved'] += additions['unresolved'] + [
        'Sapere audeはこの段落のドイツ語の説明による文脈的草案だけを置く。二つの草案内容は一致するが、ラテン語・ドイツ語のあらゆる文脈での同義、原語の字面や含意全体の保持を主張しない。',
        'alsoの根拠を先行五箇所のまとまりと読む談話上の選択。原文は形式的な証明の前提集合を列挙していない。',
        '旧草案のbg/bhは比較のために保持するが、本文の引用と標語の主張には指導排除を補わないbnを用いる。',
        '概念の定義本文は先行草案の暫定的な能力・因果・離脱の読みを引き継ぐ。六区間の草案化と意味の完成は別である。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    for compose, name in ((generic_composed, 'data/expository-discourse-basis-v1.json'),
                           (composed, 'data/kant-opening-discourse-basis-v1.json')):
        text, basis = compose()
        for filename, body in {basis['document']: text, name: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / filename
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored opening discourse differs: ' + filename)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Six opening discourse acts composed; semantic equivalence remains partial')


if __name__ == '__main__':
    main()
