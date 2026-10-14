"""Bind the isolated source formula to matter, event and ordered frames."""
from copy import deepcopy
import json

from noema.extraction import extract_document,extract_basis
from noema.grammar import parse,format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT,definition,v
from scripts.compose_limits import call as k,app,both
from scripts.compose_situated_criticism import params,args
from scripts.compose_density_formula import FORMULA,PARTIALS,CUT,FIELD,REGION,POINT,ROLES
from scripts.compose_density_boost import FRAMES

PARENT='examples/v014/einstein-density-formula.noema'
ASSIGN='h[a a a '+(' '.join([CUT]*4))+' d] c'
ELECTRIC='h[a '+FIELD+' '+REGION+' d] c'
REFERENTS=[('matter','a'),('event','a'),('oldframe','a'),('newframe','a'),('context','d'),('oldpoint',POINT),
    ('assigned',ASSIGN),('electricassigned',ELECTRIC),('frames',FRAMES)]
INPUTS=PARTIALS+REFERENTS
BINDINGS=[pair for pair in INPUTS if pair[0]!='newelectricjet']
ROOTS=['senu','senv']
MEANINGS={
    'senu':'同じ物質・出来事・文脈について、新旧二系の地点と、規格化密度・三速度成分の割当を結ぶ。順序付きの二系配置と符号付き速度、正のbeta、同じ出来事の四座標変換、新系の電場と領域の割当を保持する。五つの等式の成立や磁場は要求しない。',
    'senv':'senuの参照先と、M0390の五つの等式および新電場の必要な三偏微分sentを同じ引数で結ぶ。数値が一致する別の物体・出来事・系の量に置き換えない。',
}
LIMITS=[
    'assignedは物質・系・出来事・規格化密度・三速度成分・文脈を結ぶ関係引数である。値の一致から帰属を推定せず、関係の解釈を供給しなければ評価しない。',
    'electricassignedは新系・電場・領域・文脈への割当である。既存の磁場を含むznnや旧場の方程式を使わず、この数式で必要な電場だけを結ぶ。',
    '同じ出来事の新旧座標はs46の標準配置の変換で結ぶ。等しい時刻や同じ座標値を同じ出来事の代用にしない。原点をずらす一般の座標設定はこの標準配置に含めない。',
    'これは式の参照を明示する接続条件である。本文で特定の配置を導入する著者の提示、規格化された電気密度と物理的電荷の共有された意味、測定の実現は未完。先行する確認記録を完成へ昇格しない。',
]


def source_composed():
    doc=parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis=deepcopy(json.loads((ROOT/'data/einstein-density-formula-basis-v1.json').read_text(encoding='utf-8')))
    statements,doc['statements']=doc['statements'],[]
    conditions=[k('srd',v('light'),v('speed'),v('beta')),
        app(v('frames'),v('oldframe'),v('newframe'),v('speed'),v('context'))]
    for prefix,point,rho,vel in (('old','oldpoint','density',('ux','uy','uz')),('new','point','newdensity',('vx','vy','vz'))):
        conditions += [k('va',v(prefix+'frame')),
            k('zpb',v('matter'),v(prefix+'frame'),v('event'),v(point),v('context')),
            app(v('assigned'),v('matter'),v(prefix+'frame'),v('event'),v(rho),*map(v,vel),v('context'))]
        conditions += [k('ba',app(v(point),k(axis))) for axis in ROLES]
    conditions += [app(v('electricassigned'),v('newframe'),v('newfield'),v('region'),v('context')),
        app(v('region'),*(app(v('point'),k(axis)) for axis in ROLES))]
    transformed=k('s46',v('light'),v('speed'),v('oldpoint'))
    conditions += [k('sca',app(v('point'),k(axis)),app(transformed,k(axis))) for axis in ROLES]
    text=definition('senu',params(BINDINGS),both(*conditions))
    text+=definition('senv',params(INPUTS),both(k('senu',*args(BINDINGS)),k('sent',*args(PARTIALS))))
    doc=parse(format_graph(doc,'compact')+text);doc['statements']=statements
    basis.update(version='einstein-density-referents-basis-v1',document='examples/v014/einstein-density-referents.noema')
    basis['definitions'].update(MEANINGS);basis['unresolved']+=LIMITS
    audit_basis(doc,basis)
    return format_graph(doc,'compact')+'\n',basis


def core_composed():
    text,basis=source_composed();doc=parse(text)
    selected=extract_document(doc,roots=ROOTS,statement_indices=[])
    basis=extract_basis(doc,basis,selected,version='density-referents-core-basis-v1',document_path='examples/v014/density-referents-core.noema')
    return format_graph(selected.document,'compact')+'\n',basis

BUILDERS=((source_composed,'einstein-density-referents'),(core_composed,'density-referents-core'))


def main():
    for builder,stem in BUILDERS:
        text,basis=builder()
        for name,body in ((basis['document'],text),('data/'+stem+'-basis-v1.json',json.dumps(basis,ensure_ascii=False,indent=2)+'\n')):
            path=ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8')!=body:raise ValueError('Stored referents differ: '+name)
            else:
                with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(stem,len(text),'characters')


if __name__=='__main__':main()
