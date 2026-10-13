"""Represent a task-relative result summary and a new application objective."""
from copy import deepcopy
import json

from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant as q


def definitions():
    who,task,stage,item=map(v,('who','task','stage','item'))
    selected=app(v('selected'),item)
    text=definition('s5o','who a task a stage d selected h[a] c required h[a a a d] c',
        both(q('g','item','a',selected),q('f','item','a',op('z',selected,app(v('required'),who,task,item,stage)))))
    text+=definition('s5p','who a stage d selected h[a] c description h[a] i[e] derived h[a i[e] d] c',
        both(q('g','item','a',selected),q('f','item','a',op('y',selected,
            app(v('derived'),who,app(v('description'),item),stage)))))
    field,scene,example=map(v,('field','scene','example'))
    realized=q('g','example','a',both(app(v('application'),example,app(v('description'),item),field,scene),
        app(v('shown'),who,example,scene)))
    text+=definition('s5q','who a field a selected h[a] c description h[a] i[e] application h[a i[e] a d] c shown h[a a d] c',
        'b scene['+both(q('g','item','a',selected),q('f','item','a',op('y',selected,realized)))+']','e')
    return text


MEANINGS={
    's5o':'指定主体・課題・段階で必要とされる全項目と、指定された非空の項目範囲が過不足なく一致する。別の主体や別の課題の必要性を流用しない。',
    's5p':'指定された非空の項目範囲の全項目について、同じ主体が同じ段階までにその項目の内容の導出を提示したという条件。ここで使うderivedの健全性や内容の真理は別の条件。',
    's5q':'同じ項目範囲の各内容について、指定分野における応用例が少なくとも一つあり、それを同じ主体が当該状況で示したという目標内容。引用して課題とすることと、現にその目標が成立することは区別する。',
}


