"""Connect appositive mentions of a property bundle, distinct from its bearer."""
from copy import deepcopy
import hashlib,json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from noema.linking import relocate
from scripts.compose_load_resistance import ROOT,SOURCE as PARENT
from scripts.compose_thinking_disposition import HIGH,TRUE,FALSE
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,v
from scripts.compose_qualified_utterance import closure

LIBRARY='examples/v016/property-apposition.noema'
SOURCE='examples/v016/kant-property-apposition.noema'
CORE='examples/v016/property-apposition-core.noema'
BASIS='data/property-apposition-basis-v1.json'
READING='data/property-apposition-reading-v1.json'
REVIEW='data/kant-manuscript-obligations-v7.json'
DENOTES='h[a a '+HIGH+' a d] c'
FIELDS=[('first','a'),('second','a'),('author','a'),('referent',HIGH),('scope','a'),('context','d'),
    ('denotes',DENOTES),('before','h[a a d] c'),('clarifies','h[a a a a d] c')]


def definitions():
    return definition('ryt',' '.join(n+' '+t for n,t in FIELDS),both(
        op('u',op('e',v('first'),v('second'))),
        *[app(v('denotes'),v(n),v('author'),v('referent'),v('scope'),v('context')) for n in ('first','second')],
        app(v('before'),v('first'),v('second'),v('context')),
        op('u',app(v('before'),v('second'),v('first'),v('context'))),
        app(v('clarifies'),v('first'),v('second'),v('author'),v('scope'),v('context'))))


def additions():
    text='r ibbgermnode[] a.r ibbdetailnode[] a.r ibbdenotes[a a '+HIGH+' a d] c.r ibbclarifies[a a a a d] c.'
    body=both(op('u',op('e',k('iahleanfeature'),k('iahcallfeature'))),
        k('iahmanifest',v('person'),k('iahleanfeature'),v('point'),v('inner')),
        k('iahmanifest',v('person'),k('iahcallfeature'),v('point'),v('inner')))
    text+=definition('ibbbundle','person a inner c','b point['+body+']','e')
    for name,flag in [('ibbinner',TRUE),('ibbvocation',FALSE)]:
        text+=definition(name,'person a',k('ibbbundle',v('person'),flag),'e')
    def branch(development,bundle):
        return both(op('e',v('reading'),'r b[p '+development+']'),k('ryt',k('ibbgermnode'),k('ibbdetailnode'),k('wa'),
            'r b[p '+bundle+']',k('iagscope'),k('wh'),'p ibbdenotes','p ue','p ibbclarifies'))
    text+=definition('ibbapposition','reading '+HIGH,op('x',branch('iahinner','ibbinner'),branch('iahvocation','ibbvocation')))
    return text


def manuscript():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions())
    selected=closure(parent,[parent['statements'][-1]['body']['symbol']]);affected={'ibafamily'}
    for row in selected:
        if _references(row)&affected:affected.add(row['name'])
    mapping={d['name']:d['name'] for d in parent['declarations']}
    mapping.update({name:'ibb'+name for name in affected});mapping['ibafamily']='ibbfamily'
    assert not {mapping[n] for n in affected}&{d['name'] for d in doc['declarations']}
    for row in selected:
        if row['name'] not in affected:continue
        new=relocate(row,mapping)
        if row['name']=='ibafamily':
            new['body']=dict(kind='and',arguments=[new['body'],dict(kind='call',symbol='ibbapposition',arguments=[dict(kind='variable',name=new['parameters'][0]['name'])])])
        doc['declarations'].append(new)
    doc['statements']=deepcopy(parent['statements'][:-1])+[relocate(parent['statements'][-1],mapping)]
    return parse(format_graph(doc,'compact')),{n:mapping[n] for n in sorted(affected)}


