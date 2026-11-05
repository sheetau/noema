"""Explicit interpretation, expression and institutional effects in edition 0.16.

These are reusable constructions, not a classifier of unannotated utterances.
Relation parameters have public contracts; their truth is not fabricated here.
"""
from functools import lru_cache
from noema.constructed_discourse import function_sort, description_sort, sequence_sort
from scripts.shared_modality import v, app, call, op
from scripts.shared_reference import I, S, T, C, definition, lam, truth
from scripts.shared_time import allof
from scripts.shared_speech import TO, ACTION, args
from scripts.general_language import document

DC = description_sort(C)
FEATURES = sequence_sort(I)
FEATURE = function_sort([I, I, S], T)
MAP = function_sort([I], I)
TRANSFER = [('source', I), ('target', I), ('features', FEATURES), ('mapping', MAP),
            ('sourcefeature', FEATURE), ('targetfeature', FEATURE), ('context', S)]
EXPRESSION = function_sort([I, I, I, I, ACTION, S], T)
EXPRESS = TO + [('attitude', ACTION), ('expresses', EXPRESSION)]
CLAIMS = function_sort([I, I, I, I, DC, S], T)
DECLARE = TO + [('institution', I), ('rule', I), ('status', DC), ('claims', CLAIMS)]


def evaluate(description, world):
    return dict(kind='evaluate', content=dict(kind='disquote', description=description), situation=world)


@lru_cache(maxsize=1)
def raw():
    ds = []
    def add(n, ps, body): ds.append(definition(n, ps, T, body))
    each = allof(app('sourcefeature', v('source'), v('feature'), v('context')),
                 app('targetfeature', v('target'), app('mapping', v('feature')), v('context')))
    fold = dict(kind='fold', sequence=v('features'), initial=truth(True),
                step=lam([('acc', T), ('feature', I)], op('and', v('acc'), each)))
    add('featuretransfer', TRANSFER, allof(
        op('not', op('equal', v('features'), dict(kind='sequence', element=I, items=[]))),
        call('distinctmembers', v('features')), fold))
    license_sort = function_sort([I, I, DC, DC, MAP, S], T)
    add('metaphoricalreading', TRANSFER + [('literal', DC), ('intended', DC), ('licensed', license_sort)],
        op('and', call('featuretransfer', *args(TRANSFER)),
           app('licensed', v('source'), v('target'), v('literal'), v('intended'), v('mapping'), v('context'))))
    rel = function_sort([I, I, S], T)
    selected = function_sort([I, I, I, S], T)
    add('metonymicreference', [('occurrence', I), ('sign', I), ('target', I), ('context', S), ('associated', rel), ('selected', selected)],
        allof(app('associated', v('sign'), v('target'), v('context')),
              app('selected', v('occurrence'), v('sign'), v('target'), v('context'))))
    echo = function_sort([I, I, DC, S], T)
    reading = function_sort([I, I, DC, DC, S], T)
    add('ironicreading', [('person', I), ('activity', I), ('echoed', DC), ('intended', DC), ('context', S),
                         ('echoes', echo), ('distances', echo), ('interprets', reading)],
        allof(app('echoes', v('person'), v('activity'), v('echoed'), v('context')),
              app('distances', v('person'), v('activity'), v('echoed'), v('context')),
              app('interprets', v('person'), v('activity'), v('echoed'), v('intended'), v('context'))))
    add('expressivepresentation', EXPRESS, op('and', call('speechto', *args(TO)),
        app('expresses', v('person'), v('recipient'), v('activity'), v('subject'), v('attitude'), v('context'))))
    attitude = dict(kind='apply', function=dict(kind='disquote', description=v('attitude')), arguments=[v('person')])
    add('expressivesincere', EXPRESS, op('and', call('expressivepresentation', *args(EXPRESS)),
        dict(kind='evaluate', content=attitude, situation=v('context'))))
    add('declarativepresentation', DECLARE, op('and', call('speechto', *args(TO)),
        app('claims', v('person'), v('activity'), v('institution'), v('rule'), v('status'), v('context'))))
    authority = function_sort([I, I, I, I, DC, S], T)
    ps = DECLARE + [('authorized', authority), ('precondition', DC), ('outcome', S), ('before', function_sort([S, S], T))]
    add('declarativeeffective', ps, allof(call('declarativepresentation', *args(DECLARE)),
        app('authorized', v('person'), v('activity'), v('institution'), v('rule'), v('status'), v('context')),
        evaluate(v('precondition'), v('context')), app('before', v('context'), v('outcome')), evaluate(v('status'), v('outcome'))))
    belongs = function_sort([I, I, S], T)
    add('fictionalclaim', [('frame', I), ('voice', I), ('content', DC), ('world', S), ('belongs', belongs)],
        op('and', app('belongs', v('frame'), v('voice'), v('world')), evaluate(v('content'), v('world'))))
    marked = function_sort([I, I, I, I, I, S], T)
    add('socialregister', TO + [('community', I), ('role', I), ('marked', marked)],
        op('and', call('speechto', *args(TO)), app('marked', v('person'), v('recipient'), v('activity'), v('community'), v('role'), v('context'))))
    return ds


