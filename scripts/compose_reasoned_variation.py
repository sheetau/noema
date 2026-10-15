"""Contrast directive-only response with reasoned variation in fixed cases."""
from copy import deepcopy
import hashlib,json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_tender_care import ROOT,SOURCE as PARENT
from scripts.compose_self_benefit import SCHEMA,GOV,HIGH,REST
from scripts.compose_policy_norms import DESCRIPTION
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/reasoned-variation.noema'
SOURCE='examples/v016/kant-reasoned-variation.noema'
CORE='examples/v016/reasoned-variation-core.noema'
BASIS='data/reasoned-variation-basis-v1.json'
READING='data/reasoned-variation-reading-v1.json'
REVIEW='data/kant-manuscript-obligations-v3.json'
FIELDS=[('actor','a'),('topic','a'),('cases','h[d] c'),('assessed','h[a a d] c'),
    ('directive','h[a a d] a'),('choice','h[a a d] a'),('independent','h[a a d] c'),('reasons','h[a a d a] c')]
def params(fields):return ' '.join(n+' '+t for n,t in fields)
def av(fields):return [v(n) for n,t in fields]


def definitions():
    at=lambda name,point:app(v(name),v('actor'),v('topic'),v(point))
    valid=both(quant('g','point','d',app(v('cases'),v('point'))),quant('f','point','d',op('y',
        app(v('cases'),v('point')),at('assessed','point'))))
    text=definition('rym',params(FIELDS),valid)
    pair=both(app(v('cases'),v('first')),app(v('cases'),v('second')),op('e',at('directive','first'),at('directive','second')))
    fixed=quant('f','first','d',quant('f','second','d',op('y',pair,op('e',at('choice','first'),at('choice','second')))))
    text+=definition('ryn',params(FIELDS),both(k('rym',*av(FIELDS)),fixed))
    changed=op('u',op('e',at('choice','first'),at('choice','second')))
    reasons=quant('g','reason','a',op('u',op('e',
        app(v('reasons'),v('actor'),v('topic'),v('first'),v('reason')),
        app(v('reasons'),v('actor'),v('topic'),v('second'),v('reason')))))
    witness=quant('g','first','d',quant('g','second','d',both(pair,changed,at('independent','first'),at('independent','second'),reasons)))
    text+=definition('ryo',params(FIELDS),both(k('rym',*av(FIELDS)),witness))
    return text


