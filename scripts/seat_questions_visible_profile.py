"""Optional physical comparison and inquiry contracts, preserving the fixed core."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.magnetic_auxiliary_visible_profile import ROOT,MagneticAuxiliaryVisibleVocabulary,write_once
from scripts.seat_questions_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/seat-questions-visible-profile-v1.noema'
BASIS='data/seat-questions-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-seat-questions-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'physicalpossibleresults': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'rain'], 'materialpreservingtrial': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'town'], 'transportassessmentstandard': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'home'], 'electricaldrivingtrial': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'above'], 'trialtransportresponse': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'give'], 'motioncomparisonpreparation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'inside'], 'bodyelectromagneticfields': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'birdone'], 'internalmagneticsourcestate': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'treeone'], 'sourceattributedforce': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'aki'], 'electromagneticcouplingprocess': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'nao'], 'physicalcomparisoncase': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'book'], 'observabletransporthistory': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'fruit'], 'permittedexplanatoryaccount': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'red'], 'explanatorymechanismclassification': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'round'], 'customarytheoreticalview': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'bird'], 'theoryinterpretationview': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'rain', 'fly'], 'motiontheoryapplication': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'rain'], 'observablemotiondistinction': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'town'], 'appearanceassessmentcandidate': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'home'], 'relativemotioncurrentgeneration': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'above'], 'priortopicresumption': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'give'], 'additivecontentpresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'inside'], 'availabledeviceoperation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'birdone'], 'rotationalinductionoutput': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'treeone'], 'closedconductivepath': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'aki'], 'slidingconductivecontact': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'nao'], 'unwrappedrotationturns': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'book'], 'expressionclassinterpretation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'fruit'], 'sourceinquirysetting': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'red'], 'proposedoriginsite': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'round'], 'autonomousphysicalsource': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'bird'], 'physicalsourcesite': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'town', 'fly'], 'inquiryrequiredpremise': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'home', 'rain'], 'theoryrejectspremise': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'home', 'town'], 'premisedinquirypractice': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'home', 'home'], 'parentheticaltopicapplication': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'aki', 'home', 'above']}
CONTEXT=['同じ物体・試行・単位・全履歴と比較範囲を保つ。', '理論、見方、説明、問いと前提への帰属を区別し、引用された内容や役割を自動実行しない。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile75。既存36規約の意味・型・引数順序を保持する。', '原文の文全体を新しい原始記号にしない。磁石・導体・非対称性解消・装置・問いの失効は既存の定義から合成する。', 'physicalpossibleresultsは空引数から四引数の物理的可能性関係を返す関数値であり、談話上の個体参照ではない。', '許容試行、可能結果、応答、成功の基準を分ける。未知の入力を偽や許容済みとして補わない。', '理論による前提の拒絶は不明・不言及・単なる偽と区別する。全実数・全関数の証明を有限診断から主張しない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_seat_questions_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=75,parent_profile=74,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/birdone/fruit/akiを物理的比較・説明・探究の公開規約の語群とする。後続二要素は規約の綴りを区別し、文全体の意味は合成する。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class SeatQuestionsVisibleVocabulary(MagneticAuxiliaryVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'SeatQuestions-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'SeatQuestions-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'SeatQuestions-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-seat-questions-visible-profile-1',edition=75)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
