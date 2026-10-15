"""Separate a resistance disposition from an actually loaded situation."""
from copy import deepcopy
import hashlib,json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from noema.linking import relocate
from scripts.compose_property_apposition import ROOT,SOURCE as PARENT
from scripts.compose_load_resistance import FIELDS as RESPONSE_FIELDS,PROVIDERS
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure

LIBRARY='examples/v016/dispositional-resistance.noema'
SOURCE='examples/v016/kant-dispositional-resistance.noema'
CORE='examples/v016/dispositional-resistance-core.noema'
BASIS='data/dispositional-resistance-basis-v1.json'
REVIEW='data/kant-manuscript-obligations-v8.json'
FIELDS=RESPONSE_FIELDS+[('prospects','h[a a a a a d d] c')]


def definitions():
    prospect=app(v('prospects'),*[v(n) for n in ('object','test','protocol','loadunit','deformationunit','context','candidate')])
    fixed={n:v(n) for n,t in RESPONSE_FIELDS}
    fixed.update(context=v('candidate'),tests='l[a][v test]',scope='i[item a][e[v item][v test]]')
    response=k('rys',*[fixed[n] for n,t in RESPONSE_FIELDS])
    per_test=both(quant('g','candidate','d',prospect),quant('f','candidate','d',op('y',prospect,response)))
    return definition('ryu',' '.join(n+' '+t for n,t in FIELDS),both(k('rcm',v('tests'),v('scope')),
        quant('f','test','a',op('y',app(v('scope'),v('test')),per_test))))


def additions():
    fixed={n:k('iba'+n,v('cover'),k('wh')) for n,t in PROVIDERS}
    fixed.update(object=v('cover'),context=v('point'),scope='i[test a][k ibascope[v cover k wh[] v test]]')
    fixed.update({n:'p iba'+n for n in ('assessed','load','deformation')})
    fixed['prospects']='p ibcprospects'
    return 'r ibcprospects[a a a a a d d] c.'+definition('ibcresistant','cover a point d',k('ryu',*[fixed[n] for n,t in FIELDS]))


def manuscript():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions())
    selected=closure(parent,[parent['statements'][-1]['body']['symbol']]);affected={'ibaresistant'}
    for row in selected:
        if _references(row)&affected:affected.add(row['name'])
    mapping={d['name']:d['name'] for d in parent['declarations']}
    mapping.update({name:'ibc'+name for name in affected})
    mapping.update(ibaresistant='ibcresistant',ibadepiction='ibcdepiction',ibbfamily='ibcfamily')
    assert not ({mapping[n] for n in affected}-{'ibcresistant'})&{d['name'] for d in doc['declarations']}
    for row in selected:
        if row['name'] in affected and row['name']!='ibaresistant':doc['declarations'].append(relocate(row,mapping))
    doc['statements']=deepcopy(parent['statements'][:-1])+[relocate(parent['statements'][-1],mapping)]
    return parse(format_graph(doc,'compact')),{n:mapping[n] for n in sorted(affected)}


def build():
    doc,_=manuscript();lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['ryu'])
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='protocol_relative_counterfactual_response',parent=PARENT,document=SOURCE,
        definitions={
            'ryu':'非空で重複なく完全な試験範囲の各試験について、対象・方法・二単位・評価時点を固定した応答候補状況が少なくとも一つ存在し、全候補で既存rysの荷重と変形の条件を満たす。評価時点自体の荷重や評価済みの読みは要求しない。',
            'ibcresistant':'覆いと発話文脈から基準を固定し、各描写時点を起点にした候補状況の応答を調べる。基準の発話文脈、性質の評価時点、仮定した応答状況の三者を分ける。',
            'ibcdepiction/ibcfamily':'成長区間の同じ覆いの耐性をryuへ接続し、世話、覆いの参照、性質の組を指す同格を保持する。'},
        primitive_conventions={
            'ibcprospects':'同じ対象を評価時点の状態から指定試験法で負荷した場合に、比較対象として採用する応答状況の関係。物・試験・方法・荷重単位・変形単位・評価時点・応答状況を順に受け取る。成功した応答だけを事後に選ぶ関係ではない。',
            'assessed/load/deformation':'先行の負荷応答と同じ意味と単位規約を使い、ここでは候補状況の中で評価する。実際の試験を行ったという主張や、モデルが応答を物理的に予測できるという主張にはしない。'},
        limitations=[
            '応答候補の選定と完全性、同じ物の状態を保持する物理的根拠は解釈入力として残る。任意の関係を与えて真になっても、現実の耐性の証明にはならない。',
            '全候補で成功を要求する範囲相対の強い条件である。通常性、例外、妨害、傾向性一般の十分な理論とはしない。候補が空なら偽、関係が不明なら解釈を中止し、成功と扱わない。',
            '旧rysは実際の応答条件として保持する。試験済みという事実と、負荷すれば耐えるという性質を相互に自動推論しない。',
            '硬さの歴史語義、試験法と閾値、測定の物理的基礎、芽・自然・尊厳の説明と原文全体の意味一致は未完。',
            '八引数の部分ひな形と先行21主張を保持し、新たな原文範囲や意味確認済み区間は加算しない。'])


def review(files):
    packet=json.loads((ROOT/'data/kant-manuscript-obligations-v7.json').read_text(encoding='utf-8'));_,mapping=manuscript()
    packet.update(version='kant-manuscript-obligations-v8',supersedes='data/kant-manuscript-obligations-v7.json',document=SOURCE,
        document_sha256=hashlib.sha256(files[SOURCE].encode('utf-8')).hexdigest())
    for row in packet['obligations']:
        row['candidate_roots']=[mapping.get(n,n) for n in row['candidate_roots']]
        if row['id']=='hard_cover':
            row['candidate_roots']+=['ryu']
            row['remaining']='評価時点と負荷した場合の候補状況を分け、実際には未試験でも述べられる耐性を接続した。候補状況の選定・完全性、物理的根拠、適切な方法と閾値、硬さの語義と原文の意味一致は未確認。'
    for template in packet['templates']:template['symbol']=mapping.get(template['symbol'],template['symbol'])
    packet['evidence_files']+=[BASIS]
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
