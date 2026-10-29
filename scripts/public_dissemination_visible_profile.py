"""Public dissemination, judgments, reception and exact textual references."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.public_enlightenment_visible_profile import ROOT,PublicEnlightenmentVisibleVocabulary,write_once
from scripts.public_dissemination_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/public-dissemination-visible-profile-v1.noema'
BASIS='data/public-dissemination-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-public-dissemination-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'entrustedcivicrole': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'home', 'home'], 'selfworthcriterion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'home', 'above'], 'selfthinkingmissionsubject': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'home', 'give'], 'rationalagencydutysource': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'home', 'inside'], 'rationalpersonrole': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'home', 'aki'], 'selfassessmentresponsescene': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'home', 'nao'], 'selfassessmentnormalityorder': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'home', 'book'], 'independentjudgmentresponsescene': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'home', 'round'], 'independentjudgmentnormalityorder': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'above', 'home'], 'independentjudgmentsubject': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'above', 'above'], 'presentedjudgmentsubject': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'above', 'give'], 'publicevaluationoccasion': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'above', 'inside'], 'individualdesignationcandidate': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'above', 'aki'], 'situationdesignationcandidate': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'above', 'nao'], 'guidedpopulationreferent': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'above', 'book'], 'guidedpopulationsizethreshold': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'above', 'round'], 'institutionalroleappointment': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'give', 'home'], 'disparagingreferencepresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'give', 'above'], 'receivedparameterizedmessage': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'give', 'give'], 'relaysparameterizedmessage': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'give', 'inside'], 'understandsparameterizedmessage': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'give', 'aki'], 'judgmentvalueassessment': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'give', 'nao'], 'judgmentcontentendorsement': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'give', 'book'], 'neckheadbodypart': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'give', 'round'], 'loadbearingframe': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'inside', 'home'], 'tractiontransmissionequipment': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'inside', 'above'], 'bodilyequipmentremovalcause': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'inside', 'give'], 'sentencetextspanreference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'nao', 'inside', 'inside']}
CONTEXT=['同じ公衆・参照・仮定経過・本人・基準時・対象を各関係に保つ。', '引用候補の参照先、受領・理解・賛同・方針決定、身体と知的過程を区別する。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile107。', '27一般関係の採用済み型・引数・意味を保持し、5局所参照は文書内定義にする。', '文内文字範囲の一般参照を追加し、空白区切り参照の既存規則を変更しない。', '受領・再伝達・理解の機構、理解の評価基準、規範源や通常性入力の具体化には原契約の限界を保持する。', '伝播や予測、比喩や低く扱う呼び方の提示を、現実の真理・賛同・身体事実・対象の低価値に変えない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_public_dissemination_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=107,parent_profile=106,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='判断・任用・受領・再伝達・理解と、身体的描写および正確な文字範囲参照を区別する共有語彙。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class PublicDisseminationVisibleVocabulary(PublicEnlightenmentVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Public-dissemination profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Public-dissemination declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Public-dissemination meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-public-dissemination-visible-profile-1',edition=107)
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
    parent=PublicEnlightenmentVisibleVocabulary();vocabulary=PublicDisseminationVisibleVocabulary()
    require(len(parent._words)==1463 and len(vocabulary._words)==1491,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(vocabulary.document()['entries']==parent.document()['entries'],'Frozen core changed')
    for old,row in SOURCE_RELATIONS.items():
        entry=catalog.entries[old];d=entry['declaration'];r=CONTRACTS[row['public']]
        require(d['kind']=='primitive' and d['parameters']==r['parameters'] and d['result']==r['result'],'Source signature changed')
        require(entry['meaning_ja']==r['meaning_ja'] and entry['arguments']==r['arguments'],'Source meaning or roles changed')
        require(bool(d['parameters']),'A local reference must be defined in the document')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/public_dissemination_visible_profile.py',
        'data/kant-public-dissemination-text-anchors-v1.json',
        'scripts/public_dissemination_visible_profile_contracts.py','tests/test_public_dissemination_visible_profile.py',
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
    return dict(schema='noema-public-dissemination-visible-profile-check-1',edition=107,parent_edition=106,
        words=1491,parent_words=1463,new_general_contracts=28,new_reference_primitives=1,new_core_words=0,
        source_contracts_preserved=sorted(SOURCE_RELATIONS),document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
