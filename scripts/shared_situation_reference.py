"""An explicit context-and-address reference, without an implicit chronology."""
import json
from scripts.shared_modality import ROOT
from noema.constructed import format_graph

LIBRARY='examples/v016/shared-situation-reference-v1.noema'
BASIS='data/shared-situation-reference-basis-v1.json'
PARAMETERS=['individual','number']
ROLES=['context','address']
MEANING='指定文脈の参照表で、有理数のアドレスが指定する状況。数値の大小・差から時間順序・経過量・実在を推測しない。'
LIMITS=['文脈ごとの明示的な参照解釈を要する基本関数。期限・履行・解除・真理を代用する関数ではない。',
    'アドレスは有理数の識別値で、物理時刻・時間間隔・単位ではない。異なる値の別状況への対応や、異なる文脈間の一致は自動で保証しない。',
    'Nativeの全域関数型に従い、完全なモデルは全引数の解釈を要する。有限実行で未指定の組を要求したら未知として拒否し、既定の状況や偽へ置換しない。']

def document():
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=[dict(kind='primitive',name='situationslot',parameters=PARAMETERS,result='situation')],statements=[])

def basis():
    return dict(status='explicit_contextual_situation_reference',document=LIBRARY,definitions={},
        primitives={'situationslot':dict(parameters=PARAMETERS,result='situation',arguments=ROLES,meaning_ja=MEANING)},
        public_contracts={'situationslot':dict(arguments=[dict(role='context',sort='individual',interpretation='状況の参照表を指定する文脈識別子。'),
            dict(role='address',sort='number',interpretation='その表で状況を指定する有理数。時間順序や経過量を含意しない。')],result='situation')},limitations=LIMITS)

def prepare():
    for path,text in [(LIBRARY,format_graph(document())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')]:
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published situation reference differs')
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')

if __name__=='__main__':prepare()
