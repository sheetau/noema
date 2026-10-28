"""Payment values, method thinking and prospective undertaking with preserved contracts."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.delegated_activities_visible_profile import ROOT,DelegatedActivitiesVisibleVocabulary,write_once
from scripts.payment_prospects_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/payment-prospects-visible-profile-v1.noema'
BASIS='data/payment-prospects-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-payment-prospects-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'creditedpaymentvalue': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'inside', 'home', 'home'], 'requiredpaymentvalue': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'inside', 'home', 'above'], 'soleconditionpresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'inside', 'home', 'give'], 'valuemediumtransfer': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'inside', 'home', 'inside'], 'acceptedpaymentmedium': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'inside', 'home', 'aki'], 'taskconsiderationtransfer': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'inside', 'home', 'nao'], 'methodthinkingrequirement': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'inside', 'home', 'book'], 'taskundertaking': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'inside', 'home', 'round'], 'aversivetaskassessment': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'inside', 'above', 'home'], 'confidentprospectcandidate': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'inside', 'above', 'above'], 'prospectivelylater': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'inside', 'above', 'give']}
CONTEXT=['同じ移転・支払う側・受け手・仕事の記述・文脈・尺度を保持する。必要額と移転価値の関係は既存定義で合成する。', '本人の思考経路、他者の担当引受け、仮定上の話者の評価と見込みを分け、引用記述を提示だけから実行しない。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile97。', '11一般関係の採用済み型・引数・意味規約を保持する。本文箇所t4は文書内の参照定義とし、新しい原始語にはしない。', '支払能力・本人の思考なしの達成・他者の引受けの見込み・条件文は既存定義を合成して表す。', '既知の無償条件の0と未知を区別し、額を既定値で補わない。追加要件不要の提示から逆や現実の真理を導かない。', '継承した領域概念の意味規約とその限界を保持する。有限診断を全領域の証明とはしない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_payment_prospects_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=97,parent_profile=96,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='同じ取引の価値・思考経路・引受けの見込み・十分条件の提示を保持する共有語彙。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class PaymentProspectsVisibleVocabulary(DelegatedActivitiesVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Payment-prospects profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Payment-prospects declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Payment-prospects meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-payment-prospects-visible-profile-1',edition=97)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


def build_report():
    """Check adopted source contracts and every inherited word before use."""
    import hashlib,sys
    from noema.meaning_catalog import load_catalog
    state=json.loads((ROOT/'data/work-state.json').read_text(encoding='utf-8'))
    selected=json.loads((ROOT/state['review_index']).read_text(encoding='utf-8'))['works']['kant-1784']
    catalog=load_catalog(ROOT,selected['meaning_basis'],document_path=selected['document'])
    parent=DelegatedActivitiesVisibleVocabulary();vocabulary=PaymentProspectsVisibleVocabulary()
    require(len(parent._words)==1231 and len(vocabulary._words)==1242,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(vocabulary.document()['entries']==parent.document()['entries'],'Frozen core changed')
    for old,row in SOURCE_RELATIONS.items():
        entry=catalog.entries[old];d=entry['declaration'];r=CONTRACTS[row['public']]
        require(d['kind']=='primitive' and d['parameters']==r['parameters'] and d['result']==r['result'],'Source signature changed')
        require(entry['meaning_ja']==r['meaning_ja'] and entry['arguments']==r['arguments'],'Source meaning or roles changed')
        require(bool(d['parameters']),'A local reference must be defined in the document')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/payment_prospects_visible_profile.py',
        'scripts/payment_prospects_visible_profile_contracts.py','tests/test_payment_prospects_visible_profile.py',
        'data/writing-freeze-v1.json','data/work-state.json',state['review_index'],*catalog.source_sha256}
    # Pin executable helpers and packaged vocabulary assets directly, without
    # importing unrelated Einstein publication evidence and rendered pages.
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'scripts').glob('*.py'))
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'noema').rglob('*.py'))
    paths.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'noema/resources').rglob('*') if p.is_file())
    for cls in type(vocabulary).__mro__:
        if not cls.__module__.startswith('scripts.'):continue
        module=sys.modules[cls.__module__]
        paths.add(__import__('pathlib').Path(module.__file__).resolve().relative_to(ROOT).as_posix())
        for name in ('LIBRARY','BASIS','MANIFEST'):
            p=getattr(module,name,None)
            if isinstance(p,str) and (ROOT/p).is_file():paths.add(p)
        # Contract modules imported by constructors remain part of their meanings.
        for name in tuple(sys.modules):
            if name.startswith('scripts.') and name.endswith('_contracts'):
                paths.add(__import__('pathlib').Path(sys.modules[name].__file__).resolve().relative_to(ROOT).as_posix())
    return dict(schema='noema-payment-prospects-visible-profile-check-1',edition=97,parent_edition=96,
        words=1242,parent_words=1231,new_general_contracts=11,new_reference_primitives=0,new_core_words=0,
        source_contracts_preserved=sorted(SOURCE_RELATIONS),document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
