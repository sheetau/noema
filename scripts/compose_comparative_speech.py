"""Compose one's comparative judgment, its public expression and joint permission."""
from copy import deepcopy
import json

from noema.constructed import parse, format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, both, op, quant
from scripts.compose_situated_criticism import params
from scripts.compose_public_permission_risk import ACTION, INPUTS, FIELD_SYMBOLS, PCODE
from scripts.compose_topic_scopes import SCOPE
from scripts.compose_described_norms import RULE, TRUE

PARENT='examples/v016/kant-topic-scopes.noema'
SOURCE='examples/v016/kant-comparative-speech.noema'
CORE='examples/v016/comparative-speech-core.noema'
BASIS='data/comparative-speech-basis-v1.json'
COMPARE='h[a a a] e'
CCODE='i['+COMPARE+']'
LINK='h[a '+CCODE+' a a a d] c'
DETAILS=[('criterion',CCODE),('older','i[a]'),('newer','i[a]'),
    ('forms','i[h[a a d] c]'),('linked','i['+LINK+']'),('candidates','i[h[a d d] c]')]
DETAIL_SYMBOLS={n:'hzpdetail'+chr(ord('a')+i) for i,(n,_) in enumerate(DETAILS)}
DETAIL_MEANINGS=dict(
    criterion='話題・比較元・改訂候補の順に三個体を受け取り、評価状況ごとに改訂候補の方がよいという比較条件を返す関数の記述。本人の判断が対象とする基準であり、その妥当性や現在の改善は補わない。',
    older='比較元の表現対象の記述。現に採択済み・施行済みとはこの指定だけで認定しない。',
    newer='比較する改訂候補の表現対象の記述。現在実現している法や、採択を要求する提案とは同一視しない。',
    forms='表現対象・話題・文脈の順に、その表現がその話題を表す関係の記述。同じ話題への比較元と改訂候補の両方の結合を検査する。',
    linked='判断・比較基準の記述・話題・比較元・改訂候補・文脈の順に、判断の対象と比較方向を結ぶ関係の記述。',
    candidates='判断・判断文脈・候補状況の順に、その判断で排除されていない状況を指定する関係の記述。政策の想定結果とは区別する。')
BASE_INPUTS=[(n,t) for n,t in INPUTS if n!='message']
TARGET_INPUTS=DETAILS+BASE_INPUTS
CATALOGUE=SCOPE+[('role','h[a a d] i[a]'),('targets','h[a a d] i[h[a a] e]'),('required',RULE),('allowed',RULE)]


