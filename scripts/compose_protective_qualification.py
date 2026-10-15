"""Connect the existing joint protection account to the same qualified speaker."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT,definition
from scripts.compose_limits import call as k,app,both,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_commanded_protection import READY,LIBRARY as PROTECTION
from scripts.compose_supported_apprehension import SOURCE as PARENT

SOURCE='examples/v016/kant-protective-qualification.noema'
CORE='examples/v016/protective-qualification-core.noema'
BASIS='data/protective-qualification-basis-v1.json'
PROVIDERS=[(n,t) for n,t in READY if n not in ('planner','group','anchor')]
QUALIFICATION='h[a a a d] c'


def additions():
    text=''
    for name,sort in PROVIDERS:text+='r hzx'+name+'[a a d] '+sort+'.'
    refs={n:k('hzx'+n,v('actor'),v('group'),v('anchor')) for n,t in PROVIDERS}
    refs.update(planner=v('actor'),group=v('group'),anchor=v('anchor'))
    text+=definition('hzxgroup','actor a group a anchor d',k('rvh',*[refs[n] for n,t in READY]))
    residual=app(v('qualification'),v('actor'),v('group'),refs['community'],v('anchor'))
    text+=definition('hzxremaining','qualification '+QUALIFICATION+' actor a anchor d',
        quant('g','group','a',both(residual,k('hzxgroup',v('actor'),v('group'),v('anchor')))))
    text+=definition('hzxonly','qualification '+QUALIFICATION+' anchor d',
        k('hzwonly','i[actor a point d]['+k('hzxremaining',v('qualification'),v('actor'),v('point'))+']',v('anchor')))
    text+='r hzxannotation[a a i c[h['+QUALIFICATION+' d] c] a d] c.'
    text+=definition('hzxattribution','',
        'k hzxannotation[k hztnode[] k wa[] r c[p hzxonly] k hztscope[] k wh[]]')
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    doc=deepcopy(parent);statements=doc['statements'];doc['statements']=[]
    lookup={d['name']:d for d in doc['declarations']}
    for decl in closure(parse((ROOT/PROTECTION).read_text(encoding='utf-8')),['rvh']):
        if decl['name'] in lookup:assert decl==lookup[decl['name']],decl['name']
        else:doc['declarations'].append(decl);lookup[decl['name']]=decl
    doc=parse(format_graph(doc,'compact')+additions()+'s[k hzxattribution[]].')
    doc['statements']=statements[:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:]
    core['declarations']=closure(doc,_references(core['statements']))
    return {path:format_graph(value,'compact')+'\n' for path,value in [(SOURCE,doc),(CORE,core)]}


def basis():
    return dict(status='partial_source_connection_with_explicit_residual_qualification',definitions={
        'hzxgroup':'同じactor・group・anchorから全入力を選び、既存rvhの人数基準・全利用可能計画での要求適合・共同体を保護する計画の存在を調べる。',
        'hzxremaining':'同じ集団でhzxgroupと残余のqualificationが成立することを要求する。qualificationへ渡す共同体もhzxgroupが保護する共同体と同じ選択結果にする。',
        'hzxonly':'前段hzwonlyのremainingへ、同じ候補者・評価文脈のhzxremainingを渡す。啓蒙・影の解釈候補・引用された発言能力を保持する。',
        'hzxattribution':'残余qualificationを引数に持つ部分ひな形の記述を、同じ著者・箇所・範囲へ帰属する。'},
        providers='人数の列、数量基準、計画の関係、共同体、保護の機構と記録、命令関係を、候補者・集団・基準文脈に依存する選択関数で渡す。別集団のモデルや別時点の人数を暗黙に使わない。返された関係の内部でも既存rvhが本人・集団・計画・文脈を照合する。',
        source=dict(url='https://www.korpora.org/Kant/aa08/041.html',location='AA VIII, page 41, lines 24–25',checked_date='2026-10-15'),
        unresolved=[
            'qualificationは軍隊の制度的・軍事的役割と、保護する活動・保有の範囲が公的平穏に適切かという残余条件を持つ未充足引数である。このひな形を軍隊・平穏の完成定義としない。',
            '全利用可能計画での要求適合は規律の強い操作的候補であり、訓練・例外の頻度・服従の動機を定義したものではない。人数基準の具体的閾値を原文へ補わない。',
            '計画を利用できることを手元にあることの候補条件として使う。法的に正当な指揮権は本文へ追加しない。距離、即応性、制度的位置は残る。',
            '共同体の活動可能性と保有の維持を保護対象とする部分候補であり、暴力や騒擾の不在など公的平穏全体を同義とはしない。',
            '既存の保護機構は明示モデル内の介入比較と記録整合性を要求する。世界一般への因果保証や原文の保証の唯一の解釈ではない。',
            '要求網羅性と影の候補には全記述への量化が残る。有限診断を全域の証明とはしない。残余条件の同定と全文の意味確認は未完。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
