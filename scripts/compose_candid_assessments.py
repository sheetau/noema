"""Express a declared range of personal assessments without omitting its criticisms."""
from copy import deepcopy
import json

from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,both,op,quant
from scripts.compose_situated_criticism import params
from scripts.compose_speech_principals import PUBLIC
from scripts.compose_described_norms import TRUE

PARENT='examples/v016/kant-comparative-speech.noema'
LIBRARY='examples/v016/candid-assessments.noema'
EXAMPLE='examples/v016/candid-assessments-example.noema'
BASIS='data/candid-assessments-basis-v1.json'
CRITERION='i[h[a] e]'
RELATIONS=[('judgments','h[a a d] c'),('matters','h[a a d] c'),
    ('linked','h[a '+CRITERION+' c d] c'),('candidates','h[a d d] c')]
ASSESSMENT=[('person','a'),('judgment','a'),('subject','a'),('criterion',CRITERION),('polarity','c'),('context','d')]+RELATIONS
PRESENTATION=[(n,t) for n,t in PUBLIC if n!='message']
DISCLOSURE=PRESENTATION+[('records','j[a]'),('scope','h[a d] c'),
    ('criteria','h[a d] '+CRITERION),('polarities','h[a d] i[c]')]+RELATIONS


def definitions():
    content='b point['+op('z',op('t',app(v('criterion'),v('subject')),v('point')),v('polarity'))+']'
    text=definition('rsa','criterion h[a] e polarity c','i[subject a][j s['+content+']]','h[a] f')
    text+=definition('rsb','criterion '+CRITERION+' polarity i[c]','o a[r[p rsa]][v criterion v polarity]','i[h[a] f]')
    selected=app(v('candidates'),v('judgment'),v('context'),v('point'))
    assessed=op('z',op('t',app('s[v criterion]',v('subject')),v('point')),v('polarity'))
    text+=definition('rsc',params(ASSESSMENT),both(
        app(v('judgments'),v('person'),v('judgment'),v('context')),
        app(v('matters'),v('judgment'),v('subject'),v('context')),
        app(v('linked'),v('judgment'),v('criterion'),v('polarity'),v('context')),
        quant('g','point','d',selected),quant('f','point','d',op('y',selected,assessed))))
    text+=definition('rsd','records j[a] item a','q[v records]['+op('u',TRUE)+'][i[state c record a]['+
        op('x',v('state'),op('e',v('record'),v('item')))+']]')
    selected_entries='q[v records]['+TRUE+'][i[state c record a]['+both(v('state'),app(v('scope'),v('record'),v('context')))+']]'
    coverage=quant('f','item','a',op('y',app(v('scope'),v('item'),v('context')),k('rsd',v('records'),v('item'))))
    text+=definition('rse','records j[a] scope h[a d] c context d',both(
        op('u',op('e','d[v records]','n p a b')),selected_entries,coverage))
    code=app(v('criteria'),v('record'),v('context'));sign=app(v('polarities'),v('record'),v('context'))
    args=dict(person=v('person'),judgment=v('record'),subject=v('subject'),criterion=code,polarity='s['+sign+']',context=v('context'))
    args.update({n:v(n) for n,_ in RELATIONS})
    own=k('rsc',*(args[n] for n,_ in ASSESSMENT))
    message=k('rsb',code,sign)
    presentation=k('hzb4',*(message if n=='message' else v(n) for n,_ in PUBLIC))
    expressed='q[v records]['+TRUE+'][i[state c record a]['+both(v('state'),own,presentation)+']]'
    text+=definition('rsf',params(DISCLOSURE),both(k('rse',v('records'),v('scope'),v('context')),expressed))
    negative='q[v records]['+op('u',TRUE)+'][i[state c record a]['+op('x',v('state'),op('u','s['+sign+']'))+']]'
    text+=definition('rsg',params(DISCLOSURE),both(k('rsf',*(v(n) for n,_ in DISCLOSURE)),negative))
    return text


def library():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));lookup={d['name']:d for d in parent['declarations']}
    pending,retained={'hzb4'},set()
    while pending:
        name=pending.pop()
        if name in retained:continue
        retained.add(name);pending.update(_references(lookup[name])-retained)
    doc=deepcopy(parent);doc['declarations']=[d for d in doc['declarations'] if d['name'] in retained];doc['statements']=[]
    return parse(format_graph(doc,'compact')+definitions())


