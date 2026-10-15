"""Explain limited yielding under an explicit loading protocol."""
from copy import deepcopy
import hashlib,json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from noema.linking import relocate
from scripts.compose_cover_reference import ROOT,SOURCE as PARENT
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure

LIBRARY='examples/v016/load-resistance.noema'
SOURCE='examples/v016/kant-load-resistance.noema'
CORE='examples/v016/load-resistance-core.noema'
BASIS='data/load-resistance-basis-v1.json'
READING='data/load-resistance-reading-v1.json'
REVIEW='data/kant-manuscript-obligations-v6.json'
MEASUREMENT='h[a a a a a d] '
FIELDS=[('object','a'),('context','d'),('tests','j[a]'),('scope','h[a] c'),('protocol','a'),
    ('loadunit','a'),('deformationunit','a'),('minimum','b'),('maximum','b'),
    ('assessed',MEASUREMENT+'c'),('load',MEASUREMENT+'b'),('deformation',MEASUREMENT+'b')]
PROVIDERS=[('tests','j[a]'),('protocol','a'),('loadunit','a'),('deformationunit','a'),('minimum','b'),('maximum','b')]


def definitions():
    args=[v(n) for n in ('object','test','protocol','loadunit','deformationunit','context')]
    load=app(v('load'),*args);deformation=app(v('deformation'),*args);zero='n p a b'
    row=both(app(v('assessed'),*args),op('u',k('hc',load,v('minimum'))),
        op('u',k('hc',deformation,zero)),op('u',k('hc',v('maximum'),deformation)))
    return definition('rys',' '.join(n+' '+t for n,t in FIELDS),both(k('rcm',v('tests'),v('scope')),
        k('hc',zero,v('minimum')),op('u',k('hc',v('maximum'),zero)),
        quant('f','test','a',op('y',app(v('scope'),v('test')),row))))


def additions():
    text=''.join('r iba'+n+'[a d] '+t+'.' for n,t in PROVIDERS)
    text+='r ibascope[a d a] c.'
    text+=''.join('r iba'+n+'[a a a a a d] '+t+'.' for n,t in [('assessed','c'),('load','b'),('deformation','b')])
    fixed={n:k('iba'+n,v('cover'),k('wh')) for n,t in PROVIDERS}
    fixed.update(object=v('cover'),context=v('point'),scope='i[test a][k ibascope[v cover k wh[] v test]]')
    fixed.update({n:'p iba'+n for n in ('assessed','load','deformation')})
    return text+definition('ibaresistant','cover a point d',k('rys',*[fixed[n] for n,t in FIELDS]))


def manuscript():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(parent);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+additions())
    selected=closure(parent,['iaziayattribution']);affected={'iagresistant'}
    for row in selected:
        if _references(row)&affected:affected.add(row['name'])
    mapping={d['name']:d['name'] for d in parent['declarations']}
    mapping.update({name:'iba'+name for name in affected})
    mapping.update(iagresistant='ibaresistant',iazdepiction='ibadepiction',iazfamily='ibafamily')
    assert not ({mapping[n] for n in affected}-{'ibaresistant'})&{d['name'] for d in doc['declarations']}
    for row in selected:
        if row['name'] in affected and row['name']!='iagresistant':doc['declarations'].append(relocate(row,mapping))
    doc['statements']=deepcopy(parent['statements'][:-1])+[relocate(parent['statements'][-1],mapping)]
    return parse(format_graph(doc,'compact')),{n:mapping[n] for n in sorted(affected)}


