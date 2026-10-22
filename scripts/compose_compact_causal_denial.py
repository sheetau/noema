"""Keep causal consequences separate from unconditional prohibition of formation."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both,FALSE
from scripts.compose_protected_remarks import bind

PARENTS=('data/persistent-compact-progress-basis-v1.json','data/provisional-order-sentence-basis-v1.json')
LIBRARY='examples/v016/compact-causal-denial.noema'
BASIS='data/compact-causal-denial-basis-v1.json'
NAMES=('agreement','community','regime','audience','period')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
FIVE='l[a]['+ARGS+']'
SIX='l[a][v group '+ARGS+']'
ANCHOR='k h254z[v agreement]'
MEANINGS={
 'r5jn':'合意・共同体・制度・公衆・期間の正確な五対象列と固定基準から、同じ候補経過で同じ合意基準h254zにr5jhの共同合意が形成される内容を返す。合意内容の実施、期間の不毛化、原因性を形成に混ぜない。',
 'r5jo':'同じ五対象列と固定基準から、その同じ期間の人類の改善不在r5jmを返す。認識内容の真偽評価h26ar(reference)を候補間で固定する。合意・制度・公衆の位置を保持して因果の束縛を共通にするが、その形成や原因性は結果条件に追加しない。',
 'r5jp':'同じ候補に同じr5jhの合意形成があり、その同じ対象へのr5jgの制度固定化が実施され、同じ期間のr5joの結果が成立し、同じ合意の実施がその結果を生むh26asの因果的な働きがある。単なる共起、別合意・別期間・別候補の結果では足りない。',
 'r5jq':'正確な五対象列と固定基準からr5jpの事実的な因果結果を返す。形成・実施・不毛化・因果を一つの候補へ結ぶが、その内容を引用しただけでは現実の成功を断定しない。',
 'r5jx':'同じ五対象列・固定基準・候補について、合意形成r5jhとその同じ合意の制度方針r5jgの実施を結ぶ。因果的帰結を考える対象方針の内容であり、形成だけ、別制度の実施、結果の不毛化へ置き換えない。',
 'r5jr':'同じ五対象列・固定基準・評価点について、r5jxの同じ合意に基づく制度方針の適用・維持がr5joの不毛化へ至るというh253xの因果的帰結を述べる。両記述は段階2で引用し、実際の形成・実施・結果を実行しない。単なる形式論理の含意、原因説明を発言した事実とは分ける。',
 'r5js':'同じ検討合意h26aw・宗教制度・公衆・有効な固定期間について、合意基準が履歴内で期間開始以前にあり、指定集団の全成員が同じ合意の固定した複数当事者に過不足なく一致して全員人間である候補枠組み。実際の同意表明、制度実施、許可、因果や結果は候補選別に用いない。',
 'r5jt':'集団を先頭にした正確な六対象列から、同じr5jsの当事者集団による同じ五対象のr5jnの合意形成を返す。集団を無関係な主体へ替えず、実施や因果結果を禁止対象に追加しない。',
 'r5ju':'同じ規範の出所・当事者集団・立場・六対象列・固定基準・評価点に、r5jtの合意形成を負極性で要求するh237zを結ぶ。積極的な禁止要求であり、単なる積極的許可の欠如や、現実に合意が形成されないこととは区別する。',
 'r5jv':'同じ固定基準・規範出所・立場で、r5jsの全候補集団・合意・共同体・制度・公衆・期間へのr5juの禁止要求を述べる内容。現実の形成済み・結果の発生済み・原因性が確認できたものだけへ範囲を狭めない。',
 'r5jw':'r5jvと同じ全候補枠組みに、同じ五対象のr5jrの因果的帰結を結ぶ内容。規範的な禁止と因果的帰結は別の命題として構成し、片方から他方を自動導出しない。現実の合意や不毛化を要求する事実的因果r5jqとも区別する。',
}
LIMITS=[
 '第八文のsich einigenの全面的不許可と、最初のdadurchによる不毛化への因果的帰結を構成する依存群。既存h26as/h253x/h237zを再利用し、新しい文専用の原因・禁止基本記号は加えない。',
 '不許可は合意形成に対する負極性要求として読む。因果結果が現実に成立した合意だけを禁止対象にする読みは採らない。全候補への規範命題と、同じ合意からの帰結命題を別に置き、本文統合時に同じ著者へ接続する。',
 '事実的な因果は、形成・同じ合意内容の実施・結果の成立とh26asの寄与を同じ候補へ結ぶ。非事実的なh253xは、実施した場合の帰結を閉じた記述のまま結ぶ。どちらも共起から原因を推定する手続ではなく、現実の因果的根拠を明示する解釈入力が必要。',
 '実施内容r5jgは期間全体の同じ制度・公的問い直しの禁止であり、署名だけや別制度の成立では代用しない。結果r5joは同じ期間・全人類・固定真偽評価のr5jmへ結ぶ。唯一原因、当事者全員の直接の実行、事前には不毛でなかったことは追加しない。',
 '候補集団は合意の全当事者に一致させるが、全住民や全人類とは同一視しない。h26djの当事者は仮定される意思形成の当事者範囲として指定でき、既に同意した者だけを当事者にする読みは採らない。期間と構成員の完全な指定は入力の責任である。',
 '規範の出所と合意当事者としての立場は引数のまま保つ。全文でどの評価規範・立場を用いるかの固定、schlechterdingsの全面性、auch nurの限定、消去への見立て、後世への害の様相、前文との対照・著者帰属・全文通読は残る。意味確認文字数を増やさない。',
]
@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    formed='k r5jh['+ARGS+' v reference v candidate '+ANCHOR+']'
    result='k r5jm[v period v reference k h26ar[v reference] v candidate]'
    text='d r5jn[bindings j[a] reference d] e[b candidate['+bind(NAMES,formed)+']].\n'
    text+='d r5jo[bindings j[a] reference d] e[b candidate['+bind(NAMES,result)+']].\n'
    implemented='t[k r5jg[l[a][v community v regime v audience v period] v reference v candidate '+ANCHOR+']][v candidate]'
    text+='d r5jx[bindings j[a] reference d] e[b candidate['+bind(NAMES,both(formed,implemented))+']].\n'
    caused='k h26as[v agreement r[p r5jo] '+FIVE+' v reference v candidate]'
    text+='d r5jp['+FIELDS+' reference d candidate d] c['+both(formed,implemented,result,caused)+'].\n'
    text+='d r5jq[bindings j[a] reference d] e[b candidate['+bind(NAMES,'k r5jp['+ARGS+' v reference v candidate]')+']].\n'
    text+='d r5jr['+FIELDS+' reference d point d] c[k h253x[r c[p r5jx] '+FIVE+' r c[p r5jo] '+FIVE+' v reference v point]].\n'
    party=lambda p:'k h26dj[v agreement v '+p+' v reference v candidate '+ANCHOR+']'
    complete='f person a[z[k h246c[v group v person '+ANCHOR+']]['+party('person')+']]'
    plural='g first a[g second a['+both(party('first'),party('second'),'u[e[v first][v second]]')+']]'
    ordered='g start d['+both('k r5jf[v period v reference v candidate v start]',
        'x[e['+ANCHOR+'][v start]][k ic['+ANCHOR+' v start v candidate]]')+']'
    scope=both('k h26aw[v agreement v reference]','k h26cs[v regime v community v reference]','k ce[v audience v reference]',
        'k h257z[v reference v candidate '+ANCHOR+']',ordered,complete,plural,'f person a[y['+party('person')+'][k aa[v person]]]')
    text+='d r5js[group a '+FIELDS+' reference d candidate d] c['+scope+'].\n'
    text+='d r5jt[bindings j[a] reference d] e[b candidate['+bind(('group',*NAMES),both('k r5js[v group '+ARGS+' v reference v candidate]',formed))+']].\n'
    text+='d r5ju[source a group a role a '+FIELDS+' reference d point d] c[k h237z[v source v group v role r b[p r5jt] '+SIX+' v reference '+FALSE+' v point]].\n'
    for name,target,fields in (('r5jv','k r5ju[v source v group v role '+ARGS+' v reference v candidate]','source a role a reference d'),
        ('r5jw','k r5jr['+ARGS+' v reference v candidate]','reference d')):
        clause='y[k r5js[v group '+ARGS+' v reference v candidate]]['+target+']'
        for n in reversed(('group',*NAMES)):clause='f '+n+' a['+clause+']'
        text+='d '+name+'['+fields+'] e[b candidate['+clause+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5jh','r5jg','r5jm','r5jf'],['h26as','h253x','h237z','h26aw','h254z','h26ar','h246c'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja']
            else:doc['declarations'].append(d);imported[n]=e
    assert not set(MEANINGS)&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='same_compact_causal_result_and_unconditional_formation_prohibition',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
