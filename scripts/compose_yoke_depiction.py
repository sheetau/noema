"""Connect a source-anchored bodily release depiction to intellectual autonomy."""
from copy import deepcopy
import json

from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_thinking_disseminators import call as k,conjunction as both
from scripts.compose_described_dissemination import declaration

PARENT='examples/v016/kant-existential-dissemination.noema'
PARENT_BASIS='data/existential-dissemination-basis-v1.json'
FULL='examples/v016/kant-yoke-depiction.noema'
CORE='examples/v016/yoke-depiction-core.noema'
LIBRARY='examples/v016/traction-frame-release.noema'
BASIS='data/yoke-depiction-basis-v1.json'
READING='data/yoke-depiction-reading-v1.json'
PRIMITIVES={
 'hzpg':('[a a d] c',['part','bearer','point'],'この身体部位は同じ身体主体の首・うなじまたは頭側の部位である。足や別個体の身体部位と区別する。身体主体を人間だけに限定せず、比喩中の人にも同じ引数を使える。'),
 'hzph':('[a d] c',['object','point'],'この物体は荷重を支える枠状の構造を持つ。枠の構成材料や部材数、木製であることを固定せず、任意の紐や身体部位そのものとは区別する。'),
 'hzpi':('[a a a a d] c',['object','part','bearer','load','point'],'この装具は、同じ身体主体の同じ部位を介した牽引を、異なる対象へ機械的に伝えるよう構成されている。設計上の結合の働きであり、現在の牽引・移動・労働や強制を要求しない。部位への装着そのものは別条件である。'),
 'hzpj':('[a a a d d] c',['process','object','bearer','earlier','later'],'この過程は、同じ身体主体に装着されていた同じ物体を、その身体から取り外すことに寄与して終結させる。単なる前後の不在や無関係な過程を原因としない。主体が自分で行うことは別条件であり、他者の助力を排除しない。'),
 'hzpo':('[] a',[],'カント1784のu0011、原文位置[254,315)で、自ら未成熟のくびきを脱したことを伝播より前に置く文章箇所。物理的なくびきや、その現実の存在への参照ではない。'),
}
MEANINGS={
 'hzpk':'同じ身体主体の首・頭側の部位に装着された、牽引を別の荷へ伝える枠状の装具という描写。部位・装具・身体主体・荷を共用し、枠や部位だけが別々に存在するだけでは成立しない。牽引具としてのくびきの部分説明であり、社会的抑圧を字義の条件へ加えない。',
 'hzpm':'同じ本人の順序付き履歴で、基準時までに、本人が行う同じ過程によってhzpkの装具を取り外した。前には装着状態があり、後には同じ物体が本人のいずれの部位にも装着されていない。別部位への移し替え、他人だけによる除去、装具の分類だけの変化を成功としない。',
 'hzpn':'基準時までにhzpmの物体・本人の過程・前後点が存在するという描写側の性質。物体や過程を外から一つ選び置きせず、存在量化する。その後の身体運動や、別の拘束の不在、将来の永久的な自由を含めない。',
 'hzpp':'同じ著者wa・段落提示文脈hzp3の箇所hzpoで、本人の知的自立の達成h4qを、本人が牽引用の装具を取り外したhzpnで非字義的に提示する。既存qhで同じ人物の二つの異なる性質記述を対応させる。両方の真理や物理的拘束の現実存在は要求しない。',
}
LIMITS=[
 'FWBの字義と比喩用法、および原刊483頁を参照した採用する部分読解である。くびきの全ての歴史的形態・文化的連想・抑圧の程度・文体上の効果を確定したとはしない。',
 '首・頭側、枠状構造、機械的な牽引の結合、物理的な取り外しへの因果関与を基本関係として明示する。対訳辞書で文を変換する処理はないが、これらの基本概念の自然言語による意味規約は必要である。',
 '身体拘束の足側分類h2fや足枷の除去h2qを首側へ流用しない。装着の一般関係h2e、変化・本人の作用・行為・履歴とrcfだけを再利用する。',
 '知的な対象側h4qは既存の自ら精神へ働きかけて自立を達成する読みを保持する。本人の関与を要求するが唯一の原因とはしない。これが原文の自己解放の唯一の機構であるとは証明しない。',
 '新しい本文主張は比喩の帰属一件である。条件付きの伝播や自由の現実の成立を断言せず、対象側と描写側の出来事や物体を同一視しない。',
 '当該箇所の時間順序と伝播の同一発信者は既存hzod・hzoeで記述する。今回の一項比喩帰属だけで、全文の量化範囲・比較背景・全ての出来事対応まで確定したことにはしない。',
 '既存33文と七単位の確認を保持して一文追加する。すでに部分対応に含まれる範囲の補足なので、新しい原文文字数や意味確認済み単位は加算しない。',
]


def definitions():
    load='g load a['+both('u[e[v load][v bearer]]','u[e[v load][v object]]',
        k('hzpi','v object','v part','v bearer','v load','v point'))+']'
    part='g part a['+both(k('hzpg','v part','v bearer','v point'),
        k('h2e','v object','v part','v bearer','v point'),load)+']'
    text=declaration('hzpk',[('object','a'),('bearer','a')],'e',
        'b point['+both(k('hzph','v object','v point'),part)+']')
    release=k('rcf','i[point d][k ia[v person v anchor v point]]',
        'i[first d last d][k ic[v first v last v anchor]]',
        *('v '+n for n in ('process','object','person','earlier','later')),
        'p hzpk','p ag','p la','p df','p hzpj')
    fields=[('object','a'),('person','a'),('process','a'),('earlier','d'),('later','d'),('anchor','d')]
    text+=declaration('hzpm',fields,'c',both(k('ia','v person','v anchor','v anchor'),
        'x[e[v later][v anchor]][k ic[v later v anchor v anchor]]',release,
        k('dg','v process','v later'),'u[g part a[k h2e[v object v part v person v later]]]'))
    text+=declaration('hzpn',[('person','a')],'e','b anchor[g object a[g process a[g earlier d[g later d['+
        k('hzpm',*('v '+n for n,t in fields))+']]]]]')
    text+=declaration('hzpp',[],'c',k('qh','k hzpo[]','k wa[]','r[p h4q]','r[p hzpn]','k hzp3[]'))
    return text+'s[k hzpp[]].'


def build():
    old=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(old.document)
    assert not (set(PRIMITIVES)|set(MEANINGS))&set(old.entries)
    statements=doc['statements'];doc['statements']=[];size=len(doc['declarations'])
    text=''.join('r '+n+signature+'.' for n,(signature,_,_) in PRIMITIVES.items())
    doc=parse(format_graph(doc,'compact')+text+definitions());doc['statements']=statements+doc['statements']
    core=deepcopy(doc);core['declarations']=closure(doc,['hzpp']);core['statements']=doc['statements'][-1:]
    library=deepcopy(doc);library['declarations']=closure(doc,['hzpm']);library['statements']=[]
    primitives={d['name']:dict(parameters=d['parameters'],result=d['result'],
        arguments=PRIMITIVES[d['name']][1],meaning_ja=PRIMITIVES[d['name']][2])
        for d in doc['declarations'][size:] if d['kind']=='primitive'}
    basis=dict(status='source_anchored_self_release_depiction_not_literal_restraint_claim',document=FULL,
        parent=PARENT,inherited_meaning_basis=PARENT_BASIS,primitives=primitives,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'][size:]},
        reading_manifest=READING,limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n',
        LIBRARY:format_graph(library,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists(): assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream: stream.write(body)
    print('Self-release depiction attached without asserting literal bodily restraint',flush=True)


if __name__=='__main__':main()
