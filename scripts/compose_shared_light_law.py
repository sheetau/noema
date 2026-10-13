"""Bind the common energy/frequency factor to one light complex and two frames."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_field_equations import CUT
from scripts.compose_wave_readings import parameters, MOTION, RECORDED

PARENT = 'examples/v014/einstein-energy-questions.noema'
READ = [(n, 'a') for n in 'record target kind frame event unit observer'.split()] + [
    ('scale', 'b'), ('value', CUT), ('context', 'd'), ('recordedby', RECORDED)]
COMMON = [(n, 'a') for n in 'target oldframe newframe energykind ratekind'.split()] + [
    ('context', 'd'), ('recordedby', RECORDED), ('motion', MOTION)]
INPUTS = COMMON + [(n, CUT) for n in 'light speed ax'.split()]
for side in ('old', 'new'):
    INPUTS += [(side+n, 'a') for n in ('observer', 'event')]
    for kind in ('energy', 'rate'):
        INPUTS += [(side+kind+n, t) for n, t in (
            ('record', 'a'), ('unit', 'a'), ('scale', 'b'), ('value', CUT))]


def converted(side, kind):
    return k('bj', v(side+kind+'scale'), v(side+kind+'value'))


def numeric_condition():
    return k('seck', *(v(n) for n in ('light', 'speed', 'ax')),
             *(converted(side, kind) for kind in ('energy', 'rate') for side in ('old', 'new')))


def definitions():
    reading = k('sbw2', *(v(n) for n in ('record', 'target', 'kind', 'frame', 'event', 'unit', 'scale', 'value', 'context')),
                'p zof', 'p zog')
    text = definition('seia', parameters(READ), both(reading, k('xb', v('observer')),
        k('x4', v('observer'), v('frame'), v('context')),
        app(v('recordedby'), v('record'), v('observer'), v('context'))))
    conditions = [k('cf', v('target')), k('va', v('oldframe')), k('va', v('newframe')),
        op('u', op('e', v('oldframe'), v('newframe'))),
        op('u', op('e', v('energykind'), v('ratekind'))),
        app(v('motion'), *(v(n) for n in ('oldframe', 'newframe', 'light', 'speed', 'context')))]
    for side in ('old', 'new'):
        for kind in ('energy', 'rate'):
            fields = dict(record=v(side+kind+'record'), target=v('target'), kind=v(kind+'kind'),
                frame=v(side+'frame'), event=v(side+'event'), unit=v(side+kind+'unit'),
                observer=v(side+'observer'), scale=v(side+kind+'scale'), value=v(side+kind+'value'),
                context=v('context'), recordedby=v('recordedby'))
            conditions.append(k('seia', *(fields[n] for n, _ in READ)))
    text += definition('seib', parameters(INPUTS), both(*conditions))
    text += definition('seic', parameters(INPUTS), both(k('seib', *(v(n) for n, _ in INPUTS)), numeric_condition()))
    return text


MEANINGS = {
    'seia': '一つの値の記録を、同じ対象・量の種類・系・出来事・単位・尺度・文脈へ結ぶ。記録の観測者への帰属と、その観測者が当該系に静止する条件を加える。実測済みや記録の物理的正確さは補わない。',
    'seib': '同じ光の集合について、エネルギーと振動数の四記録を二つの異なる系へ結ぶ。各系内では観測者・出来事を共有し、系間では別でもよい。種類・単位・正の尺度・値・文脈・同じ光速度と符号付き系間速度を保持する。数値変換則の成立とは別の条件。',
    'seic': 'seibの同じ光・二系・観測者に結ばれた正のエネルギーと振動数が、各単位から基準尺度へ換算した後、同じβ(1−av/V)倍になる。両種類の値の等しさや普遍的な比例定数は要求しない。',
}


def source_composed():
    doc = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT/'data/einstein-energy-questions-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    doc = parse(format_graph(doc, 'compact') + definitions()); doc['statements'] = statements
    basis.update(version='einstein-shared-light-law-basis-v1', document='examples/v014/einstein-shared-light-law.noema')
    basis['definitions'].update(MEANINGS)
    basis['unresolved'] += [
        'u0214の同じ光のエネルギーと振動数の変換を、四つの仮定上の記録へ部分接続する。記録の実在・装置・誤差は原文へ補わない。',
        '各系内で同じ出来事と観測者を使うのは比較の明示的な設定で、原文が四つの実測を報告しているとは読まない。二系間で出来事・観測者が同一である条件は課さない。',
        '同じ光の集合、エネルギーという量の種類、通常の振動数という量の種類、方向とその光の対応、標準配置の運動はモデルの意味規約に依存する。数値から物理的同一性を導く定義ではない。',
        '全ての許容設定での法則の成立、周波数と周期の物理的構成、エネルギー密度からの導出、bemerkenswertという著者の評価と帰属の接続は未完。正の値の比に限定し、零エネルギーの問いを否定しない。',
        '新たな原始概念や局所参照は追加しない。既存の174文を保持し、部分条件を論文全体の意味一致とは認定しない。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact')+'\n', basis


def core_composed():
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=['seic'], statement_indices=[])
    projected = extract_basis(doc, basis, selected, version='shared-light-law-core-basis-v1',
        document_path='examples/v014/shared-light-law-core.noema')
    return format_graph(selected.document, 'compact')+'\n', projected


BUILDERS = ((source_composed, 'einstein-shared-light-law'), (core_composed, 'shared-light-law-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/'+stem+'-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2)+'\n')):
            path = ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored shared light law differs: '+name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
