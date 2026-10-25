"""Inclusive deadlines, explicitly grounded release and retained missed deadlines."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from scripts.shared_modality import ROOT,v,app,call,op
from scripts.shared_reference import I,S,T,C,definition,lam,truth
from scripts.shared_time import q,allof,WINDOW,ORDER
from scripts.shared_speech import ACTION as DA,PROMISE
from scripts.shared_norms import ACTION as NORM_ACTION,D as DN,RULE,TARGET

ACT=function_sort([I],C);DI=description_sort(I);DS=description_sort(S)
DH=description_sort(WINDOW);DO=description_sort(ORDER)
LIBRARY='examples/v016/shared-deadlines-v1.noema';BASIS='data/shared-deadlines-basis-v1.json'
SOURCES=[dict(document='examples/v016/shared-time-v1.noema',basis='data/shared-time-basis-v1.json',names=['chronology']),
    dict(document='examples/v016/shared-norms-v1.noema',basis='data/shared-norms-basis-v1.json',names=['normrequired','normwitness','groundedrule']),
    dict(document='examples/v016/shared-speech-v1.noema',basis='data/shared-speech-basis-v1.json',names=['speechpresented','speechto','speechtargeted','speechpromise'])]
FRAME=[('history',WINDOW),('order',ORDER),('issued',S),('due',S),('assessment',S)]
DESCRIPTIONS=[('action',DA),('historydescription',DH),('orderdescription',DO),('issueddescription',DS),('duedescription',DS),('performancedescription',DI)]
FIELDS=[('source',I),('person',I),('role',I),('performancedescription',DI),('action',DA),('historydescription',DH),
    ('orderdescription',DO),('issueddescription',DS),('duedescription',DS)]
BASE=FIELDS+[('assessment',S),('required',RULE)]
AUTH=function_sort([I,I,I,I,I,DN,S,S],T)
RELEASE=function_sort([I,I,I,I,I,I,DN,S,S],T)
RELEASED=BASE+[('authorized',AUTH),('releases',RELEASE)]


def args(ps):return [v(n) for n,t in ps]
def eq(a,b):return op('equal',a,b)
def disq(n):return dict(kind='disquote',description=v(n))
def apply(function,*values):return dict(kind='apply',function=function,arguments=list(values))
def le(a,b,order=None):return op('or',eq(a,b),apply(v('order') if order is None else order,a,b))
def frame_at(point):return [disq('historydescription'),disq('orderdescription'),disq('issueddescription'),disq('duedescription'),point]
def description():return call('deadlinedescription',*args(DESCRIPTIONS))
def demand_target():return [v('source'),v('person'),v('role'),disq('performancedescription'),description(),truth(True),disq('issueddescription')]
def occurred(action,person,point):return dict(kind='evaluate',content=apply(action,person),situation=point)
def released_args(point):return args(FIELDS)+[point,v('required'),v('authorized'),v('releases')]


@lru_cache(maxsize=1)
def raw():
    ds=[]
    for source in SOURCES:
        ds.extend(deepcopy(d) for d in parse((ROOT/source['document']).read_text(encoding='utf-8'))['declarations'] if d['name'] in source['names'])
    def add(name,ps,body,result=T):ds.append(definition(name,ps,result,body))
    valid=allof(call('chronology',v('history'),v('order')),*(app('history',v(n)) for n in ('issued','due','assessment')),
        app('order',v('issued'),v('due')),le(v('issued'),v('assessment')))
    add('deadlinevalid',FRAME,valid)
    window=allof(app('history',v('point')),app('order',v('issued'),v('point')),le(v('point'),v('due')),le(v('point'),v('assessment')))
    add('deadlinewindow',FRAME,lam([('point',S)],window),WINDOW)
    exists=q('exists','point',S,op('and',apply(call('deadlinewindow',*args(FRAME)),v('point')),occurred(v('operation'),v('actor'),v('point'))))
    observed=[('actor',I),('operation',ACT)]+FRAME
    add('deadlineobserved',observed,op('and',call('deadlinevalid',*args(FRAME)),exists))
    add('deadlineachieved',[('actor',I),('action',DA)]+FRAME,call('deadlineobserved',v('actor'),disq('action'),*args(FRAME)))
    clause=[('operation',ACT),('history',WINDOW),('order',ORDER),('issued',S),('due',S),('performance',I)]
    body=op('and',eq(v('activity'),v('performance')),
        call('deadlineobserved',v('actor'),v('operation'),v('history'),v('order'),v('issued'),v('due'),v('point')))
    add('deadlineclause',clause,lam([('actor',I),('activity',I)],dict(kind='content',variable='point',body=body)),NORM_ACTION)
    add('deadlinedescription',DESCRIPTIONS,dict(kind='quoted_application',function=dict(kind='quote',body=dict(kind='function_ref',symbol='deadlineclause')),
        arguments=args(DESCRIPTIONS)),DN)
    neverallowed=lam(TARGET,truth(False))
    required=allof(call('deadlinevalid',*frame_at(v('assessment'))),call('normrequired',*demand_target(),v('required'),neverallowed))
    add('deadlinerequired',BASE,required)
    witness=FIELDS+[('point',S),('authority',I),('reason',I),('authorized',AUTH),('releases',RELEASE)]
    common=[v('source'),v('person'),v('role'),disq('performancedescription'),description(),disq('issueddescription'),v('point')]
    releaseproof=op('and',app('authorized',v('authority'),*common),app('releases',v('authority'),v('reason'),*common))
    add('deadlinefreedat',witness,op('and',call('deadlinevalid',*frame_at(v('point'))),releaseproof))
    # deadlinerequired validates the same chronology and anchors once outside
    # the witness search. The candidate then needs only membership and bounds.
    released=q('exists','point',S,allof(apply(disq('historydescription'),v('point')),
        le(disq('issueddescription'),v('point'),disq('orderdescription')),
        le(v('point'),v('assessment'),disq('orderdescription')),
        q('exists','authority',I,q('exists','reason',I,releaseproof))))
    add('deadlinereleased',RELEASED,op('and',call('deadlinerequired',*args(BASE)),released))
    achieved=lambda point:call('deadlineachieved',v('person'),v('action'),*frame_at(point))
    add('deadlinefulfilled',BASE,op('and',call('deadlinerequired',*args(BASE)),achieved(v('assessment'))))
    pending=allof(call('deadlinerequired',*args(BASE)),v('complete'),le(v('assessment'),disq('duedescription'),disq('orderdescription')),
        op('not',achieved(v('assessment'))),op('not',call('deadlinereleased',*args(RELEASED))))
    add('deadlinepending',RELEASED+[('complete',T)],pending)
    breach=allof(call('deadlinerequired',*args(BASE)),v('complete'),apply(disq('orderdescription'),disq('duedescription'),v('assessment')),
        op('not',achieved(disq('duedescription'))),op('not',call('deadlinereleased',*released_args(disq('duedescription')))))
    add('deadlinebreached',RELEASED+[('complete',T)],breach)
    late=q('exists','point',S,allof(apply(disq('historydescription'),v('point')),apply(disq('orderdescription'),disq('duedescription'),v('point')),
        le(v('point'),v('assessment'),disq('orderdescription')),occurred(disq('action'),v('person'),v('point'))))
    add('deadlinelate',BASE+[('complete',T)],allof(call('deadlinerequired',*args(BASE)),v('complete'),op('not',achieved(disq('duedescription'))),late))
    extra=[p for p in BASE if p[0] not in {n for n,t in PROMISE}]
    add('promisedeadline',PROMISE+extra,allof(call('speechpromise',*args(PROMISE)),eq(v('context'),disq('issueddescription')),
        call('deadlinerequired',*args(BASE))))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[])


@lru_cache(maxsize=1)
def composed():return normalize_document(raw())


MEANINGS={
 'deadlinevalid':'同じ非空の時間履歴に厳密な全順序があり、起点・期限・評価点がそこに属し、起点は期限より前、評価点は起点以後である。',
 'deadlinewindow':'履歴内で起点より後、期限以下、評価点以下の時点を選ぶ関数。枠の妥当性はdeadlinevalidで別に確認する。',
 'deadlineobserved':'妥当な枠内で、指定行為者の行為内容が起点より後かつ期限・評価点以下のどこかで成立する。',
 'deadlineachieved':'同じ閉じた行為記述を評価してdeadlineobservedの条件を調べる。本人や行為記述を置き換えない。',
 'deadlineclause':'一個体の行為関数と履歴・順序・起点・期限・対象活動から、二個体の規範用内容関数を構成する。活動同一性と、その評価点までの期限内実現を内容とする。',
 'deadlinedescription':'同じ行為・時間枠・対象活動の閉じた記述をdeadlineclauseの引用へ適用し、規範用の閉じた記述を構成する。行為内容は実行しない。',
 'deadlinerequired':'妥当な時間枠で、同じ出所・本人・役割・対象活動・構成した期限条件について、起点時点の肯定的要求がある。後日の再解釈で起点の記録を書き換えない。',
 'deadlinefreedat':'妥当な起点以後の指定時点に、同じ要求対象を解除する権限が指定主体にあり、その主体が同じ理由で解除したという二関係がある。単なる採用記録の撤回ではない。',
 'deadlinereleased':'起点の要求があり、評価点までに権限と理由を持つ解除の証人がある。期限後の解除も含む。',
 'deadlinefulfilled':'起点の要求があり、同じ本人・行為・活動に対する期限条件が評価点までに成立した。解除との排他性は要求しない。',
 'deadlinepending':'起点の要求があり、評価点が期限以下で、関連範囲の調査完了が明示され、期限内の実現も解除もまだない。期限の時点自体も含む。',
 'deadlinebreached':'評価点が期限より後で、起点の要求と関連範囲の調査完了があり、期限までに実現も有効な解除もなかった。期限後の実現・解除でこの履歴条件は消えない。',
 'deadlinelate':'起点の要求と調査完了があり、期限内の実現はないが、期限後から評価点までに同じ行為内容が成立する。解除済みかどうかとは独立した遅い実現の条件。',
 'promisedeadline':'同じ話者・行為記述の約束が提示され、その提示状況が期限条件の起点と一致し、その起点に構成した期限条件への要求がある。約束だけから要求の有効性を推測しない。'}
ROLES={
 'history':'同じ時間履歴の全時点範囲。観測された点だけへ縮めない。',
 'order':'その履歴での厳密な先行関係。','issued':'約束または要求の起点。','due':'履行と解除を期限内として認める最終時点。',
 'assessment':'状態を評価する時点。','actor':'内容を実行評価する行為者。','operation':'本人から状況ごとの行為内容を返す関数。',
 'action':'同じ本人の行為内容を返す閉じた段階0の関数記述。','performance':'同じ要求対象となる活動の識別子。',
 'historydescription':'履歴範囲の閉じた記述。','orderdescription':'時間順序の閉じた記述。',
 'issueddescription':'起点の閉じた状況記述。','duedescription':'期限の閉じた状況記述。','performancedescription':'要求対象活動の閉じた個体記述。',
 'source':'要求を出す制度・規範・立場の出所。','person':'同じ要求を負う本人。約束との接続では同じ話者。','role':'要求の対象となる本人の役割。',
 'required':'同じ出所・本人・役割・活動・記述・極性・状況に対する要求。起点の記録を保持する。',
 'point':'解除の効力と行為を同じ時点として記録する状況。','authority':'解除を行う権限主体。','reason':'同じ解除の理由・証拠識別子。',
 'authorized':'権限主体・出所・本人・役割・活動・期限条件記述・起点・解除時点について解除権限があるという明示的入力。',
 'releases':'権限主体・理由・出所・本人・役割・活動・期限条件記述・起点・解除時点について解除したという明示的入力。',
 'complete':'対象期間の実現・解除について関連記録を尽くしたという明示。標本で見つからないことや未知入力の既定値ではない。'}
LIMITS=[
 '一回の起点から期限までに少なくとも一度成立すれば満たす、肯定的な期限要求の読み。起点を除き期限を含む。持続義務・反復・複数条項の全履行・遡及的免責・再有効化を自動で含めない。',
 '期限時点の解除は期限内として扱う。期限後の解除は現在までに解除済みでも、期限時点の不履行を消さない。この明示した規約をあらゆる制度に共通する規則とはしない。',
 '起点に要求があったことは、規範の正当性の普遍的証明ではない。既存groundedrule/normwitnessで同じ根拠を構成できる。解除権限と解除行為は追加の明示的解釈入力。',
 'fulfilled、released、breached、lateは排他的な状態名ではない。遅い実現や期限後の解除と、過去の期限不履行は併存する。調査完了の明示がない場合、pending/breached/lateの否定的条件を成立としない。',
 '要求対象の規範記述は引用したdeadlineclauseへ同じ閉じた引数記述を適用して構成する。真偽が偶然同じ別の行為・活動・時点の記述へ置換しない。',
 '時間履歴は将来の評価点を含む枠としても記述できるが、観測完了とは別。有限評価器は論理演算を短絡しないため、条件の外の時点も含め実行に必要な解釈が未知なら拒否する。未知を不実現へ変換しない。',
 '有限モデルと単枠束縛診断は、連続時間全域や実際の約束・制度の認定根拠を証明しない。会話採用記録の撤回だけで要求の解除を補わない。']


def basis():
    meanings={};contracts={}
    for source in SOURCES:
        old=json.loads((ROOT/source['basis']).read_text(encoding='utf-8'))
        for name in source['names']:
            meanings[name]=deepcopy(old['definitions'][name]);contracts[name]=deepcopy(old['public_contracts'][name])
    meanings.update(MEANINGS)
    uptake=json.loads((ROOT/SOURCES[2]['basis']).read_text(encoding='utf-8'))['public_contracts']['speechpromise']['arguments']
    inherited={p['role']:p['interpretation'] for p in uptake}
    for d in raw()['declarations']:
        if d['name'] in MEANINGS:
            contracts[d['name']]=dict(arguments=[dict(role=p['name'],sort=p['sort'],interpretation=
                inherited[p['name']] if d['name']=='promisedeadline' and p['name'] in inherited else ROLES[p['name']])
                for p in d['parameters']],result=d['result'])
    return dict(status='shared_deadline_fulfillment_and_grounded_release',document=LIBRARY,primitives={},definitions=meanings,
        public_contracts=contracts,preserved_sources=SOURCES,limitations=LIMITS)


def prepare():
    for path,text in ((LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')):
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published deadline source differs: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':prepare()
