"""Define agreement extent from topic-scoped, bilateral content coverage."""
from copy import deepcopy
import hashlib
import json
from noema.constructed import parse,format_graph
from noema.meaning_catalog import load_catalog
from scripts.compose_subject_bound_departure import ROOT,closure
from scripts.compose_calendar_dateline import conjunction

PARENT='examples/v016/kant-class-restricted-roles.noema'
PARENT_BASIS='data/class-restricted-roles-basis-v1.json'
FULL='examples/v016/kant-thought-correspondence.noema'
LIBRARY='examples/v016/thought-correspondence.noema'
BASIS='data/thought-correspondence-basis-v1.json'
ANNOTATIONS='data/thought-correspondence-identifiers-v1.json'
PRIMITIVES={
 'hzlf':('[a d] c',['比較論点','評価状況'],'この比較で調べる論点の範囲。結果を見て一致する論点だけを選び直さず、二文献を同じ範囲で比べる。論点の選定と網羅性の根拠は解釈条件。'),
 'hzlg':('[a a d] c',['一致範囲の候補','論点','評価状況'],'候補範囲がこの論点を含む。空の範囲も記述できる。数値・比率・論点の重要度はこの所属関係から補わない。'),
 'hzlh':('[a a a d] c',['文献','論点','内容項目','評価状況'],'この文献が当該論点について述べる思想・論旨の内容項目。項目には対象・肯否・量化・条件・発話の役割等、比較に関係する違いを保持する。文字列・真偽値・言及された対象だけへの変換ではない。抽出・帰属・網羅性の説明は解釈条件として残る。'),
 'hzli':('[a a a d] c',['比較元の内容項目','比較先の内容項目','論点','評価状況'],'当該論点の明示した比較基準で、元の内容項目に先の内容項目が対応する。異なる表現でも対応できる。単なる同時の真、同じ語の出現や論理的同値一般とは同一視しない。基準の妥当性は未完で、対称性をこの基本関係に仮定しない。'),
}
MEANINGS={
 'rqrx':'同じ論点・状況について両文献が少なくとも一つ内容を述べ、各側の全内容項目に相手側の双方向に対応する項目がある。多対多の対応を許す。片側の余分な非対応内容、片側だけの記述、双方の沈黙は成立としない。',
 'rqry':'比較論点の範囲が非空で、候補範囲に範囲外の論点がなく、範囲内の各論点で候補への所属とrqrxによる対応が同値になる。候補はその状況で対応した論点の正確な範囲を表す。対応論点がなければ空の候補が成立しうる。',
 'hzkv':'現在の比較論点hzlf、候補範囲の所属hzlg、文献が述べる内容hzlh、内容同士の対応hzliを用いてrqryを満たす。思想の一致範囲を論点ごとの双方向の内容対応として読む。真理・正しさ・因果性は導かず、語義一般との同値は未確定。',
}


def additions():
    text=''.join('r '+n+sig+'.' for n,(sig,_,_) in PRIMITIVES.items())
    def has(doc,item):return 'c[v attributed][v '+doc+' v aspect v '+item+' v scene]'
    pair=conjunction(['c[v matches][v left v right v aspect v scene]','c[v matches][v right v left v aspect v scene]'])
    text+='d rqrx[first a second a aspect a scene d attributed h[a a a d] c matches h[a a a d] c] c['+conjunction([
        'g left a['+has('first','left')+']','g right a['+has('second','right')+']',
        'f left a[y['+has('first','left')+'][g right a['+conjunction([has('second','right'),pair])+']]]',
        'f right a[y['+has('second','right')+'][g left a['+conjunction([has('first','left'),pair])+']]]',
    ])+'].'
    member='c[v includes][v extent v aspect v scene]'
    agrees='k rqrx[v first v second v aspect v scene v attributed v matches]'
    text+='d rqry[first a second a extent a scene d domain h[a d] c includes h[a a d] c attributed h[a a a d] c matches h[a a a d] c] c['+conjunction([
        'g aspect a[c[v domain][v aspect v scene]]',
        'f aspect a[y['+member+'][c[v domain][v aspect v scene]]]',
        'f aspect a[y[c[v domain][v aspect v scene]]['+conjunction(['y['+member+']['+agrees+']','y['+agrees+']['+member+']'])+']]',
    ])+'].'
    text+='d hzkv[first a second a extent a scene d] c[k rqry[v first v second v extent v scene p hzlf p hzlg p hzlh p hzli]].'
    return parse('p:'+text)['declarations']


