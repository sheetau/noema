"""Apply the kinetic-energy expression with explicit owners and unit scales."""
from copy import deepcopy
import json
from noema.grammar import parse, format_graph
from noema.extraction import extract_document, extract_basis
from noema.meaning_basis import audit_basis
from scripts.compose_convention_comparison import ROOT, CUT
from scripts.compose_force_mass_units import RESTMASS
from scripts.compose_origin_clock import definition, v
from scripts.compose_limits import call as k, app, both, op, quant, ZERO
from scripts.compose_situated_criticism import params, args

PARENT = 'examples/v014/einstein-energy-boundary.noema'
SOURCE = 'examples/v014/einstein-material-energy-extension.noema'
LIBRARY = 'examples/v014/material-energy-extension.noema'
CORE = 'examples/v014/material-energy-extension-core.noema'
READING = 'data/material-energy-extension-reading-v1.json'
NUMERIC = 'light speed beta restmass energy massscale speedscale energyscale'
META = [(n, 'h[a a d] a') for n in ('frame', 'massunit', 'speedunit', 'energyunit')]
VALUES = [(n, 'h[a a d] '+CUT) for n in NUMERIC.split()]
RELATIONS = [('framevalid', 'h[a] c'), ('restmassassigned', RESTMASS),
             ('speedassigned', 'h[a a a a '+CUT+' d] c'),
             ('lightassigned', 'h[a a a '+CUT+' d] c'),
             ('kinetic', 'h[a a a a '+CUT+' d] c'),
             ('calibrated', 'h[a a a '+CUT+' '+CUT+' '+CUT+' d] c')]
FIELDS = META+VALUES+RELATIONS
SCOPE = [('materials', 'h[a d] c'), ('cases', 'h[a a d] c')]
SOURCE_SYMBOLS = {
    'frame': 'zreaccelerationframe', 'massunit': 'zremassunit',
    'light': 'zrelight', 'speed': 'zrespeed', 'beta': 'zrebeta',
    'restmass': 'zrerestmass', 'massscale': 'zremassscale',
    'restmassassigned': 'zrerestmassassigned', 'kinetic': 'zrgkinetic',
}


def definitions():
    text = ''
    for real, name in ((False, 'sete'), (True, 'setf')):
        typ = CUT if real else 'b'; fields = [(n, typ) for n in NUMERIC.split()]
        light, speed, beta, mass, energy, M, S, E = args(fields)
        mul = lambda a, b: k('shv' if real else 'ad', a, b)
        zero = k('bb', ZERO) if real else ZERO
        valid = [k('ba', x) for x in args(fields)] if real else []
        text += definition(name, params(fields), both(*valid,
            *[k('bg' if real else 'aa', zero, scale) for scale in (M, S, E)],
            k('serc' if real else 'serb', mul(light, S), mul(speed, S), beta, mul(mass, M), mul(energy, E))))
    point, event, context = map(v, ('point', 'event', 'context'))
    value = lambda name: app(v(name), point, event, context)
    text += definition('setg', params([('point', 'a'), ('event', 'a'), ('context', 'd')]+FIELDS), both(
        app(v('framevalid'), value('frame')),
        app(v('restmassassigned'), point, event, value('massunit'), value('restmass'), context),
        app(v('speedassigned'), point, value('frame'), event, value('speedunit'), value('speed'), context),
        app(v('lightassigned'), value('frame'), event, value('speedunit'), value('light'), context),
        app(v('kinetic'), point, value('frame'), event, value('energyunit'), value('energy'), context),
        app(v('calibrated'), *[value(n) for n in ('massunit', 'speedunit', 'energyunit', 'massscale', 'speedscale', 'energyscale')], context),
        k('setf', *[value(n) for n in NUMERIC.split()])) )
    text += definition('seth', params([('context', 'd')]+SCOPE+FIELDS), quant('f', 'point', 'a',
        op('y', app(v('materials'), point, context), quant('f', 'event', 'a',
            op('y', app(v('cases'), point, event, context), k('setg', point, event, context, *args(FIELDS)))))))
    return text


MEANINGS = {
    'sete': '同じ速度単位で表した光速度と速さ、低速質量、運動エネルギーを共通基準へ換算し、既存serbを適用する有理数条件。三尺度は正で、energy*energyscale=restmass*massscale*(light*speedscale)^2*(beta-1)。',
    'setf': 'seteの実切断版。既存sercによる正の質量、非負で光速未満の速度、正規化betaを保持する。',
    'setg': '同じ物質点・出来事・文脈について、基準系、質量・速度・エネルギー単位、値の帰属、単位校正、setfの式を結ぶ。値だけが合っていても、別の対象・時点・基準系の量へ置換しない。',
    'seth': '指定された全物質点について、それぞれの全適用事例でsetgを要求する。対象や事例の存在は推定しない。',
    'seti': 'u0264の運動エネルギー式の適用拡張。前段と同じ物質点の範囲、質量・速度・基準系の対応関数とエネルギー帰属を再利用し、エネルギーの適用事例と単位校正を明示する。',
}
LIMITS = [
    '式の最右辺の運動エネルギー表現を適用する。原刊の中間積分に質量係数がない点は修正せず、先行する原文保存と質量を含む候補を維持する。',
    '単位尺度は共通の基準のエネルギー単位が質量単位と速度単位の二乗に整合することを含む校正入力である。測定・物理的実現・次元の基礎説明は未展開。',
    '物質点の範囲は前段と同じzrdmaterialを使う。エネルギーの適用事例は力の係数の適用事例と区別し、観測済みの少数例だけに制限しない。',
    '上の議論を理由とするという著者の記述を、任意に小さい電荷追加の内容seqwからsetiへの推論帰属として結ぶ。電荷追加の可能性からエネルギー式を数学的に証明したとはしない。',
    '原文のmußは推論としての必然性を提示するものと読み、行為者への命令や規範にはしない。理由の妥当性、電荷を零へ近づける物理的極限と原文全体の意味一致は未完。',
]


