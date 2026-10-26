"""Optional moving light trials, result presentation and exact text references."""
from copy import deepcopy
import json
from noema.constructed import parse,format_graph
from noema.constructed_discourse import normalize_document
from scripts.carried_clock_synchrony_profile import ROOT,CarriedClockSynchronyVocabulary,write_once,CUT
from scripts.visible_word_forms import Word,canonical,symbol
from scripts.visible_lexical_script import require
from scripts.moving_trip_visible_profile_contracts import CONTRACTS,SOURCE_RELATIONS

LIBRARY='examples/v016/moving-trip-visible-profile-v1.noema'
BASIS='data/moving-trip-visible-profile-basis-v1.json'
MANIFEST='noema/resources/visible-moving-trip-visible-profile-v1.json'
I='individual';S='situation';N='number'
EXTRA={
 'sentencespanreference':dict(parameters=[I,I,I,S],result=I,arguments=['document','first_sentence','last_sentence','context'],
    meaning_ja='同じ文書と提示文脈で、指定した最初の文から最後の文までを両端を含めて連続して対象とする本文箇所への参照。両端は同じ本文に属し、本文順序で逆転しない。文の出現そのものとは区別し、範囲の内容や真理は別に記述する。未知の範囲を補わない。'),
 'footnoteattachmentreference':dict(parameters=[I,I,N,N,S],result=I,arguments=['document','sentence','printed_number','occurrence','context'],
    meaning_ja='同じ文書・提示文脈の指定文で、指定の正整数の著者脚注番号が印刷された局所的な付着箇所への参照。occurrenceはその文にある同じ番号の記号を本文順に数えた1始まりの出現位置。文全体や注本文とは区別する。番号が別文で再使用されても同一視せず、未知の付着箇所を補わない。')}
ALL_CONTRACTS=CONTRACTS|EXTRA
PARAMETERS={n:r['parameters'] for n,r in ALL_CONTRACTS.items()}
PARTS=('home','above','give','inside','aki','nao','book','round')
SPELLINGS={name:['above','round','give',PARTS[i//8],PARTS[i%8]] for i,name in enumerate(ALL_CONTRACTS)}
CONTEXT=['同じ課題・方式・対象・文書・文脈を保持する。見かけ、可能性、採用、実施を区別する。']
LIMITS=['共通375語は不変。旧関係の型・役割・意味を任意プロファイルとして公開する。',
        '記録の成分位置は公開されたデータの欄であり語義番号ではない。未知の値を既定値で補わない。',
        '参照・引用・前方指示はその内容の真理や実験済みを意味しない。有限診断を全実数の証明としない。']


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result']) for n,r in ALL_CONTRACTS.items()],statements=[])


def basis():
    return dict(status='optional_moving_trip_visible_profile',document=LIBRARY,definitions={},primitives=ALL_CONTRACTS,
        public_contracts={n:dict(arguments=[dict(role=a,sort=s) for a,s in zip(r['arguments'],r['parameters'],strict=True)],
            result=r['result'],interpretation_inputs=CONTEXT) for n,r in ALL_CONTRACTS.items()},
        source_relations=SOURCE_RELATIONS,limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=32,parent_profile=31,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='above/round/giveを光往復とその提示・局所参照の語群とする。後続の二要素は公開規約で区別する綴りであり、文中に数値の語義表を置かない。役割と数学は本文定義として示す。')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class MovingTripVisibleVocabulary(CarriedClockSynchronyVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Moving-trip-visible profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Moving-trip-visible declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Moving-trip-visible meanings changed')
        for d in library()['declarations']:
            n=d['name'];r=ALL_CONTRACTS[n];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d;data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=r['arguments'],meaning=r['meaning_ja'],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-moving-trip-visible-profile-1',edition=32)
        data['naming_convention']+='\n'+manifest()['naming_convention'];self._document=data
        self._primitives=deepcopy(data['primitives']);self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Previous profile changed')


class MovingTextReferences:
    """Explicit, checked text locations. No inference from quoted content."""
    def __init__(self,spans,attachments):
        from scripts.text_reference_profile import TextPresentation
        self.spans=dict(spans)
        self.attachments={(d,s,TextPresentation.coordinate(n),TextPresentation.coordinate(i),c):v for (d,s,n,i,c),v in attachments.items()}

    def span(self,document,first,last,context):
        key=(document,first,last,context)
        require(key in self.spans,'Unknown sentence span reference');return self.spans[key]

    def attachment(self,document,sentence,number,occurrence,context):
        from scripts.text_reference_profile import TextPresentation
        key=(document,sentence,TextPresentation.coordinate(number),TextPresentation.coordinate(occurrence),context)
        require(key in self.attachments,'Unknown footnote attachment reference');return self.attachments[key]

    def handlers(self):return dict(sentencespanreference=self.span,footnoteattachmentreference=self.attachment)