MEANINGS = {
 'featuretransfer': '空でなく重複のない特徴列について、同じ源対象の特徴と、明示された対応写像による同じ先対象の特徴が成立する。対象の同一性、列にない特徴の移転、写像の唯一性は含まない。',
 'metaphoricalreading': '指定した特徴の対応に、同じ源・先・字義記述・意図記述・写像・文脈を結ぶ解釈の根拠を要求する比喩の読み。源の特徴は比喩の比較場面における特徴でもよく、現実世界に源対象が実在するとは限らない。字義の内容を真として実行しない。この特徴対応型以外の比喩を禁止しない。',
 'metonymicreference': '同じ文脈での二対象の関係と、同じ出現において一方で他方を指すという明示的な選択を結ぶ。関係があるだけでは参照先を選ばず、対象を同一化しない。',
 'ironicreading': '同じ話者・行為・文脈で、ある記述を反響させ、それへの距離を表し、指定した別の意図記述として解釈する読み。字義の偽を必須にせず、否定だけから皮肉を認定しない。皮肉の全用法を一つの条件へ還元する定義ではない。',
 'expressivepresentation': '同じ生起する発話行為・話者・受け手・話題に、引用した態度をその場で表す関係を結ぶ。態度について報告しただけではこの関係は成立しない。態度を実際に持つことや受け手が理解することは含めない。',
 'expressivesincere': '表出された同じ態度記述を同じ話者に適用し、表出時点でその内容も成立する。表出の存在と内心の成立を区別するための条件であり、表出一般の必須条件ではない。',
 'declarativepresentation': '同じ生起する発話に、指定した制度・規則の下で指定状態を成立させる宣言をしたという表明を結ぶ。話者の権限・手続の適格さ・実際の成立は別。',
 'declarativeeffective': '同じ宣言に、その話者・行為・制度・規則・状態に対する権限、前提の成立、後続状況での同じ状態の成立を結ぶ。権限は結果から逆算せず、宣言が実際に効力を生じたとの制度的根拠を含む解釈入力として別に説明する。',
 'fictionalclaim': '指定された物語枠・語りの声に属する状況で、引用された内容が成立する。現実の状況、別の物語枠、語り手の信頼性には移さない。',
 'socialregister': '同じ提示に、指定された共同体の慣行で話者が受け手に対して役割上の距離・敬意などを表す関係を結ぶ。実際の身分、内心の敬意、普遍的な礼儀の評価は含めない。'
}

CONTRACTS = {
 'sourcefeature': '比較場面で源対象に帰属する特徴。現実の実在を要求するかは文脈で固定する。',
 'targetfeature': '先対象に帰属すると解釈する特徴。源と同じ語義を無条件に適用しない。',
 'mapping': '源の特徴から先の特徴への、読みの根拠として先に固定した対応。',
 'licensed': 'この字義と意図をこの特徴対応で読む根拠。単なる二対象の類似とは区別する。',
 'associated': '部分と全体、作者と作品、場所と組織など、先に説明された二対象間の関係。',
 'selected': 'この出現で関係先を参照対象として選ぶ根拠。関連する全対象から自動選択しない。',
 'echoes': '話者が同じ行為で指定記述を反響・引照する。実際の先行発話がなく、期待の引照でもよい。',
 'distances': '同じ行為で同じ記述への評価上の距離を表す。記述が偽であることではない。',
 'interprets': '同じ反響する記述と意図した読みを結ぶ、文脈上の解釈根拠。',
 'expresses': '話者がこの受け手への同じ行為でこの話題に対する態度を表出する。伝聞や中立的な報告と区別し、社会的慣行と提示方法を記す。',
 'claims': '同じ行為で指定制度・規則による状態の成立を宣言すると表明する。単なる状態の予測とは区別する。',
 'authorized': '指定規則に基づく権限と手続の適格さが同じ宣言に適用され、その宣言による状態の成立を制度的に認める。状態が後に成立しただけでは補わない。',
 'belongs': '同じ物語枠・語りの声に属する評価状況。現実や別の声への移行には明示的な別対応が必要。',
 'marked': '指定共同体の慣行で、この発話行為が受け手への指定役割上の態度を表すという位置付け。'
}


def composed(): return document(raw())


def basis():
    return dict(document='examples/v016/general-pragmatics-v1.noema', primitives={}, definitions=MEANINGS,
        public_contracts={d['name']: dict(arguments=[dict(role=p['name'], sort=p['sort'],
            contract=CONTRACTS.get(p['name'])) for p in d['parameters']], result=d['result']) for d in raw()},
        new_primitives=0, limits=['解釈関係は真と決め打ちしない。欠けた入力は未知として拒否する。',
            '表出・約束・宣言の社会的働きは基本message.forceの三分類とは別の合成層。performのみから社会的成功を認定しない。',
            '規約付きの遂行的発話は、この発話行為自身を参照する文として構成できる。報告・引用の出現と行為の出現を同一視しない。'])
