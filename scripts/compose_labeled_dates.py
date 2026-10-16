"""Use calendar labels rather than period-list offsets in the source dates."""
from copy import deepcopy
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_calendar_dateline import conjunction

PARENT='examples/v016/kant-described-thoughts.noema'
PARENT_BASIS='data/described-thoughts-basis-v1.json'
FULL='examples/v016/kant-labeled-dates.noema'
LIBRARY='examples/v016/labeled-dates.noema'
BASIS='data/labeled-dates-basis-v1.json'
ANNOTATIONS='data/labeled-dates-identifiers-v1.json'
PRIMITIVES={
 'hzlm':('[a a a b d] c',['暦規約','年期間','月期間','月番号','文脈'],'指定した暦・年・文脈で、この月期間にこの月番号が付く。月列で何番目に現れるかとは区別する。原文でSeptemberに対応させる番号は9。番号の割当と暦の同定は解釈契約として残る。'),
 'hzln':('[a a a b d] c',['暦規約','月期間','日期間','日番号','文脈'],'指定した暦・月・文脈で、この日期間にこの日番号が付く。欠番があっても番号を詰め直さない。日列の位置や絶対時刻を返す関係ではない。未確認の番号を推測して補わない。'),
}


def generic():
    def year(x):return 'c[v years][v calendar v '+x+' v yearlabel v context]'
    def month(x):return 'c[v months][v calendar v year v '+x+' v monthlabel v context]'
    def day(x):return 'c[v days][v calendar v month v '+x+' v daylabel v context]'
    text=''.join('r '+n+sig+'.' for n,(sig,_,_) in PRIMITIVES.items())
    text+='d rqsd[calendar a year a month a day a yearlabel b monthlabel b daylabel b context d years h[a a b d] c months h[a a a b d] c days h[a a a b d] c] c['+conjunction([
        year('year'),month('month'),day('day'),
        'f other a[y['+year('other')+'][e[v other][v year]]]',
        'f other a[y['+month('other')+'][e[v other][v month]]]',
        'f other a[y['+day('other')+'][e[v other][v day]]]',
    ])+'].'
    return parse('p:'+text)['declarations']


def replace_dates(value):
    if isinstance(value,list):return [replace_dates(x) for x in value]
    if not isinstance(value,dict):return value
    result={k:replace_dates(v) for k,v in value.items()}
    if value.get('kind')=='call' and value.get('symbol')=='rqrm':
        result['symbol']='rqsd'
        for index in (5,6):
            number=result['arguments'][index]
            assert number['kind']=='number' and number['denominator']==1
            number['numerator']+=1
        result['arguments'][9]={'kind':'function_ref','symbol':'hzlm'}
        result['arguments'][10]={'kind':'function_ref','symbol':'hzln'}
    return result


def build():
    cat=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(cat.document)
    assert not (set(PRIMITIVES)|{'rqsd'})&set(cat.entries)
    index=next(i for i,d in enumerate(doc['declarations']) if d['name']=='hzje')
    doc['declarations'][index:index]=generic()
    for d in doc['declarations']:
        if d['name'] in ('hzje','hzkk'):d['body']=replace_dates(d['body'])
    doc=parse(format_graph(doc,'compact'))
    meanings={
        'rqsd':'同じ暦・文脈で、年番号が指定年、同じ年内の月番号が指定月、同じ月内の日番号が指定日を一意に指定する。各割当の成立と、同じ番号に対する他の期間の不在を要求する。番号を列の位置に換算せず、欠番を保持する。',
        'hzje':cat.entries['hzje']['meaning_ja'].replace('第9月、第30日','月番号9、日番号30')+' 年・月・日の番号はrqsdで暦内の一意な期間へ結び、列の位置で代用しない。',
        'hzkk':cat.entries['hzkk']['meaning_ja']+' 二つの日付はrqsdで年番号1784・月番号9・日番号13と30へ結ぶ。番号を月内の列位置と同一視しない。',
    }
    primitives=[];definitions={}
    for d in doc['declarations']:
        n=d['name'];entry=cat.entries.get(n)
        if d['kind']=='primitive':
            args,meaning=PRIMITIVES[n][1:] if n in PRIMITIVES else (entry['arguments'],entry['meaning_ja'])
            primitives.append(dict(symbol=n,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
        else:definitions[n]=meanings[n] if n in meanings else entry['meaning_ja']
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqsd'])
    basis=dict(status='label_based_calendar_addresses',document=FULL,library=LIBRARY,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,
        revision=dict(changed_definitions=['hzje','hzkk'],new_definitions=['rqsd'],new_primitives=list(PRIMITIVES)),
        primitives=primitives,definitions=definitions,
        limitations=[
            '原文の30・13を暦が付ける日番号として保存する。Septemberに月番号9を与える読みを継承する。改暦等の欠番を、番号の繰上げや列位置への置換で消さない。',
            '各番号から期間が一意に定まることを要求する。同じ暦・親期間・文脈で同じ番号が複数期間へ付く場合は不成立。複数の別名番号が同じ期間を指すことはこの条件だけでは禁止しない。',
            '一般定義は数値型のラベルを受ける。暦固有の整数性・有効番号・紀元・閏月・改暦規則は割当関係の意味契約であり、この定義から推定しない。',
            '旧rqrmは列位置による期間指定を表す一般定義として残す。日付行・脚注の三つの日付呼出しだけを番号による指定へ更新した。',
            '暦の歴史的同定、年・月・日の絶対時間との対応、地理関係、日付行と脚注全体の意味一致は未完。原文対応範囲と意味確認済み単位は増やさない。',
            '本文23文と、hzje・hzkk以外の宣言・意味規約を保存する。新しい暦・場所・時点の局所参照は追加しない。',
        ],unresolved=[dict(basis=row['basis'],historical_caveats=row['caveats']) for row in cat.lineage],predecessor_source_sha256=cat.source_sha256)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/described-thoughts-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Dateline and footnote dates now use calendar labels')


if __name__=='__main__':main()
