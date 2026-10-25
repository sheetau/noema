"""Presentation, uptake and explicitly grounded speech-act profiles."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from scripts.shared_modality import ROOT,v,app,call,op,renamed
from scripts.shared_reference import I,S,T,C,U,definition,lam
from scripts.shared_time import allof

LIBRARY='examples/v016/shared-speech-v1.noema';BASIS='data/shared-speech-basis-v1.json'
SOURCE='examples/v014/speech-principals.noema';SOURCE_BASIS='data/speech-principals-basis-v1.json'
NAMES={'rfo':'speechpresented','rga':'speechattributed','rgb':'speechdelegated','rhe':'speechownvoice',
       'rhf':'speechothervoice','rhg':'speechvoicepair','rhh':'audiencewithin'}
D=description_sort(function_sort([I],U));ACTION=description_sort(function_sort([I],C))
OCCURS=function_sort([I,S],T);PRESENTS=function_sort([I,I,S],T);CONVEYS=function_sort([I,I,I,D,S],T)
TARGETS=function_sort([I,I,D,I,ACTION,S],T)
SOLICITS=function_sort([I,I,I,ACTION,S],T)
SUPPORTS=function_sort([I,I,I,ACTION,ACTION,S],T)
REASONSHOWN=function_sort([I,I,I,S],T)
UNDERTAKES=function_sort([I,I,I,ACTION,S],T)
AUTHORITY=function_sort([I,I,I,I,ACTION,S],T)
BEFORE=function_sort([S,S],T)
BASE=[('person',I),('activity',I),('recipient',I),('subject',I),('message',D),('context',S)]
PRESENTATION=[('occurs',OCCURS),('presents',PRESENTS),('conveys',CONVEYS)]
TO=BASE+PRESENTATION
DIRECTED=TO+[('actor',I),('action',ACTION),('targets',TARGETS)]
REQUEST=TO+[('action',ACTION),('targets',TARGETS),('solicits',SOLICITS)]
PROMISE=TO+[('action',ACTION),('targets',TARGETS),('undertakes',UNDERTAKES)]
ADVICE=TO+[('action',ACTION),('targets',TARGETS),('reason',I),('goal',ACTION),('supports',SUPPORTS),('reasonshown',REASONSHOWN)]


def args(ps):return [v(n) for n,t in ps]
def reception():return [v(n) for n in ('activity','recipient','subject','message','context')]
def result_at(actor):
    return dict(kind='evaluate',content=dict(kind='apply',function=dict(kind='disquote',description=v('action')),
        arguments=[v(actor)]),situation=v('outcome'))


@lru_cache(maxsize=1)
def raw():
    old=parse((ROOT/SOURCE).read_text(encoding='utf-8'))
    ds=[renamed(d,NAMES) for d in old['declarations']]
    def add(n,ps,body):ds.append(definition(n,ps,T,body))
    audience=lam([('member',I)],op('equal',v('member'),v('recipient')))
    add('speechto',TO,call('speechpresented',v('person'),v('activity'),audience,v('subject'),v('message'),v('context'),*args(PRESENTATION)))
    received=TO+[('receives',CONVEYS)]
    add('speechreceived',received,op('and',call('speechto',*args(TO)),app('receives',*reception())))
    understood=received+[('understands',CONVEYS)]
    add('speechunderstood',understood,op('and',call('speechreceived',*args(received)),app('understands',*reception())))
    for name,relation in [('speechaccepted','accepts'),('speechdeclined','declines')]:
        add(name,understood+[(relation,CONVEYS)],op('and',call('speechunderstood',*args(understood)),app(relation,*reception())))
    add('speechtargeted',DIRECTED,op('and',call('speechto',*args(TO)),
        app('targets',v('activity'),v('subject'),v('message'),v('actor'),v('action'),v('context'))))
    target=lambda actor:call('speechtargeted',*args(TO),v(actor),v('action'),v('targets'))
    add('speechrequest',REQUEST,op('and',target('recipient'),
        app('solicits',v('person'),v('activity'),v('recipient'),v('action'),v('context'))))
    add('speechadvice',ADVICE,allof(target('recipient'),
        app('supports',v('person'),v('reason'),v('recipient'),v('action'),v('goal'),v('context')),
        app('reasonshown',v('activity'),v('recipient'),v('reason'),v('context'))))
    add('speechpromise',PROMISE,op('and',target('person'),
        app('undertakes',v('person'),v('recipient'),v('activity'),v('action'),v('context'))))
    command=TO+[('action',ACTION),('targets',TARGETS),('role',I),('claims',AUTHORITY)]
    add('speechcommand',command,op('and',target('recipient'),
        app('claims',v('person'),v('role'),v('activity'),v('recipient'),v('action'),v('context'))))
    for name,profile,ps,actor in [('requestrealized','speechrequest',REQUEST,'recipient'),('promiserealized','speechpromise',PROMISE,'person')]:
        add(name,ps+[('outcome',S),('before',BEFORE)],allof(call(profile,*args(ps)),
            app('before',v('context'),v('outcome')),result_at(actor)))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,statements=[])


@lru_cache(maxsize=1)
def composed():return normalize_document(raw())


OLD_ROLES={
 'speechpresented':['person','activity','audience','subject','message','context','occurs','presents','conveys'],
 'speechattributed':['person','activity','principal','role','audience','subject','message','context','occurs','presents','conveys','voices'],
 'speechdelegated':['person','activity','principal','role','audience','subject','message','context','occurs','presents','conveys','voices','positioned','entrusted','serves'],
 'speechownvoice':['person','activity','role','audience','subject','message','context','occurs','presents','conveys','voices'],
 'speechothervoice':['person','activity','principal','role','audience','subject','message','context','occurs','presents','conveys','voices','positioned','entrusted','serves'],
 'speechvoicepair':['person','context','voices','serves','officeactivity','officeprincipal','officerole','officeaudience','officesubject','officemessage','publicactivity','publicrole','publicaudience','publicsubject','publicmessage','occurs','presents','conveys','positioned','entrusted'],
 'audiencewithin':['actual','intended']}
MEANINGS={
 'speechto':'同じ生起する行為で同じ人が、指定受け手へ同じ対象・発話記述を提示する。単独受け手への条件であり、他の受け手の存在を排除しない。',
 'speechreceived':'同じ提示行為・受け手・対象・記述・状況で受領が成立する。理解や同意を含まない。',
 'speechunderstood':'同じ提示と受領に、同じ行為からの記述の理解を結ぶ。理解は賛同や内容の真理ではない。',
 'speechaccepted':'同じ提示・受領・理解に、同じ発話について明示的な受諾を結ぶ。行動の実現・内心の誠実さ・規範的有効性を含まない。',
 'speechdeclined':'同じ提示・受領・理解に、同じ発話について明示的な辞退を結ぶ。受諾が無いこととは別条件。',
 'speechtargeted':'同じ提示と、その同じ行為・対象・発話記述が指定行為者の行為記述を求める対象として扱うという明示的解釈を結ぶ。',
 'speechrequest':'受け手の行為を対象とする提示に、同じ話者・提示行為・受け手・行為記述に対する引受けを求める表明を結ぶ。受諾・実行・権限は別。',
 'speechadvice':'受け手の行為を対象とする提示に、話者が同じ理由によってその行為を指定目的に適するものと評価する関係と、その理由を同じ受け手へ同じ発話で示す関係を結ぶ。理由を示す助言という読みで、実際の有効性や目的達成を保証しない。',
 'speechpromise':'話者自身の行為を対象とする提示に、同じ話者が同じ受け手に対して同じ発話行為で当該行為を自ら引き受ける表明を結ぶ。単なる未来予測や受け手の行為への依頼と区別する。',
 'speechcommand':'受け手の行為を対象とする提示に、話者が同じ役割に基づく指示権限を同じ発話行為で行使すると表明する関係を結ぶ。主張した権限の正当性や服従を導かない。',
 'requestrealized':'speechrequestが成立し、指定した後続状況で同じ行為記述を受け手へ適用した内容が成立する。受諾や依頼が原因だったことは別条件。',
 'promiserealized':'speechpromiseが成立し、指定した後続状況で同じ行為記述を話者へ適用した内容が成立する。全条項の履行認定・期限違反・解除や法的有効性は扱わない。'}
ROLES={
 'person':'同じ発話の提示者。','activity':'同じ発話の生起・提示・受領等を結ぶ行為。','recipient':'実際に提示する一人の受け手。',
 'audience':'実際に提示する非空の受け手範囲。','subject':'発話のひな形を適用する対象。行為者と無断で同一視しない。',
 'message':'対象から発話値を作る閉じた関数の記述。記述同一性を使い、内容を評価しない。','context':'同じ発話行為を評価する状況。',
 'occurs':'行為・状況の生起関係。','presents':'提示者・行為・状況の提示側参加関係。',
 'conveys':'行為・受け手・対象・記述・状況の提示関係。','receives':'同じ行為から同じ受け手が同じ対象・記述を受領した関係。',
 'understands':'同じ行為からの同じ対象・記述を受け手が理解した関係。','accepts':'同じ行為に対する同じ受け手の明示的な受諾。','declines':'同じ行為に対する同じ受け手の明示的な辞退。',
 'actor':'求める行為の主体。','action':'主体から命題内容を作る閉じた行為関数の記述。予定された行為でよく、引用時は実行しない。',
 'targets':'行為・対象・表面の発話記述・行為者・行為記述・状況の解釈上の結び付け。問いの形だけから依頼を推測しない。',
 'solicits':'話者・提示行為・受け手・行為記述・状況について、受け手による当該行為の引受けを求める表明。実際の内心の欲求や受諾を条件にしない。',
 'reason':'助言の理由として同じ発話で示す根拠。','goal':'受け手に関する目的の閉じた内容関数記述。目的の実現を評価しない。',
 'supports':'話者・理由・受け手・行為記述・目的記述・状況の、行為が目的に適するとの評価関係。実際に妥当な推論であるとの認定と分ける。',
 'reasonshown':'同じ提示行為・受け手・理由・状況の、理由を明示した関係。別の発言から理由を借りない。',
 'undertakes':'話者・受け手・提示行為・行為記述・状況の、当該行為を自分に課すものとして引き受ける表明。内心の意思、成功、有効な義務の存在を含意しない。',
 'claims':'話者・役割・提示行為・受け手・行為記述・状況について、その役割の指示権限を行使すると表明する関係。権限の認可そのものではない。',
 'outcome':'内容の実現を調べる明示的な後続状況。','before':'第一状況が第二より前であるという順序関係。時刻を自動補完しない。',
 'principal':'発話の帰属先。','role':'提示者の役割。','voices':'提示者・行為・帰属先・役割・対象・記述・状況の声の帰属関係。',
 'positioned':'提示者・行為・役割・状況の分類。','entrusted':'提示者・役割・状況の委任関係。','serves':'提示者・帰属先・役割・状況の奉仕関係。',
 'actual':'実際の受け手の範囲。','intended':'想定した宛先の範囲。'}


def basis():
    old=json.loads((ROOT/SOURCE_BASIS).read_text(encoding='utf-8'))
    meanings={NAMES[n]:m for n,m in old['definitions'].items()};meanings.update(MEANINGS)
    contracts={}
    for d in raw()['declarations']:
        roles=OLD_ROLES.get(d['name'],[p['name'] for p in d['parameters']]);items=[]
        for name,p in zip(roles,d['parameters']):
            origin=name;prefix=''
            if name.startswith(('office','public')):
                prefix='職務側の' if name.startswith('office') else '本人側の';origin=name[6:]
            items.append(dict(role=name,sort=p['sort'],interpretation=prefix+ROLES[origin]))
        contracts[d['name']]=dict(arguments=items,result=d['result'])
    return dict(status='shared_presentations_uptake_and_explicit_speech_profiles',document=LIBRARY,primitives={},
        definitions=meanings,public_contracts=contracts,preserved_definitions=[dict(document=SOURCE,names=NAMES)],
        limitations=['7定義は既存speech-principalsの本体・語義を再利用する。新しい基本宣言を導入せず、残る対人的・規範的関係は型と解釈を明示する引数として渡す。',
            '依頼/理由提示型の助言/約束/命令は明示的な読みの構成であり、表面形から自動分類しない。各プロフィールは排他的でも網羅的でもない。',
            'targets/solicits/supports/undertakes/claimsの適用根拠は解釈入力である。これら社会的・志向的関係の一般理論を論理演算だけで還元したとは主張しない。',
            '提示・受領・理解・受諾・辞退・実現を分ける。受諾と辞退は互いの単なる否定ではなく、無応答や矛盾した記録も記述できる。',
            '行為者を依頼では受け手、約束では話者に固定する。引用した行為や発話の真理はプロフィール判定で評価せず、実現を問う場合だけ明示的に脱引用する。',
            '権限の行使表明と権限の正当性、引受けと有効な義務、目的への適性評価と目的達成を区別する。期限・解除・不履行判定や部分回答・会話更新は別途接続する。',
            '間接依頼は表面の問いの記述と求める行為をtargetsで結べるが、その結び付けを自動推測する仕組みではない。未知入力は偽や未受諾へ置き換えない。',
            '円文字接続、他領域への適用、学習・第三者読解は続く課題。'])


def prepare():
    for path,text in ((LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')):
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published speech module differs')
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')
