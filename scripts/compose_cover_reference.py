"""Bind a depicted cover to an earlier regime without literal identification."""
from copy import deepcopy
import hashlib,json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from noema.linking import relocate
from scripts.compose_policy_constraints import ROOT,SOURCE as PARENT
from scripts.compose_covered_unfolding import FIELDS as GROWTH,COVER
from scripts.compose_ordered_contrast import CODE,RECORD
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure

LIBRARY='examples/v016/cover-reference.noema'
SOURCE='examples/v016/kant-cover-reference.noema'
CORE='examples/v016/cover-reference-core.noema'
BASIS='data/cover-reference-basis-v1.json'
READING='data/cover-reference-reading-v1.json'
REVIEW='data/kant-manuscript-obligations-v5.json'
MAPPING='h[a a a a a d d] c'
FIELDS=[('node','a'),('antecedent','a'),('author','a'),('scope','a'),('antecedentscope','a'),
    ('context','d'),('cover','a'),('regime','d'),('content',CODE),('records',RECORD),
    ('before','h[a a d] c'),('mapping',MAPPING)]


def definitions():
    return definition('ryr',' '.join(n+' '+t for n,t in FIELDS),both(
        op('u',op('e',v('node'),v('antecedent'))),
        app(v('records'),v('antecedent'),v('author'),v('content'),v('antecedentscope'),v('context')),
        app(v('before'),v('antecedent'),v('node'),v('context')),
        op('u',app(v('before'),v('node'),v('antecedent'),v('context'))),
        app(v('mapping'),v('node'),v('author'),v('scope'),v('antecedentscope'),v('cover'),v('regime'),v('context'))))


def additions():
    text='r iazcover[a a a d] a.r iazmapping[a a a a a d d] c.'
    text+=definition('iazselected','',k('iazcover',k('iagnode'),k('wa'),k('iagscope'),k('wh')),'a')
    text+=definition('iazreference','',k('ryr',k('iagnode'),k('iafrightnode'),k('wa'),k('iagscope'),k('iacscope'),
        k('wh'),k('iazselected'),k('iaclower',k('wh')),'r d[k iafright[]]','p iaereport','p ue','p iazmapping'))
    refs=dict(object=v('object'),process=v('process'),start=v('start'),end=v('anchor'),cover=k('iazselected'),
        history='i[point d][k iaghistory[v object v anchor v point]]',
        before='i[left d right d][k iagbefore[v object v anchor v left v right]]',
        features='i[feature a][k iagfeatures[v object v anchor v feature]]')
    refs.update({n:'p iag'+n for n,t in GROWTH[6:]+COVER[1:] if n!='features'})
    body=quant('g','process','a',quant('g','start','d',both(k('rw5',*[refs[n] for n,t in GROWTH+COVER]),
        k('df',v('process'),k('qb'),v('anchor')),k('dg',v('process'),v('anchor')))))
    text+=definition('iazdepiction','object a','b anchor['+both(body,op('t',k('iawcare',v('object')),v('anchor')))+']','e')
    return text


def manuscript():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions())
    selected=closure(parent,['iayattribution']);affected={'iawdepiction','iawiahfamily'}
    for row in selected:
        if _references(row)&affected:affected.add(row['name'])
    mapping={d['name']:d['name'] for d in parent['declarations']}
    mapping.update({name:'iaz'+name for name in affected})
    mapping.update(iawdepiction='iazdepiction',iawiahfamily='iazfamily')
    assert not ({mapping[n] for n in affected}-{'iazdepiction'})&{d['name'] for d in doc['declarations']}
    for row in selected:
        if row['name'] not in affected or row['name']=='iawdepiction':continue
        new=relocate(row,mapping)
        if row['name']=='iawiahfamily':
            new['body']=dict(kind='and',arguments=[new['body'],dict(kind='call',symbol='iazreference',arguments=[])])
        doc['declarations'].append(new)
    doc['statements']=deepcopy(parent['statements'][:-1])+[relocate(parent['statements'][-1],mapping)]
    return parse(format_graph(doc,'compact')),{n:mapping[n] for n in sorted(affected)}


