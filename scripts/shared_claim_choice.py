"""A typed choice of already constructed content descriptions, without evaluation."""
import json
from scripts.shared_modality import ROOT
from noema.constructed import format_graph
from noema.constructed_discourse import description_sort

D=description_sort('content')
LIBRARY='examples/v016/shared-claim-choice-v1.noema';BASIS='data/shared-claim-choice-basis-v1.json'
PARAMETERS=['truth',D,D]
MEANING='条件が真なら第一の閉じた内容記述、偽なら第二の閉じた内容記述をそのまま返す。記述内容を実行せず、同義性で置換しない。'
LIMITS=['段階0の内容記述を選ぶ型付き基本関数。真理の判定、未知条件の既定値、自然言語の解釈、任意型の多相的な選択を提供するものではない。',
    'Noemaの通常の適用と同じく条件と両記述の構成には既知の値を要する。選択されない記述の内容真理まで実行するわけではない。',
    '入力として構成した記述の一方を保持し、新しい記述や外部由来の未認定な記述を生成しない。']

def document():return dict(schema_version='0.16',lexicon_version='0.16',declarations=[dict(kind='primitive',name='claimchoice',parameters=PARAMETERS,result=D)],statements=[])
def basis():
    roles=[('condition','truth','分岐を決める既知の真偽値。'),('positive',D,'条件が真の場合に返す閉じた内容記述。'),('negative',D,'条件が偽の場合に返す閉じた内容記述。')]
    return dict(status='typed_content_description_choice',document=LIBRARY,definitions={},
        primitives={'claimchoice':dict(parameters=PARAMETERS,result=D,arguments=[n for n,t,m in roles],meaning_ja=MEANING)},
        public_contracts={'claimchoice':dict(arguments=[dict(role=n,sort=t,interpretation=m) for n,t,m in roles],result=D)},limitations=LIMITS)
def prepare():
    for path,text in [(LIBRARY,format_graph(document())+'\n'),(BASIS,json.dumps(basis(),ensure_ascii=False,indent=2)+'\n')]:
        target=ROOT/path
        if target.exists() and target.read_text(encoding='utf-8')!=text:raise ValueError('Published claim choice differs')
        if not target.exists():target.write_text(text,encoding='utf-8',newline='\n')
if __name__=='__main__':prepare()