def build():
    doc,_=manuscript();lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['rys'])
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='protocol_relative_load_resistance_inside_depiction',parent=PARENT,document=SOURCE,
        definitions={
            'rys':'指定した試験範囲が非空で重複なく完全に列挙され、荷重下限が正、変形上限が非負である。全試験が同じ物・試験法・荷重単位・変形単位・状況について評価済みで、荷重が下限以上、変形量が0以上かつ上限以下である。',
            'ibaresistant':'覆いと発話文脈で試験範囲・方法・単位・閾値を先に固定し、各描写時点の同じ覆いの応答をrysで調べる。',
            'ibadepiction':'既存の同じ覆いを使う成長・世話の描写で、iagresistantという真偽入力をibaresistantの説明へ置き換える。成長区間の全時点で同じ基準を使う。'},
        primitive_conventions={
            'protocol':'接触・荷重の方向と与え方、支持条件、応答の基準形状と観測時点、温度等を指定する試験方法。押込み・曲げ・圧縮を無条件に同一指標へ混ぜない。',
            'assessed':'同じ物・試験・方法・二単位・状況で、荷重と変形の両読みが対応する評価。荷重単位が力、変形単位が指定変形長さの単位であることと、読みの適合を含む。校正・測定の物理的基礎は別途必要。',
            'load/deformation':'同じ六引数に対する有理数の読み。変形は指定の基準形状からの非負の変形長さであり、物体全体の剛体移動そのものではない。最大・残留等の応答の選び方は試験法で固定する。',
            'tests/scope/minimum/maximum':'結果を見て成功例だけに変更しない試験の全範囲と、その荷重単位での正の下限・変形単位での非負の上限。本文から数値を補わず明示的な解釈入力として残す。'},
        limitations=[
            '指定条件で変形しにくいという操作的候補であり、工学的な押込み硬さ・弾性率・強度・靱性の定義ではない。負荷と変形の比や材料間の一般的順位は導かない。',
            '固定した試験範囲内の評価であり、任意の力・温度・時間・方向で変形しないことや試験外での耐性を保証しない。形状・支持の効果と材料固有の性質も分離し終えていない。',
            '硬さの原文での閾値・適切な方法・量の物理的基礎、芽の名詞内容、尊厳と全文の意味一致は未完。日常語の意味を工学規格へ確定しない。',
            '測定は描写世界の解釈であり、現実に自然や覆いを測定したと断言しない。引用・帰属の非事実性と旧定義・先行21主張を保つ。',
            '八引数の部分ひな形を残し、新たな原文文字範囲と意味確認済み区間は加算しない。'])


def reading():
    return dict(checked_on='2026-10-16',sources=[
        dict(url='https://www.duden.de/rechtschreibung/hart',section='Bedeutungen 1(a)',observation='物理的な用法に、抵抗性と容易には形を変えない意味がある。現代語の比較資料であり1784年の唯一の語義確定には使わない。'),
        dict(url='https://www.nist.gov/news-events/news/2013/07/new-nist-nanoscale-indenter-takes-novel-approach-measuring-surface',observation='押込みの荷重と深さを測り、複数の表面・機械的性質を調べる装置の説明。今回の閾値判定を規格上の硬さ測定と同一視しない。')],
        interpretation='本文の物理的な描写側について、明示した負荷に対する小さい変形として抵抗性を説明する部分候補。',
        limitations=['歴史語義・具体的な試験法・数値閾値は未確定。','現代の測定技術を原文の意図や時代背景として持ち込まない。'])


def review(files):
    packet=json.loads((ROOT/'data/kant-manuscript-obligations-v5.json').read_text(encoding='utf-8'));_,mapping=manuscript()
    packet.update(version='kant-manuscript-obligations-v6',supersedes='data/kant-manuscript-obligations-v5.json',document=SOURCE,
        document_sha256=hashlib.sha256(files[SOURCE].encode('utf-8')).hexdigest())
    for row in packet['obligations']:
        row['candidate_roots']=[mapping.get(n,n) for n in row['candidate_roots']]
        if row['id']=='hard_cover':
            row['candidate_roots']+=['ibaresistant','rys']
            row['remaining']='同じ指示された覆いに、固定した負荷試験での小さい変形を要求する候補を接続した。先行範囲の選択、適切な試験法・閾値・測定の物理的基礎、硬さの語義全体と原文の意味一致は未確認。'
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