def generic_composed():
    doc=parse('n:'+definitions())
    basis=dict(version='theory-transition-basis-v1',document='examples/v014/theory-transition.noema',primitives=[],
        definitions=MEANINGS.copy(),unresolved=[
            '課題に何が必要か、どの内容を導出したか、何を応用例とし示したと認めるかは引数の関係で明示する。完全な証明検査器や分野分類の一般理論ではない。'])
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def composed():
    doc=parse((ROOT/'examples/v014/einstein-derivation-modalities.noema').read_text(encoding='utf-8'))
    statements,doc['statements']=doc['statements'],[]
    text=format_graph(doc,'compact')+definitions()+'''
r zm5[a] c.r zm6[a] i[e].r zm7[] a.r zna[a a a d] c.r znb[] a.r znc[] a.
r znd[a a d] c.r zne[] a.r znf[a i[e] a d] c.r zng[a a d] c.
r znh[a a a i[e] d a d] c.r zni[] a.r znj[] a.
'''
    who=k('rd');stage=v('context');scope=k('znb');framework=k('znc')
    derived='i[who a content i[e] stage d][g proof a[k zfr[v proof v who v content v stage '+scope+']]]'
    summary=both(k('s5o',who,k('zm7'),stage,'p zm5','p zna'),k('s5p',who,stage,'p zm5','p zm6',derived),
        q('f','item','a',op('y',k('zm5',v('item')),k('znd',framework,v('item'),stage))),
        k('zt',framework,'r[k saw[]]',scope,stage),k('zt',framework,'r[k sbd[]]',scope,stage))
    text+=definition('s5r','','b context['+summary+']','e')
    text+=definition('s5s','',k('s5q',who,k('zne'),'p zm5','p zm6','p znf','p zng'),'e')
    doc=parse(text);doc['statements']=statements
    doc=parse(format_graph(doc,'compact')+'''
s[k uh[k zni[] k rd[] r[k s5r[]] k znb[] k ri[]]].
s[k znh[k znj[] k rd[] k zm7[] r[k s5s[]] k ri[] k znb[] k ri[]]].
''')
    basis=deepcopy(json.loads((ROOT/'data/einstein-derivation-modalities-basis-v1.json').read_text(encoding='utf-8')))
    basis.update(version='einstein-theory-transition-basis-v1',document='examples/v014/einstein-theory-transition.noema')
    declarations={d['name']:d for d in doc['declarations']}
    for name,args,meaning in (
        ('zm5',['result'],'この総括が対象とする命題項目の範囲。有限の代表例の一覧とはしない。内容はzm6で指し、必要な範囲との一致はs5oで要求する。'),
        ('zm6',['result'],'対象命題項目のNoema内容の記述。新しい自然言語文字列を格納して意味の代用にはしない。具体的な全項目の割当は未完。'),
        ('zm7',[],'前段の結果を用いて応用を示す、著者の次の課題への参照。必要な命題の指定と移行先の目標で同じ参照を使う。'),
        ('zna',['agent','task','result','stage'],'指定主体が指定課題を遂行するため、その段階でこの命題項目を必要とするという関係。論理的必然性や、全ての人に必要な知識を意味しない。'),
        ('znb',[],'総括の対象である前段の第一部の論述範囲。§5末尾の第三系だけの局所仮定範囲とは区別する。'),
        ('znc',[],'二原理に沿うと本文が述べる前段の理論体系への参照。運動学という分野概念の説明をこの識別子だけで済ませない。分野名の語は今回の対応範囲に含めない。'),
        ('znd',['framework','result','stage'],'指定した命題項目が、その段階の指定理論体系に属する。真であることや、他の体系にも属することを含意しない。'),
        ('zne',[],'次に応用を示す対象分野への参照。電磁気学という分野概念の構成は後続の課題であり、この分野名の語は今回の対応範囲に含めない。'),
        ('znf',['example','content','field','scene'],'当該状況で、例が同じ内容を指定分野へ適用する例となるという関係。単なる言及、別の内容の応用、別分野への適用を区別する。一般的な適用の説明は未完。'),
        ('zng',['agent','example','scene'],'指定主体が当該状況までにこの例を提示しているという関係。利用可能な例の存在や後の提示予定だけでは成立しない。'),
        ('znh',['node','author','task','goal','stage','scope','context'],'著者がこの段階から、指定課題に結び付いた記述目標へ取り組むと提示する。目標の達成、課題の解決、後続の提示完了は含意しない。'),
        ('zni',[],'必要な命題を導いたと総括するu0150前半の箇所。'),
        ('znj',[],'同じ命題の応用を示すことへ移るu0150後半の箇所。')):
        d=declarations[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
    basis['definitions'].update(MEANINGS|{
        's5r':'現在段階で著者が次の課題に必要とする非空の全命題について、同じ内容の導出を前段の論述範囲で提示済みと総括する。命題は同じ理論体系に属し、その体系が既存の二原理saw・sbdを使うことを結ぶ。これを二原理からの証明済みという機械判定にはしない。',
        's5s':'総括と同じ命題項目と同じ内容の写像を使い、それぞれの応用例を対象分野で著者が示すという目標内容。課題の提示ではこの内容の記述を渡し、現在成立するとは断言しない。'})
    basis['unresolved'] += [
        'u0150の総括と課題への移行を部分記述した。「Kinematik」「Elektrodynamik」の分野概念そのものは今回の明示範囲から除外し、後続の概念構成へ残す。u0151以降の見出しと本文も未記述。',
        '必要な命題の範囲zm5と内容の割当zm6は、本文が暗示する範囲を指定する規約であり、既存の代表的な一式や有限検査の項目だけで全文の全必要命題を尽くしたとはしない。',
        '二原理に沿うという表現を、同じ理論が両原理を用いる条件へ部分的に接続した。無矛盾性、論理的帰結、原理と理論の完全な同値性を証明したとはしない。',
        '「必要」を次の応用課題に対する必要性へ、「その応用」を各命題に応用例があるという分配的な目標へ部分解釈した。前段全体に対する必要性や、命題群をまとめて用いる集団的な応用との区別は未確定。',
        '導出を提示済みという内容、著者がそう総括した事実、検査器による正当な導出の認定は区別する。適用例と提示行為の基礎説明、原文全体の意味一致確認は未完。']
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def main():
    for builder,name in ((generic_composed,'theory-transition'),(composed,'einstein-theory-transition')):
        text,basis=builder()
        for filename,body in ((basis['document'],text),('data/'+name+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/filename
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored theory transition differs: '+filename)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Task-relative result summary and prospective application goal composed')


if __name__=='__main__':main()
