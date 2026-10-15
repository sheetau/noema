"""Compose risk-aware undertaking and a separately scoped permission denial."""
from copy import deepcopy
import json

from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT, definition
from scripts.compose_limits import call as k, app, op, both, quant, v
from scripts.compose_qualified_utterance import closure
from scripts.compose_armed_readiness import SOURCE as PARENT
from scripts.compose_assigned_formation import QUALIFICATION
from scripts.compose_anchored_ability import IDENTITY, GOAL_FIELDS
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/risk-undertaking.noema'
EXAMPLE='examples/v016/risk-undertaking-example.noema'
SOURCE='examples/v016/kant-risk-undertaking.noema'
CORE='examples/v016/risk-undertaking-core.noema'
BASIS='data/risk-undertaking-basis-v1.json'
ACTION='i c[h[a a] e]'
BASE=[('actor','a'),('activity','a'),('description',ACTION),('anchor','d')]
RISK=[('prospects','h[a a '+ACTION+' d d] c'),('adverse','h[a d] c')]
BELIEF=[('recognizes','h[a a '+ACTION+' d] c'),('views','h[a a '+ACTION+' d d] c')]
PURSUIT=[('begins','h[a a d] c'),('pursues','h[a a '+ACTION+' d] c')]
RELATIONS=RISK+BELIEF+PURSUIT
NORM='h[a a a a '+ACTION+' c d] c'
NORMS=[('required',NORM),('allowed',NORM)]
TARGET=[('standard','a'),('actor','a'),('role','a'),('activity','a'),('description',ACTION),('anchor','d')]
DENIAL=[('population','h[a d] c'),('standardfor','h[a d] a'),('rolefor','h[a d] a'),('candidates','h[a a d] c'),('anchor','d')]
TRUE='e[n p a b][n p a b]'


def params(fields):return ' '.join(n+' '+t for n,t in fields)
def av(fields):return [v(n) for n,t in fields]


def definitions():
    risk=quant('g','outcome','d',both(app(v('prospects'),*av(BASE),v('outcome')),
        app(v('adverse'),v('actor'),v('outcome'))))
    text=definition('rwg',params(BASE+RISK),risk)
    view=app(v('views'),*av(BASE),v('view'))
    belief=both(app(v('recognizes'),*av(BASE)),quant('g','view','d',view),
        quant('f','view','d',op('y',view,k('rwg',*av(BASE[:3]),v('view'),*av(RISK)))))
    text+=definition('rwh',params(BASE+RISK+BELIEF),belief)
    text+=definition('rwi',params(BASE+RELATIONS),both(app(v('begins'),v('actor'),v('activity'),v('anchor')),
        app(v('pursues'),*av(BASE)),k('rwh',*av(BASE+RISK+BELIEF))))
    target=av(TARGET[:-1])
    permit=app(v('allowed'),*target,TRUE,v('anchor'))
    forbid=app(v('required'),*target,op('u',TRUE),v('anchor'))
    text+=definition('rwj',params(TARGET+NORMS),both(permit,op('u',forbid)))
    fields=[p for p in TARGET if p[0]!='activity']+[('candidates','h[a a d] c')]+NORMS
    eligible=app(v('candidates'),v('actor'),v('activity'),v('anchor'))
    text+=definition('rwk',params(fields),quant('f','activity','a',op('y',eligible,op('u',k('rwj',*av(TARGET+NORMS))))))
    return text


