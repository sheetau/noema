"""Fill the autonomous-use component of an explicitly partial speech restriction."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from scripts.compose_origin_clock import ROOT,definition

PARENT='examples/v016/kant-restricted-utterance.noema'
SOURCE='examples/v016/kant-qualified-utterance.noema'
CORE='examples/v016/qualified-utterance-core.noema'
BASIS='data/qualified-utterance-basis-v1.json'
NAMES=('hzuqualification','hzuonly','hzuattribution')


def definitions():
    text=definition('hzuqualification','remaining h[a d] c actor a anchor d',
        'w[t[k h4l[v actor]][v anchor]][c[v remaining][v actor v anchor]]')
    text+=definition('hzuonly','remaining h[a d] c anchor d',
        'k hztonly[i[actor a point d][k hzuqualification[v remaining v actor v point]] v anchor]')
    text+=definition('hzuattribution','',
        'k hztannotation[k hztnode[] k wa[] r c[p hzuonly] k hztscope[] k wh[]]')
    return text


def closure(doc,roots):
    lookup={d['name']:d for d in doc['declarations']};pending=set(roots);keep=set()
    while pending:
        name=pending.pop()
        if name in keep:continue
        keep.add(name);pending.update(_references(lookup[name])-keep)
    return [deepcopy(d) for d in doc['declarations'] if d['name'] in keep]


def build():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'));statements=doc['statements'];doc['statements']=[]
    assert not set(NAMES)&{d['name'] for d in doc['declarations']}
    doc=parse(format_graph(doc,'compact')+definitions()+'s[k hzuattribution[]].')
    doc['statements']=statements[:-1]+doc['statements']
    core=deepcopy(doc);core['statements']=core['statements'][-1:]
    core['declarations']=closure(doc,_references(core['statements']))
    return {SOURCE:format_graph(doc,'compact')+'\n',CORE:format_graph(core,'compact')+'\n'}


def basis():
    return dict(status='partial_qualification_with_existing_autonomous_capacity',parent=PARENT,document=SOURCE,
        definitions={
            'hzuqualification':'同じ本人・基準文脈のh4lと残りの資格条件を連言する。h4lは既存の評価済みで指導なしに自分の理解力を使えるという能力内容であり、新しい啓蒙ラベルを原始関係として加えない。',
            'hzuonly':'既存hztonlyへhzuqualificationを渡す。発言の話者と資格を持つ本人、引用の文脈と資格評価の文脈を共通にする。能力と残りの条件は必要条件であり、十分条件や実在の主張にはしない。',
            'hzuattribution':'同じ原文箇所・著者・範囲・帰属文脈で、部分的に具体化したひな形の閉じた記述を解釈注記として提示する。完成した原文主張との同義性は主張しない。'},
        reused={
            'h4l':'同じ人についてfoの全利用可能方法の評価整合性とupの成功方法の存在を要求する。',
            'bb':'同じ本人が所有する理解能力を、その本人が同じ行為で使い、その行為に他者の指導がないという目標。',
            'aa/ab/ac/ad':'人、理解能力の本人への所属、本人による能力の使用、他者による同じ行為への指導という既存の基礎関係。基礎関係の理論全体を確立したとはしない。',
            'ae/af/ap':'理解力の使用に関する利用可能方法・結果・選択された評価範囲。発話可能性のhztavailable/hztoutcomes/hztselectedとは別に保持する。'},
        remaining_argument='影への恐れ、規律ある多数の軍隊、公的平穏などの残る資格条件。同じ本人と基準文脈を受ける未充足の引数であり、これらの語を定義済みとは数えない。',
        interpretation_basis='同じ本文のu0015に接続済みのh4lを再利用する候補。docs/qualified-princes-v1.mdとdata/kant-qualified-princes-basis-v1.jsonの限界を引き継ぐ。',
        unresolved=[
            'h4lは啓蒙された人物への一つの能力的解釈であり、自律・決意・学識・政治的評価の全側面と同義とはしない。',
            'selbstの本人への照応は同じ候補者への適用で保持するが、対比・強調の含意は未記述である。',
            '資格の能力は基準時点で評価する。能力を獲得した過去の過程や、基準時点での実際の使用を追加しない。',
            '残りの資格条件は未充足。前段の指揮・保護・権限を軍隊・平穏の同義条件として勝手に代入しない。',
            '発話可能性の操作的な読み、自由国との対比、wagen、Aber auch、同時性、引用内nur、段落後半と全文の意味確認は残る。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
