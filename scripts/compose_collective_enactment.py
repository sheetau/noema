"""Connect collective office decisions to the same constitutive norm change."""
from copy import deepcopy
import json

from noema.constructed import parse,format_graph
from scripts.compose_collective_office import ROOT,SOURCE as PARENT,OFFICE,PROFILE,params,av
from scripts.compose_normative_powers import DESCRIPTION,CONTROL,EDGE,EFFECT,TRANSITION as OLD_TRANSITION
from scripts.compose_origin_clock import definition
from scripts.compose_limits import call as k,app,both,op,quant,v
from scripts.compose_qualified_utterance import closure
from scripts.compose_restricted_utterance import primitive

LIBRARY='examples/v016/collective-enactment.noema'
EXAMPLE='examples/v016/collective-enactment-example.noema'
BASIS='data/collective-enactment-basis-v1.json'
MANDATE='h[a a a '+DESCRIPTION+' j[a] d] c'
CAST='h[a c a a '+DESCRIPTION+' j[a] d] c'
APPROVAL=OFFICE+[('framework','a'),('profile',PROFILE),('exercise',DESCRIPTION),('exercisebindings','j[a]'),
    ('exercisevalid','h[j[a]] c'),('mandates',MANDATE)]
TRANSITION=APPROVAL+[(n,t) for n,t in EFFECT if n!='start']+[('controlled',CONTROL),('recognizes',EDGE)]
POWER=[(n,t) for n,t in TRANSITION if n!='end']
ACTUAL=TRANSITION+[('performed',CONTROL),('realized','h[d d] c'),('cast',CAST)]
ROOTS=['rwq','rwr','rws','rwt']


def definitions():
    mandate=app(v('mandates'),*[v(n) for n in ('framework','organization','office','exercise','exercisebindings','anchor')])
    text=definition('rwq',params(APPROVAL),both(k('rwp',*av(OFFICE)),
        'a[v exercisebindings][n p a b][v organization]',app(v('exercisevalid'),v('exercisebindings')),
        mandate,app(v('rule'),k('rwl',v('participants'),v('profile')))))
    refs={n:v(n) for n,t in TRANSITION};refs.update(actor=v('organization'),capacity=v('office'),start=v('anchor'))
    text+=definition('rwr',params(TRANSITION),both(k('rwq',*av(APPROVAL)),k('riw',*[refs[n] for n,t in OLD_TRANSITION])))
    text+=definition('rws',params(POWER),quant('g','end','d',k('rwr',*av(TRANSITION))))
    casts=quant('f','voter','a',op('y',app(v('holders'),v('voter'),v('office'),v('organization'),v('anchor')),
        app(v('cast'),v('voter'),app(v('profile'),v('voter')),*[v(n) for n in ('organization','office','exercise','exercisebindings','anchor')])))
    text+=definition('rwt',params(ACTUAL),both(k('rwr',*av(TRANSITION)),casts,
        app(v('performed'),v('organization'),v('exercise'),v('exercisebindings'),v('anchor')),
        app(v('realized'),v('anchor'),v('end'))))
    return text


def build():
    parent=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    doc=deepcopy(parent);doc['declarations']=closure(parent,['rwp','riw']);doc['statements']=[]
    assert not set(ROOTS)&{d['name'] for d in parent['declarations']}
    lib=parse(format_graph(doc,'compact')+definitions())
    text=format_graph(lib,'compact')
    for name,sort in ACTUAL:
        if name not in ('exercise','target'):
            text+=primitive('jce'+name,sort if sort.startswith('h[') else 'h[] '+sort)
    text+='r jceexercisetruth[j[a] d] c.r jcetargettruth[j[a] d] c.'
    for name,truth in [('exercise','exercise'),('alias','exercise'),('target','target'),('other','target')]:
        text+=definition('jce'+name,'bindings j[a]','b scene[k jce'+truth+'truth[v bindings v scene]]','e')
    refs={n:('p jce'+n if t.startswith('h[') else k('jce'+n)) for n,t in ACTUAL}
    refs.update(exercise='r[p jceexercise]',target='r[p jcetarget]')
    questions=[k(name,*[refs[n] for n,t in fields]) for name,fields in
        [('rwq',APPROVAL),('rwr',TRANSITION),('rws',POWER),('rwt',ACTUAL)]]
    questions+=['e[r['+questions[3]+']][r['+questions[3]+']]']
    example=parse(text+''.join('q['+q+'].' for q in questions))
    return {p:format_graph(d,'compact')+'\n' for p,d in ((LIBRARY,lib),(EXAMPLE,example))}


def basis():
    return dict(status='collective_decision_and_same_normative_transition_not_state_definition',parent=PARENT,
        definitions={
            'rwq':'同じ最高役職の共同保持rwpと、その規則で指定入力が可決されることを要求する。制度的枠組み・組織・役職・行使記述・引数・基準時点をmandatesで照合し、行使引数の先頭を同じ組織に固定する。入力は仮定でよく、投票済みとはしない。',
            'rwr':'rwqと既存riwを結ぶ。組織を行使主体、最高役職を行使の立場、基準時点を変更前として同一化する。同じ前後状況で同じ対象規範が成立・廃止される制度上の移行を要求する。',
            'rws':'同じ可決入力・行使・対象規範についてrwrを満たす結果状況が存在する。特定変更への制度的権能の候補で、現実の実行や許可は要求しない。',
            'rwt':'rwrに、全保持者が同じ行使について指定入力を行った記録、同じ組織による行使、同じ前後状況への現実の移行を加える。可決・行使・現実の効果を別々に照合する。'},
        relations={
            'mandates':'指定制度で、その役職の二値決定規則の肯定出力を、その組織のその行使記述・引数についての決定として扱う。単なる内容の類似や事後的な相関ではない。規則の対象範囲を指定する入力関係。',
            'cast':'同じ保持者が同じ組織・役職・行使記述・引数・時点について指定した二値入力を実際に行った記録。偽の入力も明示的な記録であり、賛成記録の欠落だけで反対とはしない。',
            'controlled/recognizes':'既存riwの意味規約を継承する。組織による行使選択の統制と、制度的枠組みによるその行使の構成的効果の認定。',
            'relation':'同じ出所・名宛人・立場・対象記述・引数・内容の肯否・時点への規範関係。成立廃止を内容の肯否と区別する。'},
        limitations=[
            '国家の定義ではなく、同じ共同統治役職による特定の規範変更の構成。会社・団体にも適用でき、領域・住民・公的統治の範囲は未記述。カント本文へこの特定の行使が存在すると追加しない。',
            'mandates、controlled、recognizes、castは意味規約付き入力であり、制度の社会的承認・成立・正当性や投票記録の真正性を説明し終えていない。',
            'rwsの入力は制度上の仮定でよい。全保持者の物理的な投票可能性、独立な意思形成、実際の入力を保証しない。',
            'rwtは全保持者について指定入力の記録を要求するが、相反する記録の不存在、定足数、棄権や代理投票の一般制度は扱わない。',
            '政策や行使の内容は脱引用しない。変更対象の内容が現実に実現したこと、他の規範の不変性、行使の積極的許可や道徳的正当性は導かない。',
            '共同保持の候補は一つの最高役職と有限の二値決定規則に限る。検査の有限個体・状況は全ての実制度や原文の意味一致を証明しない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
