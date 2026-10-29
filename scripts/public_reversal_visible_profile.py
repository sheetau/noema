"""Public dissemination, judgments, reception and exact textual references."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.public_dissemination_visible_profile import ROOT,PublicDisseminationVisibleVocabulary,write_once
from scripts.public_reversal_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/public-reversal-visible-profile-v1.noema'
BASIS='data/public-reversal-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-public-reversal-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'coercedstateexitrestriction': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'home', 'home'], 'collectiveactionattribution': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'home', 'above'], 'acquisitionopportunitycandidate': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'home', 'give'], 'acquisitionbasisretention': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'home', 'inside'], 'externalacquisitionopportunity': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'home', 'aki'], 'prospectiveactionreadiness': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'home', 'nao'], 'rebelliousaffectappeal': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'home', 'book'], 'actiondirectedrebelliousaffect': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'home', 'round'], 'distributivegroupscope': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'above', 'home'], 'contextualpriorinfluencecase': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'above', 'above'], 'caseprioractorgroup': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'above', 'give'], 'casepriorparticipants': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'above', 'inside'], 'caseincitingparticipants': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'above', 'aki'], 'casepriorinfluenceact': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'above', 'nao'], 'casepriorinfluencepoint': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'above', 'book'], 'caseincitingpresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'above', 'round'], 'caseincitementpoint': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'give', 'home'], 'caseprospectivepressureact': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'give', 'above'], 'caseaffectedparticipants': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'give', 'give'], 'casehistorydescription': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'give', 'inside'], 'caseprecedencedescription': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'give', 'aki'], 'casepressurestartdescription': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'give', 'nao'], 'caseretentionenddescription': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'give', 'book'], 'caseretentionassessment': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'give', 'round'], 'casepressureactdescription': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'inside', 'home'], 'scopedrelationaldepictionthree': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'inside', 'above'], 'depictionkindanaphora': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'inside', 'give'], 'salientdeparturepresentationthree': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'inside', 'inside'], 'scopedactorfocuspresentationthree': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'inside', 'aki'], 'judgmentprincipleadoption': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'inside', 'nao'], 'completedgroundsadequacyexamination': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'inside', 'book'], 'opinioncontentdescription': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'inside', 'round'], 'opinionsubjectreferent': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'aki', 'home'], 'practicalrolesuccession': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'aki', 'above'], 'unexaminedprincipleeffectcase': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'aki', 'give'], 'caseoriginlinkedtargets': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'aki', 'inside'], 'caseadoptionoriginator': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'aki', 'aki'], 'caseadoptionproductionact': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'aki', 'nao'], 'caseadoptionrecipient': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'aki', 'book'], 'caseopinionreferent': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'aki', 'round'], 'caseopiniondescription': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'nao', 'home'], 'caseadoptionpriorpoint': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'nao', 'above'], 'caseadoptionpriordescription': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'nao', 'give'], 'casetargetoutcomepoint': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'nao', 'inside'], 'casetargetsuccessionrole': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'nao', 'aki'], 'casetargetcoursedescription': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'nao', 'nao'], 'casetargetprecedencedescription': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'nao', 'book'], 'highpropertydegreeevaluationthree': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'nao', 'round'], 'exemplifieddegreepresentationthree': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'book', 'home'], 'rootedplantbody': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'book', 'above'], 'plantgrowthmedium': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'book', 'give'], 'rootmediumplacement': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'book', 'inside'], 'rootedplantgrowth': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'book', 'aki'], 'caseadoptionrecipientdescription': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'book', 'nao'], 'casetargetdepictedresponse': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'book', 'book'], 'casetargetdescription': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'book', 'round'], 'perceivedpersonalwrong': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'round', 'home'], 'retributiveresponserelation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'above', 'book', 'round', 'above']}
CONTEXT=['同じ事例・公衆・行為・参加者列・時間範囲・記述を各関係に保つ。', '帰属と世界真理、人物と描写の種類、圧力と成功、原則採用と真理を区別する。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile108。', '58一般関係の採用済み型・引数・意味を保持し、11箇所参照と補助全第三文参照は文書内定義にする。', '事例フィールドは同じ事例の値を供給する入力であり、原文の主張全体や成功を返す演算子ではない。', '強制・共同作用・能力基盤・感情・根拠吟味・役割継承の具体的機構は元契約の明示範囲を超えて保証しない。', '階数3の主張・範囲・対象列を保持し、非字義的な植え付け・頚木・報復の提示を現実の出来事へ変えない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_public_reversal_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=108,parent_profile=107,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='共同作用・状態取得・意見の採用・継承と、条件を保つ焦点・描写・程度提示を区別する共有語彙。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class PublicReversalVisibleVocabulary(PublicDisseminationVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Public-reversal profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Public-reversal declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Public-reversal meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-public-reversal-visible-profile-1',edition=108)
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
    parent=PublicDisseminationVisibleVocabulary();vocabulary=PublicReversalVisibleVocabulary()
    require(len(parent._words)==1491 and len(vocabulary._words)==1549,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(vocabulary.document()['entries']==parent.document()['entries'],'Frozen core changed')
    for old,row in SOURCE_RELATIONS.items():
        entry=catalog.entries[old];d=entry['declaration'];r=CONTRACTS[row['public']]
        require(d['kind']=='primitive' and d['parameters']==r['parameters'] and d['result']==r['result'],'Source signature changed')
        require(entry['meaning_ja']==r['meaning_ja'] and entry['arguments']==r['arguments'],'Source meaning or roles changed')
        require(bool(d['parameters']),'A local reference must be defined in the document')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/public_reversal_visible_profile.py',
        'data/kant-public-reversal-text-anchors-v1.json',
        'scripts/public_reversal_visible_profile_contracts.py','tests/test_public_reversal_visible_profile.py',
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
    return dict(schema='noema-public-reversal-visible-profile-check-1',edition=108,parent_edition=107,
        words=1549,parent_words=1491,new_general_contracts=58,new_reference_primitives=0,new_core_words=0,
        source_contracts_preserved=sorted(SOURCE_RELATIONS),document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