def additions():
    providers=[('cases','h[a a d d] c'),('assessed','h[a a d d] c'),('directive','h[a a d] a'),
        ('choice','h[a a d] a'),('judgment','h[a a d] a'),('chooses','h[a a a a d] c'),
        ('people','h[a '+DESCRIPTION+' a d] j[a]'),('scope','h[a '+DESCRIPTION+' a d a] c')]
    text=''.join(primitive('iax'+n,t) for n,t in providers)
    judgment=k('iaxjudgment',v('actor'),v('topic'),v('point'))
    independent=both(k('aa',v('actor')),k('fb',judgment,v('topic'),v('point')),
        k('rcr',v('actor'),judgment,v('point'),*['p '+n for n in ('ab','ac','fa','fb','fc','fd','ad')]),
        k('iaxchooses',v('actor'),v('topic'),judgment,k('iaxchoice',v('actor'),v('topic'),v('point')),v('point')))
    text+=definition('iaxindependent','actor a topic a point d',independent)
    text+=definition('iaxreasons','actor a topic a point d reason a',k('fc',judgment,v('reason'),v('point')))
    bindings=dict(actor=v('actor'),topic=v('topic'),cases='i[point d][k iaxcases[v actor v topic v anchor v point]]',
        assessed='i[person a matter a point d][k iaxassessed[v person v matter v anchor v point]]')
    bindings.update({n:'p iax'+n for n in ('directive','choice','independent','reasons')})
    for name,target in (('iaxdirected','ryn'),('iaxresponsive','ryo')):
        text+=definition(name,'actor a topic a anchor d',k(target,*[bindings[n] for n,t in FIELDS]))
    text+=definition('iaxbeyond','person a point d',both(k('aa',v('person')),
        quant('g','topic','a',k('iaxresponsive',v('person'),v('topic'),v('point')))))
    identities='actor a policy '+DESCRIPTION+' community a anchor d point d'
    targets=k('iaxpeople',v('actor'),v('policy'),v('community'),v('anchor'))
    scope='i[person a][k iaxscope[v actor v policy v community v anchor v person]]'
    each=quant('f','person','a',op('y',app(scope,v('person')),k('iaxbeyond',v('person'),v('point'))))
    text+=definition('iaxbeneficiaries',identities,both(k('rcm',targets,scope),each))
    rest='i[reading '+HIGH+' community a contributors j[a] anchor d start d end d late d]['+both(
        k('iaxbeneficiaries',v('actor'),v('second'),v('community'),v('anchor'),v('late')),
        app(v('remaining'),v('reading'),v('community'),v('contributors'),v('anchor'),v('start'),v('end'),v('late')))+']'
    text+=definition('iaxschema',params(SCHEMA),k('iawiatschema',v('reading'),*av(GOV),rest))
    text+=definition('iaxattribution','',k('iatreport',k('iagnode'),k('wa'),'r c[p iaxschema]',k('iagscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iaxattribution[]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rym','ryn','ryo'])
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements'])|{'iaxdirected'})
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='reasoned_variation_beyond_directive_only_profile',parent=PARENT,document=SOURCE,
        definitions={
            'rym':'同じ行為者・論点の非空の比較状況が全て評価済みである。',
            'ryn':'rymの範囲で、指示が同じなら選択も同じである。指示以外への感応がこの範囲で表れないという応答モデル。',
            'ryo':'rymの範囲に、同じ指示に対して異なる選択をし、両方で独立した判断があり、用いる理由の集合も異なる一対がある。rynとは両立しない。',
            'iaxindependent':'同じ人・論点・状況の指定判断にrcrを要求し、その同じ判断に基づく選択を結ぶ。別の判断や論点の吟味を流用しない。',
            'iaxresponsive':'同じ本人・論点・基準時で固定した候補にryoを適用する。',
            'iaxbeyond':'人であり、その評価時点に、ある論点で独立した理由付きの応答差を持つ可能な事例がある。今その判断を実行していることは要求しない。',
            'iaxbeneficiaries':'同じ政府役の主体・新政策・共同体・基準時で固定した非空の対象者全員に、政治的終点でiaxbeyondを要求する。',
            'iaxschema/iaxattribution':'既存の条件文の後件へ対象者の資格を接続し、同じ箇所・著者・範囲への部分ひな形帰属を更新する。'},
        primitive_conventions={
            'iaxcases/iaxassessed':'本人・同じ論点・基準時において実行可能と解釈した比較候補と、指示・選択・判断・理由を評価済みである条件。全現実の機会を尽くすとはしない。',
            'iaxdirective':'本人に外部から与えられた指示の内容を識別する対象。同じ指示を保つ比較であり、別の指示を同一名へ潰さない。発令権の正当性は含まない。',
            'iaxchoice/iaxjudgment/iaxchooses':'その本人・論点・候補状況で選ぶ応答、判断、およびその同じ判断に基づいてその応答を選ぶ関係。単に同時に判断があったことではない。',
            'iaxpeople/iaxscope':'その新政策で扱われる対象者の完全な一覧と範囲。原因側の民衆や政府そのものと自動同一化しない。後に尊厳の扱いを接続する際にも同じ指定を使う必要がある。'},
        limitations=[
            '機械を、外部からの指示だけで応答が決まる役割として読む政治的な比喩の候補である。物理的機械の名詞定義や、あらゆる機械には理性がないという一般命題ではない。',
            '同じ指示でも理由に基づく異なる判断が可能という強い読みを採る。原文がその必要十分条件を述べるわけではなく、理由の違いだけを原因とする介入比較も証明していない。',
            '比較は固定した論点・本人・候補に限る。異なる状況の他の事情が全て同じであることや、指示内容の一般的な同義判定までは保証しない。',
            'rynの成立を能力の欠如や人でないことへ読み替えない。比較候補が乏しければ、理性的な人にもrynが成立し得る。',
            'nunは条件文の政治的終点に置くが、以前は理性を持たなかったことや段階的な能力取得は補わない。総称的人間の対象範囲と尊厳の内容・扱いの接続は未完。',
            '旧定義と先行21主張を保存し、最後の帰属だけ改訂する。八つの引数を持つひな形は残り、原文範囲や意味確認済み区間は加算しない。'])


def reading():
    return dict(checked_on='2026-10-16',sources=[
        dict(url='https://www.korpora.org/Kant/aa08/042.html',lines='1-2',observation='人間を機械以上のものとする関係節が、その尊厳に即した扱いを述べる不定詞句に入る。'),
        dict(url='https://www.korpora.org/Kant/aa08/037.html',lines='16-26',observation='政府の目的へ受動的に向けられる役割を機構・機械の部分として述べ、公衆に著作で語る学識者として理性を使うことと両立させる。')],
        decisions=['数量比較や人間の物理的構造の否定に置き換えず、指示に限られない独立した判断の候補として表す。',
            '物理的機械の一般的な分類をこの政治的な比喩の意味説明で済ませない。選んだ操作的な条件の強さは引き続き原文と照合する。'])


def review(files):
    packet=json.loads((ROOT/'data/kant-manuscript-obligations-v2.json').read_text(encoding='utf-8'))
    packet.update(version='kant-manuscript-obligations-v3',supersedes='data/kant-manuscript-obligations-v2.json',
        document=SOURCE,document_sha256=hashlib.sha256(files[SOURCE].encode('utf-8')).hexdigest())
    for row in packet['obligations']:
        if row['id']=='more_than_machine':
            row['candidate_roots']=['iaxbeyond','iaxbeneficiaries','ryo']
            row['remaining']='指示だけで決まる応答を超える独立した理由付き判断の候補を、同じ政策の対象者と政治的終点へ接続した。操作的な条件の強さ、対象範囲、理由差の因果的な役割、物理的機械の名詞定義、原文の意味一致は未確認。'
    packet['templates'][0]['symbol']='iaxschema'
    packet['evidence_files'] += [BASIS,READING]
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