def build():
    doc,_=manuscript();lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['ryr'])
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements'])|{'iagdepiction','iawdepiction'})
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='explicit_metaphorical_backreference_to_lower_regime',parent=PARENT,document=SOURCE,
        definitions={
            'ryr':'先行箇所の同じ著者・内容記述・範囲・発話文脈への帰属と、本文上の正順・逆順の不在を確認する。現在箇所の範囲と先行箇所の範囲を区別したまま、描写物と制度状況の比喩上の対応を要求する。引用内容を実行しない。',
            'iazselected':'現在の箇所・著者・範囲・発話文脈から一つの描写上の覆いを選ぶ。描写の時点や成長の成功に応じて選び直さない。',
            'iazreference':'直前の低い自由の側の内容iafrightへの帰属と、その同じ比較文脈のiaclowerを使う。高い側の障壁へ自動で結ばない。',
            'iazdepiction':'従来の成長と世話の条件を保ち、存在量化で自由に選んでいた覆いをiazselectedへ束縛する。比喩の対応だけがあっても、別の覆いの下の成長では満たさない。',
            'iazfamily':'同じ描写への提示とiazreferenceを連言する。選んだ制度の内容や描写の現実的成立を断定せず、同じ帰属の祖先へ接続する。'},
        primitive_conventions={
            'iazcover':'指定された談話箇所で指示された描写世界の対象を返す。失敗時に適当な物を補わず、指示未確定は解釈の未確定として残す。',
            'iazmapping':'同じ箇所・著者・現在範囲・先行範囲・文脈において、描写上の覆いが指定の制度状況に対応するという指示解釈。物理的同一性、制度の真理、因果、保護の役割は含めない。'},
        limitations=[
            '直前の少ない市民的自由の側を指す読解候補であり、統治制度全般・服従の条件等を含む他の先行範囲を排除した語義確定ではない。',
            '制度状況を物理的な覆いと同一視しない。発話文脈で参照先を固定し、描写時点とは別に扱う。',
            '硬さの尺度・程度・材質、覆いの機構、芽の名詞内容、尊厳、全文の意味一致は未完。比喩の指示認定自体は解釈入力である。',
            '旧定義と先行21主張を保存する。描写記述の変更は読解の改訂であり同義変換ではない。八引数の部分ひな形を残し、新しい原文文字範囲や意味確認済み区間を加算しない。'])


def reading():
    return dict(checked_on='2026-10-16',url='https://www.korpora.org/Kant/aa08/041.html',lines='29–34',
        observation='高い自由の側と低い側を対比した後、後者の発展機会の直後に、指示詞付きの硬い覆いと芽の展開を置く。',
        interpretation='直前の低い市民的自由の側を比喩の対象側に選ぶ候補。指示詞だけから唯一の先行範囲や物理的同一性は導かない。',
        limitations=['原刊画像の新規照合は行っていない。AA電子本文を参照した。','選択した制度条件の範囲・硬さの程度・比喩の根拠は未確定。'])


def review(files):
    packet=json.loads((ROOT/'data/kant-manuscript-obligations-v4.json').read_text(encoding='utf-8'));_,mapping=manuscript()
    packet.update(version='kant-manuscript-obligations-v5',supersedes='data/kant-manuscript-obligations-v4.json',
        document=SOURCE,document_sha256=hashlib.sha256(files[SOURCE].encode('utf-8')).hexdigest())
    for row in packet['obligations']:
        row['candidate_roots']=[mapping.get(n,n) for n in row['candidate_roots']]
        if row['id']=='hard_cover':
            row['candidate_roots']=['iazreference','iazselected','iazdepiction','ryr']
            row['remaining']='直前の低い自由の側へ、同じ描写上の覆いを対応させる候補を接続した。先行範囲の選択の妥当性、硬さの程度・機構と原文全体の意味一致は未確認。'
    for template in packet['templates']:template['symbol']=mapping.get(template['symbol'],template['symbol'])
    packet['evidence_files']+=[BASIS,READING]
    return packet


def main():
    files=build();files|={BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n',READING:json.dumps(reading(),ensure_ascii=False,indent=2)+'\n',REVIEW:json.dumps(review(files),ensure_ascii=False,indent=2)+'\n'}
    for name,body in files.items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
