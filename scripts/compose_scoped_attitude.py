"""Separate persistence from attitude opportunities, and fix their conventions."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_falling_depiction import ROOT, closure

PARENT='examples/v016/kant-relative-past.noema'
PARENT_BASIS='data/relative-past-basis-v1.json'
FULL='examples/v016/kant-scoped-attitude.noema'
CORE='examples/v016/scoped-attitude-core.noema'
LIBRARY='examples/v016/persistence-attitude-scopes.noema'
BASIS='data/scoped-attitude-basis-v1.json'
ANNOTATIONS='data/scoped-attitude-identifiers-v1.json'
MEANINGS={
    'ib':'この文脈が指定する開始点から、その人の生涯の終わりまでの継続を評価する全範囲。出生からか、成人後の時点からか、基準時から残る生涯かを文脈で明示する。状態や態度が成立した点だけを選び直した範囲、都合よく途中で切った観測期間ではない。履歴内の非空で間の抜けない範囲であることはtbで検査するが、実世界の履歴の完全性や終点の同定は解釈の根拠を要する。',
    'id':'その状況で、その人が記述された性質に該当する自分の状態を好ましく受け入れる態度を保持している。瞬間的な快感や、その状態を絶えず意識していることではなく、睡眠などだけを理由に態度の消滅とはしない。積極的に嫌って抵抗する態度とは区別し、単に無反応・無自覚だから肯定的と補わない。状態の成立、能力、強制の不在、意図的な選択や将来の全出来事を予見することは含意しない。',
    'rqxf':'同じ本人と閉じた性質記述について、履歴内の非空の連続範囲全体で内容が成立し、その範囲内の非空の態度機会の全てで同じ記述への指定した態度が成立する。態度機会は範囲の部分集合であり、連続区間や範囲全体である必要はない。内容は同じ記述から実行して作り、別の内容と態度対象の混同を避ける。',
    'ie':'本人の生涯として指定する全範囲ibが履歴内の非空の連続区間であり、その全範囲で未成熟bfと、同じbfを好ましく受け入れる保持された態度idが成立する。全時点で快感や意識的な選択が生じるという読みではない。rqxfの状態範囲と態度範囲を同じibに固定した、記述の実行を使わない特殊化。',
}


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT_BASIS)


def build():
    old=parent();assert 'rqxf' not in old.entries
    doc=deepcopy(old.document)
    at=next(i for i,d in enumerate(doc['declarations']) if d['name']=='ie')
    prefix=deepcopy(doc);prefix.update(declarations=doc['declarations'][:at],statements=[])
    text='''d rqxf[person a property i[h[a] e] history h[d] c extent h[d] c occasions h[d] c before h[d d] c attitude h[a i[h[a] e] d] c] c[
 w[k tb[v history v extent v before]][
  w[f point d[y[c[v occasions][v point]][c[v extent][v point]]]][
   w[k tc[v extent c[s[v property]][v person]]][k td[v person v property v occasions v attitude]]
  ]
 ]
].'''
    parsed=parse(format_graph(prefix,'compact')+text)
    doc['declarations']=parsed['declarations']+doc['declarations'][at:]
    doc=parse(format_graph(doc,'compact'))
    basis=dict(status='standing_attitude_and_separate_temporal_scopes',document=FULL,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,primitives={},definitions={},
        predecessor_source_sha256=old.source_sha256,
        limitations=['保持された肯定的態度が生涯の範囲で続くという読みを採る。態度自体が一時的に反転する例外を許す別の読みや、原語の全用法まで同一視しない。',
            '生涯の範囲は全範囲を指す規約であり、有限の観測や区間の整合性だけで実際の生涯全体を検証したとはしない。',
            '態度の形成・消失、情緒的な愛着、将来の予見、自由意思の理論を追加しない。',
            '既存ieの構文と定義本体は保持する。新しい一般形は態度機会を別に選べるが、原文の態度を無根拠に弱めるためには使わない。'],
        unresolved=[dict(basis=r['basis'],historical_caveats=r['caveats']) for r in old.lineage])
    for d in doc['declarations']:
        n=d['name'];meaning=MEANINGS[n] if n in MEANINGS else old.entries[n]['meaning_ja']
        if d['kind']=='primitive':
            basis['primitives'][n]=dict(parameters=d['parameters'],result=d['result'],arguments=old.entries[n]['arguments'],meaning_ja=meaning)
        else:basis['definitions'][n]=meaning
    core=deepcopy(doc);core['statements']=[doc['statements'][i] for i in (2,3,11)]
    from noema.meaning_catalog import _references
    core['declarations']=closure(doc,_references(core['statements']))
    library=deepcopy(doc);library.update(declarations=closure(doc,['rqxf']),statements=[])
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/relative-past-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda obj:json.dumps(obj,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    for name,body in build().items():
        p=ROOT/name
        if p.exists():assert p.read_text(encoding='utf-8')==body,name
        else:
            with p.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
    print('Standing attitude and independent scopes composed',flush=True)


if __name__=='__main__':main()
