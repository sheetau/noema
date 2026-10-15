"""Represent permission across independently chosen topics and extents."""
import json

from noema.constructed import parse, format_graph
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params
from scripts.compose_described_norms import RULE, DESCRIPTION, TRUE

LIBRARY = 'examples/v016/choice-permissions.noema'
EXAMPLE = 'examples/v016/choice-permissions-example.noema'
BASIS = 'data/choice-permissions-basis-v1.json'
PC = 'i b[e]'
MC = 'i b[f]'
SCOPE = [('population', 'h[a] c'), ('topics', 'h[a a d] c'), ('extents', 'h[a a d] c'),
         ('candidates', 'h[a a d] c'), ('subject', 'h[a a d] a'), ('extent', 'h[a a d] a'), ('anchor', 'd')]
NORMS = [('source', 'a'), ('roles', 'h[a a d] a'), ('targets', 'h[a a d] ' + DESCRIPTION),
         ('required', RULE), ('allowed', RULE)]

def av(fields): return [v(n) for n, _ in fields]

def definitions():
    topic = app(v('subject'), v('person'), v('activity'), v('anchor'))
    extent = app(v('extent'), v('person'), v('activity'), v('anchor'))
    candidate = app(v('candidates'), v('person'), v('activity'), v('anchor'))
    selected = both(app(v('population'), v('person')), candidate,
        app(v('topics'), v('person'), topic, v('anchor')), app(v('extents'), v('person'), extent, v('anchor')))
    text = definition('rtr', params(SCOPE + [('person', 'a'), ('activity', 'a')]), selected)
    permission = k('rdm', v('source'), v('person'), app(v('roles'), v('person'), v('activity'), v('anchor')),
        v('activity'), app(v('targets'), v('person'), v('activity'), v('anchor')), TRUE, v('point'), v('required'), v('allowed'))
    text += definition('rts', params(SCOPE + NORMS + [('point', 'd')]),
        quant('f', 'person', 'a', quant('f', 'activity', 'a', op('y', k('rtr', *av(SCOPE), v('person'), v('activity')), permission))))
    requested = both(app(v('population'), v('person')), app(v('topics'), v('person'), v('topic'), v('anchor')),
        app(v('extents'), v('person'), v('amount'), v('anchor')))
    represented = quant('g', 'activity', 'a', both(candidate, op('e', topic, v('topic')), op('e', extent, v('amount'))))
    text += definition('rtt', params(SCOPE), quant('f', 'person', 'a', quant('f', 'topic', 'a', quant('f', 'amount', 'a',
        op('y', requested, represented)))))
    text += definition('rtu', params(SCOPE + NORMS), 'b point[' + both(k('rtt', *av(SCOPE)),
        k('rts', *av(SCOPE + NORMS), v('point'))) + ']', 'e')
    first = 'o a[r b[i[content e][j s[v content]]]][v permission]'
    second = 'o a[r b[i[content e][j m[v content]]]][v obedience]'
    text += definition('rtv', 'permission ' + PC + ' obedience ' + PC, 'l[' + MC + '][' + first + ' ' + second + ']', 'j[' + MC + ']')
    return text