def build():
    doc,_=manuscript();lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['ryt'])
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='apposition_of_same_composed_property_description',parent=PARENT,document=SOURCE,
        definitions={
            'ryt':'異なる二箇所が同じ著者・範囲・発話文脈で同じ階数1の性質記述を指し、本文順序が正向きで逆向きでなく、後の箇所が前を説明する。指示対象の内容を実行しない。',
            'ibbbundle':'同じ人・時点・読解について、既存iahmanifestの志向と使命に当たる二性質がともに顕在化する内容。二つの性質識別子を区別し、他人や別時点の第二性質で補わない。',
            'ibbinner/ibbvocation':'使命を内的な衝動と読む場合、課題の付与と読む場合の性質の組。各々、iahinner/iahvocationが発展させる同じiahmanifestを共有する。',
            'ibbapposition':'選ばれた発展の読みと同じ読みの性質の組を、芽の名詞句と後の説明句が指す対象にする。発展過程そのものと、時点ごとの性質の組は別の記述にする。',
            'ibbfamily':'従来の描写への提示と覆いの参照を保持し、同じ読解のibbappositionを加える。'},
        primitive_conventions={
            'ibbdenotes':'指定の著者・範囲・発話文脈の名詞句が、名詞化された性質の記述を指すという解釈。性質を持つ個人そのものや植物個体とは型を分ける。',
            'ibbclarifies':'後の箇所が前の箇所の指示を説明するという談話関係。同じ記述を繰り返すことや本文上の順序だけから自動認定しない。',
            'ibbgermnode/ibbdetailnode':'原文u0017の芽を述べる名詞句とnämlichで導かれる説明句の箇所。語の意味を原語表記で代用しない。'},
        limitations=[
            '名詞句を性質記述の名詞化として扱う候補であり、独立した抽象個体の存在や、植物の芽と人の物理的同一性を主張しない。',
            '性質記述を指すことと、その性質が誰かに実際に成立することは別である。発展には既存の潜在性・変化過程も必要で、組が現在成立するだけでは発展を導かない。',
            'Berufの二候補の選定、志向の程度、芽の生物学的内容と起源、自然の意味、原文全体の意味一致は未完。参照と説明行為の認定は解釈入力として残る。',
            '旧定義と先行21主張を保存し、八引数の部分ひな形を残す。原文の新しい対応範囲や意味確認済み区間は加算しない。'])


def reading():
    return dict(checked_on='2026-10-16',url='https://www.korpora.org/Kant/aa08/041.html',lines='33–34',
        observation='芽の名詞句に、nämlichで導かれた自由な思考へのHangとBerufの句が続く。',
        interpretation='比喩の対象側では、二つの名詞句が同じ性質の組を指す説明的同格として記述する。人そのものと芽を同一化しない。',
        limitations=['原刊画像の新規照合は行っていない。','AdelungのKeim見出しは取得できず、生物学的語義を今回確定していない。','名詞化の分析とBerufの読解候補は意味確認を残す。'])


def review(files):
    packet=json.loads((ROOT/'data/kant-manuscript-obligations-v6.json').read_text(encoding='utf-8'));_,mapping=manuscript()
    packet.update(version='kant-manuscript-obligations-v7',supersedes='data/kant-manuscript-obligations-v6.json',document=SOURCE,
        document_sha256=hashlib.sha256(files[SOURCE].encode('utf-8')).hexdigest())
    for row in packet['obligations']:
        row['candidate_roots']=[mapping.get(n,n) for n in row['candidate_roots']]
        if row['id']=='thinking_disposition':
            row['candidate_roots']+=['ibbapposition','ibbbundle','ryt']
            row['remaining']='同じ読解の傾向と使命の組を二つの名詞句が指す同格を接続した。名詞化の分析、読解候補の選定・解釈範囲、志向の尺度と原文の意味一致は未確認。'
        if row['id']=='germ':
            row['candidate_roots']+=['ibbapposition']
            row['remaining']='比喩の対象側で性質の組を指す名詞句として接続した。植物の芽・素質の名詞内容と起源、自然との関係の説明は未完。'
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
