"""Compose an explicit candidate reading of fear without supporting grounds."""
from copy import deepcopy
import json
from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT, definition
from scripts.compose_limits import call as k, app, op, both, quant, v
from scripts.compose_qualified_utterance import closure
from scripts.compose_described_apprehension import DESCRIPTION, RELATIONS as EMOTION, params, args
from scripts.compose_interpreted_depiction import SOURCE as PARENT

LIBRARY='examples/v016/supported-apprehension.noema'
EXAMPLE='examples/v016/supported-apprehension-example.noema'
SOURCE='examples/v016/kant-supported-apprehension.noema'
CORE='examples/v016/supported-apprehension-core.noema'
BASIS='data/supported-apprehension-basis-v1.json'
REVIEW='data/shadow-reading-review-v2.json'
GROUNDS=[('available','h[a a d] c'),('supports','h[a '+DESCRIPTION+' d d] c')]
RELATIONS=EMOTION+GROUNDS
FIELDS=[('person','a'),('topic',DESCRIPTION),('anchor','d')]+RELATIONS
EPISODE=[('episode','a')]+FIELDS
GENERAL=[('person','a'),('anchor','d')]+RELATIONS


def definitions():
    prospect=quant('g','prospect','d',both(app(v('anticipated'),v('episode'),v('anchor'),v('prospect')),
        app(v('adverse'),v('person'),v('prospect'))))
    state=both(app(v('experienced'),v('person'),v('episode'),v('anchor')),
        app(v('directed'),v('episode'),v('topic'),v('anchor')),app(v('aversive'),v('episode'),v('anchor')),prospect)
    text=definition('rvv',params(EPISODE),state)
    grounds=quant('g','reason','a',quant('g','prospect','d',both(
        app(v('available'),v('person'),v('reason'),v('anchor')),
        app(v('supports'),v('reason'),v('topic'),v('anchor'),v('prospect')),
        app(v('anticipated'),v('episode'),v('anchor'),v('prospect')),
        app(v('adverse'),v('person'),v('prospect')))))
    text+=definition('rvw',params(EPISODE),grounds)
    text+=definition('rvx',params(FIELDS),quant('g','episode','a',both(
        k('rvv',*args(EPISODE)),op('u',k('rvw',*args(EPISODE))))))
    text+=definition('rvy',params(GENERAL),quant('f','topic',DESCRIPTION,op('u',k('rvx',*args(FIELDS)))))
    return text


def additions():
    text=''
    for name,sort in RELATIONS:
        text+='r hzw'+name+'['+sort[2:sort.rfind(']')]+'] c.'
    text+=definition('hzwtarget','person a','b point[k rvy[v person v point '+
        ' '.join('p hzw'+n for n,t in RELATIONS)+']]','e')
    text+=definition('hzwonly','remaining h[a d] c anchor d',
        'k hzvonly[r[p hzwtarget] v remaining v anchor]')
    text+='r hzwannotation[a a i c[h[h[a d] c d] c] a d] c.'
    text+=definition('hzwattribution','',
        'k hzwannotation[k hztnode[] k wa[] r c[p hzwonly] k hztscope[] k wh[]]')
    return text


def build():
    library=parse('p:'+definitions())
    text=format_graph(library,'compact')+'r jlperson[] a.r jlepisode[] a.r jlanchor[] d.'
    text+='r jlcreature[a d] c.r jlwings[a d] c.r jlactualharm[a d] c.'
    text+=definition('jltopic','entity a','b point[w[k jlcreature[v entity v point]][k jlwings[v entity v point]]]','e')
    text+=definition('jlalias','entity a','k jltopic[v entity]','e')
    for name,sort in RELATIONS:text+='r jl'+name+'['+sort[2:sort.rfind(']')]+'] c.'
    refs={n:'p jl'+n for n,t in RELATIONS}
    refs.update(person='k jlperson[]',episode='k jlepisode[]',topic='r[p jltopic]',anchor='k jlanchor[]')
    expressions=[k('rvv',*[refs[n] for n,t in EPISODE]),k('rvw',*[refs[n] for n,t in EPISODE]),
        k('rvx',*[refs[n] for n,t in FIELDS]),k('rvy',*[refs[n] for n,t in GENERAL]),
        quant('g','entity','a','t[k jltopic[v entity]][k jlanchor[]]'),
        'k jlactualharm[k jlperson[] k jlanchor[]]']
    expressions+=['e[r['+expressions[3]+']][r['+expressions[3]+']]']
    example=parse(text+''.join('q['+q+'].' for q in expressions))
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    doc=deepcopy(parent);statements=doc['statements'];doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k hzwattribution[]].')
    doc['statements']=statements[:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:]
    core['declarations']=closure(doc,_references(core['statements']))
    return {path:format_graph(document,'compact')+'\n' for path,document in
        [(LIBRARY,library),(EXAMPLE,example),(SOURCE,doc),(CORE,core)]}


