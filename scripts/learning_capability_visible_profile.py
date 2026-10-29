"""Experience, learning capabilities, reactions and ranked content attribution."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.confinement_motion_visible_profile import ROOT,ConfinementMotionVisibleVocabulary,write_once
from scripts.learning_capability_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/learning-capability-visible-profile-v1.noema'
BASIS='data/learning-capability-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-learning-capability-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'experiencedresultpoint': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'home', 'home'], 'experienceassessmentpoint': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'home', 'above'], 'contributingexperiencesequence': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'home', 'give'], 'processinitialassessment': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'home', 'inside'], 'experiencechangecontribution': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'home', 'aki'], 'contextualfewrepetitions': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'home', 'nao'], 'examplecaseobserver': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'home', 'book'], 'examplecaseexperience': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'home', 'round'], 'recognizesexperienceexample': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'above', 'home'], 'typicalitycaseeligibility': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'above', 'above'], 'typicalitycasesequence': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'above', 'give'], 'usualproportioncriterion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'above', 'inside'], 'envisagedactionpoint': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'above', 'aki'], 'envisagedactivityattempt': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'above', 'nao'], 'scopedrankedcontentattribution': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'above', 'book'], 'comparativecontentprospect': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'above', 'round'], 'rankedforegroundbackgroundpresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'give', 'home'], 'uprightbodybalance': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'give', 'above'], 'nonfootloadcontact': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'give', 'give'], 'downwardbodytransition': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'give', 'inside'], 'intentionalsupporttransition': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'give', 'aki'], 'activityopportunitycandidate': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'give', 'nao'], 'activitybasisretention': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'give', 'book'], 'externalactivityopportunity': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'give', 'round'], 'activityopportunitypriority': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'inside', 'home'], 'activitybasismethod': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'inside', 'above'], 'activitybasismethodclassified': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'inside', 'give'], 'reactioncomparisoncandidate': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'inside', 'inside'], 'reactionbackgroundpriority': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'inside', 'aki'], 'reactioncasepriority': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'inside', 'nao'], 'harmcuecomparisoncandidate': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'inside', 'book'], 'harmcuebackgroundpriority': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'inside', 'round'], 'undertakingbackgroundcandidate': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'aki', 'home'], 'epistemiccoursepriority': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'aki', 'above'], 'nonliteralboundrelationpresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'book', 'aki', 'give']}
CONTEXT=['同じ本人・活動・経験・基準と前後状態を保持する。知的な取得と身体描写を非字義的な対応として区別する。', '通常性の候補・順序・頻度、実際の経験・想定した取り組み・取得見込み、主張・背景・理由を分ける。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile100。', '35一般関係の採用済み型・引数・意味を保持し、4局所参照は文書内定義にする。', '能力評価・因果的寄与・通常性順序・頻度・比較的な見込みは既存の合成定義で構成する。', '段階1/3の内容記述と順序付き束縛を保持し、未知を偽・同順位・空列へ補わない。', '有限診断を全領域の証明とせず、比喩・予測・評価の帰属からその現実の真理を推論しない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_learning_capability_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=100,parent_profile=99,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='経験と能力変化、活動の基盤、通常性と見込み、主張と背景の区別を保持する共有語彙。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class LearningCapabilityVisibleVocabulary(ConfinementMotionVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Learning-capability profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Learning-capability declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Learning-capability meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-learning-capability-visible-profile-1',edition=100)
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
    parent=ConfinementMotionVisibleVocabulary();vocabulary=LearningCapabilityVisibleVocabulary()
    require(len(parent._words)==1316 and len(vocabulary._words)==1351,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(vocabulary.document()['entries']==parent.document()['entries'],'Frozen core changed')
    for old,row in SOURCE_RELATIONS.items():
        entry=catalog.entries[old];d=entry['declaration'];r=CONTRACTS[row['public']]
        require(d['kind']=='primitive' and d['parameters']==r['parameters'] and d['result']==r['result'],'Source signature changed')
        require(entry['meaning_ja']==r['meaning_ja'] and entry['arguments']==r['arguments'],'Source meaning or roles changed')
        require(bool(d['parameters']),'A local reference must be defined in the document')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/learning_capability_visible_profile.py',
        'scripts/learning_capability_visible_profile_contracts.py','tests/test_learning_capability_visible_profile.py',
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
    return dict(schema='noema-learning-capability-visible-profile-check-1',edition=100,parent_edition=99,
        words=1351,parent_words=1316,new_general_contracts=35,new_reference_primitives=0,new_core_words=0,
        source_contracts_preserved=sorted(SOURCE_RELATIONS),document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
