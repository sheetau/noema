"""Preserved real-cut definitions and an explicit Einstein/public-word bridge."""
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import hashlib
import json

from noema.constructed import parse, format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import load_catalog, _references
from scripts.shared_modality import renamed
from scripts.visible_senses_vocabulary import SensesVocabulary

ROOT=Path(__file__).resolve().parents[1]
LIBRARY='examples/v016/shared-real-cuts-v1.noema'
BASIS='data/shared-real-cuts-basis-v1.json'
BRIDGE='data/einstein-real-cuts-correspondence-v1.json'
SELECTED='examples/v014/einstein-reviewed-complete-v1.noema'
SELECTED_BASIS='data/einstein-reviewed-complete-basis-v1.json'
OLD='examples/v011/real-cuts.noema'
OLD_BASIS='data/real-cuts-basis-v1.json'
ARITHMETIC=dict(aa='rationalbelow',ab='rationaladd',ac='rationalnegate',ad='rationalmultiply')
DEFINITIONS=dict(ba='cutvalid',bb='rationalcut',bc='cutincluded',bd='cutadd',be='cutnegate',
                 bf='cutdifference',bg='cutless',bi='cutmidpoint',bj='cutpositivescale')
MAPPING=ARITHMETIC|DEFINITIONS
MEANINGS={
 'cutvalid':'有理数上の性質が非空・全域でない・下方閉・最大元なしを満たす。これを実数の下側切断として採用する。',
 'rationalcut':'有理数の値rを、q<rを満たす有理数qの性質として表す。境界r自身は含まない。',
 'cutincluded':'左の性質を満たす全有理数が右の性質も満たす。双方が実数の下側切断なら左の値は右以下である。',
 'cutadd':'左の性質を満たす有理数xと右の性質を満たす有理数yが存在し、q<x+yとなる有理数qの性質を返す。切断の加算として使うときは両入力のcutvalidを別に要求する。',
 'cutnegate':'元の性質を満たさない有理数uが存在し、q<-uとなる有理数qの性質を返す。補集合の単なる符号反転で境界を含めない。',
 'cutdifference':'左の性質と右の性質のcutnegateをcutaddで結ぶ。実数の差としての利用には両入力のcutvalidを別に要求する。',
 'cutless':'左が右に含まれ、右は左に含まれない。双方が実数の下側切断なら左の値は右より厳密に小さい。',
 'cutmidpoint':'中間−先頭と最後−中間が全有理数で同じ性質になる。三入力のcutvalidや、時計・基準系・単位・物理的な同期条件はこの等式に含めない。',
 'cutpositivescale':'尺度が正の有理数で、元の性質を満たす有理数xが存在し、q<尺度*xとなる有理数qの性質を返す。尺度が0以下なら空の性質となり、実数の切断条件を満たさない。'}
ROLES=dict(cutvalid=['candidate'],rationalcut=['value'],cutincluded=['left','right'],cutadd=['left','right'],
           cutnegate=['candidate'],cutdifference=['left','right'],cutless=['left','right'],
           cutmidpoint=['start','middle','finish'],cutpositivescale=['scale','candidate'])
LIMITS=[
 '型fn[N]Tだけでは実数の切断にならない。空・全域・閉じた境界などの性質も同じ型を持つ。cutvalidと利用条件を別に確認する。',
 '有理数を有限集合へ縮めない。有限評価器は数への量化を拒否し、線形補助検証器も非線形な有理数量化を実数の量化へすり替えない。',
 '有理数埋込みの線形検査は、全ての実切断に対する体の法則や完備性の機械的証明ではない。',
 '新しい基本関係は追加しない。既存の有理数比較・和・加法逆元・積の意味規約を再利用する。',
 '一般化したcutmidpointは三値の等間隔条件であり、光信号・時計・同期の物理的な前提を主張しない。',
 '対応は明示したEinstein正本の13宣言に限る。同じ記号を使うKant文書へ流用せず、異なる名前を一つへ統合しない。']


def require(condition,message):
    if not condition:raise ValueError(message)


