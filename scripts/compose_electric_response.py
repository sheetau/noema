"""Ground an explicit intervention contrast in electric-force and current records."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document
from noema.semantic_reviews import digest
from scripts.compose_electric_action import ROOT,read,FIELDS as ELECTRIC
from scripts.compose_current_distribution import HISTORY,SCOPE,FAMILY
from scripts.compose_material_relative_frame import define,args
from scripts.compose_field_equations import ROLES
from scripts.compose_limits import R,v,call as k,app,op,both,ZERO

PARENT='examples/v014/einstein-carrier-relative-motion.noema'
PARENT_BASIS='data/carrier-relative-motion-basis-v1.json'
FULL='examples/v014/einstein-electric-response.noema'
CORE='examples/v014/electric-response-core.noema'
BASIS='data/electric-response-basis-v1.json'
ANNOTATIONS='data/electric-response-identifiers-v1.json'
LIBRARY='examples/v014/scoped-interventions.noema'
LIBRARY_BASIS='data/scoped-interventions-basis-v1.json'
RENAMES=dict(zip(('rz','rs','rt','ru','rv','rw'),('eiby','eibz','eib2','eib3','eib4','eib5')))
STATE='h[a] c';EQUATIONS='h[a '+STATE+'] c';PREDICATE='h['+STATE+'] c'
MODEL=[('variables','j[a]'),('equations',EQUATIONS),('factor','a'),('outcome','a')]
GROUND=MODEL+[('observed',STATE)]+[(n,PREDICATE) for n in ('realized','stimulus','response')]
FIELDS=ELECTRIC+[('body','a'),('lengthunit','a'),('timeunit','a'),('lower',R),('upper',R),('sections',SCOPE),
    ('cumulative',FAMILY),('current',FAMILY),('section','a'),('orientation','a'),('time',R)]
FIXED_NAMES={'body','carrier','frame','lengthunit','timeunit','chargeunit','fieldunit','forceunit','lower','upper','sections','section','orientation','time'}
FIXED=[(n,t) for n,t in FIELDS if n in FIXED_NAMES]+[('threshold',R)]
PROFILES=[(n,'h['+STATE+'] '+t) for n,t in FIELDS if n not in FIXED_NAMES]
ADAPTER=MODEL+[('observed',STATE)]+FIXED+PROFILES
TRUE=op('e',ZERO,ZERO);FALSE=op('u',TRUE)
MEANINGS={
 'eib6':'同じ二値構造方程式と背景で、互いに異なる要因・結果変数を比較する。要因を真に固定した側は解が存在して全解で結果が真、偽に固定した側も解が存在して全解で結果が偽である。共通原因による共存や無解を成功としない。これは指定モデル内の強い応答対照であり、一般の因果寄与の全語義ではない。',
 'eib7':'eib6の両介入の全解について、realizedの実内容が成立し、要因変数はstimulus、結果変数はresponseの成立とそれぞれ同値であることを要求する。観測割当ても非介入方程式に従い、要因と結果の双方が真である。同じ方程式を使うだけで物理的妥当性を自動認定せず、変数の名札と内容を接続する。',
 'eica':'同じ系・文脈・時刻の、物体内の点状担体への電気的作用eibsと、同じ物体の全断面電流履歴eibfを結ぶ。担体の出来事sb、場評価用四座標の時刻、単位付き物質領域eiro、指定断面・向き・時刻の適用範囲を共有する。作用や電流が非零であること、因果関係、担体が電流の唯一の運搬者であることは要求しない。',
 'eicb':'eicaの有効な記録について、同じ電気的力の三成分の少なくとも一つが非零である。負成分も受け入れ、合力や別担体の力を刺激に置き換えない。',
 'eicc':'eicaの記録について、同じ物体付き断面・向き・時刻の符号付き電流がeibkの非負閾値を絶対値で超える。単なる力の存在、物体の並進、別断面の電流を成功としない。',
 'eicd':'eib7の全介入解をeica/eicb/eiccへ接続する。物体・担体・評価系・単位・区間・全断面範囲・選定断面・向き・比較時刻・閾値は全解で固定し、各記録と文脈と場と電流の関数族は同じ割当てで索引する。モデル上の電気的刺激と電流応答の対照であり、原文の導体という種類や任意の電流生成の同義語ではない。',
}
LIMITS=[
 'カント側で使った一般的な有限変数介入ライブラリの六定義を、内容を変えず新しい記号名で再利用する。物理的な因果法則を新規の原始関係として追加しない。',
 '同じ方程式と背景の下で刺激を変える読みを採る場合の接続である。方程式は介入後にも機構を表すというモデル仮定であり、相関表の当てはめや検査成功からその仮定を証明しない。',
 '両側で全解が逆の応答になるという条件は一般の因果寄与より強い。既に別原因で電流が流れる例、確率的・冗長な原因、遅延応答はこの比較だけでは尽くさない。原文全体へ無条件に代入しない。',
 '刺激は指定担体・出来事への非零電気的力である。物体中の全作用をこの一記録だけで尽くすとはしない。未記述の別刺激や材料変化を固定背景とすることの適切さ、許容試行eirkと物理的可能性zrdpossibleへの接続は次の適用判断に残る。',
 '電流は既存の全履歴に基づく一断面一時刻の応答である。閾値、持続時間、通常の導電と漏れの区別、導体の語義はこのモデル対照だけでは定めない。原文207主張・著者表示判断を保持し、完成単位は増やさない。',
]

def imported():
    doc=extract_document(parse(read(LIBRARY)),roots=['ru','rw'],statement_indices=[]).document
    def rename(x):
        if isinstance(x,list):return [rename(y) for y in x]
        if isinstance(x,dict):
            y={n:rename(z) for n,z in x.items()}
            if x.get('kind')=='definition':y['name']=RENAMES[x['name']]
            if x.get('kind')=='call':y['symbol']=RENAMES[x['symbol']]
            return y
        return x
    return rename(doc)

def history():return [v('chargeunit') if n=='quantityunit' else v(n) for n,_ in HISTORY]

def definitions():
    mask='i[variable a]['+op('e',v('variable'),v('factor'))+']'
    fixed=lambda flag:'i[variable a]['+(TRUE if flag else FALSE)+']'
    goal=lambda flag:'i[state '+STATE+']['+(app(v('state'),v('outcome')) if flag else op('u',app(v('state'),v('outcome'))))+']'
    text=define('eib6',MODEL,both(op('u',op('e',v('factor'),v('outcome'))),
        *(k('eiby',v('variables'),v(n)) for n in ('factor','outcome')),
        *(k('eib5',v('variables'),v('equations'),mask,fixed(flag),goal(flag)) for flag in (True,False))))
    valid=op('x',*(k('eib3',v('variables'),v('equations'),mask,fixed(flag),v('state')) for flag in (True,False)))
    binding=both(app(v('realized'),v('state')),op('z',app(v('state'),v('factor')),app(v('stimulus'),v('state'))),
        op('z',app(v('state'),v('outcome')),app(v('response'),v('state'))))
    allbound='q['+k('eibz',v('variables'))+']['+TRUE+'][i[ok c state '+STATE+']['+both(v('ok'),op('y',valid,binding))+']]'
    text+=define('eib7',GROUND,both(k('eib6',*args(MODEL)),allbound,
        k('eib3',v('variables'),v('equations'),fixed(False),fixed(False),v('observed')),
        app(v('observed'),v('factor')),app(v('observed'),v('outcome'))))
    coords=[app(v('point'),k(n)) for n in ROLES]
    text+=define('eica',FIELDS,both(k('eibs',*args(ELECTRIC)),k('eibf',*history()),
        app(v('sections'),v('section'),v('orientation')),k('lg',v('lower'),v('upper'),v('time')),
        k('sca',coords[3],v('time')),k('sb',*[v(n) for n in ('carrier','event','frame','context','lengthunit','timeunit')],v('time'),*coords[:3]),
        k('eiro',*[v(n) for n in ('body','frame','context','lengthunit','timeunit')],*coords[:3],v('time'))))
    nonzero=[k('eibk',app(v('force'),k(n)),k('bb',ZERO)) for n in ROLES[:3]]
    text+=define('eicb',FIELDS,both(k('eica',*args(FIELDS)),op('x',nonzero[0],op('x',*nonzero[1:]))))
    current=app(app(v('current'),v('section'),v('orientation')),v('time'))
    text+=define('eicc',FIELDS+[('threshold',R)],both(k('eica',*args(FIELDS)),k('eibk',current,v('threshold'))))
    selected=[v(n) if n in FIXED_NAMES else app(v(n),v('state')) for n,_ in FIELDS]
    predicates=['i[state '+STATE+']['+k(n,*selected,*([v('threshold')] if n=='eicc' else []))+']' for n in ('eica','eicb','eicc')]
    text+=define('eicd',ADAPTER,k('eib7',*args(MODEL),v('observed'),*predicates))
    return text

def build():
    old=parse(read(PARENT));doc=deepcopy(old);doc['statements']=[];library=imported()
    meanings={RENAMES[n]:m for n,m in json.loads(read(LIBRARY_BASIS))['definitions'].items() if n in RENAMES};meanings.update(MEANINGS)
    assert not set(meanings)&{d['name'] for d in old['declarations']}
    doc['declarations']+=library['declarations'];doc=parse(format_graph(doc,'compact')+definitions());doc['statements']=old['statements']
    added=doc['declarations'][len(old['declarations']):]
    basis=dict(status='grounded_electric_response_model_dependency',document=FULL,parent=PARENT,inherited_meaning_basis=PARENT_BASIS,
        primitives={},definitions=meanings,new_signatures={d['name']:{k:d[k] for k in ('parameters','result')} for d in added},limitations=LIMITS,
        reused_library=dict(document=LIBRARY,basis=LIBRARY_BASIS,renames=RENAMES))
    body=format_graph(doc,'compact')+'\n';core=extract_document(doc,roots=list(meanings),statement_indices=[]).document
    ann=json.loads(read('data/carrier-relative-motion-identifiers-v1.json'));ann.update(document=FULL,document_sha256=digest(body.encode('utf-8')))
    enc=lambda x:json.dumps(x,ensure_ascii=False,indent=2)+'\n'
    return {FULL:body,CORE:format_graph(core,'compact')+'\n',BASIS:enc(basis),ANNOTATIONS:enc(ann)}

if __name__=='__main__':
    from scripts.audit_opening_scope import write_exact
    for p,b in build().items():write_exact(ROOT/p,b)
    print('Electric response comparison grounded in same-body physical records')
