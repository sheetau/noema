"""Bind current appointed roles and independent judgment without merging people."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,op,both,quant as q
from scripts.compose_situated_criticism import params

PARENT='examples/v014/kant-unrestricted-others.noema'
FULL='examples/v014/kant-appointed-thinkers.noema'
CORE='examples/v014/appointed-thinkers-core.noema'
LIBRARY='examples/v014/qualified-subgroups.noema'
APPOINTS='h[a a a a d] c'
APPOINTMENT=[('person','a'),('issuer','a'),('role','a'),('point','d'),('history','h[d] c'),
    ('before','h[d d] c'),('occurs','h[a d] c'),('entrusted','h[a a d] c'),('appoints',APPOINTS)]
SUBGROUP=[('members','h[a d] c'),('status','h[a d] c'),('property','h[a d] c')]


def definitions():
    invoke=lambda name,*fields:app(v(name),*(v(n) for n in fields))
    text=definition('rpt',params(APPOINTMENT),both(k('ta',v('history'),v('before')),invoke('history','point'),
        invoke('entrusted','person','role','point'),q('g','event','a',q('g','earlier','d',both(
            invoke('history','earlier'),invoke('before','earlier','point'),invoke('occurs','event','earlier'),
            invoke('entrusted','person','role','earlier'),invoke('appoints','event','issuer','person','role','earlier'))))))
    text+=definition('rpu',params([('person','a'),('point','d')]+SUBGROUP),both(
        *(invoke(n,'person','point') for n,_ in SUBGROUP)))
    shared=lambda person:k('rpu',v(person),v('point'),*(v(n) for n,_ in SUBGROUP))
    text+=definition('rpv',params([('point','d')]+SUBGROUP),q('g','person','a',shared('person')))
    text+=definition('rpw',params([('point','d')]+SUBGROUP),q('g','first','a',q('g','second','a',both(
        op('u',op('e',v('first'),v('second'))),shared('first'),shared('second')))))
    fields=[('scope','h[d] c')]+SUBGROUP
    nonempty=q('g','point','d',invoke('scope','point'))
    text+=definition('rpx',params(fields),both(nonempty,q('f','point','d',op('y',invoke('scope','point'),
        k('rpv',v('point'),*(v(n) for n,_ in SUBGROUP))))))
    text+=definition('rpy',params(fields),both(nonempty,q('g','person','a',q('f','point','d',op('y',invoke('scope','point'),shared('person'))))))
    text+=definition('rpz',params(fields),both(nonempty,q('f','point','d',op('y',invoke('scope','point'),
        k('rpw',v('point'),*(v(n) for n,_ in SUBGROUP))))))
    return text


SOURCE=[('population','a'),('governed','a'),('point','d'),('appoints',APPOINTS),('guardianrole','h[a a d] c')]
FUTURE=[('population','a'),('governed','a'),('anchor','d'),('scope','h[d] c'),('history','h[d] c'),
    ('before','h[d d] c'),('appoints',APPOINTS),('guardianrole','h[a a d] c')]


def source_definitions():
    history='i[scene d][k ia[v person v point v scene]]';before='i[first d last d][k ic[v first v last v point]]'
    text=definition('hzha','person a issuer a role a point d appoints '+APPOINTS,
        k('rpt',*map(v,('person','issuer','role','point')),history,before,'p dg','p cf',v('appoints')))
    text+=definition('hzhb','person a governed a point d appoints '+APPOINTS+' guardianrole h[a a d] c',both(k('aa',v('person')),
        q('g','issuer','a',q('g','role','a',both(app(v('guardianrole'),v('role'),v('governed'),v('point')),
            k('hzha',*map(v,('person','issuer','role','point','appoints'))))))))
    text+=definition('hzhc','person a point d',both(k('aa',v('person')),q('g','judgment','a',k('h5c',v('person'),v('judgment'),v('point')))))
    member='i[person a point d][k hg[k mp[v population] v person]]'
    status='i[person a point d][k hzhb[v person v governed v point v appoints v guardianrole]]'
    for name,target in (('hzhd','rpv'),('hzhe','rpw')):
        text+=definition(name,params(SOURCE),both(k('hi',k('mp',v('population')),'p aa'),k(target,v('point'),member,status,'p hzhc')))
    temporal=both(k('ta',v('history'),v('before')),app(v('history'),v('anchor')),
        q('f','point','d',op('y',app(v('scope'),v('point')),both(app(v('history'),v('point')),app(v('before'),v('anchor'),v('point'))))))
    text+=definition('hzhf',params(FUTURE),both(temporal,k('hi',k('mp',v('population')),'p aa'),
        k('rpz',v('scope'),member,status,'p hzhc')))
    return text


MEANINGS={
    'rpt':'同じ人・職務について現在の委任があり、同じ順序付き履歴の過去に、その人と職務への委任を伴う同じ任用行為が生起する。任用の出所・行為・時点を共有する。過去の任用だけから現在の委任を補わない。',
    'rpu':'同じ人・同じ状況が母集団への所属、指定された立場、指定性質の三条件を同時に満たす。別々の人の存在を継ぎ合わせない。',
    'rpv':'rpuを満たす人が少なくとも一人存在する。全員や複数人を要求しない。',
    'rpw':'rpuを満たす異なる二人が存在する。該当者がちょうど二人であること、母集団の全員ではないことは含まない。',
    'rpx':'非空の状況範囲の各状況でrpvが成立する。状況ごとに別の人が証人になってよい。',
    'rpy':'非空の状況範囲に対し、同じ一人が全状況でrpuを満たす。rpxより強い条件として区別する。',
    'rpz':'非空の状況範囲の各状況でrpwが成立する。各状況での二人は状況間で同一でなくてよい。',
    'hzha':'同じ人のiaの履歴、icの順序、dgの行為生起、cfの職務委任へrptを接続する。任用の具体的な出所名や日時は補わない。',
    'hzhb':'その人が、指定された対象集団の後見役として分類される職務へ任用され、現在もその職務を委ねられている。後見役の職務分類は引数の意味規約として残す。',
    'hzhc':'同じ人・状況に、本人の理解力を用い、同じ対象・理由・支持を持ち、他者の指導を伴わないh5cの判断が少なくとも一つある。恒常的な性向や全判断の自立性はこれだけでは意味しない。',
    'hzhd':'重複のない人の母集団の中に、同じ状況でhzhbとhzhcを満たす同じ人がいる。後見の対象集団と、この母集団を無条件に同一視しない。',
    'hzhe':'hzhdと同じ構成で、該当する異なる二人の存在を要求する。複数性を明示した候補であり、他の成員の不該当は要求しない。',
    'hzhf':'同じ履歴の基準より後にある非空の指定範囲の各状況で、hzheに対応する二人の存在が成立する。将来の全域を尽くすこと、自由の条件、比較的な可能性や必然性は別に指定する必要がある。',
}
LIMITS=[
    'u0011の任用された役割の中の独立した思考と、将来の状況ごとの存在についての部分構成。hzhcは実際の理由ある判断の証人であり、Selbstdenkendeの恒常的な性向の必要十分条件とはしない。',
    'guardianroleは、同じ対象集団の判断を指導する役割という分類を渡す。役割と権限の制度的・文化的意味、任用制度の成立、公開された公衆とgroßer Haufenの区別と規模の説明は未完である。',
    '自ら後見人を称するoa・obだけでは任用済みとはしない。任用行為があり現在も委任されていることと、現在その職務を遂行すること、正当性、本人の同意は別である。',
    '一人以上と二人以上の条件を区別する。原文のeinigeを固定人数、全員ではないこと、全状況で同じ人という条件へ変えない。複数性を採るhzhfは一つの明示的な部分読解である。',
    '将来範囲は空でなく、全て基準より後にある。同じ人の任用が各状況より前に必要だが、必ず基準時より前に任用済みであることは要求しない。状況間の人物交替を許す。',
    'sogarの比較背景、Dennの説明、自由の条件、未来の全域、既存の頚木の比喩や態度伝播との接続は残る。部分定義を著者の全文主張として追加せず、現時点での人の存在も補わない。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    doc=parse(format_graph(doc,'compact')+definitions()+source_definitions());doc['statements']=old['statements']
    basis=json.loads((ROOT/'data/kant-unrestricted-others-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='kant-appointed-thinkers-basis-v1',document=FULL);basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    audit_basis(doc,basis)
    files={FULL:format_graph(doc,'compact')+'\n','data/kant-appointed-thinkers-basis-v1.json':basis}
    for path,roots in ((CORE,['hzhd','hzhe','hzhf']),(LIBRARY,['rpt','rpv','rpw','rpx','rpy','rpz'])):
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
    print('Appointed roles and independent judgments bound to the same people',flush=True)


if __name__=='__main__':main()
