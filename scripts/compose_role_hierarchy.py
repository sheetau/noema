"""Scoped role order, role holders and independently issued commands."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, call, v, app, both, op, quant, lam, definition

PARENT = 'examples/v014/kant-command-delivery.noema'
RELATIONS = 'members h[a a d] c holders h[a a a d] c above h[a a a d] c'
ROLE = 'issuer a person a higher a office a organization a context d ' + RELATIONS
ROLE_FIELDS = ('issuer', 'person', 'higher', 'office', 'organization', 'context', 'members', 'holders', 'above')
COMMAND = ROLE + ' notice a action a description i[h[a] f]'


def definitions():
    inside = lambda x: app(v('scope'), v(x))
    edge = lambda x, y: app(v('order'), v(x), v(y))
    irreflexive = quant('f', 'x', 'a', op('y', inside('x'), op('u', edge('x', 'x'))))
    transitive = quant('f', 'x', 'a', quant('f', 'y', 'a', quant('f', 'z', 'a', op('y',
        both(inside('x'), inside('y'), inside('z'), edge('x', 'y'), edge('y', 'z')), edge('x', 'z')))))
    text = definition('rex', 'scope h[a] c order h[a a] c', both(irreflexive, transitive))
    text += definition('rey', 'higher a lower a scope h[a] c order h[a a] c', both(
        call('rex', v('scope'), v('order')), inside('higher'), inside('lower'), edge('higher', 'lower')))
    scope = lam('role', 'a', app(v('members'), v('role'), v('organization'), v('context')))
    order = 'i[top a bottom a][' + app(v('above'), v('top'), v('bottom'), v('organization'), v('context')) + ']'
    text += definition('rez', ROLE, both(op('u', op('e', v('issuer'), v('person'))),
        call('rey', v('higher'), v('office'), scope, order),
        *[app(v('holders'), v(person), v(role), v('organization'), v('context'))
          for person, role in (('issuer', 'higher'), ('person', 'office'))]))
    return text


def generic_composed():
    text = 'n:\n' + definitions()
    basis = {'version': 'role-hierarchy-basis-v1', 'document': 'examples/v014/role-hierarchy.noema',
        'primitives': [], 'definitions': {
            'rex': '指定した対象範囲の関係が非反射的かつ推移的である。全順序や直接の隣接関係は要求しない。空範囲では真。範囲外の辺は検査対象外。',
            'rey': 'rexが成立し、範囲内の第一対象から第二対象へ指定関係がある。異なる、比較可能な二対象を要求するので空範囲では偽。隣接辺から推移閉包を計算する定義ではない。',
            'rez': '同じ組織・状況の役職範囲と順序に対してreyが成立し、異なる二人がそれぞれ上位・下位の役職を保持する。所属、保持、上下の関係は明示的な引数であり、制度の正当性や命令権を含まない。'},
        'unresolved': ['役職の範囲・保持・上下を現実の組織へ対応させる基礎説明は引数として残る。順序だけで軍人や軍隊の制度を定義したとはしない。',
            '与えた関係は直接の報告先の一覧ではなく、指定範囲内の推移的な上下関係である。未確認の関係を偽として補わない。複数の役職を兼ねることは許すが、同じ本人を自分の上官とは数えない。']}
    audit_basis(parse(text), basis)
    return format_graph(parse(text), 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT / 'data/kant-command-delivery-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    args = [v(n) for n in ROLE_FIELDS]
    extra = definitions() + definition('hzae', ROLE, both(call('rez', *args),
        call('cf', v('issuer'), v('higher'), v('context')), call('cf', v('person'), v('office'), v('context'))))
    extra += definition('hzaf', COMMAND, both(call('hzae', *args),
        call('hzaa', *[v(n) for n in ('issuer', 'person', 'notice', 'action', 'description', 'context')])))
    extra += definition('hzag', COMMAND, both(call('hzae', *args),
        call('hzac', *[v(n) for n in ('person', 'action', 'office', 'issuer', 'notice', 'description', 'context')])))
    doc = parse(format_graph(doc, 'compact') + extra)
    doc['statements'] = statements
    basis.update(version='kant-role-hierarchy-basis-v1', document='examples/v014/kant-role-hierarchy.noema')
    generic = generic_composed()[1]
    basis['definitions'].update(generic['definitions'])
    basis['definitions'].update({
        'hzae': 'rezの同一組織の役職関係に、両者がその状況で該当職務を委ねられているcfを結ぶ。原文のOberenへの操作的な部分草案であり、軍制の説明ではない。',
        'hzaf': '同じ上位役職の本人が、同じ下位役職の本人へ、同じ行為について指定発話を実際に発出・提示する。受領、義務、実行、命令権は結論に含めない。',
        'hzag': 'hzafの関係と、同じ出所・本人・役職・行為・状況の職務要求がともに成立する。上下関係から義務を推論する定義ではない。'})
    basis['unresolved'] += generic['unresolved'] + [
        '先行版の上官関係の未記述を、本版では同一組織・状況の役職順序と保持への部分接続で進める。軍務、権限の委任、制度の正当性、有用性への批判、語義全体は引き続き未完。',
        'hzzの同一本人への実行指示を閉じた引用として渡す作例を検査する。任意のdescriptionを渡したhzafまで命令とは認定しない。既存15件の著者主張を変更せず、新しい原文主張は追加しない。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def core_composed():
    text, basis = source_composed()
    doc = parse(text)
    extracted = extract_document(doc, roots=['hzz', 'hzae', 'hzaf', 'hzag'], statement_indices=[])
    projected = extract_basis(doc, basis, extracted, version='role-hierarchy-core-basis-v1',
        document_path='examples/v014/role-hierarchy-core.noema')
    return format_graph(extracted.document, 'compact') + '\n', projected


BUILDERS = ((generic_composed, 'role-hierarchy'), (source_composed, 'kant-role-hierarchy'),
            (core_composed, 'role-hierarchy-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/' + stem + '-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored role hierarchy differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__':
    main()
