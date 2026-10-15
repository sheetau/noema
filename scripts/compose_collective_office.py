"""Compose a shared highest governing office with non-dummy decision holders."""
from copy import deepcopy
import json

from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT,definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_risk_undertaking import SOURCE as PARENT,DENIAL
from scripts.compose_assigned_formation import QUALIFICATION
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/collective-office.noema'
EXAMPLE='examples/v016/collective-office-example.noema'
SOURCE='examples/v016/kant-collective-office.noema'
CORE='examples/v016/collective-office-core.noema'
BASIS='data/collective-office-basis-v1.json'
REVIEW='data/republic-reading-review-v1.json'
PROFILE='h[a] c'
RULE='h[j[c]] c'
ORDER=[('office','a'),('organization','a'),('anchor','d'),('roles','h[a a d] c'),('above','h[a a a d] c')]
OFFICE=ORDER+[('participants','j[a]'),('holders','h[a a a d] c'),('persons','h[a] c'),('rule',RULE)]
PROVIDERS=[('office','h[a d] a'),('participants','h[a d] j[a]'),('rule','h[a a d] '+RULE)]+ORDER[3:]+[('holders','h[a a a d] c')]
TRUE='e[n p a b][n p a b]'
FALSE='u['+TRUE+']'


def params(fields):return ' '.join(n+' '+t for n,t in fields)
def av(fields):return [v(n) for n,t in fields]


def definitions():
    project='q[v participants][l[c][]][i[values j[c] person a][m[v values][l[c]['+app(v('profile'),v('person'))+']]]]'
    text=definition('rwl','participants j[a] profile '+PROFILE,project,'j[c]')
    flip='i[person a]['+op('x',both(op('e',v('person'),v('voter')),op('u',app(v('profile'),v('person')))),
        both(op('u',op('e',v('person'),v('voter'))),app(v('profile'),v('person'))))+']'
    effect=op('u',op('e',app(v('rule'),k('rwl',v('participants'),v('profile'))),
        app(v('rule'),k('rwl',v('participants'),flip))))
    search='q[k rs[v participants]]['+FALSE+'][i[found c profile '+PROFILE+']['+op('x',v('found'),effect)+']]'
    text+=definition('rwm','voter a participants j[a] rule '+RULE,both(k('rt',v('participants')),
        k('rz',v('participants'),v('voter')),search))
    each='q[v participants]['+TRUE+'][i[valid c voter a]['+both(v('valid'),k('rwm',v('voter'),v('participants'),v('rule')))+']]'
    text+=definition('rwn','participants j[a] scope h[a] c rule '+RULE,both(k('rcm',v('participants'),v('scope')),
        k('hc','n p b b','d[v participants]'),each))
    scope='i[role a]['+app(v('roles'),v('role'),v('organization'),v('anchor'))+']'
    order='i[first a second a]['+app(v('above'),v('first'),v('second'),v('organization'),v('anchor'))+']'
    highest=quant('f','role','a',op('y',both(app(v('roles'),v('role'),v('organization'),v('anchor')),
        op('u',op('e',v('role'),v('office')))),app(v('above'),v('office'),v('role'),v('organization'),v('anchor'))))
    text+=definition('rwo',params(ORDER),both(k('rex',scope,order),app(v('roles'),v('office'),v('organization'),v('anchor')),highest))
    holder=app(v('holders'),v('person'),v('office'),v('organization'),v('anchor'))
    text+=definition('rwp',params(OFFICE),both(k('rwo',*av(ORDER)),
        k('rwn',v('participants'),'i[person a]['+holder+']',v('rule')),
        quant('f','person','a',op('y',holder,app(v('persons'),v('person'))))))
    return text