def source_definitions():
    text='r iaastart[a a] d.'
    refs={'actor':v('actor'),'start':k('iaastart',v('actor'),v('activity')),
          'audience':'i[recipient a][k hztaudiencefor[v actor v recipient '+k('iaastart',v('actor'),v('activity'))+']]','template':'p hzsquotation'}
    refs.update({n:k('hzt'+n+'for',v('actor'),refs['start']) for n in ('speaker','hearers','context')})
    refs.update({n:'p hzt'+n for n,t in GOAL_FIELDS if n not in refs})
    text+=definition('iaautterance','actor a activity a',k('ruk',*[refs[n] for n,t in GOAL_FIELDS]),'e')
    text+=definition('iaaaligned','actor a activity a anchor d',both(op('e',refs['start'],v('anchor')),
        k('ruj',*[refs[n] for n,t in IDENTITY])))
    text+=''.join(primitive('iaa'+n,t) for n,t in RELATIONS+NORMS)
    text+=definition('iaaundertake','actor a activity a','b anchor['+k('rwi',v('actor'),v('activity'),
        'r c[p iaautterance]',v('anchor'),*['p iaa'+n for n,t in RELATIONS])+']','e')
    candidates=app(v('candidates'),v('actor'),v('activity'),v('anchor'))
    aligned=quant('f','activity','a',op('y',candidates,k('iaaaligned',v('actor'),v('activity'),v('anchor'))))
    denied=k('rwk',app(v('standardfor'),v('actor'),v('anchor')),v('actor'),
        app(v('rolefor'),v('actor'),v('anchor')),'r c[p iaaundertake]',v('anchor'),v('candidates'),'p iaarequired','p iaaallowed')
    text+=definition('iaadenial',params(DENIAL),quant('f','actor','a',op('y',
        app(v('population'),v('actor'),v('anchor')),both(aligned,denied))))
    text+=definition('iaacontrast','remaining '+QUALIFICATION+' '+params(DENIAL),both(
        k('hzzonly',v('remaining'),v('anchor')),k('iaadenial',*av(DENIAL))))
    sort='h['+QUALIFICATION+' '+' '.join(t for n,t in DENIAL)+'] c'
    text+='r iaaannotation[a a i c['+sort+'] a d] c.'
    text+=definition('iaaattribution','',k('iaaannotation',k('hztnode'),k('wa'),'r c[p iaacontrast]',k('hztscope'),k('wh')))
    return text


def build():
    library=parse('p:'+definitions())
    text=format_graph(library,'compact')+'r jraperson[] a.r jraactivity[] a.r jraanchor[] d.r jraachieved[a a d] c.'
    text+='r jrastandard[] a.r jrarole[] a.r jracandidates[a a d] c.'
    text+=definition('jragoal','actor a activity a','b point[k jraachieved[v actor v activity v point]]','e')
    text+=definition('jraalias','actor a activity a',k('jragoal',v('actor'),v('activity')),'e')
    text+=''.join(primitive('jra'+n,t) for n,t in RELATIONS+NORMS)
    refs=dict(actor=k('jraperson'),activity=k('jraactivity'),description='r c[p jragoal]',anchor=k('jraanchor'),
        standard=k('jrastandard'),role=k('jrarole'),candidates='p jracandidates')
    refs.update({n:'p jra'+n for n,t in RELATIONS+NORMS})
    questions=[k(name,*[refs[n] for n,t in fields]) for name,fields in
        [('rwg',BASE+RISK),('rwh',BASE+RISK+BELIEF),('rwi',BASE+RELATIONS),('rwj',TARGET+NORMS),
         ('rwk',[p for p in TARGET if p[0]!='activity']+[('candidates','h[a a d] c')]+NORMS)]]
    questions += ['t[k jragoal[k jraperson[] k jraactivity[]]][k jraanchor[]]',
                  'e[r c['+questions[2]+']][r c['+questions[2]+']]']
    example=parse(text+''.join('q['+q+'].' for q in questions))
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements=doc['statements'];doc['statements']=[]
    assert not {d['name'] for d in library['declarations']}&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions()+source_definitions()+'s[k iaaattribution[]].')
    doc['statements']=statements+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {path:format_graph(d,'compact')+'\n' for path,d in [(LIBRARY,library),(EXAMPLE,example),(SOURCE,doc),(CORE,core)]}


