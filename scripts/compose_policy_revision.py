"""Allow additions and selective retirements as well as normative replacement."""
from copy import deepcopy
import hashlib,json
from noema.constructed import parse,format_graph
from noema.extraction import _references
from noema.linking import relocate
from scripts.compose_institutional_appraisal import ROOT,SOURCE as PARENT
from scripts.compose_governing_principles import REPLACE,COMPARE
from scripts.compose_collective_office import params,av
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,both,op,v
from scripts.compose_qualified_utterance import closure

LIBRARY='examples/v016/policy-revision.noema'
SOURCE='examples/v016/kant-policy-revision.noema'
CORE='examples/v016/policy-revision-core.noema'
BASIS='data/policy-revision-basis-v1.json'
REVIEW='data/kant-manuscript-obligations-v11.json'


def norm(which,point):
    return k('rxx',v('source'),v('actor'),v('office'),v(which),v(point),v('required'))


def definitions():
    changed=op('x',op('u',norm('first','end')),op('u',norm('second','start')))
    text=definition('ryx',params(REPLACE),both(op('u',op('e',v('start'),v('end'))),
        norm('first','start'),norm('second','end'),changed,k('rx2',*av(COMPARE))))
    text+=definition('ryy',params(REPLACE),both(k('ryx',*av(REPLACE)),norm('first','end')))
    text+=definition('ryz',params(REPLACE),both(k('ryx',*av(REPLACE)),norm('second','start')))
    return text


def manuscript():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(parent);doc['statements']=[]
    adapter=definition('ibfchange',params(REPLACE[:-1]),k('ryx',*av(REPLACE[:-1]),'p h7k'))
    doc=parse(format_graph(doc,'compact')+definitions()+adapter)
    selected=closure(parent,[parent['statements'][-1]['body']['symbol']]);affected={'iarreplacement'}
    for row in selected:
        if _references(row)&affected:affected.add(row['name'])
    mapping={d['name']:d['name'] for d in parent['declarations']}
    mapping.update({name:'ibf'+name for name in affected})
    mapping.update(iarreplacement='ibfchange',iaseffect='ibfeffect',iascausal='ibfcausal',ibeschema='ibfschema',ibeattribution='ibfattribution')
    assert not ({mapping[n] for n in affected}-{'ibfchange'})&{d['name'] for d in doc['declarations']}
    for row in selected:
        if row['name'] in affected and row['name']!='iarreplacement':doc['declarations'].append(relocate(row,mapping))
    doc['statements']=deepcopy(parent['statements'][:-1])+[relocate(parent['statements'][-1],mapping)]
    return parse(format_graph(doc,'compact')),{n:mapping[n] for n in sorted(affected)}


def build():
    doc,_=manuscript();lib=deepcopy(doc);lib['statements']=[];lib['declarations']=closure(doc,['ryx','ryy','ryz','rx3'])
    core=deepcopy(doc);core['statements']=core['statements'][-1:];core['declarations']=closure(doc,_references(core['statements']))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(SOURCE,doc),(CORE,core))}


def basis():
    return dict(status='normative_revision_without_compulsory_old_policy_removal',parent=PARENT,document=SOURCE,
        definitions={
            'ryx':'異なる二文脈で、同じ規範源・主体・職務について第一原則が始点で要求され、第二原則が終点で要求される。第一原則の終点での要求がなくなるか、第二原則の始点での要求がなかったことを要求し、同じ比較範囲で両原則の内容差も確認する。',
            'ryy':'ryxのうち第一原則が終点でも要求される追加。第二原則の要求が新たに成立し、第一原則の廃止は求めない。',
            'ryz':'ryxのうち第二原則が始点から要求される選択的な取り下げ。第一原則への要求が失われ、既存の第二原則は残る。',
            'rx3':'旧来の置換条件を変更せず保持する。ryxが成立する場合は、rx3・ryy・ryzのいずれか一つに分かれる。',
            'ibfchange/ibfeffect/ibfcausal':'同じ原則・規範源・主体・職務の変化を、既存の介入モデルの効果へ渡す。変化が原因側と独立に起きる例は従来どおり因果条件から除く。',
            'ibfschema/ibfattribution':'政府の資格、組織的な自己利益判断、公的理性使用の必要条件を保持し、新しい変化条件を使う部分ひな形へ帰属する。'},
        interpretation='原文の政府の原則への作用を、旧原則の要求消失と新原則の要求成立の同時発生だけに限定していた制約を緩める。原文がこの三分類や特定の規範状態を明示したとの主張ではない。',
        limitations=[
            '規範上の要求の前後差を扱う候補であり、採択・撤回の発話行為や行政手続そのものではない。原則を信念・目的・慣行と捉える読み、要求の強さの変化は未記述。',
            '指定した二原則と二文脈に相対的な変化である。他の原則の追加・撤回を排除せず、途中の全時点の維持も要求しない。',
            '内容差は同じ比較範囲の実例によって確認する。単なる記述名の違いを変化と数えず、範囲の適切さと全状況での差は別の課題にする。',
            '要求がなくなることは、反対内容への要求や禁止ではない。要求される内容が現実に履行されることも条件にしない。',
            '構造モデル内の因果依存と履歴・評価済み条件は従来のまま残る。原文の作用一般の語義、焦点、尊厳・残余条件と全文の意味一致は未完。',
            '旧定義・先行21主張と8引数のひな形を保存し、新しい原文範囲や意味確認済み区間を加算しない。'])


def review(files):
    packet=json.loads((ROOT/'data/kant-manuscript-obligations-v10.json').read_text(encoding='utf-8'));_,mapping=manuscript()
    packet.update(version='kant-manuscript-obligations-v11',supersedes='data/kant-manuscript-obligations-v10.json',document=SOURCE,
        document_sha256=hashlib.sha256(files[SOURCE].encode('utf-8')).hexdigest())
    for row in packet['obligations']:
        row['candidate_roots']=[mapping.get(n,n) for n in row['candidate_roots']]
        if row['id']=='government':
            row['candidate_roots']=list(dict.fromkeys(row['candidate_roots']+['ryx','ibfchange']))
            row['remaining']='同じ政府役の原則変化に、置換に加えて追加と選択的な取り下げを認めた。要求の前後差に限定した読みの適合、国家・役職・管轄の基礎、作用と焦点の全体は未確認。'
    for template in packet['templates']:template['symbol']=mapping.get(template['symbol'],template['symbol'])
    packet['evidence_files']+=[BASIS]
    return packet


def main():
    files=build();files|={BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n',REVIEW:json.dumps(review(files),ensure_ascii=False,indent=2)+'\n'}
    for name,body in files.items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
