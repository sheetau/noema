"""Name an ordered group of quoted utterances without distributing its role."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.language import convert
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT


def definitions():
    return '''
r ga[j[i[f]] i[h[a] e] d] c.
d gb[parts j[i[f]] topic i[h[a] e] scene d] c[
 w[u[e[d[v parts]][n p a b]]][k ga[v parts v topic v scene]]
].
d gc[parts j[i[f]] entry i[f]] c[
 q[v parts][u[e[n p a b][n p a b]]][i[found c item i[f]][x[v found][e[v item][v entry]]]]
].
'''


def generic_composed():
    doc = parse('n:\n' + definitions())
    primitive = next(d for d in doc['declarations'] if d['name'] == 'ga')
    basis = {'version': 'quoted-groups-basis-v1', 'document': 'examples/v014/quoted-groups.noema',
        'primitives': [{'symbol': 'ga', 'parameters': primitive['parameters'], 'result': 'truth',
            'arguments': ['quoted_parts', 'topic_description', 'context'],
            'meaning_ja': '指定文脈で、順序付きの発話記述のまとまり全体を、指定した事柄の標語として位置付ける。各部分を個別の標語とすること、各発話の実行や達成、部分の同義性は含まない。事柄はNoemaの性質定義の記述で与える。'}],
        'definitions': {
            'gb': '引用のまとまりが空でなく、そのまとまり全体についてgaが成立する。単独の部分に同じ役割があるとは推定しない。',
            'gc': '指定した発話記述が引用の列のいずれかの出現にある。列の順序と重複は変更せず、引用内容を評価しない。'},
        'unresolved': ['標語としての社会的な位置付けは基本関係gaの意味規約であり、文章からの自動認定は行わない。',
            '列は引用した発話の意味記述の順序を保持するが、原語の綴りや印刷上の字体を再現する仕組みではない。']}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = convert(parse((ROOT / 'examples/v013/kant-reasoned-judgment.noema').read_text(encoding='utf-8')), '0.14')
    base = deepcopy(doc)
    base['statements'], base['declarations'] = [], []
    for declaration in doc['declarations']:
        if declaration['name'] == 'bo':
            text = format_graph(base, 'compact') + '\n' + definitions() + '''
d bt[] j[i[f]][l[i[f]][r[k bl[k ao[]]] r[k bn[k ao[]]]]].
d bo[] e[b scene[k gb[k bt[] r[p bi] v scene]]].
'''
            base = parse(text)
        else:
            base['declarations'].append(deepcopy(declaration))
    base['statements'] = doc['statements']
    text = format_graph(base, 'compact') + '\n'
    basis = deepcopy(json.loads((ROOT / 'data/kant-reasoned-judgment-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-quoted-group-basis-v1', document='examples/v014/kant-quoted-group.noema')
    generic = generic_composed()[1]
    basis['primitives'] += generic['primitives']
    basis['definitions'].update(generic['definitions'])
    basis['definitions'].update({
        'bt': 'ラテン語の呼びかけblとドイツ語の呼びかけbnを、この順序で引用した二要素のまとまり。二つの発話内容を同一化しない。',
        'bo': 'btのまとまり全体を、先行定義biで述べた事柄の標語として位置付ける内容。bnだけを標語とする旧草案と区別する。'})
    basis['unresolved'] += generic['unresolved'] + [
        'この草案は二つの呼びかけをまとまりとして標語の指示対象に採る。原文の指示範囲を一意に確定したとは主張せず、旧版のbnだけを指す読みも比較用に保持する。',
        '原刊の配置の確認は未完。Bielefeldの閲覧は拒否され、DTAの画像閲覧はこの環境で利用できなかった。転記本文の確認と画像の確認を混同しない。',
        '標語の社会的な使用、ラテン語の行為性、基本概念の解釈と全文の意味確認は残る。']
    audit_basis(parse(text), basis)
    return text, basis


def main():
    for compose, filename in ((generic_composed, 'data/quoted-groups-basis-v1.json'),
                              (source_composed, 'data/kant-quoted-group-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored quoted group differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Ordered quoted groups composed; role does not distribute to each part')


if __name__ == '__main__':
    main()