def definitions():
    # Assert the same comparison at the topic passed to the message function.
    factory='i[comparison '+COMPARE+' older a newer a][i[subject a][j s['+app(v('comparison'),v('subject'),v('older'),v('newer'))+']]]'
    text=definition('rru',params(DETAILS[:3]),'o a[r['+factory+']][v criterion v older v newer]','i[h[a] f]')
    template=[('comparison',COMPARE),('criterion',CCODE),('older','a'),('newer','a'),
        ('forms','h[a a d] c'),('linked',LINK),('candidates','h[a d d] c')]+ACTION
    selected=app(v('candidates'),v('judgment'),v('context'),v('point'))
    judgment=quant('g','judgment','a',both(k('fa',v('person'),v('judgment'),v('context')),
        k('fb',v('judgment'),v('subject'),v('context')),
        app(v('linked'),v('judgment'),v('criterion'),v('subject'),v('older'),v('newer'),v('context')),
        quant('g','point','d',selected),quant('f','point','d',op('y',selected,
            op('t',app(v('comparison'),v('subject'),v('older'),v('newer')),v('point'))))))
    public=op('t',app(k('rrh',*(v(n) for n,_ in ACTION)),v('person'),v('activity')),v('context'))
    body=both(op('u',op('e',v('older'),v('newer'))),
        app(v('forms'),v('older'),v('subject'),v('context')),
        app(v('forms'),v('newer'),v('subject'),v('context')),judgment,public)
    text+=definition('rrv',params(template),'i[person a activity a][b context['+body+']]','h[a a] e')
    message=k('rru',*(v(n) for n,_ in DETAILS[:3]))
    arguments=[v('criterion'),'o r[v criterion]']+[v(n) for n,_ in DETAILS[1:]]
    arguments += ['o r['+message+']' if n=='message' else v(n) for n,_ in ACTION]
    text+=definition('rrw',params(TARGET_INPUTS),'o a[r[p rrv]]['+' '.join(arguments)+']','i[h[a a] e]')
    selected=both(app(v('people'),v('person'),v('anchor')),app(v('activities'),v('person'),v('activity'),v('anchor')))
    permission=k('rdm',v('ruler'),v('person'),'s['+app(v('role'),v('person'),v('activity'),v('anchor'))+']',
        v('activity'),app(v('targets'),v('person'),v('activity'),v('anchor')),TRUE,v('point'),v('required'),v('allowed'))
    policy=quant('f','person','a',quant('f','activity','a',op('y',selected,permission)))
    text+=definition('rrx',params(CATALOGUE),'b point['+both(k('rrr',*(v(n) for n,_ in SCOPE)),policy)+']','e')
    codes=[(n,'i['+t+']') for n,t in CATALOGUE]
    text+=definition('rry',params(codes),'o a[r b[p rrx]]['+' '.join(v(n) for n,_ in CATALOGUE)+']',PCODE)
    conjunction='i[left e right e][b point['+both(op('t',v('left'),v('point')),op('t',v('right'),v('point')))+']]'
    text+=definition('rrz','left '+PCODE+' right '+PCODE,'o a[r b['+conjunction+']][v left v right]',PCODE)
    return text