def basis():
    return dict(status='explicit_candidate_not_unique_or_complete_translation',definitions={
        'rvv':'同じ本人・情動状態・対象記述・基準文脈について、既存rvmの不快な不利益予期を状態ごとに取り出す。',
        'rvw':'本人が基準文脈で利用できる理由があり、その理由が同じ対象記述について、同じ状態で予期する不利益候補の少なくとも一つを支持する。支持の対象を別の記述や候補で代用しない。',
        'rvx':'rvvを満たす状態のうち、rvwを満たさない状態が少なくとも一つある。別の情動状態への理由でこの状態を根拠付けない。',
        'rvy':'全対象記述についてrvxが成立しない。恐れ全般の不在ではなく、理由に支えられない不利益予期の不在という候補。有限の話題一覧には限定しない。',
        'hzwtarget':'rvyを同じ本人と評価文脈へ適用した性質記述。',
        'hzwonly':'未充足だったtargetにhzwtargetを渡す。描写・対応・啓蒙・発言能力との既存接続を保持する。',
        'hzwattribution':'残る資格条件を引数に持つ候補解釈の記述を帰属する。解釈の唯一性やその内容の現実の真理は断言しない。'},
        parameters={
            'available':'同じ本人が同じ基準文脈で利用できる理由。理由が世界のどこかに存在するだけとは異なる。',
            'supports':'理由・対象記述・基準文脈・予期候補を結ぶ、指定した評価基準での支持関係。候補の実現や理由の演繹的証明、本人による実際の理由採用を含意しない。理由の評価基準自体は入力として残る。'},
        unresolved=[
            '辞書の関連表現は候補の根拠であり、カントの意図を一意に確定しない。政治的不安や迷信だけへ狭めず、候補解釈として保存する。',
            '少なくとも一つの不利益予期に利用可能な支持があればrvwは成立する。全予期の根拠付け、恐れの程度の合理性、実際の動機や原因は意味に追加していない。',
            '利用可能性と支持の意味規約、および既存情動関係の基礎付けは未完。支持を真理・証明・主観的確信へ自動変換しない。',
            '全記述への量化を保存する。有限検査は二つの明示した記述への具体化だけであり、全域の真理は検証していない。実行器は全記述域の直接評価を拒否する。',
            '字義的な恐れ・影の存在は解釈先の成立条件ではない。原文の比喩的対応qaは引き続き別に与える。',
            'remainingには軍隊・公的平穏等が残り、啓蒙の全意味・強調・自由国との対比・全文の意味確認も未完。'])


def review():
    return dict(status='documented_candidate_not_unique_reading',checked_date='2026-10-15',
        primary_url='https://www.korpora.org/Kant/aa08/041.html',location='AA VIII, page 41, lines 23–27',
        lexical_url='https://www.kassiber.de/grimmschatten.htm',
        lexical_location='Adelung: Grammatisch-kritisches Wörterbuch, Der Schatten, 1, proverb paragraph',
        short_excerpt='Seinen eigenen Schatten fliehen, figürlich, sich ohne Ursache fürchten.',
        evidence='項目本文の転載を確認した。関連する慣用表現に、理由なく恐れるという説明がある。原刊のページ画像は未照合。',
        inference='この語義用例から、理由に支えられない恐れをカントの描写の解釈候補として採る。原文と同一の言い回しではなく、この候補の唯一性の証拠とはしない。',
        choice='Ursacheを本草案では正当化の理由として具体化する。心理状態の発生原因の不在や、実際の危険の不在とは区別する。')


def main():
    payload=build()|{p:json.dumps(value,ensure_ascii=False,indent=2)+'\n' for p,value in [(BASIS,basis()),(REVIEW,review())]}
    for name,body in payload.items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
