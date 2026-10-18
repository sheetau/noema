"""Frame the current document as an answer to its following title question."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_calendar_dateline import conjunction

PARENT='examples/v016/kant-shared-public-scope.noema'
PARENT_BASIS='data/shared-public-scope-basis-v1.json'
FULL='examples/v016/kant-answer-heading.noema'
CORE='examples/v016/answer-heading-core.noema'
LIBRARY='examples/v016/answer-heading.noema'
BASIS='data/answer-heading-basis-v1.json'
ANNOTATIONS='data/answer-heading-identifiers-v1.json'
MEANINGS={
 'rqu5':'文書内にある導入的な言及が、その同じ文書を後続する問いの箇所が表す内容への回答として位置付ける。言及の成立・記載先・回答としての対象・本文順序を同じ文脈で結ぶ。問いと導入箇所は別であり、回答の正しさや説明の十分性は含意しない。',
 'hzs3':'表題の導入hzs2が現在の論説hzik内にあり、その同じ論説を、後続する表題箇所hziaの問いへの回答として位置付ける。既存の表題と冒頭の提示文脈whを共有する。冒頭第一文だけを回答全文とする条件や、脚注での言及だけで表題を代用する条件は加えない。',
}


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not ({'hzs2'}|set(MEANINGS))&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    text='d rqu5[introduction a document a question a context d] c['+conjunction([
        'u[e[v introduction][v question]]','k dg[v introduction v context]',
        'k hzjk[v introduction v document v context]',
        'k hzjj[v introduction v document v question v context]',
        'k ue[v introduction v question v context]'])+'].'
    text+='r hzs2[] a.d hzs3[] c[k rqu5[k hzs2[] k hzik[] k hzia[] k wh[]]].s[k hzs3[]].'
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements+doc['statements']
    core=deepcopy(doc);core['declarations']=closure(doc,['hzs3','hzic','hzlt']);core['statements']=[doc['statements'][i] for i in (0,24,34)]
    library=deepcopy(doc);library['declarations']=closure(doc,['rqu5']);library['statements']=[]
    reference=next(d for d in doc['declarations'] if d['name']=='hzs2')
    basis=dict(status='current_document_framed_as_answer_by_its_heading',document=FULL,parent=PARENT,
        inherited_meaning_basis=PARENT_BASIS,
        primitives={'hzs2':dict(parameters=reference['parameters'],result=reference['result'],arguments=[],
            meaning_ja='カント1784の表題にある導入「Beantwortung der Frage:」の箇所u0005。現在の論説を回答として紹介する表題内の使用を指す。問い本体u0006、脚注の現在の回答への言及hzls、他文献の紹介行為とは区別する。')},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},
        limitations=[
            '表題の名詞句を、現在の論説を後続の問いへの回答として位置付ける導入として読む。新しい基本関係は加えず、既存の言及・文書内の記載・本文順序を合成する。',
            '問いの参照先hziaは既存の本文箇所である。u0005の照応と位置付けを確認しても、u0006の定義質問と啓蒙の語義やu0008の回答内容を確認済みにはしない。',
            '回答という位置付けは正答、十分な説明、原理の真理、執筆・印刷の日時、実際の読者への回答要求を含意しない。',
            '既存34文・全定義と七つの意味確認の依存関係を保存し、表題の位置付けを一文追加する。全体確認は別の明示的なレビューで判断する。'])
    body=format_graph(doc,'compact')+'\n'
    annotations=json.loads((ROOT/'data/cross-reference-identifiers-v1.json').read_text(encoding='utf-8'))
    annotations.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',ANNOTATIONS:json.dumps(annotations,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body
        else:
            with p.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Document answer heading connected to the existing title question',flush=True)


if __name__=='__main__':main()
