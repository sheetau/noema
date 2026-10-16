"""Separate an assessed independent-response profile from a current episode."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant as q
from scripts.compose_situated_criticism import params
from scripts.compose_appointed_thinkers import APPOINTS

PARENT='examples/v014/kant-appointed-thinkers.noema'
FULL='examples/v014/kant-independent-profiles.noema'
CORE='examples/v014/independent-profiles-core.noema'
LIBRARY='examples/v014/assessed-response-profiles.noema'
ZERO='n p a b';ONE='n p b b';TRUE=op('e',ZERO,ZERO)
PROFILE=[('points','h[a d] j[d]'),('cases','h[a d d] c'),('assessed','h[a d d] c'),
    ('weights','h[a d d] b'),('threshold','h[a d] b'),('topics','h[a d d] a'),('presented','h[a a d] c')]
GROUP=[('population','a'),('governed','a'),('anchor','d'),('appoints',APPOINTS),('guardianrole','h[a a d] c')]+PROFILE
FUTURE=GROUP+[('future','h[d] c'),('history','h[d] c'),('before','h[d d] c')]


def av(fields):return [v(n) for n,_ in fields]


def definitions():
    fields='points j[d] cases h[d] c assessed h[d] c response h[d] c weights h[d] b threshold b'
    total=k('rd4',v('points'),'i[scene d]['+TRUE+']',v('weights'))
    score=k('rd4',v('points'),v('response'),v('weights'))
    text=definition('rqa',fields,both(k('rd5',*map(v,('points','cases','assessed','weights'))),
        k('hc',ZERO,v('threshold')),op('u',k('hc',ONE,v('threshold'))),
        op('u',k('hc',score,k('hb',v('threshold'),total)))))
    fields=[('person','a'),('anchor','d')]+PROFILE[:5]+[('response','h[a d d] c')]
    bind=lambda name:'i[scene d]['+app(v(name),v('person'),v('anchor'),v('scene'))+']'
    text+=definition('rqb',params(fields),k('rqa',app(v('points'),v('person'),v('anchor')),
        bind('cases'),bind('assessed'),bind('response'),bind('weights'),app(v('threshold'),v('person'),v('anchor'))))
    return text


def source_definitions():
    text=definition('hzhg','person a topic a scene d presented h[a a d] c',both(k('aa',v('person')),
        app(v('presented'),v('person'),v('topic'),v('scene')),
        q('g','judgment','a',both(k('h5c',v('person'),v('judgment'),v('scene')),
            k('fb',v('judgment'),v('topic'),v('scene'))))))
    response='i[person a anchor d scene d]['+k('hzhg',v('person'),
        app(v('topics'),v('person'),v('anchor'),v('scene')),v('scene'),v('presented'))+']'
    text+=definition('hzhh',params([('person','a'),('anchor','d')]+PROFILE),both(k('aa',v('person')),
        k('rqb',v('person'),v('anchor'),*av(PROFILE[:5]),response)))
    member='i[person a point d][k hg[k mp[v population] v person]]'
    status='i[person a point d][k hzhb[v person v governed v point v appoints v guardianrole]]'
    property='i[person a point d]['+k('hzhh',v('person'),v('point'),*av(PROFILE))+']'
    text+=definition('hzhi',params(GROUP),both(k('hi',k('mp',v('population')),'p aa'),
        k('rpw',v('anchor'),member,status,property)))
    temporal=both(k('ta',v('history'),v('before')),app(v('history'),v('anchor')),
        q('f','point','d',op('y',app(v('future'),v('point')),both(
            app(v('history'),v('point')),app(v('before'),v('anchor'),v('point'))))))
    text+=definition('hzhj',params(FUTURE),both(temporal,k('hi',k('mp',v('population')),'p aa'),
        k('rpz',v('future'),member,status,property)))
    return text


MEANINGS={
    'rqa':'指定範囲を非空・重複なし・過不足なしで列挙し、全場面が評価済みで正の重みを持つ。応答が成立する重みの合計が、全重みと0より大きく1以下の閾値の積以上である。境界値と例外を許す。',
    'rqb':'rqaの列挙・範囲・評価済み条件・重み・閾値・応答を同じ本人と基準状況に固定する。現在の応答から他の場面の応答や評価基準を補わない。',
    'hzhg':'同じ人・場面に指定話題が提示され、その人の独立した理由ある判断h5cが、その同じ話題について述べる。別の話題の判断や他人の判断では満たさない。',
    'hzhh':'同じ本人・基準状況の明示した評価場面にhzhgを接続してrqbを満たす。評価場面は仮定場面でもよく、基準状況での実際の判断hzhcは要求しない。',
    'hzhi':'同じ人の母集団で、現在任用された役割hzhbと、同じ基準での応答プロフィールhzhhを満たす異なる二人がいる。任用された人とプロフィールを持つ人を分けない。',
    'hzhj':'基準より後の非空の指定範囲で、各状況にhzhiと同じ二人の存在条件を課す。人物は交替してよいが、各人のプロフィールの基準はその役割の状況に結ぶ。',
}
LIMITS=[
    'Selbstdenkendeの性向へ向けた、評価範囲と基準を明示する応答プロフィールの候補。一回の現実の判断、一切例外のない全判断の自立、考えたいという態度のいずれとも同一視しない。',
    '評価場面の範囲・話題・重み・閾値は結果を見る前に選定する解釈条件であり、数値を語の意味へ一律に固定しない。有限プロフィールから全ての未知場面や生涯の性向を推定しない。',
    '単一場面も形式上は指定できるが、その結果から広い性向を推論する規則はない。恒常性の評価には適切な場面の選定と範囲の説明が別途必要。',
    '仮定場面と本人の現実の能力を結ぶ反事実的な妥当性、心理機構、想像・探索・疑問を含む思考全般、原文に適した性向基準の確定は未完。',
    '既存hzhd・hzhe・hzhfの出来事による部分構成は保持し、新しいプロフィールによる構成を別の明示的な候補にする。任用・後見役の意味規約と未完事項を引き継ぐ。',
    '自由の条件、sogarの比較背景、Dennの説明、後続の頚木と態度伝播は未接続。著者の主張を追加せず、原文文字範囲や意味確認済み区間数は増やさない。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+source_definitions());doc['statements']=old['statements']
    basis=json.loads((ROOT/'data/kant-appointed-thinkers-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='kant-independent-profiles-basis-v1',document=FULL);basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    audit_basis(doc,basis)
    files={FULL:format_graph(doc,'compact')+'\n','data/kant-independent-profiles-basis-v1.json':basis}
    for path,roots in ((CORE,['hzhc','hzhi','hzhj']),(LIBRARY,['rqa','rqb'])):
        selected=extract_document(doc,roots=roots,statement_indices=[]);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path=path)
    return {p:x if isinstance(x,str) else json.dumps(x,ensure_ascii=False,indent=2)+'\n' for p,x in files.items()}


def main():
    for p,body in build().items():
        path=ROOT/p
        if path.exists():assert path.read_text(encoding='utf-8')==body,p
        else:
            with path.open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    print('Assessed response profiles composed without asserting current episodes',flush=True)


if __name__=='__main__':main()
