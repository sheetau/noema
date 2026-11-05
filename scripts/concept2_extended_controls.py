"""Small native-typed witnesses, independent of the Kant text and glyph encoder."""
from copy import deepcopy
from scripts.kant_type_grammar import BASE_TYPES


def cases(codec,a,b,p):
    def v(name):return dict(kind='variable',name=name)
    def num(n,d=1):return dict(kind='number',numerator=n,denominator=d)
    def eq(a,b):return dict(kind='equal',arguments=[a,b])
    def both(a,b):return dict(kind='and',arguments=[a,b])
    def call(name,*args):return dict(kind='call',symbol=name,arguments=list(args))
    def lam(types,slot=0):return dict(kind='lambda',parameters=[dict(name='x'+chr(97+i),sort=t) for i,t in enumerate(types)],body=v('x'+chr(97+slot)) if types else num(0))
    def quote(body,rank=None):return dict(kind='quote',body=body,**({'rank':rank} if rank is not None else {}))
    def quant(kind,name,sort,body):return dict(kind=kind,variable=name,sort=sort,body=body)
    types=list(BASE_TYPES)+[
        dict(kind='sequence',element='number'),dict(kind='description',result='truth'),
        dict(kind='description',rank=2,result='individual'),dict(kind='question',parameters=[]),
        dict(kind='question',parameters=['individual','number']),dict(kind='function',parameters=[],result='truth'),
        dict(kind='function',parameters=['individual','number'],result='situation'),
        dict(kind='sequence',element=dict(kind='description',rank=1,result=dict(kind='question',parameters=['number']))),
        dict(kind='function',parameters=[dict(kind='sequence',element='number'),dict(kind='description',rank=2,result='truth')],result=dict(kind='question',parameters=['message']))]
    rows=[]
    def add(key,title,body,kind='assert'):
        source=codec.validate_native(dict(kind=kind,body=deepcopy(body)))
        rows.append(dict(key=key,title=title,source=source))
    for i,t in enumerate(types):add('type-'+str(i),'型を保つ束縛 '+str(i+1),quant('forall' if i%2==0 else 'exists','x',t,eq(v('x'),v('x'))))
    for i,ts in enumerate(([],['number'],['individual']*2,['individual','number','situation'],[types[-1],types[-2]])):
        for slot in range(max(1,len(ts))):
            f=lam(ts,slot);add(f'lambda-{i}-{slot}',f'型列 {i+1}・引数 {slot+1}',eq(f,f))
    outer=lam(['number','individual']);outer['body']=v('x')
    add('outer-reference','複数引数lambdaから外側を参照',quant('forall','x','situation',eq(outer,outer)))
    nested=both(quant('exists','x','number',eq(v('x'),v('x'))),eq(v('x'),v('x')))
    add('shadow-return','同名束縛の終了後に外側へ戻る',quant('forall','x','individual',nested))
    add('quote-binding','引用ごとに複数束縛を分離',eq(quote(lam(['number','individual'])),quote(lam(['number','individual']))))
    for slot in (0,1,2):
        f=lam(['number','number','number'],slot)
        add('apply-slot-'+str(slot),'複数適用・第'+str(slot+1)+'引数',eq(dict(kind='apply',function=f,arguments=[num(11),num(22),num(33)]),num((11,22,33)[slot])))
    seq=dict(kind='sequence',element='number',items=[num(1),num(2)])
    empty=dict(kind='sequence',element='number',items=[])
    content=dict(kind='content',variable='world',body=eq(num(1),num(1)))
    message=dict(kind='message',force='direct',content=content)
    pred=dict(kind='lambda',parameters=[dict(name='x',sort='number')],body=eq(v('x'),num(1)))
    expressions=[
        ('negative-rational',eq(num(-7,3),num(-14,6))),
        ('empty-sequence',eq(empty,empty)),('sequence',eq(seq,seq)),
        ('length',eq(dict(kind='length',sequence=seq),num(2))),
        ('position',dict(kind='position',sequence=seq,index=num(0),value=num(1))),
        ('concat',eq(dict(kind='concat',left=seq,right=empty),seq)),
        ('fold',eq(dict(kind='fold',sequence=seq,initial=num(0),step=lam(['number','number'],1)),num(2))),
        ('disquote',eq(dict(kind='disquote',description=quote(num(1))),num(1))),
        ('ranked-disquote',eq(quote(dict(kind='disquote',description=quote(num(1)),rank=0),1),quote(num(1),1))),
        ('quoted-lift',eq(dict(kind='quoted_lift',description=quote(num(1))),quote(quote(num(1))))),
        ('quoted-application',eq(dict(kind='quoted_application',function=quote(lam(['number'])),arguments=[quote(num(2))]),quote(dict(kind='apply',function=lam(['number']),arguments=[num(2)])))),
        ('answer-matches',dict(kind='answer_matches',question=dict(kind='question',function=pred),arguments=[num(1)])),
        ('message-content',eq(dict(kind='message_content',message=message),content)),
        ('evaluate',quant('forall','world','situation',dict(kind='evaluate',content=content,situation=v('world')))),
        ('function-reference',dict(kind='apply',function=dict(kind='function_ref',symbol=p),arguments=[call(a)])),
        ('empty-application',eq(dict(kind='apply',function=lam([]),arguments=[]),num(0))),
    ]
    for key,body in expressions:add(key,'構文対照：'+key,body)
    for kind in ('not','or','implies','iff'):
        args=[eq(num(1),num(1))]
        if kind!='not':args.append(eq(num(1),num(2)))
        add('logic-'+kind,'論理結合：'+kind,dict(kind=kind,arguments=args))
    add('ask','質問を発する',dict(kind='question',function=pred),'ask')
    for force in ('assert','ask','direct'):add('perform-'+force,'メッセージの力：'+force,dict(kind='message',force=force,content=content),'perform')
    return rows