def example_text():
    text='r jdfirst[] a.r jdsecond[] a.r jdperson[] a.r jdact[] a.r jdsubject[] a.r jdrole[] a.r jdrecipient[] a.r jdchannel[] a.r jdcontext[] d.'
    text+='r jdmetone[a d] c.r jdmettwo[a d] c.r jdscope[a d] c.r jdaudience[a] c.'
    text+='r jdjudgments[a a d] c.r jdmatters[a a d] c.r jdlinked[a '+CRITERION+' c d] c.r jdcandidates[a d d] c.'
    text+='r jdchoosecriterion[a '+CRITERION+' '+CRITERION+'] '+CRITERION+'.r jdchoosepolarity[a i[c] i[c]] i[c].'
    text+='r jdvoices[a a a a a i[h[a] f] d] c.'
    for name,primitive in (('jdstandardone','jdmetone'),('jdstandardtwo','jdmettwo')):
        text+=definition(name,'subject a','b point['+k(primitive,v('subject'),v('point'))+']','e')
    text+=definition('jdcriteria','record a context d',k('jdchoosecriterion',v('record'),'r[p jdstandardone]','r[p jdstandardtwo]'),CRITERION)
    text+=definition('jdpolarities','record a context d',k('jdchoosepolarity',v('record'),'r['+TRUE+']','r['+op('u',TRUE)+']'),'i[c]')
    refs=dict(person=k('jdperson'),activity=k('jdact'),subject=k('jdsubject'),role=k('jdrole'),recipient=k('jdrecipient'),
        channel=k('jdchannel'),context=k('jdcontext'),audience='p jdaudience',voices='p jdvoices',
        records='l[a][k jdfirst[] k jdsecond[]]',scope='p jdscope',criteria='p jdcriteria',polarities='p jdpolarities')
    refs.update({n:'p jd'+n for n,_ in RELATIONS})
    for symbol,name in (('rsf','jdcomplete'),('rsg','jdcritical')):
        text+=definition(name,'',k(symbol,*(refs[n] for n,_ in DISCLOSURE)))
    return text+'q[k jdcomplete[]].q[k jdcritical[]].q[t[k jdstandardtwo[k jdsubject[]]][k jdcontext[]]].'


def build():
    doc=library();example=parse(format_graph(doc,'compact')+example_text())
    return {LIBRARY:format_graph(doc,'compact')+'\n',EXAMPLE:format_graph(example,'compact')+'\n'}


def basis():
    return dict(status='scope_relative_assessment_disclosure_not_complete_frankness',document=LIBRARY,example=EXAMPLE,parent=PARENT,
        definitions=dict(rsa='一つの評価基準と肯否から、その話題で基準が指定の真偽になると述べる肯定発話を作る。肯否が偽なら基準の否定を述べる。',
            rsb='基準と肯否の閉じた記述からrsaの発話関数の記述を構成する。構成だけで内容を評価しない。',
            rsc='本人・判断・話題・基準の記述・肯否・文脈を結び、その判断の非空の候補全てで指定評価が成立する。現在の真理は要求しない。',
            rsd='判断記録の有限列に同じ個体が含まれる。順序・重複を消して列を変更する操作ではない。',
            rse='列が非空で、列の各項目が指定範囲に入り、指定範囲の全項目が列に含まれる。範囲と列のすり替えや未開示項目の除外を区別する。',
            rsf='rseを保ち、全項目にrscの本人の評価と同じ話題・発話の公的自己提示hzb4を要求する。全て同じ人・行為・役割・宛先・文脈へ結ぶ。',
            rsg='rsfの範囲に少なくとも一つ否定評価がある。基準が望ましい要件の充足を表す場合に、その不充足を含む批判的提示の作例となる。'),
        interfaces=dict(scope='判断記録・文脈を受け取り、開示の対象として明示した範囲への所属を返す。本人の全ての考えを列挙済みとは認定しない。',
            criteria='判断記録・文脈に、その評価基準の閉じた一項内容関数の記述を返す。',
            polarities='同じ判断記録・文脈に、肯否の閉じた真偽式の記述を返す。',
            linked='判断・基準の記述・肯否・文脈を結ぶ。話題はmatters、本人はjudgmentsで同じ判断へ結ぶ。',
            candidates='判断・判断文脈・候補状況を結ぶ。政策の想定結果とは別であり、現実を含むとは限らない。'),
        unresolved=['率直さを全ての内心の開示や恐れの不在と同一視しない。rsfは明示した評価範囲についての省略のない提示という検討用の条件であり、franknessやfreimüthigの必要十分条件ではない。',
            '範囲は入力であり、話者が恣意的に範囲を狭めていないこと、現実の考えを全て調査したこと、意図的な隠蔽や誤導がないことをこの定義だけでは保証しない。',
            'rsgの否定が批判として働くには、基準が満たすべき要件の充足などを表すという意味規約が必要。任意の否定を批判と同一視しない。賛否混合や肯定だけのrsfも表せる。',
            '列の順序や重複は保存するが、現在の全項目検査では判定に重みを付けない。重複が多いほど強い批判になるとは扱わない。',
            '同じ提示行為と同じ公的枠を要求する。一つの講演や文書で複数の内容を述べる読みであり、別々の発言を無条件に同じ行為として束ねない。',
            '現在の要件充足、本人の否定評価、実際の提示を分ける。真理・正当性・相手の同意・法の採択や改正を提示から推定しない。',
            '今回は独立した意味条件と作例である。カント本文の許可対象、すでにある法への照応、sogarの強調へは未接続であり、原文対応範囲や全文完成件数を増やさない。'])


def main():
    for path,text in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        target=ROOT/path
        if target.exists():
            if target.read_text(encoding='utf-8')!=text:raise ValueError('Stored candid assessment differs: '+path)
        else:
            with target.open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
        print(path,len(text),'characters')


if __name__=='__main__':main()
