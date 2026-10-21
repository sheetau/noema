"""Correct the matter/person order without rewriting pinned v1 evidence."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import format_graph,parse
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT

PARENT='data/irrational-perpetuation-basis-v1.json'
LIBRARY='examples/v016/spiritual-guardians-v2.noema'
BASIS='data/spiritual-guardians-basis-v2.json'
REPLACEMENTS={'r45e':'r45q','r45h':'r45r','r45i':'r45s','r45k':'r45t','r45p':'r45u'}
MEANINGS={
    'r45q':'同じ政治的共同体の人民r45dについて、本人が同じ役割を持ち、少なくとも一人の他の構成員を指導・監督するdc。同じ相手の宗教的な生き方に関わる同じ事柄をsg[事柄, 相手, 基準]で分類し、その事柄が同じ本人・相手・役割の担当範囲h253rに入る。r45eのsg引数逆順を訂正した定義であり、役割・相手・事柄を別の証人から集めず、全人民を一人で指導するとは要求しない。',
    'r45r':'同じ人民・政治的共同体・固定基準に属する宗教上の後見役r45qが非空であり、全本人・役割・事柄の該当例に、同じ出所から同じ本人の未成熟への要求r45gがある方針内容。未成熟な人や要求済みの役割だけへ対象を絞らず、相手への未成熟要求とは分ける。',
    'r45s':'出所・人民・政治的共同体の正確な三個体列と固定基準から、引数順を訂正したr45rの方針内容を作る。段階2の閉じた記述として渡せ、引用しただけでは方針や未成熟を実行しない。',
    'r45t':'同じ出所・人民・共同体のr45s方針を、同じ整合性基準と固定基準のr45jで不合理と評価する内容。対象を旧r45iに戻さず、方針や本人の未成熟を実行しない。',
    'r45u':'同じ出所・人民・共同体・整合性基準・固定基準について、訂正済み方針r45sへのr45tの評価と、同じr45sから同じ共同体のr45o持続へ至るh253xの帰結を結ぶ。評価と帰結の対象を一致させ、旧r45iを混ぜない。方針や結果を実行しない。',
}
LIMITS=[
    'sgの公開済み意味規約はmatter, person, sceneであるが、旧r45eと検査モデルがward, matter, referenceで共有していた誤りを訂正する。旧定義・検査・報告は履歴として保存し、今後の最終文統合ではr45q/r45r/r45s/r45t/r45uを使う。',
    '新しい基本関係や原文解釈は追加しない。訂正は後見役の対象分類と、その依存先の引用対象へ伝播する。r45dの人民、r45f/gの本人への未成熟要求、r45jの評価、r45l/m/n/oの持続内容はそのまま保持する。',
    '本文95主張はこの誤った依存群をまだ使っておらず、訂正で既存の意味判断を変更しない。最終文146文字は未確認。評価基準の内容指定、全文の参照供給、selbst wieder、Denn、著者帰属を残す。',
]


@lru_cache(None)
def parent():return load_catalog(ROOT,PARENT)


def rename(node):
    if isinstance(node,dict):return {k:REPLACEMENTS.get(v,v) if k in ('name','symbol') and isinstance(v,str) else rename(v) for k,v in node.items()}
    if isinstance(node,list):return [rename(v) for v in node]
    return node


def declarations():
    old=parent();rows=[]
    for n in REPLACEMENTS:
        d=rename(deepcopy(old.entries[n]['declaration']))
        if n=='r45e':
            calls=[]
            def correct(node):
                if isinstance(node,dict):
                    if node.get('kind')=='call' and node.get('symbol')=='sg':
                        calls.append(node);node['arguments'][0],node['arguments'][1]=node['arguments'][1],node['arguments'][0]
                    for value in node.values():correct(value)
                elif isinstance(node,list):
                    for value in node:correct(value)
            correct(d);assert len(calls)==1
        rows.append(d)
    return rows


def build():
    old=parent();doc=deepcopy(old.document);assert not set(MEANINGS)&set(old.entries)
    doc['declarations']+=declarations();doc=parse(format_graph(doc,'compact'));assert not doc['statements']
    basis=dict(status='corrected_religious_matter_person_order_and_policy_targets',document=LIBRARY,
        primitives={n:dict(parameters=e['declaration']['parameters'],result=e['declaration']['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in old.entries.items() if e['kind']=='primitive'},
        definitions={n:e['meaning_ja'] for n,e in old.entries.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in old.entries.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(old.source_sha256)},
        superseded_definitions=REPLACEMENTS,limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
