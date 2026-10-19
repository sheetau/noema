"""Give the adopted timidity reading a response disposition, not actual fear."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse, format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT, closure
from scripts.compose_courageous_undertaking import replace_symbols

PARENT='examples/v016/kant-generalized-deterrence.noema'
PARENT_BASIS='data/generalized-deterrence-basis-v1.json'
FULL='examples/v016/kant-fear-proneness.noema'
CORE='examples/v016/fear-proneness-core.noema'
LIBRARY='examples/v016/fear-proneness.noema'
BASIS='data/fear-proneness-basis-v1.json'
ANNOTATIONS='data/fear-proneness-identifiers-v1.json'
MAPPING={'hzub':'r2br','r2bj':'r2bs','r2bk':'r2bt','r2bl':'r2bu','r2bm':'r2bv','r2bn':'r2bw','r2bo':'r2bx'}
PRIMITIVES={
 'hzys':(['person','goal','anchor','candidate'],'同じ本人・活動記述・基準の心理的条件を保ち、活動へ向かう試みについて害の手掛かりに接する仮定の比較状況。手掛かりは背景の強度基準で弱い刺激まで含む。実際の危険の大きさとは区別し、恐れたかどうかで範囲を選ばない。学習や別の性向の獲得により本人を交換する状況は含めない。何が弱い刺激かと比較範囲の適切さは解釈入力として明示する。'),
 'hzyt':(['person','goal','anchor','preferred','other'],'同じ本人・活動記述・基準の比較状況について、刺激の受容や妨害などの背景条件による通常性の厳密な優先関係。恐れの成立そのものを選別基準としない。非反射性・推移性・極小状況への到達条件は既存rqt4で検査する。'),
}
MEANINGS={
 'r2bp':'同じ本人に、活動bbへ向かう後続の試みgqが少なくとも一つあり、その試みに伴う害への恐れmcが同じ状況で成立する。十分な勇気の欠如や実際の回避は要求しない。',
 'r2bq':'同じ事例の本人について、基準の心理的条件を保ち弱い害の手掛かりにも接する比較状況hzysと、その通常性hzytを既存hzq6へ渡す。非空の通常候補すべてでr2bpが成立する応答傾向。基準で現在恐れていること、勇気がないこと、実際に回避することとは区別する。',
 'r2br':'同じ事例で先行例の認識grと恐れやすい傾向r2bqが成立し、前者が後者に実際に因果的に寄与する。因果の結果記述もr2bqへ固定し、旧来の一時的状態hzuaへの原因では代用しない。',
 'r2bs':'通常比較状況の通常事例で、同じ先行例が恐れやすい傾向へ寄与するr2brを要求する。外側の事例一般化と、内側の本人の反応傾向を別々に束縛する。',
 'r2bt':'同じ基準における因果的な恐れやすさの一般化r2bsと、既存r2biの因果的回避の頻度を合わせる。傾向の成立だけから実際の回避を導かない。',
 'r2bu':'更新したr2btを著者へ帰属し、学習の見込みに後続する本文順を保持する。',
 'r2bv':'同じ危険の程度e4と更新したr2btを既存の質的期待比較へ渡す。比較両側のQを同じ新しい内容にする。',
 'r2bw':'更新したr2btと期待背景r2bvを同じ本文箇所の主張と背景の組にする。',
 'r2bx':'危険の程度、学習を理由とする関係、著者と本文順を保持し、恐れやすさと回避頻度の主張・期待背景を同じ範囲へ帰属する。',
}
LIMITS=[
 'schüchternを、この活動へ向かう場面で害の手掛かりに恐れやすい性向として読む。Adelungの受動的語義を根拠とする文脈上の選択であり、同語の全語義や唯一の歴史的読解を主張しない。',
 '傾向は生涯の性格でも不可逆の変化でもない。基準の心理的条件を固定する局所的な性向であり、その持続期間や以前の不存在は原文から補わない。',
 '通常候補での応答は既存hzq6で記述する。弱い刺激、比較範囲、妨害と通常性の根拠は明示的な解釈入力であり、心理学的な測定や反事実的妥当性を形式だけで証明しない。',
 '勇気と恐れやすさは別条件とする。行動する勇気がありながら恐れやすい人も、恐れをまだ感じていない人もこの性向を持ち得る。回避は別節の既存hzucとr2biで扱う。',
 '例の認識から性向への因果的寄与を要求するが、唯一の原因、新たな取得の前後比較、永続性は追加しない。架空の例、有限等重みの頻度、学習の見込み、末尾一文全体の確認は残る。',
 '本文52文の第37文だけを改訂する。先頭六文と十一単位の確認を保持し、新しい対応範囲や意味確認済み分量を加算しない。',
]


@lru_cache(None)
def parent(): return load_catalog(ROOT,PARENT_BASIS)


def definitions():
    return '''
r hzys[a i[h[a] e] d d] c.r hzyt[a i[h[a] e] d d d] c.
d r2bp[person a] e[b scene[g act a[w[k gq[v person v act v scene]][k mc[v person v act v scene]]]]].
d r2bq[item a] e[c[k hzq6[p r2bp
 i[person a anchor d scene d][k hzys[v person r[p bb] v anchor v scene]]
 i[person a anchor d first d last d][k hzyt[v person r[p bb] v anchor v first v last]]
]][k gd[v item]]].
d r2br[item a] e[b scene[w[t[k gr[v item]][v scene]][w[t[k r2bq[v item]][v scene]][
 k hzie[v item r[p gr] v item r[p r2bq] v scene]
]]]].
'''


def build():
    old=parent();doc=deepcopy(old.document);statements=doc['statements'];doc['statements']=[]
    assert not (set(MEANINGS)|set(PRIMITIVES))&set(old.entries)
    size=len(doc['declarations']);doc=parse(format_graph(doc,'compact')+definitions())
    for name in ('r2bj','r2bk','r2bl','r2bm','r2bn','r2bo'):
        row=replace_symbols(deepcopy(old.entries[name]['declaration']),MAPPING)
        row['name']=MAPPING[name];doc['declarations'].append(row)
    doc['statements']=deepcopy(statements);doc['statements'][37]=replace_symbols(doc['statements'][37],MAPPING)
    doc=parse(format_graph(doc,'compact'))
    core=deepcopy(doc);core.update(declarations=closure(doc,['r2bx']),statements=[doc['statements'][37]])
    library=deepcopy(doc);library.update(declarations=closure(doc,['r2bq']),statements=[])
    added=doc['declarations'][size:];by_name={d['name']:d for d in added};assert len(added)==11
    basis=dict(status='fear_proneness_adopted_in_causal_generalization',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={n:dict(parameters=by_name[n]['parameters'],result=by_name[n]['result'],arguments=args,meaning_ja=meaning)
            for n,(args,meaning) in PRIMITIVES.items()},definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/generalized-deterrence-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda v:json.dumps(v,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',LIBRARY:format_graph(library,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}


def main():
    from scripts.audit_opening_scope import write_exact
    for p,body in build().items():write_exact(ROOT/p,body)
    print('Fear proneness adopted at statement 37; 52 statements retained',flush=True)


if __name__=='__main__':main()
