"""Apply the existing coefficient law to each scoped material point and case."""
from copy import deepcopy
import json
from noema.grammar import parse,format_graph
from noema.extraction import extract_document,extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_convention_comparison import ROOT,CUT
from scripts.compose_force_mass_units import RESTMASS,NUMERIC
from scripts.compose_origin_clock import definition,v
from scripts.compose_limits import call as k,app,both,op,quant
from scripts.compose_situated_criticism import params,args

PARENT='examples/v014/einstein-arbitrary-small-charge.noema'
SOURCE='examples/v014/einstein-material-mass-extension.noema'
LIBRARY='examples/v014/material-mass-extension.noema'
CORE='examples/v014/material-mass-extension-core.noema'
READING='data/material-mass-extension-reading-v1.json'
META=[(n,'h[a a d] a') for n in ('forceframe','accelerationframe','massunit','forceunit','accelerationunit')]
VALUES=[(n,'h[a a d] '+CUT) for n in NUMERIC.split()]
RELATIONS=[('framevalid','h[a] c'),('comoving','h[a a a d] c'),
    ('convention','h[a a a a a a d] c'),('restmassassigned',RESTMASS),
    ('calibrated','h[a a a '+CUT+' '+CUT+' '+CUT+' d] c')]
FIELDS=META+VALUES+RELATIONS
SCOPE=[('materials','h[a d] c'),('cases','h[a a d] c')]


def definitions():
    point,event,context=map(v,('point','event','context'))
    value=lambda name:app(v(name),point,event,context)
    text=definition('seqy',params([('point','a'),('event','a'),('context','d')]+FIELDS),both(
        app(v('framevalid'),value('forceframe')),app(v('framevalid'),value('accelerationframe')),
        app(v('comoving'),point,value('forceframe'),event,context),
        app(v('convention'),point,value('forceframe'),value('accelerationframe'),event,value('forceunit'),value('accelerationunit'),context),
        app(v('restmassassigned'),point,event,value('massunit'),value('restmass'),context),
        app(v('calibrated'),*[value(n) for n in ('massunit','forceunit','accelerationunit','massscale','forcescale','accelerationscale')],context),
        k('seqa',*(value(n) for n in NUMERIC.split()))))
    text+=definition('seqz',params([('context','d')]+SCOPE+FIELDS),quant('f','point','a',
        op('y',app(v('materials'),point,context),quant('f','event','a',
            op('y',app(v('cases'),point,event,context),k('seqy',point,event,context,*args(FIELDS)))))))
    return text


MEANINGS={
    'seqy':'同じ物質点・出来事・文脈の二基準系、三単位と尺度、低速質量と二係数について、共動・数値化規約・質量帰属・単位校正を保持し、既存のseqaを適用する。係数式だけで物理的な帰属を補わない。',
    'seqz':'指定範囲の全物質点について、その点の指定された全出来事でseqyが成り立つ。対象や出来事の存在は推定せず、選ばれた一例の成立で別の例の失敗を隠さない。',
    'sera':'u0260前半の質量結果の適用拡張を、前半と同じ物質点の範囲zrdmaterialにseqzを適用して記述する部分内容。元の数値規約を単位尺度付きで一般化したseqaを共有する。',
}
LIMITS=[
    '対象・出来事ごとの値と、全ての適用事例を指定する範囲を入力として持つ。範囲の完全性、速度や質量の測定、基準系の実現を有限事例から認定しない。',
    '単位校正は同じ質量・力・加速度の単位を、共通基準に対する正の三尺度へ結ぶ入力関係である。基準の力＝基準の質量×基準の加速度という整合性を含む解釈であり、その物理的実現と次元の基礎説明は未展開。',
    '前段のseqwを理由にseraを主張する著者への帰属を加える。任意に小さい電荷を加えられることだけから質量の式を数学的に証明しない。電荷追加時の質量・運動の振舞いと極限での移行に関する物理的な論証は残る。',
    '物質点の基礎説明、ここでいう電子の物理的意味と、原文区間全体の意味一致は未完である。元の電荷追加の可能性と今回の係数結果の内容を同一の述語にまとめない。',
]


def build():
    old=parse((ROOT/PARENT).read_text(encoding='utf-8'));doc=deepcopy(old);doc['statements']=[]
    values={}
    meanings={
        'forceframe':'力数値を定める瞬間共動系','accelerationframe':'加速度数値を定める基準系',
        'massunit':'低速質量の単位','forceunit':'力の単位','accelerationunit':'加速度の単位',
        'light':'光速度の値','speed':'同じ基準系と規約での速度の値','beta':'同じ光速度と速度に対する正のbeta',
        'restmass':'低速質量の値','massscale':'質量単位の尺度','forcescale':'力単位の尺度','accelerationscale':'加速度単位の尺度',
        'longitudinal':'縦の質量係数','transverse':'横の質量係数'}
    for name,sort in META+VALUES:values['zre'+name]=(sort,'同じ物質点・出来事・文脈に対応する'+meanings[name]+'。観測からの決定方法は未展開。')
    values.update(zrerestmassassigned=(RESTMASS,'指定対象・出来事・質量単位・値・文脈への低速質量の帰属。'),
        zrecalibrated=(RELATIONS[-1][1],'指定した三単位と三尺度の共通基準への校正関係。基準の力は基準の質量と加速度の積に整合すると指定する。'),
        zrecases=(SCOPE[-1][1],'同じ物質点・文脈で質量結果を適用する出来事の全範囲。実測済み事例だけに制限しない。'),
        zrenode=('a','u0260前半の質量結果を一般の物質点へ適用する主張箇所。'),
        zrelink=('a','u0260のdennによる電荷追加から質量結果への理由づけの箇所。'),
        zrescope=('a','u0260の同じ物質点の範囲と数値化規約における適用拡張の議論。'))
    text=definitions()+''.join('r '+name+'[] '+sort+'.' for name,(sort,_) in values.items())
    fixed=[v('context'),'p zrdmaterial',k('zrecases')]+[k('zre'+n) for n,_ in META+VALUES]
    fixed+=['p va','p zpa','p zraconvention',k('zrerestmassassigned'),k('zrecalibrated')]
    text+=definition('sera','','b context['+k('seqz',*fixed)+']','e')
    doc=parse(format_graph(doc,'compact')+text)
    new=parse(format_graph(doc,'compact')+
        's[k uh[k zrenode[] k rd[] r[k sera[]] k zrescope[] k ri[]]].'+
        's[k zc[k zrelink[] k rd[] r[k seqw[]] r[k sera[]] k zrescope[] k ri[]]].')['statements']
    doc['statements']=old['statements']+new
    basis=json.loads((ROOT/'data/einstein-arbitrary-small-charge-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-material-mass-extension-basis-v1',document=SOURCE)
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS;lookup={d['name']:d for d in doc['declarations']}
    for name,(_,meaning) in values.items():
        d=lookup[name];basis['primitives'].append(dict(symbol=name,parameters=d['parameters'],result=d['result'],arguments=[],meaning_ja=meaning))
    audit_basis(doc,basis)
    files={SOURCE:format_graph(doc,'compact')+'\n','data/einstein-material-mass-extension-basis-v1.json':basis}
    for path,roots,indices in ((LIBRARY,['seqy','seqz'],[]),(CORE,[],[len(old['statements']),len(old['statements'])+1])):
        selected=extract_document(doc,roots=roots,statement_indices=indices);stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path=path)
    return {p:t if isinstance(t,str) else json.dumps(t,ensure_ascii=False,indent=2)+'\n' for p,t in files.items()}


def main():
    for name,body in build().items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body),flush=True)


if __name__=='__main__':main()