def additions():
    text=''.join(primitive('iab'+n,t) for n,t in PROVIDERS)
    refs=dict(office=k('iaboffice',v('organization'),v('anchor')),organization=v('organization'),anchor=v('anchor'),
        participants=k('iabparticipants',v('organization'),v('anchor')),persons='p aa')
    refs.update({n:'p iab'+n for n in ('roles','above','holders')})
    refs['rule']=k('iabrule',v('organization'),refs['office'],v('anchor'))
    text+=definition('iabsharing','organization a anchor d',k('rwp',*[refs[n] for n,t in OFFICE]))
    text+=definition('iabpolity','civic h[a d] c organization a anchor d',both(app(v('civic'),v('organization'),v('anchor')),
        k('iabsharing',v('organization'),v('anchor'))))
    fields=[('remaining',QUALIFICATION),('civic','h[a d] c')]+DENIAL[1:]
    population='i[organization a point d][k iabpolity[v civic v organization v point]]'
    text+=definition('iabcontrast',params(fields),k('iaacontrast',v('remaining'),population,*av(DENIAL[1:])))
    sort='h['+' '.join(t for n,t in fields)+'] c'
    text+='r iabannotation[a a i c['+sort+'] a d] c.'
    text+=definition('iabattribution','',k('iabannotation',k('hztnode'),k('wa'),'r c[p iabcontrast]',k('hztscope'),k('wh')))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    lib=dict(parent,declarations=closure(parent,['rs','rt','rz','rcm','rex']),statements=[])
    lib=parse(format_graph(lib,'compact')+definitions())
    text=format_graph(lib,'compact')
    for name,sort in OFFICE:text+=primitive('jda'+name,sort if sort.startswith('h[') else 'h[] '+sort)
    text+='r jdavoter[] a.r jdasecond[] a.'
    refs={n:('p jda'+n if t.startswith('h[') else k('jda'+n)) for n,t in OFFICE}
    question=k('rwp',*[refs[n] for n,t in OFFICE])
    questions=[question,k('rwm',k('jdavoter'),refs['participants'],refs['rule']),
        k('rwm',k('jdasecond'),refs['participants'],refs['rule']),k('rwo',*[refs[n] for n,t in ORDER]),
        'e[r['+question+']][r['+question+']]']
    example=parse(text+''.join('q['+q+'].' for q in questions))
    doc=deepcopy(parent);doc['statements']=[]
    names={d['name'] for d in doc['declarations']}
    assert not {d['name'] for d in lib['declarations'] if d['name'].startswith('rw')}&names
    doc=parse(format_graph(doc,'compact')+definitions()+additions()+'s[k iabattribution[]].')
    doc['statements']=parent['statements'][:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in [(LIBRARY,lib),(EXAMPLE,example),(SOURCE,doc),(CORE,core)]}


def basis():
    return dict(status='shared_highest_governing_office_with_open_civic_basis',parent=PARENT,document=SOURCE,
        definitions={
            'rwl':'指定した保持者の順序に沿って、各人の二値入力を列へ射影する。位置と人物の対応を保持する。',
            'rwm':'重複のない保持者列に本人が含まれ、他の入力を固定して本人の入力だけを反転すると決定が変わる組合せがある。実際にその入力を行ったとは限らない。',
            'rwn':'保持者の完全な非空列が少なくとも二人を含み、全員がrwmを満たす。名簿だけ複数で、一人以外の判断が常に無関係な制度は満たさない。',
            'rwo':'同じ組織・文脈の役職順序が厳密な部分順序であり、指定役職が全ての他の対象役職より上位にある。最大元と単に極大な役職を区別する。',
            'rwp':'rwoの最高役職について、その同じ役職の人である保持者全員を列挙し、同じ決定規則でrwnを満たす。',
            'iabsharing':'同じ組織・基準文脈の最高役職、保持者列、決定規則を選び、rwpを評価する。',
            'iabpolity':'iabsharingと、その組織の残る市民的・国家的構成条件civicを合わせる。civicは未充足であり国家の完成した語義とはしない。',
            'iabcontrast':'前段iaacontrastの未指定の対象主体範囲をiabpolityへ具体化する。発言資格と非許可の基準文脈、活動の参照を保持する。',
            'iabattribution':'同じ原文箇所・著者・範囲・帰属文脈で具体化した候補解釈を提示する。制度や発言の実在を断言しない。'},
        inputs={
            'roles/above':'同じ組織で統治上の意思決定権限に関わる役職の範囲と推移的な上下関係。儀礼上の席次や直接の報告先だけの辺と区別する。',
            'holders/participants':'その最高役職で意思決定を担う人と、その全員の重複のない順序付き列。全国民、全住民、軍隊の全構成員と同一とは限らない。',
            'rule':'列の各位置の保持者の入力から制度上の決定を返す純粋な二値関数。実際の投票結果や履行とは別。',
            'civic':'市民的共同体、国家としての統治範囲、規範変更権能、対外的地位などの残る構成。単なる会社や委員会を自由国と確定するための省略可能な条件ではない。'},
        reading_review=REVIEW,
        interpretation='Adelungの共和国の狭い語義にある、最高権力が複数に委ねられる側面を具体化した候補。選挙、全員一致、平等な重み、普通選挙を要件へ補わない。',
        limitations=[
            '同じ一つの最高役職を複数で担う構造に限る。最高権限の分立、身分制、連邦制、複合君主制との境界、代表資格、制度の成立や正当性は未完。',
            '入力の反転は制度上の影響可能性であり、実際の政治的影響力、物理的な選択可能性、独立な意思形成、腐敗や強制の不在を証明しない。',
            '保持者が少数の身分や家族に限られる場合も排除しない。全保持者の影響可能性はこの操作的な候補の条件で、歴史上の全共和国の必要十分条件ではない。',
            '決定規則の単調性や多数決は要求しない。並びを変える場合は、各位置の人物に対応して規則も変更する必要がある。',
            '有限列の全二値組合せを既存rsで生成する。全個体の全関数を列挙せず、列外の入力は含めない。保持者数に対して指数的な計算量が残る。',
            '1811年版の電子転写を参照した。1784年本文の唯一の解釈、語義の全側面、国家の残余条件、非許可を判断する基準、全文の意味確認は未完。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
