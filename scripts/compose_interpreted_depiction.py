"""Evaluate the recorded interpretation itself while preserving an unasserted depiction."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT,definition
from scripts.compose_qualified_utterance import closure
from scripts.compose_cast_shadow import LIBRARY as OPTICS,REGION,RELATIONS as OPTICAL
from scripts.compose_described_apprehension import LIBRARY as AFFECT,RELATIONS as EMOTION,DESCRIPTION

PARENT='examples/v016/kant-qualified-utterance.noema'
LIBRARY='examples/v016/interpreted-depiction.noema'
EXAMPLE='examples/v016/interpreted-depiction-example.noema'
SOURCE='examples/v016/kant-interpreted-depiction.noema'
CORE='examples/v016/interpreted-depiction-core.noema'
BASIS='data/interpreted-depiction-basis-v1.json'
TEMPLATE='h['+DESCRIPTION+' h[a d] c d] c'


def definitions():
    return definition('rvu','node a author a target '+DESCRIPTION+' depiction '+DESCRIPTION+' person a mappingcontext d anchor d',
        'w[k qh[v node v author v target v depiction v mappingcontext]][t[c[s[v target]][v person]][v anchor]]')


def additions():
    text='r hzvsource[] a.r hzvblocker[] a.'
    for name,sort in [('contains','h[a a d] c')]+OPTICAL+EMOTION:
        text+='r hzv'+name+'['+sort[2:sort.rfind(']')]+'] c.'
    refs={n:'p hzv'+n for n,t in REGION}
    refs.update(source='k hzvsource[]',blocker='k hzvblocker[]',region='v region',anchor='v point')
    text+=definition('hzvshadow','region a','b point[k rvt['+' '.join(refs[n] for n,t in REGION)+']]','e')
    text+=definition('hzvdepiction','person a','b point[u[k rvm[v person r[p hzvshadow] v point '+
        ' '.join('p hzv'+n for n,t in EMOTION)+']]]','e')
    text+=definition('hzvcondition','target '+DESCRIPTION+' remaining h[a d] c actor a anchor d',
        'w[k rvu[k hztnode[] k wa[] v target r[p hzvdepiction] v actor k wh[] v anchor]][c[v remaining][v actor v anchor]]')
    text+=definition('hzvonly','target '+DESCRIPTION+' remaining h[a d] c anchor d',
        'w[k qh[k hztnode[] k wa[] v target r[p hzvdepiction] k wh[]]]['+
        'k hzuonly[i[actor a point d][k hzvcondition[v target v remaining v actor v point]] v anchor]]')
    text+='r hzvannotation[a a i c['+TEMPLATE+'] a d] c.'
    text+=definition('hzvattribution','',
        'k hzvannotation[k hztnode[] k wa[] r c[p hzvonly] k hztscope[] k wh[]]')
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    library=deepcopy(parent);library['statements']=[];library['declarations']=closure(parent,['qh','qi'])
    library=parse(format_graph(library,'compact')+definitions())
    text=format_graph(library,'compact')+'r jknode[] a.r jkauthor[] a.r jkperson[] a.r jkcontext[] d.r jkanchor[] d.'
    text+='r jktruth[a d] c.r jkpictured[a d] c.r jkarbitrary[d] c.'
    text+=definition('jktarget','person a','b point[k jktruth[v person v point]]','e')
    text+=definition('jkdepiction','person a','b point[k jkpictured[v person v point]]','e')
    condition='k rvu[k jknode[] k jkauthor[] r[p jktarget] r[p jkdepiction] k jkperson[] k jkcontext[] k jkanchor[]]'
    old='k qi[k jknode[] k jkauthor[] r[p jktarget] r[p jkdepiction] b point[k jkarbitrary[v point]] k jkcontext[]]'
    text+='q['+condition+'].q['+old+'].q[e[r b['+condition+']][r b['+condition+']]].'
    example=parse(text)
    doc=deepcopy(parent);statements=doc['statements'];doc['statements']=[];names={d['name']:d for d in doc['declarations']}
    for path in (OPTICS,AFFECT):
        for decl in parse((ROOT/path).read_text(encoding='utf-8'))['declarations']:
            if decl['name'] in names:assert decl==names[decl['name']],decl['name']
            else:doc['declarations'].append(decl);names[decl['name']]=decl
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k hzvattribution[]].')
    doc['statements']=statements[:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {LIBRARY:format_graph(library,'compact')+'\n',EXAMPLE:format_graph(example,'compact')+'\n',
        SOURCE:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n'}


def basis():
    return dict(status='explicit_open_figurative_reading_with_composed_literal_depiction',parent=PARENT,
        definitions={
            'rvu':'同じ著者・箇所・解釈文脈のqhで結ばれた対象記述そのものを評価し、同じ本人について指定評価文脈で成立することを要求する。別に渡された内容で対象記述の真理を代用しない。描写記述は実行しない。',
            'hzvshadow':'同じ光源・遮蔽物の直接光を失う非空領域というrvtの性質。影という綴りへの置換ではない。',
            'hzvdepiction':'hzvshadowの記述へ向けられた、不利益を予期する不快な心理状態rvmが本人に成立しないという字義的な描写。影の実在も、この描写の現実の真理も本文には追加しない。',
            'hzvcondition':'明示的に渡された意図された性質記述をrvuで同じ候補者・評価時点へ結び、残りの資格条件と連言する。',
            'hzvonly':'比喩の対応qhを独立に要求し、hzvconditionを既存hzuonlyへ渡す。対象者が空・発話不能だからという理由で、未成立の対応を成立済みにしない。',
            'hzvattribution':'部分ひな形の閉じた記述を、同じ箇所・著者・範囲・帰属文脈に解釈注記として帰属する。'},
        contexts={'mapping':'whは著者・箇所に関する描写と意図された記述の対応を置く文脈。',
            'evaluation':'anchorは候補者の能力・意図された性質・発言可能性を評価する文脈。同じ時点であると暗黙に固定しない。'},
        unresolved=[
            '意図された性質の記述targetは未充足である。影を政治的な不安や迷信等へ勝手に置き換えず、解釈の決定と根拠は別途必要。',
            '原文の比喩的な読みを採る場合の部分構成であり、唯一の読みと確定した訳ではない。qhは対応を入力として受け、対応の妥当性自体を証明しない。',
            'rvuは既存qiの自由な内容引数を使わない後継操作である。qiの歴史的な定義と資料は変更しない。',
            '字義的な描写のrvmは恐れの一側面を表す候補であり、rvtも幾何光学の直接光に限定される。両定義の未解決事項を引き継ぐ。',
            'remainingには軍隊・公的平穏等の未充足条件が残る。啓蒙の全意味、強調、同時性、自由国との対比、段落後半と全文の意味確認も未完。',
            '本文の解釈注記はひな形の記述を保持するだけで、意図された性質、比喩の対応、光学的な影、心理状態、能力を実行評価しない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
