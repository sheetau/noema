"""Give a closed policy claim the existing public-use permission content."""
from copy import deepcopy
import json
from noema.constructed import parse, format_graph
from noema.constructed_specialization import specialize_definition
from scripts.compose_closed_claim_policies import ROOT, SOURCE as PARENT, DESCRIPTION, POLICY, catalogue
from scripts.compose_claim_conformance import params, av
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k, app, both, op, quant, v
from scripts.compose_qualified_utterance import closure

SOURCE = 'examples/v016/kant-public-reason-claim.noema'
CORE = 'examples/v016/public-reason-claim-core.noema'
EXAMPLE = 'examples/v016/public-reason-claim-example.noema'
BASIS = 'data/public-reason-claim-basis-v1.json'
FIELDS = [field for field in POLICY if field[0] not in ('targets', 'required')]


def extend(parent):
    doc = deepcopy(parent)
    statements, doc['statements'] = doc['statements'], []
    content = both(k('aa', v('person')), quant('f', 'role', 'a',
        op('t', k('h7d', v('actor'), v('person'), v('role')), v('context'))))
    body = both(op('e', 'd[v bindings]', 'n p c b'), quant('g', 'actor', 'a', quant('g', 'person', 'a',
        both('a[v bindings][n p a b][v actor]', 'a[v bindings][n p b b][v person]', content))))
    doc = parse(format_graph(doc, 'compact') + definition('iavclaim', 'bindings j[a]', 'b context[' + body + ']', 'e'))
    target_type = next(d for d in doc['declarations'] if d['name'] == 'ryi')['parameters'][5]['sort']
    trace = specialize_definition(doc, 'ryi', 'iavpolicy', {5: catalogue(('iavclaim',), target_type['element'])})
    wrapper = definition('iavtreatment', params(FIELDS), k('iavpolicy', *av(FIELDS), 'p h7k'), 'h[j[a]] e')
    doc = parse(format_graph(trace.document, 'compact') + wrapper)
    doc['statements'] = statements
    return doc, trace


def demo(core):
    text = format_graph(core, 'compact') + '''
r jwsource[] a.r jwactor[] a.r jwoffice[] a.r jwperson[] a.r jwnow[] d.
r jwscope[a] c.r jwcases[d] c.
d jwpolicy[bindings j[a]] e[c[k iavtreatment[k jwsource[] k jwactor[] k jwoffice[] l[a][k jwperson[]] p jwscope p jwcases]][v bindings]].
q[t[k iavclaim[l[a][k jwactor[] k jwperson[]]]][k jwnow[]]].
q[t[c[k ryi[k jwsource[] k jwactor[] k jwoffice[] l[a][k jwperson[]] p jwscope l[i[h[j[a]] e]][r[p iavclaim]] p jwcases p h7k]][l[a][]]][k jwnow[]]].
q[t[k jwpolicy[l[a][]]][k jwnow[]]].
q[e[r[p jwpolicy]][r[p jwpolicy]]].
'''
    return parse(text)


def build():
    doc, _ = extend(parse((ROOT / PARENT).read_text(encoding='utf-8')))
    core = deepcopy(doc); core['statements'] = []
    core['declarations'] = closure(doc, ['iavclaim', 'iavpolicy', 'iavtreatment', 'ryi'])
    example = demo(core)
    return {path: format_graph(value, 'compact') + '\n' for path, value in ((SOURCE, doc), (CORE, core), (EXAMPLE, example))}


def basis():
    return dict(status='concrete_public_permission_claim_connected', parent=PARENT, document=SOURCE,
        definitions={
            'iavclaim': '行為主体・本人の二個体列を取り、本人が人間であることと、その本人の全ての公的使用について行為主体から衝突のない積極的許可があることをh7dで表す。全ての立場を量化し、一つの立場だけ選んで禁止を隠さない。',
            'iavpolicy': 'この一つの基準をryiへ静的に束縛した政策関数。規範の出所・政府役の主体・職務・対象者・比較状況は引数として残す。',
            'iavtreatment': 'iavpolicyの要求関係を既存h7kへ接続する。外側の政策への要求と、公的活動への許可h7bおよび禁止h7aは異なる関係である。'},
        limitations=[
            '公的理性使用の許可を一つの具体的な扱いの基準として構成した解釈注記である。尊厳の全体やu0017の唯一の読みとはせず、著者による新しい主張を追加しない。',
            '活動・立場・公衆の分類には既存ca〜ceを使う。分類の基礎説明は未完で、現実世界の分類器や自動翻訳を実装したものではない。',
            '許可を実際の行使、能力、無干渉、積極的支援と同一視しない。実行cgを評価せずに許可を表せる。対象となる活動がない場合は全称条件として成立し、活動の存在を補わない。',
            '内側の許可の出所は行為主体、外側の基準を課す出所はsourceである。政府の正当な資格や人間の尊厳の根拠はこれだけでは説明されない。',
            '同じ記述・引数・極性を保持するが、別名への規範移転はしない。比較状況の範囲外も含む無条件の権利を証明したものではない。',
            '原文の新規対応範囲、全文の意味確認済み区間は追加しない。'])


def main():
    for name, body in (build() | {BASIS: json.dumps(basis(), ensure_ascii=False, indent=2) + '\n'}).items():
        path = ROOT / name
        if path.exists(): assert path.read_text(encoding='utf-8') == body, name
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(name, len(body))


if __name__ == '__main__': main()
