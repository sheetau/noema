"""Explicitly promote the latest causal contrast and construct its attribution payload."""
from copy import deepcopy
import json
from noema.grammar import parse as legacy_parse
from noema.constructed import parse,format_graph,promote
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import app,call as k
from scripts.compose_situated_criticism import params
from scripts.compose_qualified_utterance import closure
from scripts.compose_causal_outcome_contrast import SOURCE as FIELDS

PARENT='examples/v014/kant-causal-outcome-contrast.noema'
PARENT_BASIS='data/kant-causal-outcome-contrast-basis-v1.json'
FULL='examples/v016/kant-quoted-outcomes.noema'
LIBRARY='examples/v016/quoted-causal-outcomes.noema'
BASIS='data/quoted-outcomes-basis-v1.json'
CODES=[(n,'i b['+t+']') for n,t in FIELDS]
RECORD='h[a a i b[c] a d] c'


def definitions():
    text=definition('hzhl',params(CODES),'o a[r b[p hzhk]]['+' '.join(v(n) for n,t in CODES)+']','i b[c]')
    fields=[('node','a'),('author','a')]+CODES+[('scope','a'),('context','d'),('records',RECORD)]
    text+=definition('hzhm',params(fields),app(v('records'),v('node'),v('author'),
        k('hzhl',*(v(n) for n,t in CODES)),v('scope'),v('context')))
    return text


MEANINGS={
    'hzhl':'同じ対象・活動種類・二つの結果記述・可能性の基準・候補関係の閉じた式記述を、既存hzhkへの適用の記述として組み立てる。結果は層1の真理値型の式の記述であり、構成だけでは対象の指示、活動種類、候補、因果、結果を評価しない。',
    'hzhm':'同じhzhlの記述を、指定箇所・著者・範囲・帰属文脈へ結ぶ提示記録があることを表す。内容の真理や、原文の具体的な概念が充足したことを含意しない。可能性を評価する基準anchorと帰属文脈contextを別の役割として保持する。',
}
LIMITS=[
    '0.16の既存の型付き記述構成と層1の引用を明示的に使う。0.14の解析器・意味規約・記述済み本文を上書きせず、旧版の引用禁止も解除しない。',
    'hzhkは層0の結果記述を評価するため、引用全体には層1が必要である。構成する入力の式記述も層1とし、その中に結果記述の層0引用を保持する。層を下げる暗黙変換はしない。',
    '記録関係は著者がこの記述内容を提示したという解釈を与える入力である。引用だけで著者帰属や真理を捏造せず、実際の原文箇所と具体化した内容の対応は別途確認する。',
    '対象・活動種類・結果記述・基準・候補関係を全て渡せる構成だが、革命・専制・圧迫・改革の意味を具体化した完成した訳文ではない。今回は著者の新しい主張を追加しない。',
    '同じ対象を指す別の式や、同じ真偽を持つ別の結果も、構文記述としては区別する。任意の同義表現の自動同一化は行わない。',
    '0.16試作の実行時の層検査と回数上限を引き継ぐ。任意の高階関数に対する事前の効果検査、無矛盾性・停止性の一般証明、無限領域の評価は未完である。',
    '他の0.16本文枝との統合は行わず、今回の0.14累積本文の明示的な後継とする。新しい原文範囲や意味確認済み区間数は加算しない。',
]


def build():
    old=legacy_parse((ROOT/PARENT).read_text(encoding='utf-8'))
    parent_basis=json.loads((ROOT/PARENT_BASIS).read_text(encoding='utf-8'));audit_basis(old,parent_basis)
    doc=promote(old);statements=deepcopy(doc['statements']);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=statements
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['hzhl','hzhm'])
    basis=dict(status='explicit_016_quotation_bridge_not_completed_source_attribution',document=FULL,library=LIBRARY,
        parent=PARENT,inherited_meaning_basis=PARENT_BASIS,definitions=MEANINGS,
        new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in doc['declarations'] if d['name'] in MEANINGS},
        limitations=LIMITS)
    return {FULL:format_graph(doc,'compact')+'\n',LIBRARY:format_graph(lib,'compact')+'\n',
        BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Causal contrast quotations constructed without executing their content',flush=True)


if __name__=='__main__':main()
