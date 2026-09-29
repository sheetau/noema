"""Compose preserved opening and motto drafts; remove the unlinked topic symbol.

This writes a new edition/example, never overwrites the historical drafts.
"""
import json
from pathlib import Path

from noema.grammar import parse
from noema.meaning_basis import audit_basis

ROOT = Path(__file__).resolve().parents[1]


def composed():
    opening = (ROOT / 'examples/v09/kant-opening-draft.noema').read_text(encoding='utf-8')
    motto = (ROOT / 'examples/v010/kant-motto-draft.noema').read_text(encoding='utf-8')
    extra = 'r al[a e d] c.\nr am[f h[a] e] c.\nr ao[] a.\n'
    text = opening.replace('i:', 'k:', 1).replace('d ba[', extra + 'd ba[', 1)
    text += '\nd bi[change a] e[b scene[g person a[g before d[k be[v person v change v before v scene]]]]].\n'
    text += motto[motto.index('d bg['):motto.index('s[k am[')]
    text += 's[k am[k bh[] p bi]].\n'
    basis = json.loads((ROOT / 'data/kant-opening-basis-v1.json').read_text(encoding='utf-8'))
    later = json.loads((ROOT / 'data/kant-motto-basis-v1.json').read_text(encoding='utf-8'))
    basis['version'] = 'kant-linked-basis-v1'
    basis['document'] = 'examples/v011/kant-linked-draft.noema'
    for entry in later['primitives']:
        if entry['symbol'] in ('al', 'ao'):
            basis['primitives'].append(entry)
        elif entry['symbol'] == 'am':
            entry['parameters'][1] = {'kind': 'function', 'parameters': ['individual'], 'result': 'content'}
            entry['arguments'][1] = 'property'
            entry['meaning_ja'] = '発話が、性質によって記述された事柄の標語として位置付けられる。性質は対象から状況ごとの真偽へ写す定義を受け取る。原文の名詞を未説明の別記号として与えない。標語の社会的な働きの一般的定義は未完。'
            basis['primitives'].append(entry)
    basis['definitions']['bi'] = '変化過程について、ある人と先行状況があり、その人が先行状況から評価状況への変化を通じてbeを満たすという内容。離脱の定義から構成した性質であり、過程の時間的な全容を定義し終えたものではない。'
    basis['definitions'].update({name: later['definitions'][name] for name in ('bg', 'bh')})
    basis['unresolved'] = basis['unresolved'][:-1] + [
        'ラテン語の標語とドイツ語の説明との関係、および帰結を示すalsoの談話上の意味。',
        '啓蒙を、離脱を完了した過程の性質として記述する読みと、歴史的・社会的運動としての意味の違い。',
        '全対象・全状況で同じ性質となる異なる記述の仕方を、この関数型の同一性では区別しない。',
        '勇気・原因・能力・指導・標語などの基本関係の一般的な意味説明。']
    audit_basis(parse(text), basis)
    return text, basis


def main():
    text, basis = composed()
    outputs = {basis['document']: text, 'data/kant-linked-basis-v1.json': json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}
    for name, body in outputs.items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Existing composed draft differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
    print('Kant linked draft and basis reproduced; source equivalence remains partial')


if __name__ == '__main__':
    main()
