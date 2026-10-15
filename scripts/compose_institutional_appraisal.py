"""Constitute institutional acceptance from scoped, assessed procedural inputs."""
from copy import deepcopy
import hashlib,json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from noema.linking import relocate
from scripts.compose_governing_role import ROOT,SOURCE as PARENT
from scripts.compose_self_benefit import BASE,TRUE
from scripts.compose_collective_office import params,av
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/institutional-appraisal.noema'
SOURCE='examples/v016/kant-institutional-appraisal.noema'
CORE='examples/v016/institutional-appraisal-core.noema'
BASIS='data/institutional-appraisal-basis-v1.json'
REVIEW='data/kant-manuscript-obligations-v10.json'
CONSTITUTES='h['+' '.join(t for n,t in BASE)+' j[a] a] c'
FIELDS=BASE+[('participants','j[a]'),('scope','h[a] c'),('persons','h[a] c'),('classified','h[a] c'),
    ('positions','h[a] c'),('rule','a'),('constitutes',CONSTITUTES),('decides','h[a j[c]] c')]


def definitions():
    participant=app(v('scope'),v('person'))
    return definition('ryw',params(FIELDS),both(k('rcm',v('participants'),v('scope')),
        quant('f','person','a',op('y',participant,both(app(v('persons'),v('person')),app(v('classified'),v('person'))))),
        app(v('constitutes'),*av(BASE),v('participants'),v('rule')),
        app(v('decides'),v('rule'),k('rwl',v('participants'),v('positions')))))


def additions():
    prefix='h['+' '.join(t for n,t in BASE)
    text=''.join(primitive('ibe'+name,sort) for name,sort in (
        ('participants',prefix+'] j[a]'),('scope',prefix+' a] c'),('classified',prefix+' a] c'),
        ('position',prefix+' a] c'),('rule',prefix+'] a'),('constitutes',CONSTITUTES),
        ('decides','h[a j[c]] c'),('collective','h[a d] c')))
    refs={n:v(n) for n,t in BASE}
    refs.update(participants=k('ibeparticipants',*av(BASE)),persons='p aa',rule=k('iberule',*av(BASE)),
        constitutes='p ibeconstitutes',decides='p ibedecides')
    refs.update({name:'i[person a]['+k('ibe'+target,*av(BASE),v('person'))+']' for name,target in
        [('scope','scope'),('classified','classified'),('positions','position')]})
    human=k('aa',v('assessor'));group=k('ibecollective',v('assessor'),v('context'))
    individual=both(human,op('u',group),k('iatawareness',*av(BASE)))
    institutional=both(op('u',human),group,k('ryw',*[refs[n] for n,t in FIELDS]))
    return text+definition('ibeawareness',params(BASE),op('x',individual,institutional))


def manuscript():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions())
    selected=closure(parent,[parent['statements'][-1]['body']['symbol']]);affected={'iatawareness'}
    for row in selected:
        if _references(row)&affected:affected.add(row['name'])
    mapping={d['name']:d['name'] for d in parent['declarations']}
    mapping.update({name:'ibe'+name for name in affected})
    mapping.update(iatawareness='ibeawareness',iatappraisal='ibeappraisal',ibdschema='ibeschema',ibdattribution='ibeattribution')
    assert not ({mapping[n] for n in affected}-{'ibeawareness'})&{d['name'] for d in doc['declarations']}
    for row in selected:
        if row['name'] in affected and row['name']!='iatawareness':doc['declarations'].append(relocate(row,mapping))
    doc['statements']=deepcopy(parent['statements'][:-1])+[relocate(parent['statements'][-1],mapping)]
    return parse(format_graph(doc,'compact')),{n:mapping[n] for n in sorted(affected)}


def build():
    doc,_=manuscript();lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['ryw'])
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='institutional_acceptance_from_constitutive_procedure',parent=PARENT,document=SOURCE,
        definitions={
            'ryw':'同じ判断主体・行為主体・受益対象・政策記述・評価手続記述・文脈について、完全な非空の参加者列と全員の入力確認を要求する。その判断で有効な構成規則と順序付き参加者列を照合し、同じ規則で既存rwlが射影した入力列を計算する。',
            'ibeawareness':'人の直接的認識と、組織の構成規則による採用を区別する。人の枝は既存iatawarenessを使い、組織の枝はrywを使う。人・組織の両分類が同時に肯定された入力や両方未該当の入力は採用しない。',
            'ibeappraisal':'既存ryaの認識条件をibeawarenessへ接続する。非空の判断候補の全てで同じ利益評価が成立する条件を保ち、組織の採用だけで実際の利益を断言しない。',
            'ibeschema/ibeattribution':'同じ統治主体・政策・共同体・時間の条件を保持した本文で、新しい自己利益判断と帰属を参照する。'},
        primitive_conventions={
            'ibecollective':'指定時点に、個人の心理とは区別する組織的判断主体として扱う分類。人でない物を全て組織と扱うための既定値ではない。',
            'ibeparticipants/ibescope':'同じ判断に入力する担当者全員の重複しない順序付き列と同じ範囲。住民全員・組織の全構成員と同一とは限らず、一人の担当者でもよい。',
            'ibeclassified/ibeposition':'同じ判断について各担当者の手続上の入力が確認済みであることと、その肯否。私的な信念や公衆への発言の有無を自動的に代入しない。不明を反対票にしない。',
            'iberule/ibedecides':'入力列の各位置と判断結果を結ぶ手続の識別子と計算。同じ識別子は同じ引数規約・計算を指す。識別子だけを手続の説明済みの意味とはしない。規則の計算はNoemaで定義することもできる。',
            'ibeconstitutes':'指定された判断・担当者の順序・規則において、その規則の出力を組織の採用として扱う構成関係が有効であること。単なる集計や組織名での発言から補わない。'},
        limitations=[
            '制度上の採用を組織の肯定判断に使う候補である。私的な信念の全員一致・多数決・単独指導者の規則など、いずれかを全政府へ固定しない。',
            '構成規則の成立・承認・正当性、担当者の資格や入力の成立過程、異議や棄権、矛盾する複数判断の整合性は未完。二値入力のこの候補だけで組織的判断一般を説明し終えない。',
            '組織として採用することから、全構成員の私的信念・内容の真理・政策の実施を導かない。逆に一人や多数の私的信念だけから組織の判断を導かない。',
            '現実の政府の意思決定方法を原文から特定していない。読みの適合、利益の尺度、政府や国家の全意味、尊厳・残余条件と全文の意味一致は未完。',
            '旧定義・先行21主張と8引数のひな形を保存し、新たな原文範囲や意味確認済み区間は加算しない。'])


def review(files):
    packet=json.loads((ROOT/'data/kant-manuscript-obligations-v9.json').read_text(encoding='utf-8'));_,mapping=manuscript()
    packet.update(version='kant-manuscript-obligations-v10',supersedes='data/kant-manuscript-obligations-v9.json',document=SOURCE,
        document_sha256=hashlib.sha256(files[SOURCE].encode('utf-8')).hexdigest())
    for row in packet['obligations']:
        row['candidate_roots']=[mapping.get(n,n) for n in row['candidate_roots']]
        if row['id']=='self_benefit':
            row['candidate_roots']+=['ibeawareness','ryw']
            row['remaining']='同じ政府・政策の利益判断に、確認済み担当者入力と有効な構成規則による組織的採用を接続した。規則の成立、入力の過程、実際の制度への適合、利益の読みと原文の意味一致は未確認。'
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
