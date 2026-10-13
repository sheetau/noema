"""Link public/private roles and access without conflating their permissions."""
from copy import deepcopy
import json
import re

from noema.grammar import format_graph, parse
from noema.linking import link_documents
from noema.meaning_basis import audit_basis
from scripts.compose_limits import ROOT, v, call, app, op, both, quant, definition

PARENT = 'examples/v014/kant-open-access.noema'
ROLES = 'examples/v011/kant-public-private.noema'


def linkage():
    pairs = {}
    for label, path, basis_path in (
        ('current', PARENT, 'data/kant-open-access-basis-v1.json'),
        ('roles', ROLES, 'data/kant-public-private-basis-v1.json')):
        doc = parse((ROOT / path).read_text(encoding='utf-8'))
        basis = json.loads((ROOT / basis_path).read_text(encoding='utf-8'))
        audit_basis(doc, basis)
        pairs[label] = (doc, basis)
    upgraded = deepcopy(pairs['roles'][0])
    upgraded['schema_version'] = upgraded['lexicon_version'] = '0.14'
    upgraded = parse(format_graph(upgraded, 'compact'))
    return link_documents({'current': pairs['current'][0], 'roles': upgraded}), pairs


def bridge_definitions(mapping):
    left, right = app(v('left'), v('person')), app(v('right'), v('person'))
    text = definition('rdl', 'left h[a] c right h[a] c', both(quant('g', 'person', 'a', left),
        quant('f', 'person', 'a', both(op('y', left, right), op('y', right, left)))))
    text += 'r h6t[a a d] c.r h6u[a a a i[h[a] f] d] c.\n'
    params = 'person a activity a role a audience a channel a subject a description i[h[a] f] context d'
    names = ('person', 'activity', 'role', 'audience', 'channel', 'subject', 'description', 'context')
    role = lambda name, *args: call(mapping[name], *(v(arg) for arg in args))
    text += definition('h6v', params, both(role('da', 'person', 'activity', 'role', 'context'),
        role('cc', 'activity', 'audience', 'context'), role('ce', 'audience', 'context'),
        call('rdl', 'i[reader a][k h6t[v audience v reader v context]]',
            'i[reader a][w[k aa[v reader]][k h6n[v reader v context]]]'),
        call('h6u', v('activity'), v('channel'), v('subject'), v('description'), v('context'))))
    for symbol, access in (('h6w', 'h6q'), ('h6x', 'h6r')):
        text += definition(symbol, params + ' authority a', both(call('h6v', *(v(n) for n in names)),
            call(access, *(v(n) for n in ('authority', 'channel', 'subject', 'description', 'context')))))
    text += definition('h6y', params + ' authority a', both(call('h6v', *(v(n) for n in names)),
        call(mapping['bf'], v('authority'), v('person'), v('role'), role('dc', 'person', 'activity'), v('context'))))
    return text


def source_composed():
    linked, pairs = linkage()
    doc = deepcopy(linked.document)
    statements, doc['statements'] = doc['statements'], []
    mapping = linked.symbols['roles']
    doc = parse(format_graph(doc, 'compact') + bridge_definitions(mapping))
    doc['statements'] = statements
    basis = deepcopy(pairs['current'][1])
    basis.update(version='kant-public-use-link-basis-v1', document='examples/v014/kant-public-use-link.noema')
    def explanation(text):
        return re.sub(r'(?<![a-z2-7])[a-z2-7]+(?![a-z2-7])', lambda m: mapping.get(m[0], m[0]), text)
    for row in pairs['roles'][1]['primitives']:
        moved = deepcopy(row)
        moved['symbol'] = mapping[row['symbol']]
        moved['meaning_ja'] = explanation(row['meaning_ja'])
        basis['primitives'].append(moved)
    basis['definitions'].update({mapping[name]: explanation(meaning) for name, meaning in pairs['roles'][1]['definitions'].items()})
    decls = {row['name']: row for row in doc['declarations']}
    for name, args, meaning in (
        ('h6t', ['audience', 'reader', 'context'], '指定した宛先・公衆が、その文脈で向けられている読者の範囲を表す。実際に受領した人数や有限の構成員列ではなく、想定された宛先の各人への展開である。範囲の社会的な根拠は未完。'),
        ('h6u', ['activity', 'channel', 'subject', 'message_description', 'context'], 'この理性使用の活動記述が、この経路を使い、この対象について、この発話記述を公衆へ提示するものとして計画・分類される。実行や受領を主張しない。活動記述と具体的な提示行為の一般的な対応は未完。')):
        row = decls[name]
        basis['primitives'].append({'symbol': name, 'parameters': row['parameters'], 'result': row['result'], 'arguments': args, 'meaning_ja': meaning})
    basis['definitions'].update({
        'rdl': '二つの対象範囲が外延的に一致し、共に非空である。部分集合や偶然一人が重なるだけでは成立しない。',
        'h6v': '旧草案の公的使用の分類を満たし、同じ活動の指定宛先が公衆に分類され、その想定読者範囲と取得条件の読者範囲が非空で一致する。同じ活動の経路・対象・発話記述も固定する。実行や許可は含まない。',
        'h6w': 'h6vで分類・宛先・内容を固定した活動について、同じ読者範囲の全員に、その経路から取得する方法の許可h6qがある。発言者本人が活動を行う許可とは分ける。',
        'h6x': 'h6vで固定した同じ活動・読者範囲について、同じ経路・内容を取得する実効的機会h6rが全員にある。現に読んだことや意味の理解は含まない。',
        'h6y': 'h6vで固定した同じ活動をその本人がその立場で実行することについて、同じ規範の出所の積極的な許可があり禁止と衝突していない。読者の取得許可を代用しない。'})
    basis['unresolved'] += [explanation(text) for text in pairs['roles'][1]['unresolved']] + [
        '旧公的・私的使用の草案を0.14へ明示的に上げ、全宣言・参照を一対一に移した。同じ綴りの異なる基本概念を共有していない。旧版と現行版の全文書への射影を検査する。',
        '読者範囲の一致は、双方が正しい公衆の範囲であることを証明しない。旧ceに相当する公衆分類、学識者としての立場、市民的職務、想定読者の意味規約は未完成である。',
        '読者の取得許可と発言者の発言許可は異なる関係として保持する。h6w/h6x/h6yの間の無条件な同値性や、公的使用の自由全体との同値性は主張しない。',
        '活動の実行、個々の伝達経路、集団内の能力変化、討議と応答、原文の様相・頻度・程度・留保への統合は残る。本文への新たな実際の成立主張は追加していない。']
    basis['role_linkage'] = {'sources': {'current': PARENT, 'roles': ROLES}, 'symbols': linked.symbols,
        'statement_maps': linked.statements, 'roles_edition_change': ['0.11', '0.14'],
        'shared_declarations': [], 'linking_alone_is_not_semantic_equivalence': True}
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def main():
    text, basis = source_composed()
    for path, body in ((ROOT / basis['document'], text), (ROOT / 'data/kant-public-use-link-basis-v1.json',
            json.dumps(basis, ensure_ascii=False, indent=2) + '\n')):
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Stored public-use linkage differs')
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Public/private roles linked and publication/access permissions kept separate')


if __name__ == '__main__':
    main()