def build():
    cat=load_catalog(ROOT,PARENT_BASIS);doc=deepcopy(cat.document)
    assert not (set(PRIMITIVES)|{'rqrx','rqry'})&set(cat.entries)
    at=next(i for i,d in enumerate(doc['declarations']) if d['name']=='hzkv')
    doc['declarations'][at:at+1]=additions();doc=parse(format_graph(doc,'compact'))
    lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rqrx','rqry'])
    primitives=[];definitions={}
    for d in doc['declarations']:
        n=d['name'];entry=cat.entries.get(n)
        if d['kind']=='primitive':
            args,meaning=PRIMITIVES[n][1:] if n in PRIMITIVES else (entry['arguments'],entry['meaning_ja'])
            primitives.append(dict(symbol=n,parameters=d['parameters'],result=d['result'],arguments=args,meaning_ja=meaning))
        else:definitions[n]=MEANINGS[n] if n in MEANINGS else entry['meaning_ja']
    basis=dict(status='partial_explicit_topic_correspondence_reading',document=FULL,library=LIBRARY,
        revises_document=PARENT,revises_meaning_basis=PARENT_BASIS,
        revision=dict(primitive_replaced_by_definition='hzkv',new_primitives=list(PRIMITIVES),new_definitions=['rqrx','rqry']),
        primitives=primitives,definitions=definitions,
        limitations=[
            'wiefernを、明示した比較論点のうち思想内容が対応する正確な範囲を問うものとして読む。元の範囲・程度という未分解の規約を具体化した候補で、数値的程度や全語義を確定しない。',
            '比較領域は非空だが、対応する論点が一つもなければ空の候補範囲を許す。双方が沈黙する論点は対応に数えない。非対応から積極的な反対・矛盾は導かない。',
            '内容対応は同じ論点・状況で双方向に要求する。項目数や字面の同一性、一対一対応、両文献の真理性・無矛盾性は要求しない。',
            '比較領域の選定、項目帰属の網羅性、項目の構造と対応基準の説明はなお解釈入力に残る。文全体の一致を返す基本関係を、これら四つのより局所的な関係へ分解した。',
            '一致の比較状況を、偶発性・因果寄与・可能性の既存接続と共有する。記述された問いを提示するだけで候補を評価したり実際の一致を肯定したりしない。',
            '既存23文とhzkv以外の宣言・意味規約を保存する。旧hzkvへの完全な同値を主張しない。脚注全体の意味一致と以前からの未完事項は残る。',
        ],
        unresolved=[dict(basis=row['basis'],historical_caveats=row['caveats']) for row in cat.lineage],
        predecessor_source_sha256=cat.source_sha256)
    body=format_graph(doc,'compact')+'\n'
    ann=json.loads((ROOT/'data/class-restricted-roles-identifiers-v1.json').read_text(encoding='utf-8'))
    ann.update(document=FULL,document_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest())
    return {FULL:body,LIBRARY:format_graph(lib,'compact')+'\n',BASIS:json.dumps(basis,ensure_ascii=False,indent=2)+'\n',
        ANNOTATIONS:json.dumps(ann,ensure_ascii=False,indent=2)+'\n'}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Thought correspondence decomposed into topic, attribution and bilateral matching')


if __name__=='__main__':main()
