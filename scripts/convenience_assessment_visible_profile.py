"""Convenience assessment with explicit state descriptions and preserved goals."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.causal_attitudes_visible_profile import ROOT,CausalAttitudesVisibleVocabulary,write_once
from scripts.convenience_assessment_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES,SPECIALIZATIONS
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/convenience-assessment-visible-profile-v1.noema'
BASIS='data/convenience-assessment-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-convenience-assessment-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'practicalgoalattainment': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'above', 'home', 'home'], 'contextualconvenienceburden': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'above', 'home', 'above'], 'convenienceassessmentperson': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'above', 'home', 'give'], 'stateconveniencecandidate': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'round', 'above', 'home', 'inside']}
CONTEXT=['本人・対象状態の記述・基準文脈・仮定状況を保持する。状態の維持、目標達成、同じ方法の負担を合成で結ぶ。', '目的・評価範囲・便宜さの基準は明示的な解釈入力であり、好意、現実の選択や実行とは区別する。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile95。', '3関係の型・引数・採用済み意味規約を保持する。源ujは特定状態の原始語を追加せず、一般候補関係へ既存bfの性質記述を渡す定義で表す。', '本文の割合・原因・便宜さを一語化せず、既存のrj/rk/ul/unと方法・結果の条件を合成する。', '候補の採用から引用した状態を実行せず、未指定入力を真偽の既定値で埋めない。有限検査は全領域の証明ではない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_convenience_assessment_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=95,parent_profile=94,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='目的と状態を保って便宜さを評価する共有語彙。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class ConvenienceAssessmentVisibleVocabulary(CausalAttitudesVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Convenience-assessment profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Convenience-assessment declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Convenience-assessment meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-convenience-assessment-visible-profile-1',edition=95)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


def case_specialization(name='uj',property_name='bf'):
    from scripts.shared_modality import call,v
    from scripts.shared_reference import definition
    return definition(name,[('person','individual'),('context','situation'),('case','situation')],'truth',
        call('stateconveniencecandidate',v('person'),dict(kind='quote',body=dict(kind='function_ref',symbol=property_name)),v('context'),v('case')))


def build_report():
    """Check adopted source contracts and every inherited word before use."""
    import hashlib,sys
    from noema.meaning_catalog import load_catalog
    state=json.loads((ROOT/'data/work-state.json').read_text(encoding='utf-8'))
    selected=json.loads((ROOT/state['review_index']).read_text(encoding='utf-8'))['works']['kant-1784']
    catalog=load_catalog(ROOT,selected['meaning_basis'],document_path=selected['document'])
    parent=CausalAttitudesVisibleVocabulary();vocabulary=ConvenienceAssessmentVisibleVocabulary()
    require(len(parent._words)==1194 and len(vocabulary._words)==1198,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(vocabulary.document()['entries']==parent.document()['entries'],'Frozen core changed')
    for old,row in SOURCE_RELATIONS.items():
        entry=catalog.entries[old];d=entry['declaration'];r=CONTRACTS[row['public']]
        require(d['kind']=='primitive' and d['parameters']==r['parameters'] and d['result']==r['result'],'Source signature changed')
        require(entry['meaning_ja']==r['meaning_ja'] and entry['arguments']==r['arguments'],'Source meaning or roles changed')
        require(bool(d['parameters']),'A local reference must be defined in the document')
    for old,specialization in SPECIALIZATIONS.items():
        entry=catalog.entries[old];d=entry['declaration']
        require(d['kind']=='primitive' and d['parameters']==specialization['parameters'] and d['result']==specialization['result'],'Specialized source signature changed')
        require(entry['meaning_ja']==specialization['meaning_ja'] and entry['arguments']==specialization['arguments'],'Specialized source meaning changed')
        property_declaration=catalog.entries[specialization['property']]['declaration']
        require(property_declaration['kind']=='definition' and [p['sort'] for p in property_declaration['parameters']]==['individual'] and property_declaration['result']=='content','Specialized property type changed')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/convenience_assessment_visible_profile.py',
        'scripts/convenience_assessment_visible_profile_contracts.py','tests/test_convenience_assessment_visible_profile.py',
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
    return dict(schema='noema-convenience-assessment-visible-profile-check-1',edition=95,parent_edition=94,
        words=1198,parent_words=1194,new_general_contracts=4,new_reference_primitives=0,new_core_words=0,
        source_contracts_preserved=sorted(SOURCE_RELATIONS),source_specializations=SPECIALIZATIONS,document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