def build():
    parent = parse((ROOT / 'examples/v016/kant-focused-permission.noema').read_text(encoding='utf-8'))
    norm = next(d for d in parent['declarations'] if d['name'] == 'rdm')
    doc = dict(parent, declarations=[norm], statements=[])
    library = parse(format_graph(doc, 'compact') + definitions())
    text = format_graph(library, 'compact')
    for name, fields, result in [
        ('jdpopulation', 'a', 'c'), ('jdtopics', 'a a d', 'c'), ('jdextents', 'a a d', 'c'),
        ('jdcandidates', 'a a d', 'c'), ('jdsubject', 'a a d', 'a'), ('jdextent', 'a a d', 'a'),
        ('jdanchor', '', 'd'), ('jdsource', '', 'a'), ('jdroles', 'a a d', 'a'),
        ('jdrequired', 'a a a a ' + DESCRIPTION + ' c d', 'c'), ('jdallowed', 'a a a a ' + DESCRIPTION + ' c d', 'c'),
        ('jdexec', 'a a d', 'c'), ('jdobeys', 'd', 'c')]:
        text += 'r ' + name + '[' + fields + '] ' + result + '.'
    text += definition('jdaction', 'person a activity a', 'b point[k jdexec[v person v activity v point]]', 'e')
    text += definition('jdtargets', 'person a activity a anchor d', 'r[p jdaction]', DESCRIPTION)
    scope = ['p jd' + n for n, _ in SCOPE[:-1]] + ['k jdanchor[]']
    norms = ['k jdsource[]', 'p jdroles', 'p jdtargets', 'p jdrequired', 'p jdallowed']
    text += definition('jdpolicy', '', k('rtu', *(scope + norms)), 'e')
    text += definition('jdobedience', '', 'b point[k jdobeys[v point]]', 'e')
    text += definition('jdquoted', '', k('rtv', 'r b[k jdpolicy[]]', 'r b[k jdobedience[]]'), 'j[' + MC + ']')
    text += 'q[k rtt[' + ' '.join(scope) + ']].'
    text += 'q[k rts[' + ' '.join(scope + norms + ['k jdanchor[]']) + ']].'
    text += 'q[t[k jdpolicy[]][k jdanchor[]]].'
    literal = 'l[' + MC + '][r b[c[i[content e][j s[v content]]][k jdpolicy[]]] r b[c[i[content e][j m[v content]]][k jdobedience[]]]]'
    text += 'q[e[k jdquoted[]][' + literal + ']].'
    text += 'q[t[k jdobedience[]][k jdanchor[]]].'
    return {LIBRARY: format_graph(library, 'compact') + '\n', EXAMPLE: format_graph(parse(text), 'compact') + '\n'}

def basis():
    return dict(status='independent_choice_scope_and_ordered_quoted_permission_directive',
        definitions={
            'rtr': '同じ本人・基準文脈で選んだ活動候補が、本人の希望する話題と程度の両方に属する。候補の実行は要求しない。',
            'rts': 'rtrの全対象について、同じ出所・本人・役割・行為・閉じた記述を積極的に許可し、反対要求がない。選択は基準文脈に固定し、規範は評価状況で照合する。',
            'rtt': '各本人の希望する話題と程度の全組合せに、それと一致する活動候補が存在する。候補一覧から未許可の組合せを落とすだけでは網羅したことにならない。',
            'rtu': '候補範囲の網羅性rttと、その全対象への許可rtsを同時に要求する内容。',
            'rtv': '許可内容を述べる主張と服従内容を求める指令を、順序を保持した二つの発話記述として構成する。構成時にはどちらの内容も実行しない。'},
        parameter_conventions={
            'topics/extents': '本人が基準文脈で希望する話題・程度の範囲。各軸を独立に選べるという読みを明示する。',
            'candidates/subject/extent': '活動候補の範囲とその話題・程度。実行済みの行為だけを一覧にしない。候補の物理的実行可能性は別の条件。',
            'roles/targets': '同じ本人・活動・基準文脈の役割と、閉じた行為内容の記述。記述を原語文字列で代用しない。',
            'example_jdobeys': '例では服従内容を外部入力として残す。何に従うか、命令の出所・範囲、実行による履行の説明は未接続。'},
        limitations=[
            'カントu0017の引用に必要な選択範囲と発話の順序のための基盤であり、本文の完成訳や新たな原文対応としては数えない。',
            '話題と程度の直積は明示した読みであり、全自然言語の自由選択表現をこの条件へ固定しない。希望の範囲に存在条件を足さず、空なら全称条件は真になる。',
            '程度は型aの対象として参照する。この基盤だけでは連続量、上限、単位、望む以上の量への許可を定義していない。',
            'rttは候補の存在を要求し、現実の実行や実行能力を要求しない。全ての候補が現実に存在するとする存在論ではない。',
            'rtvは許可を述べる主張と指令の列である。許可を新設する遂行的発話の一般理論ではなく、後半への服従を前半の許可の成立条件へ自動で加えない。',
            '発話者・聞き手、ただしの談話上の関係、誰だけがそれを言えるかという上位の条件、軍隊・国家・服従の基礎説明は未接続。',
            '今回の例では服従内容を入力として残す。引用の作成・保持から実際の服従、引用者の賛同、現実の規範の成立は導かない。'])

def main():
    for name, body in (build() | {BASIS: json.dumps(basis(), ensure_ascii=False, indent=2) + '\n'}).items():
        path = ROOT / name
        if path.exists():
            assert path.read_text(encoding='utf-8') == body, name
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(name, len(body))

if __name__ == '__main__': main()
