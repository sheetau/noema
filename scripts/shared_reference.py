"""Explicit referent candidates and compositional presupposition packages."""
from functools import lru_cache
import json
from noema.constructed import format_graph
from noema.constructed_discourse import normalize_document,function_sort
from scripts.shared_modality import ROOT,v,app,call,op
from scripts.shared_time import q,allof

I='individual';S='situation';T='truth';C='content';U='message'
CANDIDATES=function_sort([I,S],T)
ASSIGNMENT=function_sort([I,I,I],T)
TIME_ASSIGNMENT=function_sort([I,I,S],T)
PAIR=function_sort([T],C)
CONSUMER=function_sort([C,U],T)
PACKAGE=function_sort([CONSUMER],T)
LIBRARY='examples/v016/shared-reference-v1.noema'
BASIS='data/shared-reference-basis-v1.json'


def truth(value):
    return op('equal',dict(kind='number',numerator=0,denominator=1),dict(kind='number',numerator=0 if value else 1,denominator=1))
def evaluate(content,world=None):return dict(kind='evaluate',content=content,situation=v('world') if world is None else world)
def content(body):return dict(kind='content',variable='world',body=body)
def lam(parameters,body):return dict(kind='lambda',parameters=[dict(name=n,sort=t) for n,t in parameters],body=body)
def definition(name,parameters,result,body):
    return dict(kind='definition',name=name,parameters=[dict(name=n,sort=t) for n,t in parameters],result=result,body=body)
def member(name):return app('candidates',v(name),v('world'))
def part(pair,background):return call('presupposed' if background else 'atissue',v(pair))


@lru_cache(maxsize=1)
def raw():
    defs=[]
    def add(name,params,result,body):defs.append(definition(name,params,result,body))
    base=[('candidates',CANDIDATES),('world',S)]
    add('referenceexists',base,T,q('exists','referent',I,member('referent')))
    add('referencemissing',base,T,op('not',call('referenceexists',v('candidates'),v('world'))))
    only=q('forall','other',I,op('implies',member('other'),op('equal',v('referent'),v('other'))))
    add('referencevalue',base+[('referent',I)],T,op('and',member('referent'),only))
    add('referenceunique',base,T,q('exists','referent',I,call('referencevalue',v('candidates'),v('world'),v('referent'))))
    add('referenceambiguous',base,T,q('exists','referent',I,q('exists','other',I,
        allof(member('referent'),member('other'),op('not',op('equal',v('referent'),v('other')))))))
    for name,target,relation in (('individualrole',I,ASSIGNMENT),('situatedrole',S,TIME_ASSIGNMENT)):
        params=[('context',I),('role',I),('target',target),('assignment',relation)]
        match=app('assignment',v('context'),v('role'),v('target'))
        only=q('forall','other',target,op('implies',app('assignment',v('context'),v('role'),v('other')),
                                                    op('equal',v('target'),v('other'))))
        add(name,params,T,op('and',match,only))
    params=[('mention',I),('context',I),('referent',I),('accessible',ASSIGNMENT),('denotes',ASSIGNMENT),('compatible',ASSIGNMENT)]
    add('anaphoriccandidate',params,T,q('exists','antecedent',I,allof(
        app('accessible',v('mention'),v('antecedent'),v('context')),
        app('denotes',v('antecedent'),v('referent'),v('context')),
        app('compatible',v('mention'),v('referent'),v('context')))))
    choose=op('or',op('and',v('background'),evaluate(v('presupposition'))),
                   op('and',op('not',v('background')),evaluate(v('issue'))))
    add('presupposition',[('presupposition',C),('issue',C)],PAIR,lam([('background',T)],content(choose)))
    for name,flag in (('presupposed',True),('atissue',False)):
        add(name,[('pair',PAIR)],C,app('pair',truth(flag)))
    pre=evaluate(part('pair',True));issue=evaluate(part('pair',False))
    for name,body in (('licensedpositive',op('and',pre,issue)),('licensednegative',op('and',pre,op('not',issue))),('unsupported',op('not',pre))):
        add(name,[('pair',PAIR),('world',S)],T,body)
    params=[('candidates',CANDIDATES),('property',CANDIDATES)]
    defined=content(call('referenceunique',v('candidates'),v('world')))
    predicated=content(q('exists','referent',I,op('and',member('referent'),app('property',v('referent'),v('world')))))
    add('definitestatement',params,PAIR,call('presupposition',defined,predicated))
    add('presuppnegate',[('pair',PAIR)],PAIR,call('presupposition',part('pair',True),content(op('not',evaluate(part('pair',False))))))
    params=[('left',PAIR),('right',PAIR)]
    p1,p2=evaluate(part('left',True)),evaluate(part('right',True))
    a1,a2=evaluate(part('left',False)),evaluate(part('right',False))
    filtered=op('and',p1,op('implies',a1,p2))
    for name,presupposed,issue in (
        ('presuppif',filtered,op('implies',a1,a2)),
        ('presuppglobalif',op('and',p1,p2),op('implies',a1,a2)),
        ('presuppand',filtered,op('and',a1,a2))):
        add(name,params,PAIR,call('presupposition',content(presupposed),content(issue)))
    add('speechpackage',[('presupposition',C),('act',U)],PACKAGE,
        lam([('consumer',CONSUMER)],app('consumer',v('presupposition'),v('act'))))
    add('speechvalid',[('package',PACKAGE),('world',S)],T,
        app('package',lam([('background',C),('act',U)],evaluate(v('background')))))
    add('speechmatches',[('package',PACKAGE),('act',U)],T,
        app('package',lam([('background',C),('stored',U)],op('equal',v('stored'),v('act')))))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=defs,statements=[])


