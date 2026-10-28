"""Delegated activities, social roles and readable records with explicit descriptions."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.convenience_assessment_visible_profile import ROOT,ConvenienceAssessmentVisibleVocabulary,write_once
from scripts.delegated_activities_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/delegated-activities-visible-profile-v1.noema'
BASIS='data/delegated-activities-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-delegated-activities-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'performsjudgment': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'home', 'home'], 'judgmenttopic': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'home', 'above'], 'medicalcaretopic': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'home', 'give'], 'performsrecipientmeasure': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'home', 'inside'], 'socialroleholder': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'home', 'aki'], 'recipientactivityrolefunction': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'home', 'nao'], 'rolequalificationrequirement': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'home', 'book'], 'recipientactivityexpertise': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'home', 'round'], 'recordrealizeswork': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'above', 'home'], 'persistentexternalrecord': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'above', 'above'], 'readablerecord': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'above', 'give'], 'principalrecipientactivityduty': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'above', 'inside'], 'orderedleafcarrier': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'above', 'aki'], 'intendedcarrierform': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'above', 'nao'], 'recognizableconditionalpresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'above', 'book'], 'methodeffortrequirement': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'above', 'round'], 'provideractivityrolefunction': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'give', 'home'], 'principalprovideractivityduty': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'give', 'above'], 'provideractivityexpertise': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'give', 'give'], 'communityroleappointment': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'give', 'inside'], 'communityactivityentrustment': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'give', 'aki'], 'publicreligiousservice': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'give', 'nao'], 'hypotheticalfirstpersoncase': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'give', 'book'], 'hypotheticalfirstpersonpresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'give', 'round'], 'nonexhaustiveexamplepresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'inside', 'home'], 'provideraccess': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'inside', 'above'], 'substitutedtaskprovision': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'inside', 'give'], 'writtenexpressionwork': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'inside', 'inside'], 'moralselfevaluation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'inside', 'aki'], 'dieteticregimentopic': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'inside', 'nao'], 'spiritualwelfaretopic': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'inside', 'book'], 'bodilyhealthtopic': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'inside', 'round'], 'continuingrecipientassistance': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'give', 'aki', 'home']}
CONTEXT=['本人・提供者・役割・受け手・共同体・時点を保持する。活動の記述を、実行や成功そのものと同一視しない。', '記録・作品・媒体、社会的な位置付け・資格要求・知識技能・実行をそれぞれ独立した条件として合成する。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile96。', '33一般関係の型・引数・採用済み意味規約を保持し、一文の主張や特定の登場対象を原始語にしない。', '本・聖職者・医師の条件、代替供給、努力なしの達成、仮定的帰結は既存の本文定義を合成する。', '記述・非網羅的な例の列を提示しただけでは、その内容、列外の例、現実の行為や同意を推論しない。', '継承した領域概念の意味規約とその限界を保持する。有限診断を全領域の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_delegated_activities_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=96,parent_profile=95,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='本人と提供者を区別し、社会的役割・記録・仮定的提示を合成する共有語彙。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class DelegatedActivitiesVisibleVocabulary(ConvenienceAssessmentVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Delegated-activities profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Delegated-activities declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Delegated-activities meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-delegated-activities-visible-profile-1',edition=96)
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
    parent=ConvenienceAssessmentVisibleVocabulary();vocabulary=DelegatedActivitiesVisibleVocabulary()
    require(len(parent._words)==1198 and len(vocabulary._words)==1231,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(vocabulary.document()['entries']==parent.document()['entries'],'Frozen core changed')
    for old,row in SOURCE_RELATIONS.items():
        entry=catalog.entries[old];d=entry['declaration'];r=CONTRACTS[row['public']]
        require(d['kind']=='primitive' and d['parameters']==r['parameters'] and d['result']==r['result'],'Source signature changed')
        require(entry['meaning_ja']==r['meaning_ja'] and entry['arguments']==r['arguments'],'Source meaning or roles changed')
        require(bool(d['parameters']),'A local reference must be defined in the document')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/delegated_activities_visible_profile.py',
        'scripts/delegated_activities_visible_profile_contracts.py','tests/test_delegated_activities_visible_profile.py',
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
    return dict(schema='noema-delegated-activities-visible-profile-check-1',edition=96,parent_edition=95,
        words=1231,parent_words=1198,new_general_contracts=33,new_reference_primitives=0,new_core_words=0,
        source_contracts_preserved=sorted(SOURCE_RELATIONS),document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
