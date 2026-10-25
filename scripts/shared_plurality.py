"""Finite groups, shared events, object assignments and explicit reciprocals."""
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,sequence_sort
from scripts.shared_modality import ROOT,v,app,call,op,renamed
from scripts.shared_reference import I,S,T,truth,lam,definition
from scripts.shared_time import q,allof
from scripts.shared_readings import num

N='number'; MEMBERS=sequence_sort(I)
GROUP=function_sort([I],T); PAIR=function_sort([I,I],T)
TRACE=function_sort([I,S],T); RELATION=function_sort([I,I,S],T)
CHOICE=function_sort([I],I)
SOURCE='examples/v014/scoped-groups.noema'
NAMES={'rp':'coveredgroups','rr':'collectiveaction'}
LIBRARY='examples/v016/shared-plurality-v1.noema'
BASIS='data/shared-plurality-basis-v1.json'
ACTION=[('context',S),('occurs',TRACE),('participates',RELATION),('affects',RELATION)]
OBJECTS=[('actors',GROUP),('targets',GROUP)]+ACTION
OLD_PARAMS={'coveredgroups':[('actors',GROUP),('targets',GROUP),('relation',PAIR)],
            'collectiveaction':[('actors',GROUP),('context',S),('occurs',TRACE),('participates',RELATION)]}


def seq(*items):return dict(kind='sequence',element=I,items=list(items))
def fold(sequence,initial,parameters,body):
    return dict(kind='fold',sequence=sequence,initial=initial,step=lam(parameters,body))
def apply_expr(function,*args):return dict(kind='apply',function=function,arguments=list(args))
def neq(a,b):return op('not',op('equal',a,b))
def each(group,name,body):return q('forall',name,I,op('implies',app(group,v(name)),body))
def some(group,name,body):return q('exists',name,I,op('and',app(group,v(name)),body))
def args(ps):return [v(n) for n,t in ps]
def act(actor,target):return call('actionobject',actor,v('event'),target,*args(ACTION))
def acts(actor,target):return q('exists','event',I,act(actor,target))