def digest(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')


@lru_cache(maxsize=1)
def catalog():
    state=json.loads((ROOT/'data/work-state.json').read_text(encoding='utf-8'))
    index=json.loads((ROOT/state['review_index']).read_text(encoding='utf-8'))
    selected=index['works']['einstein-1905']
    require(selected['document']==SELECTED and selected['meaning_basis']==SELECTED_BASIS,'Active Einstein selection changed')
    c=load_catalog(ROOT,SELECTED_BASIS,document_path=SELECTED)
    prior=json.loads((ROOT/state['progress_report']).read_text(encoding='utf-8'))['source_sha256']
    require(all(prior.get(p)==stamp and digest((ROOT/p).read_bytes())==stamp for p,stamp in c.source_sha256.items()),
            'Selected source differs from preserved judgments')
    return c


def injective_mapping(document,mapping):
    names={d['name'] for d in document['declarations']}
    require(set(mapping)<=names,'Mapping names an unknown source')
    require(len(set(mapping.values()))==len(mapping),'Mapping merges different source names')
    require(not set(mapping.values())&(names-set(mapping)),'Mapping captures an unchanged declaration')
    result=renamed(document,mapping)
    require(renamed(result,{v:k for k,v in mapping.items()})==document,'Mapping is not reversible')
    return result


@lru_cache(maxsize=1)
def composed():
    c=catalog();vocab=SensesVocabulary();old=parse((ROOT/OLD).read_text(encoding='utf-8'))
    original={d['name']:d for d in old['declarations']}
    for n in MAPPING.keys()&original.keys():
        require(c.entries[n]['declaration']==original[n],'Selected mathematical declaration changed: '+n)
    selected=[deepcopy(d) for d in c.document['declarations'] if d['name'] in MAPPING]
    require(_references(selected)<=set(MAPPING),'Mathematical projection has external dependencies')
    doc=dict(schema_version='0.16',lexicon_version='0.16',declarations=selected,statements=[])
    doc=normalize_document(injective_mapping(doc,MAPPING))
    for d in doc['declarations']:
        if d['kind']=='primitive':
            require(d==vocab._plain_declaration(d['name']),'Arithmetic signature changed')
            old_name=next(k for k,v in ARITHMETIC.items() if v==d['name']);entry=c.entries[old_name]
            require(entry['meaning_ja']=='[current の記号名] '+vocab.entry(d['name'])['meaning']
                    and entry['arguments']==vocab.entry(d['name'])['roles'],'Arithmetic convention changed')
    return doc


@lru_cache(maxsize=1)
def basis():
    vocab=SensesVocabulary();primitives={};contracts={}
    for d in composed()['declarations']:
        name=d['name']
        if d['kind']=='primitive':
            entry=vocab.entry(name)
            primitives[name]=dict(parameters=d['parameters'],result=d['result'],arguments=entry['roles'],meaning_ja=entry['meaning'])
            contracts[name]=dict(arguments=[dict(role=n,sort=t) for n,t in zip(entry['roles'],d['parameters'],strict=True)],
                                  result=d['result'],interpretation_inputs=entry['context'])
        else:
            contracts[name]=dict(arguments=[dict(role=n,sort=p['sort']) for n,p in zip(ROLES[name],d['parameters'],strict=True)],
                result=d['result'],interpretation_inputs=['有理数は標準の正確な算術で解釈する。','実数として扱う入力にはcutvalidを別に要求する。'])
    return dict(status='shared_preserved_real_cut_definitions',document=LIBRARY,primitives=primitives,
                definitions=MEANINGS,public_contracts=contracts,
                preserved_sources=[dict(document=SELECTED,basis=SELECTED_BASIS,renaming=MAPPING)],limitations=LIMITS)


@lru_cache(maxsize=1)
def correspondence():
    c=catalog();target={d['name']:d for d in composed()['declarations']};vocab=SensesVocabulary();direct,_=c._dependencies()
    def closure(names):
        seen=set();pending=set(names)
        while pending:
            n=pending.pop()
            if n not in seen:seen.add(n);pending.update(direct[n]-seen)
        return seen
    uses=[closure(_references(s)) for s in c.document['statements']]
    rows=[]
    # Validate injectivity against every original declaration, not just the projection.
    injective_mapping(c.document,MAPPING)
    for old,new in MAPPING.items():
        entry=c.entries[old];d=target[new]
        require(renamed(entry['declaration'],MAPPING)==d,'Source mapping changes payload')
        rows.append(dict(source_symbol=old,shared_word=new,kind=d['kind'],source_basis=entry['meaning_basis'],
            source_meaning=entry['meaning_ja'],shared_meaning=MEANINGS.get(new,vocab.entry(new)['meaning'] if new in vocab._words else None),
            source_declaration_sha256=digest(encoded(entry['declaration'])),shared_declaration_sha256=digest(encoded(d)),
            direct_dependencies=sorted(direct[old]),statement_indices=[i for i,names in enumerate(uses) if old in names],
            judgment=('same_exact_rational_convention_and_ordered_roles' if d['kind']=='primitive' else 'injective_renaming_of_typed_definition_with_explicit_general_contract'),
            physical_context_added=False))
    return dict(schema='noema-public-word-correspondence-1',work='einstein-1905',document=SELECTED,
                document_sha256=digest((ROOT/SELECTED).read_bytes()),library=LIBRARY,rows=rows,
                reviewer='assistant',original_manuscript_modified=False,old_reviews_rebound=False,
                quotation_names_merged=False,full_manuscript_mapping_complete=False)


def write_new(path,value):
    target=ROOT/path;body=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    require(not target.exists() or target.read_text(encoding='utf-8')==body,'Published real-cut artifact differs: '+path)
    if not target.exists():target.write_text(body,encoding='utf-8',newline='\n')


def prepare():
    write_new(LIBRARY,format_graph(composed())+'\n');write_new(BASIS,basis());write_new(BRIDGE,correspondence())
