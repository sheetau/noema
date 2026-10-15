"""Require a policy to include a concrete criterion for the same beneficiaries."""
from copy import deepcopy
import hashlib,json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_reasoned_variation import ROOT,SOURCE as PARENT,SCHEMA,GOV,HIGH,params,av
from scripts.compose_policy_norms import DESCRIPTION
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure

LIBRARY='examples/v016/policy-constraints.noema'
SOURCE='examples/v016/kant-policy-constraints.noema'
CORE='examples/v016/policy-constraints-core.noema'
BASIS='data/policy-constraints-basis-v1.json'
REVIEW='data/kant-manuscript-obligations-v4.json'
FIELDS=[('policy',DESCRIPTION),('constraint','h[j[a]] e'),('cases','h[d] c')]
BOUND=[('source','a'),('actor','a'),('office','a'),('policy',DESCRIPTION),('community','a'),('anchor','d')]
TRUE='e[n p a b][n p a b]'


def definitions():
    selected=app(v('cases'),v('point'))
    policy=op('t',app('s[v policy]','l[a][]'),v('point'))
    constraint=op('t',app(v('constraint'),'l[a][]'),v('point'))
    text=definition('ryp',params(FIELDS),both(quant('g','point','d',selected),
        quant('f','point','d',op('y',selected,op('y',policy,constraint)))))
    text+=definition('ryq',params(FIELDS),quant('g','point','d',both(selected,policy)))
    return text


def additions():
    text='r iaynormcases['+' '.join(t for n,t in BOUND)+' d] c.'
    people=k('iaxpeople',v('actor'),v('policy'),v('community'),v('anchor'))
    scope='i[person a][k iaxscope[v actor v policy v community v anchor v person]]'
    cases='i[point d]['+k('iaynormcases',*av(BOUND),v('point'))+']'
    text+=definition('iaycontent',params(BOUND),k('iavtreatment',v('source'),v('actor'),v('office'),people,scope,cases),'h[j[a]] e')
    valid=both(k('rcm',people,scope),quant('g','point','d',app(cases,v('point'))))
    text+=definition('iaymeaning',params(BOUND),both(valid,k('ryp',v('policy'),k('iaycontent',*av(BOUND)),'i[point d]['+TRUE+']')))
    rest='i[reading '+HIGH+' community a contributors j[a] anchor d start d end d late d]['+both(
        k('iaymeaning',v('source'),v('actor'),v('office'),v('second'),v('community'),v('anchor')),
        app(v('remaining'),v('reading'),v('community'),v('contributors'),v('anchor'),v('start'),v('end'),v('late')))+']'
    text+=definition('iayschema',params(SCHEMA),k('iaxschema',v('reading'),*av(GOV),rest))
    text+=definition('iayattribution','',k('iatreport',k('iagnode'),k('wa'),'r c[p iayschema]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iayattribution[]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['ryp','ryq'])
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements'])|{'ryq'})
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='policy_includes_same_beneficiary_public_permission_criterion',parent=PARENT,document=SOURCE,
        definitions={
            'ryp':'非空の比較状況の全てで、同じ政策記述を空の引数列で適用した内容が成立するなら、指定の必要条件も成立する。必要条件との同値や政策の実例は要求しない。',
            'ryq':'同じ比較状況のどこかで政策内容が成立することを、rypと別に検査する。',
            'iaycontent':'前段と同じ主体・政策・共同体・基準時の対象者へ、既存iavtreatmentの要求維持・現在の要求と公的理性使用の許可を結ぶ。',
            'iaymeaning':'対象者一覧の適合と比較状況の非空性を検査し、全評価状況で新政策の内容がiaycontentを含意することを要求する。公的許可だけを尊厳の全条件へ置き換えない。',
            'iayschema/ iayattribution':'同じ新政策への自己利益判断と対象者の資格を保ったまま、政策の必要条件を後件へ加え、その部分ひな形を同じ著者・箇所・文脈へ帰属する。'},
        primitive_conventions={
            'iaynormcases':'出所・主体・職務・政策記述・共同体・基準時で固定する、基準への要求の維持を調べる比較状況。対象者を候補ごとに選び直さない。'},
        limitations=[
            '公的理性使用の許可は扱いの一つの必要条件として接続した。政策がほかの条件を含むことを許し、これだけを尊厳の必要十分条件とはしない。',
            '含意は適用した内容についてであり、異なる記述を同一名へ変換せず、規範や認識を別名へ自動移転しない。既存の政策記述と主体を保持する。',
            '全状況の含意は一般の意味条件である。有限モデルの検査を無限の状況領域の証明に数えない。',
            '政策が全比較状況で偽なら含意だけは成立し得る。ryqを別に設け、本文の自己利益判断では従来のrx6が実現側・非実現側の非空の候補を要求することも保つ。現在の現実での履行は補わない。',
            '対象者・比較状況・規範の正当性、尊厳の他の内容と根拠、全文の意味一致は未完。旧iaustanding/iautreatmentの可変基準一覧は自動では使わず、静的に展開済みのiavtreatmentを使う。',
            '旧定義と先行21主張を保存する。八引数の部分ひな形は残り、原文範囲と意味確認済み区間は加算しない。'])


def review(files):
    packet=json.loads((ROOT/'data/kant-manuscript-obligations-v3.json').read_text(encoding='utf-8'))
    packet.update(version='kant-manuscript-obligations-v4',supersedes='data/kant-manuscript-obligations-v3.json',
        document=SOURCE,document_sha256=hashlib.sha256(files[SOURCE].encode('utf-8')).hexdigest())
    for row in packet['obligations']:
        if row['id']=='human_patient':
            row['candidate_roots']=['iaxbeneficiaries','iaycontent','iavclaim']
            row['remaining']='同じ新政策・主体・共同体・基準時の対象者を、独立判断の資格と具体的な許可基準の両方へ接続した。総称的人間の範囲と原文全体の意味一致は未確認。'
        if row['id']=='dignified_treatment':
            row['candidate_roots']=['iaymeaning','iaycontent','iavclaim','iavtreatment']
            row['remaining']='同じ対象者への公的理性使用の許可と基準への要求を、新政策内容の必要条件として本文へ接続した。尊厳の他の内容・根拠・規範の正当性は未説明で、この一基準との同値を要求していない。'
    packet['templates'][0]['symbol']='iayschema';packet['evidence_files']+=[BASIS]
    return packet


def main():
    files=build();files|={BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n',REVIEW:json.dumps(review(files),ensure_ascii=False,indent=2)+'\n'}
    for name,body in files.items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