def build():
    old = parse((ROOT/PARENT).read_text(encoding='utf-8')); doc = deepcopy(old); doc['statements'] = []
    descriptions = {
        'speedunit': '同じ物質点・出来事・文脈の光速度と速さを表す共通単位。',
        'energyunit': '同じ物質点・出来事・文脈の運動エネルギーの単位。',
        'energy': '同じ物質点・出来事・文脈に対応する運動エネルギーの値。帰属は既存zrgkineticへ結ぶ。',
        'speedscale': '速度単位の共通基準に対する正の尺度。光速度と物体の速さへ同じ尺度を使う。',
        'energyscale': 'エネルギー単位の共通基準に対する正の尺度。',
        'speedassigned': '同じ物質点・基準系・出来事・速度単位・値・文脈への速さの帰属。',
        'lightassigned': '同じ基準系・出来事・速度単位・値・文脈への光速度の帰属。',
        'calibrated': '質量・速度・エネルギーの三単位と尺度を、エネルギー=質量×速度二乗という共通基準の関係へ結ぶ校正入力。',
        'cases': '同じ物質点・文脈で運動エネルギーの式を適用する出来事の全範囲。力の係数の適用事例とは区別する。',
    }
    values = {'zrk'+n: (sort, descriptions[n]) for n, sort in FIELDS+SCOPE if n in descriptions}
    values.update(zrknode=('a', 'u0264の物質点への運動エネルギー式の適用を述べる箇所。'),
                  zrklink=('a', 'u0264で上の議論を理由として参照する箇所。'),
                  zrkscope=('a', 'u0264で前段と共有する物質点の範囲とエネルギーの数値化規約。'))
    additions = definitions()+''.join('r '+n+'[] '+sort+'.' for n, (sort, _) in values.items())
    fixed = [v('context'), 'p zrdmaterial', k('zrkcases')]
    fixed += ['p va' if n == 'framevalid' else k(SOURCE_SYMBOLS.get(n, 'zrk'+n)) for n, _ in FIELDS]
    additions += definition('seti', '', 'b context['+k('seth', *fixed)+']', 'e')
    doc = parse(format_graph(doc, 'compact')+additions)
    claims = 's['+k('uh', k('zrknode'), k('rd'), 'r['+k('seti')+']', k('zrkscope'), k('ri'))+'].'
    claims += 's['+k('zc', k('zrklink'), k('rd'), 'r['+k('seqw')+']', 'r['+k('seti')+']', k('zrkscope'), k('ri'))+'].'
    doc['statements'] = old['statements']+parse(format_graph(doc, 'compact')+claims)['statements']
    basis = json.loads((ROOT/'data/einstein-energy-boundary-basis-v1.json').read_text(encoding='utf-8'))
    basis.update(version='einstein-material-energy-extension-basis-v1', document=SOURCE)
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    lookup = {d['name']: d for d in doc['declarations']}
    for name, (_, meaning) in values.items():
        d=lookup[name]; basis['primitives'].append(dict(symbol=name, parameters=d['parameters'], result=d['result'], arguments=[], meaning_ja=meaning))
    audit_basis(doc, basis)
    files = {SOURCE: format_graph(doc, 'compact')+'\n', 'data/einstein-material-energy-extension-basis-v1.json': basis}
    for path, roots, indices in ((LIBRARY, ['sete', 'setf', 'setg', 'seth'], []), (CORE, ['sete'], [len(old['statements']), len(old['statements'])+1])):
        selected=extract_document(doc, roots=roots, statement_indices=indices); stem=path.rsplit('/',1)[1][:-6]
        files[path]=format_graph(selected.document,'compact')+'\n'
        files['data/'+stem+'-basis-v1.json']=extract_basis(doc,basis,selected,version=stem+'-basis-v1',document_path=path)
    return {p: body if isinstance(body,str) else json.dumps(body,ensure_ascii=False,indent=2)+'\n' for p,body in files.items()}


def main():
    for path, body in build().items():
        destination=ROOT/path
        if destination.exists(): assert destination.read_text(encoding='utf-8')==body,path
        else:
            with destination.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(path,len(body),flush=True)


if __name__=='__main__': main()
