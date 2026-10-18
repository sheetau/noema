"""Ask for a characterization, not merely an extensionally matching alias."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT,closure

PARENT='examples/v016/kant-bodily-acquisition.noema'
PARENT_BASIS='data/bodily-acquisition-basis-v1.json'
FULL='examples/v016/kant-explanatory-question.noema'
CORE='examples/v016/explanatory-question-core.noema'
LIBRARY='examples/v016/explanatory-question.noema'
BASIS='data/explanatory-question-basis-v1.json'
ANNOTATIONS='data/explanatory-question-identifiers-v1.json'
CODE='i[h[a] e]'
CRITERION='h['+CODE+' '+CODE+' d] c'
CCODE='i['+CRITERION+']'
QUESTION='g['+CODE+']'
QCODE='i b['+QUESTION+']'
MEANINGS={
 'rqwc':'同じ参照と候補について、rqqpの外延条件と、指定文脈で参照の構成・成立条件を明らかにする説明としての条件をともに求める。外延が同じだけの別名を自動で説明と認めない。',
 'rqwd':'同じ参照・評価文脈・説明基準の記述から、rqwcを満たす性質記述を求める質問を作る。答えの存在・唯一性や聞き手の理解の成功を追加主張しない。',
 'rqwe':'参照・文脈・説明基準の閉じた記述を保って、rqwdの適用の層1記述を合成する。構成時に文脈・基準・参照内容や候補の判定を実行しない。',
 'rqwf':'同じ文脈記述を評価して、別々の問いと回答の箇所を同じ著者へ結ぶ。rqweの問いの提示、指定説明候補の提示、本文順序、回答としての提示を求める。候補が実際に正しい・十分であるかは実行しない。',
 'hzv7':'第一段落のbiと同じ啓蒙の意味内容について、表題・冒頭の文脈whでhzv6の説明を求める性質記述型の問い。現在の対象例を列挙する問いや単なる別名を求める問いとは分ける。',
 'hzva':'著者waが表題箇所hziaに、この文脈での啓蒙の説明を求める問いを提示していること。答えの正しさや存在、現実の聞き手への依頼を含めない。',
 'hzvb':'hzvaと同じ質問記述を、冒頭wbでのbiの説明提示へ回答として接続する。旧hzicの外延一致だけの質問への接続を置き換え、本文全体の説明の十分性は認定しない。',
}
LIMITS=[
 '「何か」を、この文脈で概念の内容・構成を明らかにする説明を求める問いとして読む。対象の実例・別名・測定値だけを求める問いとはしない。自然言語のwhat・wasの全用法の定義ではない。',
 'hzv6は二つの記述と文脈の間の説明関係であり、外延一致や構文同一性へ還元しない。候補が成立条件を明らかにするかの判断基準を意味規約として持つ。学習した翻訳規則や原文ごとの答えの表ではない。',
 '説明として適切かを判定する汎用アルゴリズムや、全読者が理解するという心理学的保証は要求しない。意味規約を持つ関係を記述できることと、現実の全候補の真偽を自動判定することは別である。',
 '参照と候補が同じ構文でも、定義を展開して構成を明らかにする用途なら説明たりうる。単に違う文字列なら説明だとも、同じ記述なら必ず循環的だとも判定しない。',
 'biは同じ本人の帰責された未成熟から自立的な行使能力への移行という、第一段落で確認した内容記述。表題の問いはその概念の説明を求めるが、著者自身の答えや哲学的主張が真であることを先取りしない。',
 '質問記述は脱引用を含むため層1を保つ。全候補の有限列挙、答えの生成、自然言語の自動翻訳は行わない。',
 '本文先頭の旧質問接続を質問の提示へ改訂し、同じ新質問と冒頭の回答との接続を末尾へ移す。他の39文と九つの既存意味判断を保持する。表題全体の判断は別の確認記録で行う。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def definitions():
    text='d rqwc[reference '+CODE+' candidate '+CODE+' context d explains '+CRITERION+'] c[w[k rqqp[v reference v candidate]][c[v explains][v reference v candidate v context]]].'
    fields='reference '+CODE+' context i[d] criterion '+CCODE
    text+='d rqwd['+fields+'] '+QUESTION+'[j v[i[candidate '+CODE+'][k rqwc[v reference v candidate s[v context] s[v criterion]]]]].'
    text+='d rqwe['+fields+'] '+QCODE+'[o a[r b[p rqwd]][o r[v reference] o r[v context] o r[v criterion]]].'
    pair='questionnode a answernode a author a '+fields+' answer '+CODE+' presents h[a a '+QCODE+' d] c defines h[a a '+CODE+' d] c before h[a a d] c responds h[a a a d] c'
    clauses=['u[e[v questionnode][v answernode]]',
        'c[v presents][v questionnode v author k rqwe[v reference v context v criterion] s[v context]]',
        'c[v defines][v answernode v author v answer s[v context]]',
        'c[v before][v questionnode v answernode s[v context]]',
        'c[v responds][v author v questionnode v answernode s[v context]]']
    body=clauses[-1]
    for clause in reversed(clauses[:-1]):body='w['+clause+']['+body+']'
    text+='d rqwf['+pair+'] c['+body+'].'
    text+='r hzv6['+CODE+' '+CODE+' d] c.'
    args='r[p bi] r[k wh[]] r[p hzv6]'
    text+='d hzv7[] '+QUESTION+'[k rqwd['+args+']].'
    text+='d hzva[] c[k hzib[k hzia[] k wa[] k rqwe['+args+'] k wh[]]].'
    text+='d hzvb[] c[k rqwf[k hzia[] k wb[] k wa[] '+args+' r[p bi] p hzib p ua p ue p hzcs]].'
    return text


def build():
    cat=parent();doc=deepcopy(cat.document);old=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    assert not (set(MEANINGS)|{'hzv6'})&set(cat.entries)
    assert old[0]==dict(kind='assert',body=dict(kind='call',symbol='hzic',arguments=[]))
    doc=parse(format_graph(doc,'compact')+definitions()+'s[k hzva[]].s[k hzvb[]].')
    doc['statements']=doc['statements'][:1]+old[1:]+doc['statements'][1:]
    core=deepcopy(doc);core['declarations']=closure(doc,['hzv7','hzva','hzvb']);core['statements']=[doc['statements'][0],doc['statements'][40]]
    lib=deepcopy(doc);lib['declarations']=closure(doc,['rqwf']);lib['statements']=[]
    added=doc['declarations'][size:];primitive=next(d for d in added if d['name']=='hzv6')
    basis=dict(status='explanatory_definition_question_and_nonfactive_response',document=FULL,library=LIBRARY,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={'hzv6':dict(parameters=primitive['parameters'],result=primitive['result'],arguments=['reference','candidate','context'],
            meaning_ja='同じ課題文脈で、候補の性質記述が参照する概念の構成・成立条件を明らかにする説明を与える。外延が偶然同じ実例一覧や未説明の別名だけでは満たさない。記述の定義を展開した説明は使える。著者が提示したという事実、実際の読者の理解、新規性、唯一の正解であることとは区別する。')},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    text=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/bodily-acquisition-identifiers-v1.json').read_text(encoding='utf-8'));ann.update(document=FULL,document_sha256=digest(text.encode('utf-8')))
    enc=lambda obj:json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
    return {FULL:text,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    for name,text in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==text,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
    print('Explanatory question and separate answer presentation composed',flush=True)


if __name__=='__main__':main()
