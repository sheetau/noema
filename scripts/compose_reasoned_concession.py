"""Connect a reasoned assertion and a separately attributed expectation contrast."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_careful_prevention import ROOT,closure
from scripts.compose_scalar_backgrounds import PC,PAIR,ORDER

PARENT='examples/v016/kant-careful-prevention.noema'
PARENT_BASIS='data/careful-prevention-basis-v1.json'
FULL='examples/v016/kant-reasoned-concession.noema'
CORE='examples/v016/reasoned-concession-core.noema'
LIBRARY='examples/v016/expected-outcome-contrast.noema'
BASIS='data/reasoned-concession-basis-v1.json'
ANNOTATIONS='data/reasoned-concession-identifiers-v1.json'
MEANINGS={
 'rqvq':'閉じた二内容PとQの記述から、同じ状況でPかつQとなる内容の記述を合成する。構成時には内容を評価しない。',
 'rqvr':'同じ二内容から、同じ状況でPかつQでないという比較側の記述を合成する。Pの否定や、PかつQ全体の否定ではない。',
 'rqvs':'同じPについて、PかつQがPかつ非Qより厳密に見込まれにくいという背景内容。既存rqtsに二つの記述を渡し、同じ視点と基準文脈で比較の反射性・推移性を検査する。数値条件付き確率、論理的含意、因果関係とはしない。',
 'rqvt':'異なる二つの文章箇所について正順が成立し逆順が成立しない。出来事の時間順ではない。文書全体の順序理論を証明するものではない。',
 'hztv':'危険が非常に大きいわけではないe4と、例による萎縮・通常の回避gxを同じ条件側・帰結側に用い、rqvsの比較を著者waが提示する期待の背景とする。単なるgxの否定から全員が恐れないとは導かない。',
 'hztw':'gxの主張記述とhztvの背景記述を、既存rstによる組として保持する。否定や帰属で二つを同一視しない。',
 'hztx':'危険の程度・学習の見込みの理由付けft、萎縮の帰属gy、主張と期待背景の帰属rqtvを結合する。先行の危険提示から、程度・理由・萎縮へ向かう本文順を検査し、引用した内容を実行しない。',
}
REFERENCES={'hztz':'カントu0009のNun istから段落末までの一文にある、zwar・allein・dochを含む対比の範囲。内容や期待が完全に記述済みであることを表す印ではない。'}
LIMITS=[
 '同じ前提を持つ二内容の質的な見込みを比較する読解候補。条件付き確率への変換や、前提だけから期待背景を推論する規則はない。',
 '比較はPかつQとPかつ非Qの間で行う。非Qは全員が萎縮せず全く回避しないという強い反対を含意しない。gx内の有限事例・範囲・通常性の操作化は既存の制約として残る。',
 'ftの学習見込みを理由として接続するが、現実に能力を取得したことや学べるなら安全という論理的含意は追加しない。',
 'hztvの背景は著者の提示への帰属であり、著者の実際の心理状態、全読者の同意、世界の事実の真理を認定しない。zwar・allein・doch全般の唯一の定義ではない。',
 'e4・fs・gxの既存の部分解釈を本文へ接続する。身体的な歩行・転倒との対応、実際の因果と採用された原因説明、通常性の一般理論、語義と第二段落全体の意味確認は残る。',
 '新しい意味の基本関係や文法演算子はない。既存37文と九単位の意味判断を保持し、本文に一つの候補帰属を加える。原文対応文字数と全体確認数は増やさない。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def definitions():
    text=''
    for name,conclusion in [('rqvq','t[v right][v scene]'),('rqvr','u[t[v right][v scene]]')]:
        factory='r b[i[left e right e][b scene[w[t[v left][v scene]]['+conclusion+']]]]'
        text+='d '+name+'[premise '+PC+' outcome '+PC+'] '+PC+'[o a['+factory+'][v premise v outcome]].'
    text+='d rqvs[premise '+PC+' outcome '+PC+' observer a anchor d ranking '+ORDER+'] e['+\
        'k rqts[k rqvq[v premise v outcome] l['+PC+'][k rqvr[v premise v outcome]] v observer v anchor v ranking]].'
    text+='d rqvt[first a second a context d before h[a a d] c] c['+\
        'w[u[e[v first][v second]]][w[c[v before][v first v second v context]][u[c[v before][v second v first v context]]]]].'
    text+='r hztz[] a.'
    text+='d hztv[] e[b anchor[t[k rqvs[r b[k e4[]] r b[k gx[]] k wa[] v anchor p hzpt]][v anchor]]].'
    text+='d hztw[] '+PAIR+'[k rst[r c[k gx[]] r c[k hztv[]]]].'
    clauses=['k ft[]','k gy[]','k rqtv[k g2[] k wa[] k hztw[] k g2[] k hztz[] k wh[]]']
    clauses+=['k rqvt[k '+a+'[] k '+b+'[] k wh[] p ue]' for a,b in [('hzsq','fu'),('fu','fv'),('fv','g2')]]
    body=clauses[-1]
    for clause in reversed(clauses[:-1]):body='w['+clause+']['+body+']'
    return text+'d hztx[] c['+body+'].'


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    assert not (set(MEANINGS)|set(REFERENCES))&set(old.entries)
    doc=parse(format_graph(doc,'compact')+definitions()+'s[k hztx[]].');doc['statements']=statements+doc['statements']
    core=deepcopy(doc);core['declarations']=closure(doc,['hztx']);core['statements']=doc['statements'][-1:]
    library=deepcopy(doc);library['declarations']=closure(doc,['rqvs','rqvt']);library['statements']=[]
    added=doc['declarations'][size:]
    basis=dict(status='reasoned_claim_and_separate_expectation_background',document=FULL,library=LIBRARY,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=REFERENCES[d['name']]) for d in added if d['kind']=='primitive'},
        definitions=MEANINGS,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n';ann=json.loads((ROOT/'data/careful-prevention-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Reason and separate expectation background connected',flush=True)


if __name__=='__main__':main()
