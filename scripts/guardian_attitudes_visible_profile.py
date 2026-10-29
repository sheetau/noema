"""Supervision, purpose, appraisal and attributed evaluation with preserved contracts."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.payment_prospects_visible_profile import ROOT,PaymentProspectsVisibleVocabulary,write_once
from scripts.guardian_attitudes_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/guardian-attitudes-visible-profile-v1.noema'
BASIS='data/guardian-attitudes-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-guardian-attitudes-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'contextualfemaleclassification': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'home', 'home'], 'supervisoryposition': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'home', 'above'], 'situationalprecedence': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'home', 'give'], 'performedaction': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'home', 'inside'], 'aestheticpersonassessment': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'home', 'aki'], 'propertylabelpresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'home', 'nao'], 'supervisionundertaking': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'home', 'book'], 'parameterizedactivitypurpose': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'home', 'round'], 'describedactivitypurpose': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'above', 'home'], 'supervisoryrankatleast': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'above', 'above'], 'describedpositionundertaking': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'above', 'give'], 'beneficiarygoodassessment': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'above', 'inside'], 'intrinsicgoalreadiness': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'above', 'aki'], 'highpropertydegree': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'above', 'nao'], 'favorableeventpresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'above', 'book'], 'criticalevaluationdistance': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'above', 'round'], 'focusedclaimassurance': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'give', 'home'], 'additivepropertypresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'give', 'above'], 'propertyjudgmentcandidate': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'give', 'give'], 'recognizedjudgmentproperty': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'give', 'inside'], 'overwhelmingproportioncriterion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'give', 'aki'], 'goalactivityoutcome': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'give', 'nao'], 'adverseoutcome': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'give', 'book'], 'goalactivityriskdegree': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'give', 'round'], 'highriskcriterion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'inside', 'home'], 'goalactivityburden': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'inside', 'above'], 'arduousburdencriterion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'aki', 'inside', 'give']}
CONTEXT=['同じ人物・対象・行為・状況・記述と順序付き引数を保持し、判断の候補と可能結果を混同しない。', '目標・評価・呼称・確言・追加の提示から引用内容の現実の成立を導かない。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile98。', '27一般関係の採用済み型・引数・意味を保持する。特定文や人物の参照は文書内で定義し、原始語にしない。', '割合・厳密な過半数・順位・引受け・判断・因果的寄与・評価は既存定義の合成を保つ。', '尺度・分類・監督・目的の意味規約に記録された説明の限界を保持し、有限診断を一般理論の証明とはしない。', '未知を偽や0へ補わず、引用の評価や批判的距離から真理や反対命題を導かない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_guardian_attitudes_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=98,parent_profile=97,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='同じ対象の監督・引受け・目的・危険判断と評価の提示を区別する共有語彙。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class GuardianAttitudesVisibleVocabulary(PaymentProspectsVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Guardian-attitudes profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Guardian-attitudes declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Guardian-attitudes meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-guardian-attitudes-visible-profile-1',edition=98)
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
    parent=PaymentProspectsVisibleVocabulary();vocabulary=GuardianAttitudesVisibleVocabulary()
    require(len(parent._words)==1242 and len(vocabulary._words)==1269,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(vocabulary.document()['entries']==parent.document()['entries'],'Frozen core changed')
    for old,row in SOURCE_RELATIONS.items():
        entry=catalog.entries[old];d=entry['declaration'];r=CONTRACTS[row['public']]
        require(d['kind']=='primitive' and d['parameters']==r['parameters'] and d['result']==r['result'],'Source signature changed')
        require(entry['meaning_ja']==r['meaning_ja'] and entry['arguments']==r['arguments'],'Source meaning or roles changed')
        require(bool(d['parameters']),'A local reference must be defined in the document')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/guardian_attitudes_visible_profile.py',
        'scripts/guardian_attitudes_visible_profile_contracts.py','tests/test_guardian_attitudes_visible_profile.py',
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
    return dict(schema='noema-guardian-attitudes-visible-profile-check-1',edition=98,parent_edition=97,
        words=1269,parent_words=1242,new_general_contracts=27,new_reference_primitives=0,new_core_words=0,
        source_contracts_preserved=sorted(SOURCE_RELATIONS),document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
