"""Bind provisional order and normative self-legislation in one hypothetical history."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from noema.semantic_reviews import digest
from scripts.compose_grounded_step import ROOT,closure
from scripts.compose_qualitative_influence import both
from scripts.compose_protected_remarks import bind

PARENTS=('data/legislative-touchstone-basis-v1.json','data/insight-threshold-basis-v1.json','data/institutional-outlook-basis-v1.json')
LIBRARY='examples/v016/provisional-self-legislation.noema'
BASIS='data/provisional-self-legislation-basis-v1.json'
NAMES=('people','community','law','regime','activity','field','audience','group','recipient','policy')
FIELDS=' '.join(n+' a' for n in NAMES)
ARGS=' '.join('v '+n for n in NAMES)
REF='k h26b7[]'
LAW='v people v community v law'
PRIMITIVES={}
MEANINGS={
 'r5gs':'同じ人民・共同体・法と一つの候補経過で、r5epの結論独立の仮定範囲、r5eqの人民自身への衝突のない積極的許可、r5grの短期の制度導入と公的批評・目的・洞察到達がともに成立する。導入主体を同じ人民へ束縛し、全条項の採択をその同じ活動と開始点に置く。洞察の真偽評価は引数で固定し、成功する評価点を存在量化して選ばない。',
 'r5gt':'同じ十対象と固定した洞察の真偽評価について、r5gsを満たす候補経過・開始・終了が少なくとも一組存在する。同じ候補内の正当な自己賦課と短期の実施可能性であり、別候補の許可と導入を合わせず、全候補での成功、現実の自己賦課、現在の投票を要求しない。',
 'r5gu':'正確な人民・共同体・法・制度・活動・領域・公衆・提案集団・宛先・政策の十対象列と固定した真偽評価から、r5gtの暫定的自己賦課可能性を返す閉じた内容族。外側の評価点は候補や規範評価点を変更しない。全文の量化と談話提示へ同じ対象を渡すための部品である。',
 'r5gv':'同じ正確な十対象列の先頭三対象にr5eiの完全な人民と非空の法案の枠組みを要求する内容族。制度や活動や提案の成功によって一般的な法律の範囲を選別せず、許可や実行も実評価しない。他の七対象は後続の同じ構成への束縛を保つ。',
 'r5gw':'同じ正確な十対象列・基準・候補・起点について、同じ人民が同じ採択活動に関してよりよい法を期待するr5fnの字義的な描写内容。期待内容は同じ人民・共同体・法へ結ぶ。可能性r5gtには連言せず、gleichsamの描写側に引用して用いる。',
 'r5gx':'同じ正確な十対象列の先頭三対象についてr5esの規範的な自己賦課可能性を返す。前文の問いに使われた同じ内容を、この文の対象列へ持ち上げる照応先。これだけで短期・公的批評・洞察・保護を追加せず、前文のすべての法案を肯定するとも言わない。',
}
LIMITS=[
 'u0013第七文[1437,2309)のdiesesとwäre ... möglichのための依存群。直前のob ein Volk sich selbst ... auferlegen könnteを受け、一定期間の条件下で人民が自らにその法を課し得ることとして読む。一般の外的な採択主体だけに置き換えず、導入主体と法を課される人民を同じ集団へ束縛する。',
 '自己賦課は共同体への公的採択の帰属である。全員の心理的同意、直接投票、現行制度上の立法権能、聖職者が法を制定するという追加はしない。一般の立法可能性との対応は前文の基準命題に残し、新定義でその同値を恒真化しない。',
 '同じ候補のr5ep・r5eq・r5grを連言し、その外で候補と期間を存在量化する。規範的資格の対象は同じ法の自己賦課r5enであり、各条項・導入活動・期間の実施は同じ候補のr5grで別に評価する。実施できるだけ、許可があるだけ、別候補でそれぞれ成立するだけでは可能としない。',
 '人民・法・導入制度・活動・公衆・提案集団・宛先・保護政策の対象は一組に保つ。洞察内容の真偽評価は固定引数であり、真になる評価点を候補ごとに選び直さない。規範と候補の参照基準は既存h26b7をそのまま使う。',
 'r5gtは指定された構成の可能性を返す部品である。全法案が許されるという普遍命題でも、この実施構成が現に存在するという断言でもない。全文における不定の法・制度・活動などの量化、文脈範囲、著者帰属はまだここでは断定しない。',
 'gleichsamの期待描写は同じ十対象列で別に用意するが、実際の期待、よりよい法の到来、現実の洞察到達や提案の実施を可能性の条件へ加えない。引用した描写の内容を成立させずに記述できる。',
 '短期間ならどんな法でも許される、期間中に全市民が実際に批評する、到達点で旧制度を必ず廃止する、改革側の共同体が実在する、全員が共同提案に加わる、という追加はしない。前段までの各依存群の限定を維持する。',
 '目的の文章上の帰属、聖職者への取り立て、etwaと接続法、非全員の譲歩、王座の換喩、Nun・wohl・gleichsamの提示関係、全文の量化・著者帰属・通読は残る。第七文の確認文字数は加算しない。',
]

@lru_cache(None)
def parents():return tuple(load_catalog(ROOT,p) for p in PARENTS)

def definitions():
    period='v people '+LAW+' v regime v activity '+REF+' v candidate v start v end v field v audience v group v recipient v policy v assessment'
    text='d r5gs['+FIELDS+' assessment d candidate d start d end d] c['+both(
        'k r5ep['+LAW+' v candidate]','k r5eq['+LAW+' v candidate]','k r5gr['+period+']')+'].\n'
    text+='d r5gt['+FIELDS+' assessment d] c[g candidate d[g start d[g end d[k r5gs['+ARGS+' v assessment v candidate v start v end]]]]].\n'
    for root,extra,body in (
        ('r5gu',' assessment d','k r5gt['+ARGS+' v assessment]'),
        ('r5gv','','k r5ei['+LAW+' '+REF+']'),
        ('r5gw',' reference d candidate d anchor d','k r5fn[v people v activity '+LAW+' v reference v candidate v anchor]'),
        ('r5gx','','k r5es['+LAW+']')):
        text+='d '+root+'[bindings j[a]'+extra+'] e[b point['+bind(NAMES,body)+']].\n'
    return text

def build():
    sources=parents();doc=deepcopy(sources[0].document);doc.update(declarations=[],statements=[]);imported={}
    for source,roots in zip(sources,(['r5ep','r5eq','r5ei','r5es','h26b7'],['r5gr'],['r5fn'])):
        for d in closure(source.document,roots):
            n=d['name'];e=source.entries[n]
            if n in imported:assert d==imported[n]['declaration'] and e['meaning_ja']==imported[n]['meaning_ja'],n
            else:doc['declarations'].append(d);imported[n]=e
    assert not set(MEANINGS)&set().union(*(set(s.entries) for s in sources))
    doc=parse(format_graph(doc,'compact')+definitions());ds={d['name']:d for d in doc['declarations']}
    prims={n:dict(parameters=ds[n]['parameters'],result=ds[n]['result'],arguments=e['arguments'],meaning_ja=e['meaning_ja']) for n,e in imported.items() if e['kind']=='primitive'}
    paths=set().union(*(set(s.source_sha256) for s in sources))
    basis=dict(status='same_candidate_provisional_self_legislation_possibility',document=LIBRARY,primitives=prims,
        definitions={n:e['meaning_ja'] for n,e in imported.items() if e['kind']=='definition'}|MEANINGS,
        imported_symbols={n:e['meaning_basis'] for n,e in imported.items()},
        import_source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)},limitations=LIMITS)
    return {LIBRARY:format_graph(doc,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n'}
