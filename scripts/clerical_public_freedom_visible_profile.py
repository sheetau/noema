"""Reviewed thoughts, institutional proposals and scholarly public roles."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.clerical_obligation_visible_profile import ROOT,ClericalObligationVisibleVocabulary,write_once
from scripts.clerical_public_freedom_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS,EXTRA,MATH_ALIASES
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require

LIBRARY='examples/v016/clerical-public-freedom-visible-profile-v1.noema'
BASIS='data/clerical-public-freedom-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-clerical-public-freedom-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'reviewconclusioncompleted': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'round', 'inside', 'birdone', 'birdone', 'home', 'home'], 'reviewaspectscope': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'round', 'inside', 'birdone', 'birdone', 'home', 'above'], 'religiousinstitutionalfield': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'round', 'inside', 'birdone', 'birdone', 'home', 'give'], 'institutionalconfiguration': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'round', 'inside', 'birdone', 'birdone', 'home', 'inside'], 'institutionalconfigurationimplementation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'round', 'inside', 'birdone', 'birdone', 'home', 'aki'], 'configurationqualitypreorder': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'round', 'inside', 'birdone', 'birdone', 'home', 'nao'], 'referenceboundproposal': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'round', 'inside', 'birdone', 'birdone', 'home', 'book'], 'referenceboundproposalpresentation': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'round', 'inside', 'birdone', 'birdone', 'home', 'round'], 'scholarlynormsourcereference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'round', 'inside', 'birdone', 'birdone', 'above', 'home'], 'scholarlycommunicationperiodframe': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'round', 'inside', 'birdone', 'birdone', 'above', 'above'], 'scholarlyrolereference': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'round', 'inside', 'birdone', 'birdone', 'above', 'give'], 'judgmentmessageexamination': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'birdone', 'fruit', 'treeone', 'inside', 'give', 'round', 'inside', 'birdone', 'birdone', 'above', 'inside']}
CONTEXT=['同じ本人・判断・見解・関連事項と、同じ領域・構成・比較基準を保持する。', '学識者の立場・規範源・課題期間を雇用職務と分け、自由・使命・伝達・改善実施を別に構成する。']
LIMITS=['固定アルファベットと共通375語を維持する任意profile127。', '採用済み12一般関係の型・全引数・意味を保持する。原文箇所は文書内定義。', '判断による検討を受け手の理解と同一化せず、結論の真理や確定原則の採用を追加しない。', '本人の提案と受け手への提示を分け、改善・採用実施を閉じた記述に保持する。', '全見解・全提案・伝達候補の範囲を許可・実行・成功で選び直さない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_clerical_public_freedom_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=127,parent_profile=126,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='吟味判断、制度構成の比較と提案、学識者の公的役割を区別する共有語彙。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class ClericalPublicFreedomVisibleVocabulary(ClericalObligationVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Clerical public freedom profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Clerical public freedom declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Clerical public freedom meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-clerical-public-freedom-visible-profile-1',edition=127)
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
    parent=ClericalObligationVisibleVocabulary();vocabulary=ClericalPublicFreedomVisibleVocabulary()
    require(len(parent._words)==1824 and len(vocabulary._words)==1836,'Unexpected vocabulary boundary')
    require(all(vocabulary._words[n]==w and vocabulary._symbols[n]==parent._symbols[n]
                for n,w in parent._words.items()),'Parent word or spelling changed')
    require(vocabulary.document()['entries']==parent.document()['entries'],'Frozen core changed')
    for old,row in SOURCE_RELATIONS.items():
        entry=catalog.entries[old];d=entry['declaration'];r=CONTRACTS[row['public']]
        require(d['kind']=='primitive' and d['parameters']==r['parameters'] and d['result']==r['result'],'Source signature changed')
        require(entry['meaning_ja']==r['meaning_ja'] and entry['arguments']==r['arguments'],'Source meaning or roles changed')
        require(bool(d['parameters']),'A local reference must be defined in the document')
    paths={LIBRARY,BASIS,MANIFEST,'scripts/clerical_public_freedom_visible_profile.py',
        'data/kant-clerical-public-freedom-text-anchors-v1.json',
        'scripts/clerical_public_freedom_visible_profile_contracts.py','tests/test_clerical_public_freedom_visible_profile.py',
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
    return dict(schema='noema-clerical-public-freedom-visible-profile-check-1',edition=127,parent_edition=126,
        words=1836,parent_words=1824,new_general_contracts=12,new_reference_primitives=0,new_core_words=0,
        source_contracts_preserved=sorted(SOURCE_RELATIONS),document_integration_credit=0,
        limitations=LIMITS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