@lru_cache(maxsize=1)
def composed():return normalize_document(raw())


MEANINGS={
 'referenceexists':'同じ評価状況に参照候補が少なくとも一つある。',
 'referencemissing':'同じ評価状況に参照候補がない。候補情報の未提供ではない。',
 'referencevalue':'指定個体が同じ状況で唯一の参照候補である。',
 'referenceunique':'同じ状況で唯一の参照候補が存在する。',
 'referenceambiguous':'同じ状況に異なる参照候補が二つ以上ある。',
 'individualrole':'同じ文脈・役割に対象個体が一意に割り当てられる。',
 'situatedrole':'同じ文脈・役割に対象状況が一意に割り当てられる。',
 'anaphoriccandidate':'同じ文脈でアクセス可能な先行箇所が対象を指し、現在の言及もその対象への適合条件を満たす。',
 'presupposition':'前提内容と主張・問いの対象内容を一組にする。真の選択子で前提、偽で対象内容を返す関数として表現する。',
 'presupposed':'組に保存された前提内容を取得する。',
 'atissue':'組に保存された主張・問いの対象内容を取得する。',
 'licensedpositive':'指定状況で前提と対象内容がともに成立する。',
 'licensednegative':'指定状況で前提が成立し、対象内容が成立しない。',
 'unsupported':'指定状況で前提が成立しない。対象内容が偽だという判定や、関係の情報不足とは区別する。',
 'definitestatement':'候補の一意性を前提とし、その同じ候補が指定性質を満たすことを対象内容とする。',
 'presuppnegate':'前提を保存して対象内容だけを否定する。',
 'presuppif':'左の前提と、左の対象内容が成立する場合の右の前提を要求する。対象内容は左から右への含意。',
 'presuppglobalif':'左右の前提をともに要求し、左から右への含意を対象内容とする。',
 'presuppand':'左の前提と、左の対象内容が成立する場合の右の前提を要求する。対象内容は左右の論理積。',
 'speechpackage':'前提内容と発話値を同じ組に保存し、その二値を受け取る判定関数へ渡す。',
 'speechvalid':'保存した発話の前提が指定状況で成立する。発話内容や回答の成立は要求しない。',
 'speechmatches':'保存した発話値の働きと内容が指定の発話値と等しい。話者や文言の同一性ではない。'}
ROLES={
 'candidates':'文脈と記述に適合する参照候補の全範囲。候補不明を空としない。',
 'world':'判定する同じ評価状況。','referent':'判定する候補個体。',
 'context':'発話または引用・報告で採用した指示文脈。','role':'話者・場所・時点等の指定役割。',
 'target':'役割に割り当てる個体または状況。','assignment':'文脈・役割・対象の対応。一意性は定義で検査する。',
 'mention':'現在の言及箇所。','accessible':'現在箇所・先行箇所・文脈のアクセス可能性。談話規則を明示する。',
 'denotes':'先行箇所・対象・文脈の指示対応。','compatible':'現在箇所・対象・文脈が性数等の指定適合条件を満たすこと。',
 'presupposition':'前提となる内容。','issue':'主張・問いの対象となる内容。','pair':'前提と対象内容の組。',
 'property':'同じ候補について述べる性質。参照候補の選定とは別の関係。',
 'left':'順序付き結合の左側の組。','right':'順序付き結合の右側の組。',
 'act':'既存の主張・問い・指示の発話値。','package':'前提と発話値を保持する組。'}


def basis():
    return dict(status='shared_reference_and_presupposition',document=LIBRARY,primitives={},definitions=MEANINGS,
        public_contracts={d['name']:dict(arguments=[dict(role=p['name'],sort=p['sort'],interpretation=ROLES[p['name']])
            for p in d['parameters']],result=d['result']) for d in raw()['declarations']},
        design_sources=[dict(path='docs/cross-reference-v1.md',relation='rqso',reuse='文脈条件内の存在・一意性の構成。引数を一般化し、本体一致は主張しない。'),
                        dict(path='docs/cover-reference-v1.md',relation='ryr',reuse='先行箇所と対象と文脈の接続を保つ。自動的な先行詞選択は行わない。'),
                        dict(path='docs/spec-v010.md',reuse='主張・問い・指示の働きを区別する既存発話型。')],
        limitations=['前提の投射は明示した読みを選び、自然言語から自動推測しない。',
                    '関係が未知なら実行器は停止する。前提不成立と未知は同一ではない。',
                    '照応の候補選定、役割対応、社会的前提の採否は明示的な解釈入力。',
                    '省略補完、読みの選択履歴、円文字の共有語彙登録、第三者読解は未完。'])


def prepare():
    for path,text in ((LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')):
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published reference module differs: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':prepare()
