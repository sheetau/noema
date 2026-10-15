"""Attach an explicitly open qualification template to Kant's upper restriction."""
import json
from copy import deepcopy
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app
from scripts.compose_anchored_ability import ONLY

PARENT='examples/v016/kant-shared-quotation.noema'
ABILITY='examples/v016/anchored-ability.noema'
SOURCE='examples/v016/kant-restricted-utterance.noema'
CORE='examples/v016/restricted-utterance-core.noema'
BASIS='data/restricted-utterance-basis-v1.json'
TEMPLATE='h[h[a d] c d] c'
PROVIDERS=[('population','h[a] c'),('audiencefor','h[a a d] c'),('speakerfor','h[a d] i b[a]'),
    ('hearersfor','h[a d] i b[h[a d] c]'),('contextfor','h[a d] i b[d]')]
PROVIDERS += [(n,t) for n,t in ONLY if n not in ('population','eligible','start','audiencefor','speakerfor','hearersfor','contextfor','template')]


def primitive(name,sort):
    depth=1
    for pos in range(2,len(sort)):
        depth+=(sort[pos]=='[')-(sort[pos]==']')
        if not depth:break
    return 'r '+name+'['+sort[2:pos]+'] '+sort[pos+1:].strip()+'.'


def declarations():
    text=''.join(primitive('hzt'+n,t) for n,t in PROVIDERS)
    refs={n:'p hzt'+n for n,t in ONLY}
    refs.update(start=v('anchor'),template='p hzsquotation',
        eligible='i[actor a]['+app(v('criterion'),v('actor'),v('anchor'))+']',
        audiencefor='i[actor a recipient a][k hztaudiencefor[v actor v recipient v anchor]]')
    for name in ('speakerfor','hearersfor','contextfor'):
        refs[name]='i[actor a][k hzt'+name+'[v actor v anchor]]'
    text+=definition('hztonly','criterion h[a d] c anchor d',k('run',*[refs[n] for n,t in ONLY]))
    text+='r hztnode[] a.r hztscope[] a.r hztannotation[a a i c['+TEMPLATE+'] a d] c.'
    text+=definition('hztattribution','',k('hztannotation',k('hztnode'),k('wa'),'r c[p hztonly]',k('hztscope'),k('wh')))
    return text


def build():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements=doc['statements'];doc['statements']=[]
    names={d['name']:d for d in doc['declarations']}
    for declaration in parse((ROOT/ABILITY).read_text(encoding='utf-8'))['declarations']:
        if declaration['name'] in names:assert declaration==names[declaration['name']],declaration['name']
        else:doc['declarations'].append(declaration)
    doc=parse(format_graph(doc,'compact')+declarations()+'s[k hztattribution[]].')
    doc['statements']=statements+doc['statements']
    lookup={d['name']:d for d in doc['declarations']};pending=_references(doc['statements'][-1:]);keep=set()
    while pending:
        name=pending.pop()
        if name in keep:continue
        keep.add(name);pending.update(_references(lookup[name])-keep)
    core=deepcopy(doc);core['declarations']=[d for d in doc['declarations'] if d['name'] in keep];core['statements']=doc['statements'][-1:]
    return {SOURCE:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n'}


def basis():
    return dict(status='partial_upper_restriction_with_explicit_open_qualification',parent=PARENT,document=SOURCE,
        definitions={
            'hztonly':'資格条件と基準文脈を引数に取る部分ひな形。既存runにより全対象者の参照整合を要求し、同じ話者・聞き手・基準文脈のhzsquotationを発言できる人なら、同じ本人・基準文脈で資格条件を満たすという必要条件を表す。',
            'hztattribution':'原文箇所・著者・部分ひな形の閉じた記述・範囲・文脈に関する解釈注記の帰属。資格条件を埋めた完成主張や、引用の実際の発言・許可・服従を断言しない。'},
        bindings={
            'criterion':'同じ本人と基準文脈を受ける、明示的に未充足の資格条件。原文の啓蒙、影への恐れ、軍隊、公的平穏の意味を説明済みの一語へ置き換えたものではない。',
            'anchor':'発言可能性と資格を評価する同じ基準文脈。著者への帰属文脈whとは別の引数で、刊行日時などへ暗黙に固定しない。',
            'hztpopulation':'限定を調べる対象者範囲。特定の君主一人を原文から勝手に補わない。',
            'hztaudiencefor/hztspeakerfor/hzthearersfor/hztcontextfor':'候補者と同じ基準文脈に対する聞き手範囲と閉じた参照記述。runが指示先を照合する。',
            'hzteventsfor/hztoccurs/hztagent/hztpresents/hztconveys/hztbefore':'同じ引用ひな形の発話列を、同じ話者が順序付きで指定聞き手へ提示する出来事と内容対応。',
            'hztavailable/hztoutcomes/hztselected':'同じ話者・方法・基準文脈についての利用可能性と結果評価。',
            'hztannotation':'第17区間の限定構造に対する部分的な解釈注記。完成した原文の命題との同義性は主張しない。'},
        unresolved=[
            '資格条件の引数は未充足である。啓蒙・影への恐れ・軍隊・公的平穏は今回の対応範囲に含めず、命令・保護・権限の既存定義を原文の同義条件として自動代入しない。',
            '必要条件を表し、条件を満たせば発言できるという十分条件や、条件を満たす人の存在を導かない。空の既知の対象範囲では普遍条件が空虚に真となる。',
            '発言可能性は指定した方法・評価範囲に相対的な操作的読みである。政治的な発言の許容・勇気・効果まで説明したとはしない。',
            'Aber auch、同時性、対比されるFreistaatとwagen、引用中nurの留保、段落後半の議論は未接続である。',
            '引用内の許可と履行指令は既存hzsquotationを保持する。その提示可能性から、内側の内容の真理や要求の履行を推定しない。',
            '今回の原文対応はnur derjenigeとkann das sagenの限定・可能性の部分構造だけで、文章や段落全体の意味確認は未完である。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
