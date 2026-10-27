"""Optional physical-meaning question and characterized-object consideration."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document,function_sort,description_sort
from noema.constructed_semantics import FunctionValue,DescriptionValue
from scripts.third_frame_claim_visible_profile import ROOT,ThirdFrameClaimVisibleVocabulary,write_once,CUT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
CONTRACTS={'asksphysicalfunctionmeaning': {'parameters': ['individual',
                                                'individual',
                                                {'kind': 'description',
                                                 'result': {'kind': 'function',
                                                            'parameters': [{'kind': 'function',
                                                                            'parameters': ['number'],
                                                                            'result': 'truth'}],
                                                            'result': {'kind': 'function',
                                                                       'parameters': ['number'],
                                                                       'result': 'truth'}}},
                                                'individual',
                                                'situation'],
                                 'result': 'truth',
                                 'arguments': ['node', 'author', 'function_description', 'scope', 'context'],
                                 'meaning_ja': '著者が指定した関数の物理的な意味を問いとして提示する。値を問う計算問題とは区別する。'},
 'selectscharacterizedobjectforconsideration': {'parameters': ['individual',
                                                               'individual',
                                                               'individual',
                                                               {'kind': 'description', 'result': 'content'},
                                                               'individual',
                                                               'situation'],
                                                'result': 'truth',
                                                'arguments': ['node',
                                                              'author',
                                                              'object',
                                                              'characterization',
                                                              'scope',
                                                              'reference'],
                                                'meaning_ja': 'authorがnodeでobjectを、characterizationに記述された対象としてscopeの考察へ取り上げ、注意をその対象へ向ける論述行為。記述は同じ対象の特徴・設定を指定し、合成側がobjectとの同一参照を保つ。視覚的な目撃、材料の切断、実験の実行、記述内容の真理や考察目的の達成を含意しない。仮定の採用や結果の断言とは別の提示関係。'}}
SOURCE_RELATIONS={'zhg': 'asksphysicalfunctionmeaning', 'eisnx': 'selectscharacterizedobjectforconsideration'}

LIBRARY='examples/v016/transverse-endpoint-claim-visible-profile-v1.noema'
BASIS='data/transverse-endpoint-claim-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-transverse-endpoint-claim-visible-profile-v1.json'
ALL_CONTRACTS=CONTRACTS
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={'asksphysicalfunctionmeaning': ['above', 'round', 'treeone', 'home', 'nao', 'book', 'give', 'rain'],
 'selectscharacterizedobjectforconsideration': ['above',
                                                'round',
                                                'treeone',
                                                'home',
                                                'nao',
                                                'book',
                                                'give',
                                                'town']}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語とアルファベットを維持する。採用済みの問い・対象選定の意味を任意プロファイルへ公開する。',
 '同じ関数・対象・特徴・論述範囲・文脈を合成側で保持する。',
 '問いの提示は解答や計算の成功を、対象選定は視覚的目撃・物質の切断・実験・内容の真理を含意しない。',
 '参照取得と引用は内容を実行しない。有限診断を一般実数域の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_transverse_endpoint_claim_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=56,parent_profile=55,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/treeone/home/nao/book/giveを物理的意味の問いと特徴付き対象の考察への選定の語群とする。後続要素は公開規約を区別する綴りであり、対象や引数は本文で結ぶ。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class TransverseEndpointClaimVisibleVocabulary(ThirdFrameClaimVisibleVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'TransverseEndpointClaim-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'TransverseEndpointClaim-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'TransverseEndpointClaim-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-transverse-endpoint-claim-visible-profile-1',edition=56)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')
