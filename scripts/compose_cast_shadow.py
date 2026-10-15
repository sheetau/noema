"""Describe source-relative direct-light occlusion and quote a shadow-region property."""
import json
from noema.constructed import parse,format_graph
from scripts.compose_origin_clock import ROOT,definition
from scripts.compose_limits import call as k,app,op,both,quant,v
from scripts.compose_described_apprehension import LIBRARY as AFFECT,RELATIONS as AFFECT_RELATIONS,DESCRIPTION

LIBRARY='examples/v016/cast-shadow.noema'
EXAMPLE='examples/v016/cast-shadow-example.noema'
BASIS='data/cast-shadow-basis-v1.json'
RELATIONS=[('emits','h[a a d] c'),('route','h[a a a d] c'),('otherwiseclear','h[a a d] c'),
    ('intercepts','h[a a d] c'),('opaque','h[a a d] c')]
BASE=[('source','a'),('blocker','a'),('place','a'),('anchor','d')]
FIELDS=BASE+RELATIONS
REGION=[('source','a'),('blocker','a'),('region','a'),('anchor','d'),('contains','h[a a d] c')]+RELATIONS
def params(fields):return ' '.join(n+' '+t for n,t in fields)
def args(fields):return [v(n) for n,t in fields]


def definitions():
    candidate=both(app(v('emits'),v('source'),v('patch'),v('anchor')),
        app(v('route'),v('patch'),v('place'),v('path'),v('anchor')),
        app(v('otherwiseclear'),v('path'),v('blocker'),v('anchor')))
    # route has patch, place and path individual arguments plus the context.
    text=definition('rvp',params(BASE+[('patch','a'),('path','a')]+RELATIONS[:3]),candidate)
    potential=k('rvp',*args(BASE),v('patch'),v('path'),*args(RELATIONS[:3]))
    blocked=both(app(v('intercepts'),v('blocker'),v('path'),v('anchor')),
        app(v('opaque'),v('blocker'),v('path'),v('anchor')))
    exists=lambda body:quant('g','patch','a',quant('g','path','a',body))
    text+=definition('rvq',params(FIELDS),exists(both(potential,blocked)))
    text+=definition('rvr',params(FIELDS),both(k('rvq',*args(FIELDS)),
        quant('f','patch','a',quant('f','path','a',op('y',potential,blocked)))))
    text+=definition('rvs',params(FIELDS),both(k('rvq',*args(FIELDS)),exists(both(potential,op('u',blocked)))))
    member=app(v('contains'),v('region'),v('place'),v('anchor'))
    text+=definition('rvt',params(REGION),both(quant('g','place','a',member),
        quant('f','place','a',op('y',member,k('rvq',*args(FIELDS))))))
    return text


def build():
    library=parse('p:'+definitions())
    affect=parse((ROOT/AFFECT).read_text(encoding='utf-8'))
    text=format_graph(library,'compact')+format_graph(affect,'compact').split(':',1)[1]
    text+='r jysource[] a.r jyblocker[] a.r jyplace[] a.r jyregion[] a.r jyanchor[] d.r jyperson[] a.'
    for name,sort in [('contains','h[a a d] c')]+RELATIONS+AFFECT_RELATIONS:
        text+='r jy'+name+'['+sort[2:sort.rfind(']')]+'] c.'
    ref={n:'k jy'+n+'[]' for n,t in BASE};ref.update({n:'p jy'+n for n,t in RELATIONS})
    region=ref|dict(region='v region',anchor='v point',contains='p jycontains')
    text+=definition('jytopic','region a','b point['+k('rvt',*[region[n] for n,t in REGION])+']','e')
    fear=k('rvm','k jyperson[]','r[p jytopic]','k jyanchor[]',*['p jy'+n for n,t in AFFECT_RELATIONS])
    clear=k('rvn','k jyperson[]','l['+DESCRIPTION+'][r[p jytopic]]','k jyanchor[]',*['p jy'+n for n,t in AFFECT_RELATIONS])
    region['region']='k jyregion[]';region['anchor']='k jyanchor[]'
    questions=[k(symbol,*[ref[n] for n,t in FIELDS]) for symbol in ('rvq','rvr','rvs')]
    questions += [k('rvt',*[region[n] for n,t in REGION]),k('rvo','r[p jytopic]','k jyanchor[]'),fear,clear,
        'e[r['+fear+']][r['+fear+']]']
    text+=''.join('q['+q+'].' for q in questions)
    return {LIBRARY:format_graph(library,'compact')+'\n',EXAMPLE:format_graph(parse(text),'compact')+'\n'}


def basis():
    return dict(status='source_relative_direct_light_shadow_model',definitions={
        'rvp':'同じ光源の発光部分から同じ場所へ至る直接経路があり、指定遮蔽物だけを除けば他の条件はその経路を遮らない。',
        'rvq':'rvpの経路の少なくとも一つに、同じ遮蔽物が介在し、その経路に対して不透明である。指定光源からの直接光の一部または全部を失う条件。',
        'rvr':'rvqに加え、rvpの全経路が同じ遮蔽物で遮られる。候補経路が空である暗さを完全な影とは数えない。',
        'rvs':'rvqに加え、rvpのうち同じ遮蔽物では遮られない経路がある。全遮光と部分遮光を分ける。',
        'rvt':'指定領域に場所があり、その全成員が同じ光源・遮蔽物・文脈のrvqを満たす。領域の最大性や連結性は要求しない。',
        'jytopic':'作例の同じ光源と遮蔽物についてrvtを満たす領域の性質。名詞の綴りでなく、この合成した性質の記述をrvmへ渡す。'},
        inputs={
            'emits':'光源の発光部分と文脈。幾何学的な点があるだけでは発光としない。',
            'route':'発光部分・到達場所・直接経路・文脈の対応。反射・屈折を経る経路をこの直接経路へ混ぜない。',
            'otherwiseclear':'指定遮蔽物を取り除き、他の条件を保持した場合に、その経路を妨げる他の遮蔽がないこと。指定遮蔽物とは無関係な暗さを因果的に帰属しないための比較条件。',
            'intercepts':'指定物体がその直接経路に介在すること。同じ光源へ向かう別経路への介在では代用しない。',
            'opaque':'指定物体がその経路の直接光を透過させないこと。介在だけで不透明とはしない。',
            'contains':'領域と場所の所属。空領域を影の実例としない。'},
        references=[dict(url='https://science.nasa.gov/eclipses/geometry/',role='完全な遮光と部分的な遮光の区別'),
            dict(url='https://openstax.org/books/college-physics-2e/pages/25-1-the-ray-aspect-of-light',role='直線の光線による幾何光学のモデル範囲')],
        limitations=[
            '指定光源からの直接光に相対的な影である。他の光源や反射光が照らしていても成立し得る。周囲より暗いという観測だけではこの条件にならない。',
            '経路と不透明性を用いた幾何光学モデル。回折・散乱・透過率・波長依存、強度の連続量、光学的な画像の形や色は扱わない。',
            '発光・経路・遮蔽・領域は意味規約を持つ入力であり、座標から交点を計算したり物理的な真偽を測定したりする実装ではない。',
            'otherwiseclearは背景を保った比較の入力であり、その現実への適合は別に必要。複数の物体が同時に同じ経路を遮る場合を、単独物体への寄与として数えない。',
            '対象の性質を記述しても、そのような影の領域が現実に存在するとは限らない。情動の検査はこの性質を実行しない。',
            'カントのSchattenの比喩の対象と心理的・政治的含意、発言資格への接続は未完。字義の一構成を原文の完成訳として追加しない。'])


def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists():assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))


if __name__=='__main__':main()
