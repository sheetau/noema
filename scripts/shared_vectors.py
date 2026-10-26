"""Preserved component lists, parameterized vector operations and affine conditions."""
from copy import deepcopy
from functools import lru_cache
from noema.constructed import format_graph
from noema.constructed_discourse import normalize_document
from noema.meaning_catalog import _references
from scripts.shared_real_cuts import ROOT,catalog,injective_mapping,require,digest,encoded,write_new,SELECTED,SELECTED_BASIS
from scripts.shared_modality import renamed
from scripts.shared_cut_analysis import MAPPING as EARLIER_MAPPING

LIBRARY='examples/v016/shared-vectors-v1.noema'
BASIS='data/shared-vectors-basis-v1.json'
BRIDGE='data/einstein-vectors-correspondence-v1.json'
DEFINITIONS=dict(shm='vectorcomponents',shn='vectorvalid',sho='vectorcompare',shp='vectorcombine',
    shq='vectoraffinevalue',shr='vectorequalincrement',shs='vectoruniform',sht='vectoraffine')
MAPPING=EARLIER_MAPPING|DEFINITIONS
MEANINGS={
 'vectorcomponents':'成分を識別する個体の有限列が非空で、同じ個体を重複して含まない。成分名だけから次元や物理的な軸を推測しない。',
 'vectorvalid':'成分列がvectorcomponentsを満たし、指定された妥当性判定がベクトルの全ての選択成分に成立する。未選択成分は検査しない。',
 'vectorcompare':'成分列がvectorcomponentsを満たし、全ての選択成分で左右の値に指定比較関係が成立する。比較関係が値の等号であることや値の有効性は自動で補わない。',
 'vectorcombine':'同じ成分を左右のベクトルから読み、指定二項演算を左・右の順で適用する関数を返す。列・妥当性・演算の代数法則は要求しない。',
 'vectoraffinevalue':'出力成分ごとに、その成分の定数項を初期値とし、指定成分列の順に、行列の出力行・入力列の値と入力成分値の指定積を、指定加算で集計する。空列は定数項、重複列は重複して集計する。妥当な列や演算規約は別に要求する。',
 'vectorequalincrement':'二つの出発ベクトルに同じ変位を加え、指定変換の前後と二つの増分が全て有効であることを要求する。両出発点の変換後の増分を、同じ選択成分と指定比較関係で比較する。',
 'vectoruniform':'成分列が有効で対象範囲が非空である。その範囲の全出発点対と、有効かつ両移動先が範囲に残る全変位についてvectorequalincrementを要求する。比較の前提を満たす変位がない場合の空虚な成立を排除せず、対象範囲全体の妥当性やアフィン形を単独では保証しない。',
 'vectoraffine':'同じ成分列の定数項と全行列成分が有効で、対象範囲が非空である。全対象入力と変換結果が有効で、指定された同じ行列・定数項のvectoraffinevalueと変換結果が指定比較関係で一致する。入力ごとに行列や定数項を選び直さない。'}
ROLES=dict(vectorcomponents=['components'],vectorvalid=['components','vector','valid'],
    vectorcompare=['components','left','right','comparison'],vectorcombine=['left','right','operation'],
    vectoraffinevalue=['components','matrix','offset','vector','addition','multiplication'],
    vectorequalincrement=['components','first','second','displacement','transform','valid','comparison','addition','difference'],
    vectoruniform=['components','domain','transform','valid','comparison','addition','difference'],
    vectoraffine=['components','domain','transform','matrix','offset','valid','comparison','addition','multiplication'])
CONTEXT=[
 '値の型はfn[N]Tだが、この型だけで実数切断ではない。valid、comparison、各演算の解釈を利用箇所で明示する。',
 '行列は出力成分・入力成分の順に受け取る。成分は個体で識別し、有限列は順序と重複を保持する。']
LIMITS=[
 '指定された比較・二項演算が実数の等号・加算・積だとは自動的に仮定しない。群や体の法則は別の前提である。',
 'vectoraffinevalueだけでは空列や重複列を拒否しない。vectoraffineなど利用側の妥当性条件と分ける。',
 'vectoruniformから連続性・線形性・アフィン形を導く定理は追加していない。対象域や有効な変位が足りなければ条件は弱くなる。',
 '定数真偽の関数を値にしたNative診断と、値の型をtruthへ明示変更した有限モデルは、全実切断についての証明ではない。',
 '二つの成分の有限診断を任意次元の完全な証明とせず、型・元本体・全ての束縛は別に保存して照合する。']


@lru_cache(maxsize=1)
def composed():
    c=catalog();injective_mapping(c.document,MAPPING)
    selected=[deepcopy(d) for d in c.document['declarations'] if d['name'] in DEFINITIONS]
    require(_references(selected)<=set(DEFINITIONS),'Vector definitions have an external dependency')
    return normalize_document(injective_mapping(dict(schema_version='0.16',lexicon_version='0.16',declarations=selected,statements=[]),DEFINITIONS))


@lru_cache(maxsize=1)
def basis():
    contracts={}
    for d in composed()['declarations']:
        contracts[d['name']]=dict(arguments=[dict(role=n,sort=p['sort']) for n,p in zip(ROLES[d['name']],d['parameters'],strict=True)],
            result=d['result'],interpretation_inputs=CONTEXT)
    return dict(status='shared_preserved_parameterized_vectors',document=LIBRARY,primitives={},definitions=MEANINGS,
        public_contracts=contracts,preserved_sources=[dict(document=SELECTED,basis=SELECTED_BASIS,renaming=DEFINITIONS)],limitations=LIMITS)


@lru_cache(maxsize=1)
def correspondence():
    c=catalog();targets={d['name']:d for d in composed()['declarations']};direct,_=c._dependencies()
    def closure(names):
        seen=set();pending=set(names)
        while pending:
            name=pending.pop()
            if name not in seen:seen.add(name);pending.update(direct[name]-seen)
        return seen
    uses=[closure(_references(s)) for s in c.document['statements']];rows=[]
    for old,new in DEFINITIONS.items():
        e=c.entries[old];d=targets[new];require(renamed(e['declaration'],DEFINITIONS)==d,'Vector source payload changed')
        rows.append(dict(source_symbol=old,shared_word=new,source_basis=e['meaning_basis'],source_meaning=e['meaning_ja'],
            shared_meaning=MEANINGS[new],source_declaration_sha256=digest(encoded(e['declaration'])),
            shared_declaration_sha256=digest(encoded(d)),direct_dependencies=sorted(direct[old]),
            statement_indices=[i for i,names in enumerate(uses) if old in names],judgment='injective_renaming_with_explicit_parameter_interpretations'))
    return dict(schema='noema-public-word-correspondence-1',work='einstein-1905',document=SELECTED,
        document_sha256=digest((ROOT/SELECTED).read_bytes()),library=LIBRARY,rows=rows,
        previous_correspondence='data/einstein-cut-analysis-correspondence-v1.json',combined_mapping=MAPPING,
        reviewer='assistant',original_manuscript_modified=False,old_reviews_rebound=False,
        quotation_names_merged=False,full_manuscript_mapping_complete=False)


def prepare():
    write_new(LIBRARY,format_graph(composed())+'\n');write_new(BASIS,basis());write_new(BRIDGE,correspondence())
