"""Optional text-reference meanings; the 375-word common core is unchanged."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path

from noema.constructed import format_graph, parse
from noema.constructed_discourse import normalize_document
from scripts.visible_senses_vocabulary import SensesVocabulary
from scripts.visible_word_forms import Word, canonical, symbol
from scripts.visible_lexical_script import require

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = 'examples/v016/text-reference-profile-v1.noema'
BASIS = 'data/text-reference-profile-basis-v1.json'
MANIFEST = 'noema/resources/visible-text-reference-profile-v1.json'
EDITION = 17
PARAMETERS = dict(textpresentation=[], sentencereference=['situation','number','number'],
                  textbefore=['individual','individual','situation'])
RESULTS = dict(textpresentation='situation',sentencereference='individual',textbefore='truth')
ROLES = dict(textpresentation=[], sentencereference=['context','paragraph','sentence'],
             textbefore=['first','second','context'])
MEANINGS = {
    'textpresentation': 'この文書で指示の基準として指定する、対象文章の提示文脈。読む時刻・文章内容の真理・出来事が起こる状況とは同一視しない。対象文章と採用する区分規約は使用時の指示条件で固定する。',
    'sentencereference': '同じ提示文脈で、指定した本文段落の指定した文の談話箇所を指す。本文段落と文はそれぞれ1始まりの正整数で指定する。文の内容や、その範囲を対象化した別の個体とは区別する。位置は語義の辞書番号ではない。',
    'textbefore': '指定文脈の本文順序で第一箇所が第二箇所より前にある。出来事の時間順序や因果の向きとは別の関係。'}
CONTEXT = [
    '対象文章と提示文脈を固定する。本文段落には前付・署名・日付・著者注・編集注を混ぜない。',
    '文の境界は対象文章に対して明示して検証する。句点で自動分割した結果を無条件に採用しない。',
    '同じ文脈の同じ段落・文位置は同じ談話箇所を指し、異なる位置は異なる文の出現である。別文脈間の同一性は補わない。']
LIMITS = [
    '本文の位置による指示は、指示した文の意味内容を表現する代わりにはならない。参照先の内容は別に記述する。',
    'Nativeの完全なモデルは全引数の解釈を要する。有限実行で未指定の位置や文脈を要求した場合は未知として拒否し、既定の個体や偽に置換しない。',
    'このプロファイルは共通基盤375語に追加して選ぶ3語の文書参照語彙であり、旧第16版424語の置換版ではない。',
    '文番号は指示先の位置であって、語の意味・対象の性質・真理を決定する記号番号ではない。']
SPELLINGS = dict(textpresentation=['book','inside','above','home'],
                 sentencereference=['book','inside','above','book'],
                 textbefore=['book','inside','above','above'])


def library():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[
        dict(kind='primitive',name=n,parameters=p,result=RESULTS[n]) for n,p in PARAMETERS.items()],statements=[])


def basis():
    return dict(status='optional_text_reference_profile',document=LIBRARY,definitions={},
        primitives={n:dict(parameters=p,result=RESULTS[n],arguments=ROLES[n],meaning_ja=MEANINGS[n]) for n,p in PARAMETERS.items()},
        public_contracts={n:dict(arguments=[dict(role=r,sort=s) for r,s in zip(ROLES[n],p,strict=True)],
            result=RESULTS[n],interpretation_inputs=CONTEXT) for n,p in PARAMETERS.items()},limitations=LIMITS)


def manifest():
    return dict(schema='noema-visible-optional-profile-1',edition=EDITION,core_edition=12,
        library=LIBRARY,basis=BASIS,spellings=SPELLINGS,
        naming_convention='book/inside/aboveを本文の中の参照と順序の語群とする。homeは提示文脈、bookは文の出現、aboveは本文で先にある関係を区別する綴りであり、語義は公開規約から学習する。')


def write_once(path, value):
    text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n'
    path=ROOT/path;require(not path.exists() or path.read_text(encoding='utf-8')==text,'Published artifact differs: '+str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():path.write_text(text,encoding='utf-8',newline='\n')


def prepare():
    write_once(LIBRARY,format_graph(library())+'\n');write_once(BASIS,basis());write_once(MANIFEST,manifest())


class TextReferenceVocabulary(SensesVocabulary):
    def __init__(self):
        super().__init__();data=self.document();parent=deepcopy(data)
        require(json.loads((ROOT/MANIFEST).read_text(encoding='utf-8'))==manifest(),'Text reference profile changed')
        require(parse((ROOT/LIBRARY).read_text(encoding='utf-8'))==library(),'Text reference declarations changed')
        require(json.loads((ROOT/BASIS).read_text(encoding='utf-8'))==basis(),'Text reference meanings changed')
        for d in library()['declarations']:
            n=d['name'];require(n not in self._words,'Profile name collision')
            word=canonical(Word('compound',tuple(SPELLINGS[n])),self)
            data['primitives'][n]=d
            data['compounds'][n]=dict(parts=list(word.parts),parameters=d['parameters'],result=d['result'],
                roles=ROLES[n],meaning=MEANINGS[n],context=CONTEXT,contrast=LIMITS,aliases=[])
            self._words[n]=word
        data.update(schema='noema-visible-text-reference-profile-1',edition=EDITION)
        data['naming_convention']+='\n'+manifest()['naming_convention']
        self._document=data;self._primitives=deepcopy(data['primitives'])
        self._symbols={n:symbol(w,self) for n,w in self._words.items()}
        require(len(set(self._symbols.values()))==len(self._words),'Profile spelling collision')
        self._by_symbol={s:n for n,s in self._symbols.items()};self._order=self._topological()
        normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
            declarations=[self._plain_declaration(n) for n in self._order],statements=[]))
        for field in ('entries','compounds','definitions','primitives'):
            require(all(data[field].get(n)==d for n,d in parent[field].items()),'Common core changed')


class TextPresentation:
    """Partial known readings, with unknown-input rejection and no truth defaults.

    Positions are actual paragraph/sentence coordinates, never lexical IDs.
    The finite reader does not claim to interpret every number in a total model.
    """
    def __init__(self, anchor, layouts):
        require(anchor in layouts,'Unknown presentation anchor')
        self.anchor=anchor;self.layouts={};self.positions={}
        for context,layout in layouts.items():
            copied={};positions={}
            for coordinate,node in layout.items():
                require(isinstance(coordinate,tuple) and len(coordinate)==2,'Expected paragraph/sentence coordinate')
                key=tuple(self.coordinate(x) for x in coordinate)
                require(key not in copied and node not in positions,'Ambiguous sentence occurrence')
                copied[key]=node;positions[node]=key
            self.layouts[context]=copied;self.positions[context]=positions

    @staticmethod
    def coordinate(value):
        require(type(value) in (int,Fraction),'Sentence position must be exact numeric data')
        value=Fraction(value)
        require(value.denominator==1 and value>0,'Sentence position must be a positive integer')
        return int(value)

    def reference(self,context,paragraph,sentence):
        require(context in self.layouts,'Unknown presentation context')
        key=(self.coordinate(paragraph),self.coordinate(sentence))
        require(key in self.layouts[context],'Unknown sentence position')
        return self.layouts[context][key]

    def before(self,first,second,context):
        require(context in self.positions,'Unknown presentation context')
        positions=self.positions[context]
        require(first in positions and second in positions,'Unknown discourse occurrence')
        return positions[first]<positions[second]

    def handlers(self):
        return dict(textpresentation=lambda:self.anchor,sentencereference=self.reference,textbefore=self.before)