def basis():
    return dict(status='candidate_risk_aware_undertaking_and_standard_relative_denial',parent=PARENT,document=SOURCE,
        definitions={
            'rwg':'同じ本人・活動・目標記述・文脈の可能結果に、本人に不利益となるものがある。実行や現在の害を要求しない。',
            'rwh':'同じ目標記述を認識し、本人が採る非空の判断候補の全てでrwgが成立する。現実にも危険があるとは限らない。',
            'rwi':'同じ活動を同じ目標記述のために開始し、その時点でrwhを満たす。成功、恐れの不在、最終結果の不利益は要求しない。',
            'rwj':'同じ基準・主体・役割・活動・段階2の記述・文脈に積極的許可があり、不実行の要求がない。既存rdmの型を段階2の記述へ具体化したもの。',
            'rwk':'同じ主体の指定した活動候補のどれにもrwjが成立しない。禁止だけでなく積極的許可の不在でも成立し、能力の欠如を意味しない。',
            'iaautterance':'先行本文と同じhzsquotation、同じ話者・聞き手・基準文脈を用いた発言目標。活動に対応する基準文脈を明示する。',
            'iaaaligned':'活動の基準文脈、話者、聞き手が同じ対象に一致する。別の参照によって非許可を空虚に成立させない。',
            'iaaundertake':'その発言目標を同じ主体が危険を認識して試みるというrwiの内容。発言の成功や規範の成立を実行条件にしない。',
            'iaadenial':'指定した主体全てについて、候補活動の参照一致と、その試みに対するrwkを要求する。自由国の分類、基準、役割、候補範囲は未充足の引数。',
            'iaacontrast':'既存hzzonlyとiaadenialを同じ基準文脈で連言する。左側の発言資格と右側の非許可を結び、非許可を発言の物理的不可能へ変えない。対比の因果的な説明や含意は付加しない。',
            'iaaattribution':'この開いたひな形を原文箇所・著者・範囲・帰属文脈へ結ぶ解釈注記。試み・危険・不許可を現実の断言にはしない。'},
        relations={
            'prospects/adverse':'目標に向かう同じ活動の可能結果と本人への不利益。活動の実際の成功結果だけに狭めず、失敗や途中の不利益を含む。',
            'recognizes/views':'同じ本人・活動・目標の記述を認識して採る判断候補。空集合を肯定判断とせず、実際の文脈を必ず含むとも定めない。',
            'begins/pursues':'同じ本人が同じ活動を開始したことと、その活動が記述された目標を目指すこと。目標達成や不安の心理状態とは異なる。',
            'required/allowed':'指定基準の同じ対象についての要求・積極的許可。基準は法に限定せず、政治的・実践的判断の基準も区別して指定できる。'},
        reading=dict(source='artifacts/written-units-v1/kant-1784.json',unit='kant-1784:u0017',phrase='nicht wagen darf',
            dictionary='https://www.duden.de/rechtschreibung/wagen',accessed='2026-10-15',
            evidence='現代辞書の、失敗や不利益の可能性があっても試みる用法を参考にした。1784年の語義やこの箇所のdarfの読みを確定する証拠ではない。',
            interpretation='危険を認識した発言の試みに、指定基準で整合的な許可がないという候補。法的禁止だけにも、物理的な不可能だけにも固定しない。'),
        unresolved=[
            'Freistaatの制度的な構成、集団が意思決定し発言する仕組み、政治的な危険の内容と基準は未完。分類引数を定義済みの語として数えない。',
            '候補範囲は実行済みの活動に限らないという意味規約を持つ。実際の選択肢の網羅性は入力の検証事項で、空の候補や空の主体範囲では全称は真になり得る。',
            'wagenの勇気・ためらい・危険への因果的な態度、darfの歴史的・文脈的な読みは未確定。合理的な危険評価の一般理論ではない。',
            '認識・判断候補・活動開始・目的・不利益は意味規約を持つ基本関係として残る。段階2記述はその原語を符号化した文字列ではない。',
            '左側の資格限定と右側の制度的対比の論証関係、Aber auch、引用内nur、段落後半、全文の意味確認は未完。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
