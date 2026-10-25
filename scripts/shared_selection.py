"""Existing truth indicators, rational selection and finite selected counts."""
from copy import deepcopy
from functools import lru_cache
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.shared_modality import ROOT,v,call,op,renamed
from scripts.shared_reference import T,definition
from scripts.shared_time import allof
from scripts.shared_plurality import MEMBERS,GROUP

N='number'
SOURCE='examples/v014/proportions.noema'
SOURCE_BASIS='data/proportions-basis-v1.json'
QUANTITIES='examples/v016/shared-quantities-v1.noema'
QUANTITY_BASIS='data/shared-quantities-basis-v1.json'
PLURAL='examples/v016/shared-plurality-v1.noema'
PLURAL_BASIS='data/shared-plurality-basis-v1.json'
LIBRARY='examples/v016/shared-selection-v1.noema'
BASIS='data/shared-selection-basis-v1.json'
NAMES={'ha':'rationaladd','hd':'truthindicator','he':'indicatorvalid','hf':'occurrencecount'}
NEW_NAMES=('truthindicator','indicatorvalid','occurrencecount','selectnumber','countselected')
QUANTITY_NAMES=('rationaladd','rationalmultiply')
PLURAL_NAMES=('memberof','distinctmembers')


@lru_cache(maxsize=1)
def raw():
    quantities=parse((ROOT/QUANTITIES).read_text(encoding='utf-8'))
    source=parse((ROOT/SOURCE).read_text(encoding='utf-8'))
    plural=parse((ROOT/PLURAL).read_text(encoding='utf-8'))
    declarations=[deepcopy(d) for d in quantities['declarations'] if d['name'] in QUANTITY_NAMES]
    old={d['name']:d for d in source['declarations']}
    # The old addition signature must agree with the already public primitive.
    assert renamed(old['ha'],NAMES)==next(d for d in declarations if d['name']=='rationaladd')
    declarations.extend(renamed(old[n],NAMES) for n in ('hd','he','hf'))
    declarations.extend(deepcopy(d) for d in plural['declarations'] if d['name'] in PLURAL_NAMES)
    body=call('rationaladd',call('rationalmultiply',call('truthindicator',v('condition')),v('whenyes')),
        call('rationalmultiply',call('truthindicator',op('not',v('condition'))),v('whenno')))
    declarations.append(definition('selectnumber',[('condition',T),('whenyes',N),('whenno',N)],N,body))
    body=allof(call('indicatorvalid'),call('distinctmembers',v('members')),
        op('equal',call('occurrencecount',v('members'),v('property')),v('count')))
    declarations.append(definition('countselected',[('members',MEMBERS),('property',GROUP),('count',N)],T,body))
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=declarations,statements=[])


@lru_cache(maxsize=1)
def composed():return normalize_document(raw())


ROLES={
 'condition':'どちらの有理数値を選ぶかを表す既知の真理値。',
 'whenyes':'条件が真である場合の有理数値。引数は選択前に評価する。',
 'whenno':'条件が偽である場合の有理数値。引数は選択前に評価する。',
 'members':'計数する個体の有限列。出現数では重複を残し、個体数では重複を拒否する。',
 'property':'各個体が該当するかを表す既知の性質。',
 'count':'該当する個体に要求する個数。有理数型だが成立時は非負整数。'}


def basis():
    old=json.loads((ROOT/SOURCE_BASIS).read_text(encoding='utf-8'))
    quantities=json.loads((ROOT/QUANTITY_BASIS).read_text(encoding='utf-8'))
    plural=json.loads((ROOT/PLURAL_BASIS).read_text(encoding='utf-8'))
    primitives={n:deepcopy(quantities['primitives'][n]) for n in QUANTITY_NAMES}
    indicator=deepcopy(next(r for r in old['primitives'] if r['symbol']=='hd'));indicator['symbol']='truthindicator'
    primitives['truthindicator']=indicator
    meanings={NAMES[n]:old['definitions'][n] for n in ('he','hf')}
    meanings.update({n:plural['definitions'][n] for n in PLURAL_NAMES})
    meanings.update(selectnumber='真ならwhenyes、偽ならwhennoの有理数値を、既存の数値指示関数と積・和から構成する。引数の遅延評価ではない。',
        countselected='指示関数の真偽両方の規約が成立し、列に同じ個体の重複がなく、該当個体の出現数が指定数に等しい。空列は0。')
    contracts={n:deepcopy(quantities['public_contracts'][n]) for n in QUANTITY_NAMES}
    contracts.update({n:deepcopy(plural['public_contracts'][n]) for n in PLURAL_NAMES})
    labels={'truthindicator':['condition'],'indicatorvalid':[],'occurrencecount':['members','property']}
    for d in raw()['declarations']:
        n=d['name']
        if n in contracts:continue
        sorts=d['parameters'] if d['kind']=='primitive' else [p['sort'] for p in d['parameters']]
        names=labels.get(n,[p['name'] for p in d['parameters']]) if d['kind']=='definition' else labels[n]
        contracts[n]=dict(arguments=[dict(role=role,sort=t,interpretation=ROLES[role]) for role,t in zip(names,sorts)],result=d['result'])
    return dict(status='shared_truth_numeric_selection',document=LIBRARY,primitives=primitives,definitions=meanings,
        public_contracts=contracts,preserved_definitions=[dict(document=SOURCE,names=NAMES),
            dict(document=QUANTITIES,names={n:n for n in QUANTITY_NAMES}),dict(document=PLURAL,names={n:n for n in PLURAL_NAMES})],
        limitations=['truthindicatorは既存hdの基本規約を再利用する。新しい原始概念を作らない。真偽の両値はindicatorvalidで検査できる。',
            'selectnumberは標準の指示関数・有理数加算・乗算という規約の下で値を選ぶ。型だけで任意の外部解釈を標準算術と認定しない。',
            '引数の評価は従来どおり厳密。未選択側が未知でも評価は拒否し、0を掛けて不明値を消したことにしない。',
            'occurrencecountは列の出現を数える。countselectedは列全体の重複を拒否し、母集団の完全性や代表性は別途指定する。',
            '有限条件の数値選択は任意型の遅延条件式や、未知の個体を新設する操作ではない。円文字接続と多部分の可視例を続ける。'])


def prepare():
    for path,text in ((LIBRARY,format_graph(composed())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')):
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published selection module differs: '+path)
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')


if __name__=='__main__':prepare()
