"""Small scope/geometry witnesses, separate from the Kant source text."""
from copy import deepcopy
from scripts import concept2_composition as c


def controls(dictionary,a,b,p):
    def word(name):return dict(form='word',parts=dictionary['selected_spellings'][name])
    def call(name,*args):return dict(kind='call',symbol=word(name),arguments=list(args))
    def native(name,*args):return dict(kind='call',symbol=name,arguments=list(args))
    def binary(kind,a,b):return dict(kind=kind,arguments=[a,b])
    def eq(a,b):return binary('equal',a,b)
    def both(a,b):return binary('and',a,b)
    def scope(body,quotation=False):return dict(form='scope',quotation=quotation,body=body)
    def role(v):return dict(form='role-definition',lane=-1,value=v)
    use=dict(form='role-use',lane=-1)
    av,bv=call(a),call(b);an,bn=native(a),native(b)
    def exists(body):return dict(kind='exists',variable='va',sort='individual',body=body)
    def quote(body):return dict(kind='quote',body=body)
    def pair(v):return eq(dict(form='dot-definition',label=0,value=v),dict(form='dot-use',label=0))
    def var(name):return dict(kind='variable',name=name)
    def lam(body):return dict(kind='lambda',parameters=[dict(name='va',sort='individual')],body=body)
    def apply(f,x):return dict(kind='apply',function=f,arguments=[x])
    examples=[
        ('段の上書きと復帰',
         both(eq(role(av),av),both(exists(scope(eq(role(bv),use))),eq(use,av))),
         both(eq(an,an),both(exists(eq(bn,bn)),eq(an,an)))),
        ('引用ごとの独立した宣言',
         eq(quote(scope(eq(role(av),use),True)),quote(scope(eq(role(bv),use),True))),
         eq(quote(eq(an,an)),quote(eq(bn,bn)))),
        ('同じドット識別形を順に二対使う',both(pair(av),pair(bv)),both(eq(an,an),eq(bn,bn))),
        ('語の略記は適用先を取り込まない',
         both(dict(kind='call',symbol=dict(form='word-definition',label=0,parts=dictionary['selected_spellings'][p]),arguments=[av]),
              dict(kind='call',symbol=dict(form='word-use',label=0),arguments=[bv])),
         both(native(p,an),native(p,bn))),
        ('未充足の役割を引数で埋める',apply(lam(call(p,var('va'))),av),apply(lam(native(p,var('va'))),an)),
        ('外側と内側の束縛を区別する',
         exists(dict(kind='forall',variable='vb',sort='individual',body=eq(var('va'),var('vb')))),
         exists(dict(kind='forall',variable='vb',sort='individual',body=eq(var('va'),var('vb'))))),
    ]
    result=[]
    for title,body,expected in examples:
        plan=scope(dict(kind='assert',body=deepcopy(body)),True)
        expected=dict(kind='assert',body=expected)
        assert c.expand_plan(plan,dictionary)==expected,title
        drawing=c.compile_units(c.plan_units(plan))
        result.append(dict(title=title,plan=plan,expected=expected,drawing=drawing))
    return result


def geometry_controls():
    result=[]
    for side in (-1,1):
        for contact in (False,True):
            for sectors in ((1,), (0,1,6,7), tuple(range(8))):
                outside=set(sectors)-({3,4} if side<0 else {7,0})
                if outside:result.append((f'中大円：向き{side}・接触側90度{int(contact)}・外側{len(outside)}区間',c.eclipse(side,contact,sectors)))
    for direction in range(8):result.append((f'中心からの方向 {direction*45}°',c.direction_shape(direction)))
    for side in (-1,1):
        for lane in (-1,1):
            result.append((f'大円の斜め端 → 小円：左右{side}・上下{lane}',c.large_link_shape(side,lane)))
    for lanes in ((-1,1),(-1,0,1)):
        a,b=c.continuation_witness(lanes)
        result.append((f'{len(lanes)}段の改行：行末／次行頭',a+c.move(b,180)))
    for title,shapes in result:c.ink_check(shapes)
    return result