def build():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8')); statements,doc['statements']=doc['statements'],[]
    text=definitions()+'r hzpactivities[a a d] c.r hzpnode[] a.r hzpscope[] a.'
    for n,t in DETAILS:text+='r '+DETAIL_SYMBOLS[n]+'[a a d] '+t+'.'
    fields={n:app('p '+DETAIL_SYMBOLS[n],v('person'),v('activity'),v('anchor')) for n,_ in DETAILS}
    fields.update({n:app('p '+FIELD_SYMBOLS[n],v('person'),v('activity'),v('anchor')) for n,_ in BASE_INPUTS})
    text+=definition('hzptarget','person a activity a anchor d',k('rrw',*(fields[n] for n,_ in TARGET_INPUTS)),'i[h[a a] e]')
    refs=dict(ruler='r[k hzmruler[]]',anchor='r[k wh[]]',people='r[p hzmpeople]',activities='r[p hzpactivities]',
        subject='r[p '+FIELD_SYMBOLS['subject']+']',domains='r[p hzodomains]',role='r[p '+FIELD_SYMBOLS['role']+']',
        targets='r[p hzptarget]',required='r[p h7a]',allowed='r[p h7b]')
    text+=definition('hzpcomparative','',k('rry',*(refs[n] for n,_ in CATALOGUE)),PCODE)
    text+=definition('hzppolicy','',k('rrz',k('hzopolicy'),k('hzpcomparative')),PCODE)
    text+=definition('hzpsafety','','b context['+k('rrm',k('hzppolicy'),v('context'),'p hzmprospects','p hzmadverse')+']','e')
    text+=definition('hzpinsight','','b context['+k('rrq',k('hzmruler'),'r c[k hzpsafety[]]',v('context'),'p hznalternatives','p hznawareness')+']','e')
    text+=definition('hzpattribution','',k('hznreport',k('hzpnode'),k('wa'),'r d[k hzpinsight[]]',k('hzpscope'),k('wh')))
    doc=parse(format_graph(doc,'compact')+text+'s[k hzpattribution[]].');doc['statements']=statements[:-1]+doc['statements']
    lookup={d['name']:d for d in doc['declarations']};pending,retained=_references(doc['statements'][-1:]),set()
    while pending:
        name=pending.pop()
        if name in retained:continue
        retained.add(name);pending.update(_references(lookup[name])-retained)
    core=deepcopy(doc);core['declarations']=[d for d in doc['declarations'] if d['name'] in retained];core['statements']=doc['statements'][-1:]
    return {SOURCE:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n'}


def basis():
    return dict(status='partial_public_expression_of_comparative_judgments',document=SOURCE,parent=PARENT,
        definitions=dict(rru='同じ比較基準・比較元の表現・改訂候補から、その話題についての肯定発話の記述を構成する。内容の真理は構成時に評価しない。',
            rrv='同じ話題の異なる二表現について本人の判断が同じ基準と比較順序へ結ばれ、非空の判断候補で比較が成立する。本人の能力使用と同じ公的提示をrrhで要求する。',
            rrw='比較基準の関数と記述、二表現、判断の関係、rruの発話を同じ入力から構成し、rrvの閉じた行為記述にする。',
            rrx='同じ話題範囲・人物・活動について、指定された各行為記述への許可を要求する。話題と行為の結合は本文の構成器hzptargetで保証する。',
            rry='rrxの対象範囲・行為記述選択・規範関係を閉じた方針記述にする。',
            rrz='二つの方針が同じ評価状況で共に成立する内容の記述を構成する。構成時に方針を実行しない。',
            hzptarget='同じ本人・活動・基準文脈の項目からrrwの比較発言を構成する。話題と役割は許可側と共有する。',
            hzpcomparative='比較発言として選んだ活動について、その構成済み記述への許可を同じ統治者に結ぶ。',
            hzppolicy='従来の公的使用の方針hzopolicyと比較発言の許可を併記する。一般的な許可を比較発言だけへ縮めない。',
            hzpsafety='同じ想定結果で両方の方針が成立することを保ち、指定不利益がないか調べる。',
            hzpinsight='同じ統治者が結合方針の安全性を認識し肯定するという既存rrqの部分条件。',
            hzpattribution='新しい部分内容を同じ著者へ帰属し、先行16文を保持する。'),
        bindings={DETAIL_SYMBOLS[n]:dict(field=n,type=t,meaning=DETAIL_MEANINGS[n],selection='同じ本人・活動・基準文脈に対応する閉じた記述。') for n,t in DETAILS} | dict(
            hzpactivities='比較する考えの提示として対象に選ぶ活動。一般的な公的使用hzmactivitiesと区別する。',
            hzpnode='比較発言の許可を補った本文位置。',hzpscope='認識・立法の範囲・安全性・比較発言の部分範囲。'),
        unresolved=['Gedankenを、比較基準に結ばれた本人の肯定判断と、その同じ内容の提示として部分記述する。問い・留保・複数論点や思考一般を全てこの形へ還元しない。',
            '比較基準は入力であり、特定の正義観・数値尺度・優先順位を原文へ補わない。比較元と候補は異なる表現対象だが、意味内容が異なることや実際の改善は要求しない。',
            'formsは同じ話題を表現する案と対象の対応、linkedは同じ判断・基準記述・比較順序、candidatesは同じ判断・文脈の候補。媒体・法文・表現の基礎説明と評価基準の妥当性は未完。',
            '判断候補での比較成立と現在の改善を分ける。提示は相手の同意や採択を要求する発話ではなく、法が変更されたことや実現可能性を追加しない。',
            '従来の公的使用と今回の比較発言は、それぞれの活動範囲を保つ。二つの許可が別々の想定結果で成立するだけでは結合方針の実現としない。',
            '範囲・活動・比較項目の網羅性、空の選択の空虚な真、立法の意味、理性と理解力、洞察の基礎課題を継承する。',
            'sogarと率直な批判、比較・強調、先行する統治者への照応、後続の実例は未記述。全文の意味確認済みには数えない。'])


def main():
    for name,text in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():
            if path.read_text(encoding='utf-8')!=text:raise ValueError('Stored comparative speech differs: '+name)
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)
        print(name,len(text),'characters')


if __name__=='__main__':main()
