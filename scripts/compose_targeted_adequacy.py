"""Bind the opening deficits to the same described goal, not an implicit task."""
from copy import deepcopy
import hashlib
import json

from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-author-credit.noema'
PARENT_BASIS='data/author-credit-basis-v1.json'
FULL='examples/v016/kant-targeted-adequacy.noema'
LIBRARY='examples/v016/targeted-adequacy.noema'
BASIS='data/targeted-adequacy-basis-v1.json'
ANNOTATIONS='data/targeted-adequacy-identifiers-v1.json'
PRIMITIVES={
 'hzin':'指定状況で、同じ本人が指定された目標の性質記述を本人について実現することに向け、文脈上十分な決意を持つ。対象記述を明示し、別の目標への決意から推定しない。決意の採用・維持という態度であり、行為の実行や成功の保証ではない。十分さの閾値は文脈に依存する。',
 'hzio':'指定状況で、同じ本人が指定された目標の性質記述を本人について実現することに向け、文脈上十分な勇気を持つ。別の目標への勇気から推定しない。恐れ・困難に直面して行動へ向かう態度の十分さであり、客観的危険の有無・実行・成功を含意しない。',
 'hzip':'指定状況で、同じ本人が指定された目標の性質記述を本人について実現するのに、理解能力が文脈上十分である。対象の区別・判断に使う能力の十分さをその目標について評価し、別の目標での十分さ、実際の使用、決意や勇気の十分さから推定しない。',
}
MEANINGS={
 'rqqy':'本人の自立的使用bbに向けた決意hzinが、同じ本人・評価状況で十分でないという内容。対象を省略した旧bqとは区別する。',
 'rqqz':'本人の自立的使用bbに向けた勇気hzioが、同じ本人・評価状況で十分でないという内容。対象を省略した旧brとは区別する。',
 'rqrh':'同じ本人・評価状況でrqqyとrqqzがともに成立する内容。決意と勇気の不足を連言とする先行の読みを維持し、いずれも同じ自立的使用bbへ向ける。',
 'rqri':'本人の自立的使用bbに必要な理解能力hzipが、同じ本人・評価状況で十分でないという内容。対象を省略した旧bjとは区別する。',
 'bd':'bcの未成熟にあり、同じ本人の自立的使用bbへ向けた決意と勇気の不足rqrhが、その未成熟bfへ実際に因果的に寄与し、同じ目標に必要な理解能力の不足rqriは実際の原因ではない。単なる原因説明への採用では満たさない。',
 'be':'同じ本人の自己に原因が帰せられた未成熟から自立的使用の能力への変化。ag・bd・xd・laを満たし、同じ過程の構成内容を本人のbpからupへの変化としてhzidに結ぶ。bdの因果要因は同じ自立的使用bbについての不足を使う。責任概念全体と能力評価の妥当性は未完。',
}


def build():
    catalog=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(catalog.document)
    index=next(i for i,d in enumerate(doc['declarations']) if d['name']=='bd')
    prefix=deepcopy(doc);prefix['declarations']=prefix['declarations'][:index];prefix['statements']=[]
    code='i[h[a] e]'
    additions=''.join('r '+n+'[a '+code+' d] c.' for n in PRIMITIVES)
    for n,relation in [('rqqy','hzin'),('rqqz','hzio'),('rqri','hzip')]:
        additions+='d '+n+'[person a] e[b scene[u[k '+relation+'[v person r[p bb] v scene]]]].'
    additions+='d rqrh[person a] e[b scene[w[t[k rqqy[v person]][v scene]][t[k rqqz[v person]][v scene]]]].'
    extended=parse(format_graph(prefix,'compact')+additions)
    doc['declarations'][index:index]=extended['declarations'][index:]
    def rewrite(node):
        if isinstance(node,dict):
            return {k:({'bs':'rqrh','bj':'rqri'}.get(v,v) if k=='symbol' else rewrite(v)) for k,v in node.items()}
        if isinstance(node,list):return [rewrite(v) for v in node]
        return node
    bd=next(d for d in doc['declarations'] if d['name']=='bd');bd['body']=rewrite(bd['body'])
    doc=parse(format_graph(doc,'compact'));lib=deepcopy(doc);lib['statements']=[]
    lib['declarations']=closure(doc,['bi','ed','rqqv','bs','bj'])
    primitives=[];definitions={}
    for d in doc['declarations']:
        n=d['name'];old=catalog.entries.get(n)
        if d['kind']=='primitive':
            primitives.append(dict(symbol=n,parameters=d['parameters'],result=d['result'],
                arguments=['本人','本人について実現する目標の性質記述','評価状況'] if n in PRIMITIVES else old['arguments'],
                meaning_ja=PRIMITIVES[n] if n in PRIMITIVES else old['meaning_ja']))
        else:definitions[n]=MEANINGS[n] if n in MEANINGS else old['meaning_ja']
    basis=dict(status='opening_deficits_bound_to_one_explicit_goal',document=FULL,library=LIBRARY,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,
        revision=dict(changed_bodies=['bd'],new_primitives=list(PRIMITIVES),new_definitions=['rqqy','rqqz','rqri','rqrh'],
            clarified_inherited_conventions=['be'],statement_syntax_unchanged=True),primitives=primitives,definitions=definitions,
        limitations=['対象となる目標を明示した修正であり、十分さの程度基準、決意と勇気の不足の連言、wennの条件提示と自己責任の全意味は未完。',
            '旧ai・aj・akとbq・br・bj・bsは他の箇所の意味を黙って変えないため保存する。目標が未指定の評価を新しい評価へ自動変換しない。',
            '目標は性質の記述で指し、同じ本人へ適用する。目標を実際に達成したことや、その記述の真偽を評価してから態度を認める条件にはしない。',
            '異なる記述の同義性は自動判定しない。本文の能力・理解力・自立的使用の一般的な基礎説明と全段落の意味確認は残る。',
            '署名の依存宣言と本文文は変えていないが、版を更新したため、その単位の確認も新しい記録へ明示的に結び直す。'],
        unresolved=[dict(basis=row['basis'],historical_caveats=row['caveats']) for row in catalog.lineage],
        predecessor_source_sha256=catalog.source_sha256)
    body=format_graph(doc,'compact')+'\n'
    annotations=json.loads((ROOT/'data/author-credit-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(annotations,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Opening deficits now name the same goal; legacy assessments remain separate')


if __name__=='__main__':main()
