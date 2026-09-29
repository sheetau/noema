"""Compose a contextual discernment reading without aliasing the German gloss."""
from copy import deepcopy
import json

from noema.grammar import format_graph, parse
from noema.meaning_basis import audit_basis
from scripts.compose_contextual_ability import ROOT


def definitions():
    return '''
d ya[person a matter a judgments h[a a d] c matters h[a a d] c reasons h[a a d] c support h[a a d] c] e[
 b scene[g act a[g reason a[
  w[c[v judgments][v person v act v scene]][
   w[c[v matters][v act v matter v scene]][
    w[c[v reasons][v act v reason v scene]][c[v support][v reason v act v scene]]]]
 ]]]
].
d yb[person a scene d relevant h[a a d] c judgments h[a a d] c matters h[a a d] c reasons h[a a d] c support h[a a d] c available h[a a d] c outcomes h[a a d d] c selected h[a a d d] c] c[
 w[g matter a[c[v relevant][v person v matter v scene]]][
  f matter a[y[c[v relevant][v person v matter v scene]][
   k xd[v person k ya[v person v matter v judgments v matters v reasons v support] v scene v available v outcomes v selected]
  ]]
 ]
].
'''


def generic_composed():
    text = (ROOT / 'examples/v013/contextual-ability.noema').read_text(encoding='utf-8') + definitions()
    doc = parse(text)
    basis = deepcopy(json.loads((ROOT / 'data/contextual-ability-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='reasoned-judgment-basis-v1', document='examples/v013/reasoned-judgment.noema')
    basis['definitions'].update({
        'ya': '指定対象について、その人が判断し、その同じ判断で使った理由がその判断を支える、という内容。判断主体・対象・用いた理由・支持の関係を引数として分ける。理由が存在するだけでは成立しない。',
        'yb': '評価する事柄が空でなく、その全てについて、yaの判断内容を指定した結果範囲で達成する方法xdがある。事柄ごとに異なる方法でもよい。現時点で全判断を実行済みとはしない。'})
    basis['unresolved'] += ['ybは事柄・評価範囲・理由の支持を明示した判断能力の構成例であり、知恵やsapereの全用法に共通する必要十分条件ではない。',
        '理由として使うことと理由が判断を支えることは別の引数である。支持の規範、判断や理由の一般的な基礎付けは引数の意味規約で明示する必要がある。']
    audit_basis(doc, basis)
    return format_graph(doc, 'compact') + '\n', basis


def source_composed():
    doc = parse((ROOT / 'examples/v013/kant-described-explanations.noema').read_text(encoding='utf-8'))
    base = deepcopy(doc)
    base['statements'], base['declarations'] = [], []
    for declaration in doc['declarations']:
        if declaration['name'] == 'bk':
            text = format_graph(base, 'compact') + '''
r fa[a a d] c.r fb[a a d] c.r fc[a a d] c.r fd[a a d] c.r fe[a a d] c.
''' + definitions() + '''
d bk[person a] e[b scene[k yb[v person v scene p fe p fa p fb p fc p fd p ae p af p ap]]].
'''
            base = parse(text)
        else:
            base['declarations'].append(deepcopy(declaration))
    base['statements'] = doc['statements']
    text = format_graph(base, 'compact') + '\n'
    basis = deepcopy(json.loads((ROOT / 'data/kant-described-explanations-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='kant-reasoned-judgment-basis-v1', document='examples/v013/kant-reasoned-judgment.noema')
    declarations = {d['name']: d for d in parse(text)['declarations']}
    records = (
        ('fa', ['person', 'judgment', 'situation'], 'その状況で、その人がその判断行為を行う。判断の正しさや、その人の理解能力の所有だけでは成立しない。'),
        ('fb', ['judgment', 'matter', 'situation'], 'その状況で、その判断が指定した事柄についての判断である。別の事柄に対する正しい判断で代用しない。'),
        ('fc', ['judgment', 'reason', 'situation'], 'その状況で、その判断において指定した理由が用いられる。理由が存在することや、事後的に誰かが理由を付けることだけでは成立しない。'),
        ('fd', ['reason', 'judgment', 'situation'], 'その状況の評価基準で、その理由が指定した判断を支える。理由として用いたことだけから支持の成立を推定しない。規範的な評価の基準自体は別途明示する。'),
        ('fe', ['person', 'matter', 'situation'], 'その状況でその人の判断能力を評価する対象として採る事柄。全ての事柄や人生全体を無条件に対象としない。'))
    for name, labels, meaning in records:
        basis['primitives'].append({'symbol': name, 'parameters': declarations[name]['parameters'],
            'result': 'truth', 'arguments': labels, 'meaning_ja': meaning})
    generic = generic_composed()[1]
    basis['definitions'].update({name: generic['definitions'][name] for name in ('ya', 'yb')})
    basis['definitions'].update({
        'bk': 'ラテン語の呼びかけの目的について、理由に支えられた判断を指定範囲の事柄について行えるというybの構成的な読解を置く。ドイツ語のbmとは別の定義である。',
        'bl': 'bkの判断能力へ向けて勇気を持つよう促す発話。実行や成功を断言しない。audeの遂行的な含意全体を定義したとはしない。'})
    basis['unresolved'] += [
        'この文書ではラテン語のbkをbmの別名とする旧草案を置き換えた。説明関係ufは保持するが、blとbnの意味同一性は要求しない。',
        'sapereの分別・判断の語義を参照した構成的な読解であり、理由や評価範囲の形式化は実装上の解釈である。原文がこれらの条件を列挙したとは主張しない。',
        'boは従来のドイツ語の呼びかけbnを標語として指す読みを保持する。ラテン語も含む引用全体への指示範囲は未確定。',
        'ラテン語の原綴り・歴史的含意・audeの行為性、理由の支持規範、原刊確認と全文の意味確認は残る。']
    audit_basis(parse(text), basis)
    return text, basis


def main():
    for compose, filename in ((generic_composed, 'data/reasoned-judgment-basis-v1.json'),
                              (source_composed, 'data/kant-reasoned-judgment-basis-v1.json')):
        text, basis = compose()
        for name, body in {basis['document']: text, filename: json.dumps(basis, ensure_ascii=False, indent=2) + '\n'}.items():
            path = ROOT / name
            if path.exists():
                if path.read_text(encoding='utf-8') != body:
                    raise ValueError('Stored reasoned judgment differs: ' + name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream:
                    stream.write(body)
    print('Reasoned judgment goal differs from mere use of an owned faculty')


if __name__ == '__main__':
    main()
