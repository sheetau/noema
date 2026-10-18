"""Separate undertaking a described task from merely having courage for it."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-answer-heading.noema'
PARENT_BASIS='data/answer-heading-basis-v1.json'
FULL='examples/v016/kant-courageous-undertaking.noema'
CORE='examples/v016/courageous-undertaking-core.noema'
LIBRARY='examples/v016/courageous-undertaking.noema'
BASIS='data/courageous-undertaking-basis-v1.json'
ANNOTATIONS='data/courageous-undertaking-identifiers-v1.json'
MEANINGS={
 'hzs4':'同じ本人・状況・閉じた目標の性質記述について、十分な勇気hzioがあり、本人がその目標を試みる行為f5が実際に生起dgし、その行為を本人が行うdfという内容。勇気だけ、別人の試み、別の目標への試みは足りない。目標の達成・能力・成功や客観的危険を要求しない。',
 'hzs5':'hzs4の勇気を伴う取り組みを求める命令型の発話。引用・発話の成立から、求めた取り組みの実行や成功は推論しない。',
 'hzs6':'ラテン語のaudeを、既存bkの判断能力という目標へ勇気を持って取り組むよう促す読み。勇気だけを求める旧blと比較可能にし、ドイツ語bnとは別の内容を保持する。sapereの能力としての構成的な読みは継承し、その唯一性や全語義の確認は主張しない。',
 'hzs7':'更新したラテン語hzs6と既存のドイツ語bnを、この順序で含む二つの閉じた発話記述。片方だけの標語や両者の同義性に縮めない。',
 'hzsa':'既存gbによる標語の位置付けをhzs7の二つの発話記述に適用する内容。啓蒙の性質biと標語の読みは従来どおりで、実行の成立は主張しない。',
 'hzsb':'冒頭六箇所の提示。旧cpのラテン語引用blをhzs6へ、標語boをhzsaへ更新する。定義・条件・ドイツ語引用・説明の向き・帰結・順序は保持する。引用された勇気・取り組み・目標を実行評価しない。',
}


def replace_symbols(value,mapping):
    if isinstance(value,dict):
        return {k:mapping.get(v,v) if k=='symbol' else replace_symbols(v,mapping) for k,v in value.items()}
    if isinstance(value,list):return [replace_symbols(v,mapping) for v in value]
    return value


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not set(MEANINGS)&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    addition='''
d hzs4[person a goal i[h[a] e]] e[b scene[
 w[k hzio[v person v goal v scene]][g act a[
  w[k f5[v person v act v goal v scene]][w[k df[v person v act v scene]][k dg[v act v scene]]]
 ]]
]].
d hzs5[person a goal i[h[a] e]] f[j m[k hzs4[v person v goal]]].
d hzs6[person a] f[k hzs5[v person r[p bk]]].
d hzs7[] j[i[f]][l[i[f]][r[k hzs6[k ao[]]] r[k bn[k ao[]]]]].
'''
    doc=parse(format_graph(doc,'compact')+addition)
    lookup={d['name']:d for d in doc['declarations']}
    for parent,name,mapping in [('bo','hzsa',{'bt':'hzs7'}),('cp','hzsb',{'bl':'hzs6','bo':'hzsa'})]:
        declaration=replace_symbols(deepcopy(lookup[parent]),mapping);declaration['name']=name
        doc['declarations'].append(declaration)
    doc['statements']=deepcopy(statements)
    doc['statements'][1]=replace_symbols(statements[1],{'cp':'hzsb'})
    doc=parse(format_graph(doc,'compact'))
    core=deepcopy(doc);core['declarations']=closure(doc,['hzsb','wa','wh','wb','wc','wd','we','wf','wg'])
    core['statements']=[doc['statements'][1]]
    library=deepcopy(doc);library['declarations']=closure(doc,['hzs4','hzs5']);library['statements']=[]
    basis=dict(status='explicit_practical_reading_of_latin_directive',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,primitives={},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},
        limitations=[
            'audeを勇気を伴う取り組みの要求と読む候補。命令の充足条件へ試みを加えるが、命令を引用した本文は実際の試みや達成を断言しない。',
            'bkの判断能力としてのsapereの読みは独立した検討項目である。これを知恵一般やラテン語全用法の定義にはしない。',
            '勇気と実際の試みを既存関係で結ぶ。客観的危険、恐れの実在、恐れの克服過程、成功、唯一の試みを追加しない。',
            '旧bl・cp・boは比較用に残す。本文の第二文はhzsbへ切り替え、標語も同じ更新済みの発話を指す。',
            '第一段落全体は未確認。語義・程度基準・条件の解釈などの残件を、型検査や有限モデルだけで解決済みと扱わない。'])
    body=format_graph(doc,'compact')+'\n'
    annotations=json.loads((ROOT/'data/answer-heading-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',ANNOTATIONS:json.dumps(annotations,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Courage, actual undertaking and the quoted directive separated',flush=True)


if __name__=='__main__':main()
