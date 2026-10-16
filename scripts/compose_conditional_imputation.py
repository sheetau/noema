"""Separate a causal criterion, self-imputation, and a quoted conditional claim."""
from copy import deepcopy
import hashlib
import json

from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure

PARENT='examples/v016/kant-targeted-adequacy.noema'
PARENT_BASIS='data/targeted-adequacy-basis-v1.json'
FULL='examples/v016/kant-conditional-imputation.noema'
LIBRARY='examples/v016/conditional-imputation.noema'
BASIS='data/conditional-imputation-basis-v1.json'
ANNOTATIONS='data/conditional-imputation-identifiers-v1.json'
CONVENTION='指定状況の評価において、本人について記述された状態が、その本人の選択や不作為に関する落ち度として本人に帰せられる。単に本人の特徴が原因であること、未履行であること、誰かが非難したという発話記録とは区別する。法的制裁、故意、唯一の原因という条件は含めない。一般的な帰責の基本関係として採り、正当な帰責基準の全理論をこの宣言で与えたとはしない。状態の実際の成立は呼出側で別に要求する。'
MEANINGS={
 'rqrj':'同じ本人・状況で未成熟bcが成立し、その同じ状態bfが本人に落ち度として帰せられる。因果条件bdの成立を必要条件にはしない。',
 'rqrk':'評価状況の全対象について、既存bdの因果条件が成立するなら、同じ対象・状況のrqrjの自己に責任がある未成熟が成立する、という条件的な内容。逆向き、該当者の存在、条件の現実の成立は追加しない。',
 'rqrl':'比較用の強い読み。評価状況の全対象でbdの因果条件とrqrjの分類が同値である内容。rqrkの一方向だけの条件と区別し、本文で提示された内容へ自動追加しない。',
 'bd':'同じ目標bbについての決意・勇気の不足rqrhが未成熟bfの実際の原因で、理解能力の不足rqriがその原因ではないという既存の因果条件。今回の読みでは自己に責任がある状態rqrjとは別で、著者はrqrkで前者を後者の十分条件として提示する。',
 'bp':'rqrjの自己に責任がある未成熟を状況ごとに評価する内容。以前のbdの別名から分け、初文の離脱の始状態と第三文の条件の結論が同じ性質を指すようにする。',
 'be':'同じ本人について、rqrjの自己に責任がある未成熟から自立的使用の能力へ移る過程。ag・xd・laと、同じ本人のbpからupへの変化というhzidを保持する。特定の因果条件bdをあらゆる始状態へ必要条件として課さない。',
 'cp':'冒頭六箇所の相違・順序・説明・帰結を結ぶ。第一・第二箇所ではbi・bfの概念説明を提示し、第三箇所では因果条件から帰責された未成熟への一方向の条件rqrkを主張する。引用と標語、談話上の根拠は前版を保持し、内容の真偽は提示関係から推論しない。',
}


def build():
    catalog=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(catalog.document)
    index=next(i for i,d in enumerate(doc['declarations']) if d['name']=='bd')+1
    assert not {d['name'] for d in doc['declarations']}&{'hziq','rqrj','rqrk','rqrl'}
    prefix=deepcopy(doc);prefix['declarations']=prefix['declarations'][:index];prefix['statements']=[]
    additions=('r hziq[a i[h[a] e] d] c.'+
        'd rqrj[person a scene d] c[w[k bc[v person v scene]][k hziq[v person r[p bf] v scene]]].'+
        'd rqrk[] e[b scene[f person a[y[k bd[v person v scene]][k rqrj[v person v scene]]]]].'+
        'd rqrl[] e[b scene[f person a[z[k bd[v person v scene]][k rqrj[v person v scene]]]]].')
    extended=parse(format_graph(prefix,'compact')+additions);doc['declarations'][index:index]=extended['declarations'][index:]
    def replace_calls(value):
        if isinstance(value,dict):
            return {k:('rqrj' if k=='symbol' and v=='bd' else replace_calls(v)) for k,v in value.items()}
        if isinstance(value,list):return [replace_calls(v) for v in value]
        return value
    for d in doc['declarations']:
        if d['name'] in ('bp','be'):d['body']=replace_calls(d['body'])
    cp=next(d for d in doc['declarations'] if d['name']=='cp');changed=[]
    def rewrite_presentation(value):
        if isinstance(value,dict):
            if value.get('kind')=='call' and value.get('symbol')=='ua' and value['arguments'][2]==dict(kind='quote',body=dict(kind='function_ref',symbol='bp')):
                changed.append(value['arguments'][0]);value=deepcopy(value);value['symbol']='uc'
                value['arguments'][2]=dict(kind='quote',body=dict(kind='call',symbol='rqrk',arguments=[]))
                return value
            return {k:rewrite_presentation(v) for k,v in value.items()}
        if isinstance(value,list):return [rewrite_presentation(v) for v in value]
        return value
    cp['body']=rewrite_presentation(cp['body']);assert changed==[dict(kind='variable',name='ve')]
    doc=parse(format_graph(doc,'compact'));lib=deepcopy(doc);lib['statements']=[]
    lib['declarations']=closure(doc,['bi','bd','rqrk','rqrl'])
    primitives=[];definitions={}
    for d in doc['declarations']:
        n=d['name'];old=catalog.entries.get(n)
        if d['kind']=='primitive':
            primitives.append(dict(symbol=n,parameters=d['parameters'],result=d['result'],
                arguments=['本人','本人の状態を指定する性質記述','評価状況'] if n=='hziq' else old['arguments'],
                meaning_ja=CONVENTION if n=='hziq' else old['meaning_ja']))
        else:definitions[n]=MEANINGS[n] if n in MEANINGS else old['meaning_ja']
    basis=dict(status='conditional_reading_separates_causal_criterion_and_self_imputation',document=FULL,library=LIBRARY,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,
        revision=dict(changed_bodies=['bp','be','cp'],new_primitives=['hziq'],new_definitions=['rqrj','rqrk','rqrl'],statement_syntax_unchanged=True),
        primitives=primitives,definitions=definitions,
        limitations=['wennをここでは十分条件を提示する読みとして記述する。定義的な同値の読みの可能性を排除せず、比較用rqrlを残す。この読解の唯一性や段落全体の意味一致は未確認。',
            'hziqは帰責の意味規約を明示した基本関係で、原因だけから責任を推論する一般規則ではない。責任の正当化、程度、例外、評価基準の一般理論は未完。',
            '条件は著者の主張として引用する。引用内容を真と認定せず、偽の条件や誤った帰責も記述できる。',
            '決意と勇気の不足を連言にする読み、十分さ、能力評価範囲、自立的使用と離脱の説明は残る。',
            'bpを参照する全ての記述は、この版で因果条件そのものではなくrqrjを参照する。署名の依存内容は変更しない。'],
        unresolved=[dict(basis=row['basis'],historical_caveats=row['caveats']) for row in catalog.lineage],predecessor_source_sha256=catalog.source_sha256)
    body=format_graph(doc,'compact')+'\n';annotations=json.loads((ROOT/'data/targeted-adequacy-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(annotations,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Causal criterion, imputed state and quoted conditional are distinct')


if __name__=='__main__':main()