@lru_cache(maxsize=1)
def raw():
    old=parse((ROOT/SOURCE).read_text(encoding='utf-8'))
    defs=[renamed(d,NAMES) for d in old['declarations'] if d['name'] in NAMES]
    def add(name,params,body,result=T):defs.append(definition(name,params,result,body))
    add('memberof',[('members',MEMBERS),('member',I)],fold(v('members'),truth(False),[('found',T),('item',I)],
        op('or',v('found'),op('equal',v('item'),v('member')))))
    # Fold constructs checks against the already visited suffix; no arithmetic
    # primitive, number-domain enumeration, deduplication or hidden host set.
    CHECK=function_sort([MEMBERS],T)
    appended=dict(kind='concat',left=v('later'),right=seq(v('item')))
    step=lam([('later',MEMBERS)],op('and',op('not',call('memberof',v('later'),v('item'))),app('check',appended)))
    checks=fold(v('members'),lam([('later',MEMBERS)],truth(True)),[('check',CHECK),('item',I)],step)
    add('distinctmembers',[('members',MEMBERS)],apply_expr(checks,seq()))
    add('membercount',[('members',MEMBERS),('count',N)],op('and',call('distinctmembers',v('members')),
        op('equal',dict(kind='length',sequence=v('members')),v('count'))))
    add('groupexists',[('group',GROUP)],q('exists','member',I,app('group',v('member'))))
    add('groupincludes',[('group',GROUP),('included',GROUP)],each('included','member',app('group',v('member'))))
    add('groupall',[('group',GROUP),('property',GROUP)],op('and',call('groupexists',v('group')),
        each('group','member',app('property',v('member')))))
    add('groupplural',[('group',GROUP)],some('group','member',some('group','other',neq(v('member'),v('other')))))
    injection=each('group','member',each('group','other',op('implies',neq(v('member'),v('other')),
        neq(app('assignment',v('member')),app('assignment',v('other'))))))
    add('groupinjection',[('group',GROUP),('assignment',CHOICE)],injection)
    participation=op('and',app('occurs',v('event'),v('context')),app('participates',v('actor'),v('event'),v('context')))
    add('distributedaction',OLD_PARAMS['collectiveaction'],op('and',call('groupexists',v('actors')),
        each('actors','actor',q('exists','event',I,participation))))
    event_assigned=[('actors',GROUP),('assignment',CHOICE)]+OLD_PARAMS['collectiveaction'][1:]
    chosen_event=app('assignment',v('actor'))
    add('assignedactions',event_assigned,op('and',call('groupexists',v('actors')),each('actors','actor',op('and',
        app('occurs',chosen_event,v('context')),app('participates',v('actor'),chosen_event,v('context'))))))
    add('distinctactions',event_assigned,op('and',call('assignedactions',*args(event_assigned)),
        call('groupinjection',v('actors'),v('assignment'))))
    add('exactparticipants',[('actors',GROUP),('event',I),('context',S),('participates',RELATION)],
        q('forall','actor',I,op('iff',app('actors',v('actor')),app('participates',v('actor'),v('event'),v('context')))))
    add('actionobject',[('actor',I),('event',I),('target',I)]+ACTION,
        allof(participation,app('affects',v('event'),v('target'),v('context'))))
    all_same_event=each('actors','actor',act(v('actor'),v('target')))
    add('collectiveobject',OBJECTS,op('and',call('groupexists',v('actors')),
        some('targets','target',q('exists','event',I,all_same_event))))
    add('eachobject',OBJECTS,op('and',call('groupexists',v('actors')),
        each('actors','actor',some('targets','target',acts(v('actor'),v('target'))))))
    add('sameobject',OBJECTS,op('and',call('groupexists',v('actors')),
        some('targets','target',each('actors','actor',acts(v('actor'),v('target'))))))
    assigned=[('actors',GROUP),('targets',GROUP),('assignment',CHOICE)]+ACTION
    choice=app('assignment',v('actor'))
    add('assignedobjects',assigned,op('and',call('groupexists',v('actors')),
        each('actors','actor',op('and',app('targets',choice),acts(v('actor'),choice)))))
    add('distinctobjects',assigned,op('and',call('assignedobjects',*args(assigned)),
        call('groupinjection',v('actors'),v('assignment'))))
    only=each('actors','actor',each('targets','target',op('implies',acts(v('actor'),v('target')),
        op('equal',v('target'),choice))))
    add('exclusiveobjects',assigned,op('and',call('assignedobjects',*args(assigned)),only))
    reciprocal=[('group',GROUP),('relation',RELATION),('context',S)]
    edge=app('relation',v('member'),v('other'),v('context'))
    back=app('relation',v('other'),v('member'),v('context'))
    different=neq(v('member'),v('other'))
    def neighbor(body):return some('group','other',op('and',different,body))
    forms={
        'reciprocalall':each('group','member',each('group','other',op('implies',different,edge))),
        'reciprocalneighbors':each('group','member',op('and',neighbor(edge),neighbor(back))),
        'reciprocalpairs':each('group','member',neighbor(op('and',edge,back)))}
    for name,body in forms.items():add(name,reciprocal,op('and',call('groupplural',v('group')),body))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=defs,statements=[])


@lru_cache(maxsize=1)
def composed():return normalize_document(raw())


MEANINGS={
 'coveredgroups':'非空の行為者群と対象群について、各行為者に相手があり、各対象にも担当者がいる。全組合せや担当の一意性は要求しない。旧rpの本体を保持。',
 'collectiveaction':'非空の行為者群の全員が、同じ状況で生じる一つの出来事に参加する。旧rrの本体を保持。',
 'memberof':'指定個体が有限列のいずれかの位置に現れる。順序と重複は所属の真偽を変えない。',
 'distinctmembers':'有限列の個体に重複がない。空列でも成立する。',
 'membercount':'重複のない有限列の長さが指定した数に等しい。空列は0。列が母集団を尽くすことは別に指定する。',
 'groupexists':'集団の構成員が存在する。',
 'groupincludes':'includedの全員がgroupに含まれる。数学的な包含なので空集団も許す。',
 'groupall':'集団が非空で、全員が指定性質を満たす。',
 'groupplural':'集団に異なる二個体が存在する。',
 'groupinjection':'集団内で異なる個体への割当値が異なる。空集団でも成立する。',
 'distributedaction':'非空の集団の各人が、同じ状況で生じる何らかの出来事に参加する。出来事が同一か別個かは問わない。',
 'assignedactions':'非空の各行為者に割り当てた出来事が同じ状況で発生し、本人がその出来事に参加する。',
 'distinctactions':'assignedactionsを満たし、異なる行為者への割当出来事が異なる。他の共同出来事の存在は妨げない。',
 'exactparticipants':'その出来事の同じ状況における参加者が指定集団とちょうど一致する。発生や非空性は別条件。',
 'actionobject':'同じ出来事が発生し、同じ行為者が参加し、その出来事が同じ対象へ作用する。',
 'collectiveobject':'非空の全行為者が、同じ候補対象へ作用する一つの出来事に参加する。',
 'eachobject':'非空の各行為者が、候補対象の何かへ作用する出来事に参加する。対象と出来事は各人ごとに選べる。',
 'sameobject':'同じ候補対象について、非空の各行為者がその対象へ作用する出来事に参加する。出来事は各人ごとに選べる。',
 'assignedobjects':'明示した割当関数が各行為者へ候補対象を指定し、各人がその同じ対象へ作用する出来事に参加する。',
 'distinctobjects':'assignedobjectsを満たし、異なる行為者への割当対象が異なる。未選択の他の対象への作用を禁止しない。',
 'exclusiveobjects':'assignedobjectsを満たし、同じ候補対象範囲で各人が作用する対象は割当対象だけである。各人の対象が互いに異なるかは別条件。',
 'reciprocalall':'二人以上の集団で、異なる全ての順序対について関係が成立する。自己関係は要求しない。',
 'reciprocalneighbors':'二人以上の集団で、全員に関係を向ける相手と関係を向けてくる相手がいる。二つの相手は異なってよい。',
 'reciprocalpairs':'二人以上の集団で、全員に双方向の関係を持つ相手が少なくとも一人いる。集団全員の全組合せは要求しない。'}
ROLES={
 'actors':'この記述で固定する行為者の集団。所属を個体の性質として与える。',
 'targets':'この記述で候補とする対象の集団。',
 'relation':'指定した順序の二個体の関係。相互性の定義では最後に同じ評価状況を取る。',
 'context':'発生・参加・作用または相互関係を評価する同じ状況。',
 'occurs':'出来事と状況に対する発生関係。',
 'participates':'行為者・出来事・状況についての能動的な参加。単独で結果を起こせることや共同意図は別条件。',
 'affects':'出来事・対象・状況についての作用。運搬・点検など具体的な作用を定義して渡す。',
 'members':'個体の明示的な有限列。順序と重複を保持し、母集団の完全な列挙かどうかは別に指定する。',
 'member':'所属を調べる個体。','count':'重複のない列に要求する個体数。有理数型だが成立時には非負整数になる。',
 'group':'記述対象の集団。文脈を反映する場合は、その状況に固定した性質を渡す。',
 'included':'包含される側の集団。','property':'各構成員に要求する性質。',
 'event':'同じ行為・出来事を指す個体。','actor':'参加する同じ行為者。','target':'作用を受ける同じ対象。',
 'assignment':'個体から個体を選ぶ明示的な関数。定義に応じて対象または出来事を割り当てる証人であり、関係全体をこの関数と同一視しない。'}


def basis():
    contracts={}
    for d in raw()['declarations']:
        ps=OLD_PARAMS.get(d['name'],[(p['name'],p['sort']) for p in d['parameters']])
        contracts[d['name']]=dict(arguments=[dict(role=n,sort=t,interpretation=ROLES[n]) for n,t in ps],result=d['result'])
    return dict(status='shared_plurality_conventions',document=LIBRARY,primitives={},definitions=MEANINGS,
        public_contracts=contracts,preserved_definitions=[dict(document=SOURCE,names=NAMES)],
        design_sources=['docs/scoped-groups-v1.md','docs/plural-actions-v1.md','docs/proportions-v1.md'],
        limitations=['集団の同定・全列挙、出来事の粒度、参加と作用の意味は明示的な入力規約。共有の意図や単独の因果的十分性を補わない。',
            '各人への分配は出来事の相違を要求しない。distinctactionsは異なる出来事への割当を要求し、別の共同出来事がないことは要求しない。',
            '対象割当は具体的な証人を渡す。関係が多値でも別の割当が成立し得るため、ある割当の失敗から全割当の不在を導かない。',
            '相互性の三条件は区別した読み。自然言語の「互いに」の唯一の意味や連鎖的な全用法とはしない。',
            '物質量・単位、無限集合の濃度、円文字登録、学習文書・第三者読解は別途扱う。未知入力は否定に置き換えず評価を拒否する。'])


def prepare():
    for path,text in ((LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')):
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published plurality module differs: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':prepare()
