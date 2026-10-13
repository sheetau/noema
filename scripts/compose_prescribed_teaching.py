"""Institutional standards, actual communication and its normative target."""
from copy import deepcopy
import json

from noema.extraction import extract_document, extract_basis
from noema.grammar import parse, format_graph
from noema.meaning_basis import audit_basis
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_situated_criticism import generic_composed as speech_document, params, args, MESSAGE
from scripts.compose_assessed_payments import TRUE, PUBLIC

PARENT = 'examples/v014/kant-enacted-standing.noema'
CRITERION = 'h[a '+MESSAGE+'] e'
CRITERIA = 'j['+CRITERION+']'
SERVES = 'h[a a a d] c'
ADOPTED = 'h[a a '+CRITERIA+' d] c'
SETTINGS = [('principal','a'), ('role','a'), ('standard','a'), ('students','h[a] c'),
    ('congregation','h[a] c'), ('subject','a'), ('message',MESSAGE), ('criteria',CRITERIA),
    ('serves',SERVES), ('adopted',ADOPTED)]
RELATIONS = [('positioned','h[a a a d] c'), ('entrusted','h[a a d] c'),
    ('occurs','h[a d] c'), ('presents','h[a a d] c'), ('conveys','h[a a a '+MESSAGE+' d] c')]
DUTY = 'person a action a role a issuer a teaching i[h[a a] e] context d'
DUTY_NAMES = 'person action role issuer teaching context'


def definitions():
    step = both(v('accepted'), op('t', app(v('criterion'), v('subject'), v('message')), v('context')))
    text = definition('rfu', 'subject a message '+MESSAGE+' criteria '+CRITERIA,
        'b context[q[v criteria]['+TRUE+'][i[accepted c criterion '+CRITERION+']['+step+']]]', 'e')
    audience = 'i[recipient a]['+op('x', app(v('students'), v('recipient')), app(v('congregation'), v('recipient')))+']'
    actual = k('rfo', v('person'), v('activity'), audience, v('subject'), v('message'), v('context'),
        v('occurs'), v('presents'), v('conveys'))
    linked = both(app(v('serves'), v('person'), v('principal'), v('role'), v('context')),
        app(v('adopted'), v('principal'), v('standard'), v('criteria'), v('context')),
        app(v('positioned'), v('person'), v('activity'), v('role'), v('context')),
        app(v('entrusted'), v('person'), v('role'), v('context')))
    body = both(linked, actual, op('t', k('rfu', v('subject'), v('message'), v('criteria')), v('context')))
    text += definition('rfv', params(SETTINGS+RELATIONS), 'i[person a activity a][b context['+body+']]', 'h[a a] e')
    return text


MEANINGS = {
    'rfu': '同じ対象・発話記述に、明示した有限列の基準を同じ状況で適用し、全基準を満たすという内容。空列は真だが、未知の基準を空列へ置き換えない。基準が内容の真理や本人の信念を要求する場合だけ、それらも評価される。',
    'rfv': '同じ本人・活動・組織・委任された役割・採用基準・状況を結び、二つの受け手範囲の和集合へ同じ対象と発話記述を実際に伝達し、rfuの基準を満たすという内容を構成する。和集合は非空でなければならない。',
}
LIMITS = [
    '教えることの部分モデルとして、基準に従う実際の提示を扱う。受け手が理解・記憶・学習したことや、話者が信じていることは自動的に付けない。',
    '基準はNoemaで記述する関数の列であり、対訳語彙や自然言語の埋込みではない。列の採用・完全性・正当性と、各基準を満たすことは別の問題である。',
    '組織への奉仕と、その組織が同じ基準列を採用する関係は型付きのモデル入力。任命の歴史・受諾・制度上の正当性まで説明し終えたことにはしない。',
]


def generic_composed():
    text, basis = speech_document(); basis = deepcopy(basis)
    doc = parse(text+definitions())
    basis.update(version='prescribed-teaching-basis-v1', document='examples/v014/prescribed-teaching.noema')
    basis['definitions'].update(MEANINGS); basis['unresolved'] += LIMITS
    audit_basis(doc, basis)
    return format_graph(doc, 'compact')+'\n', basis


def source_composed():
    doc = parse((ROOT/PARENT).read_text(encoding='utf-8'))
    basis = deepcopy(json.loads((ROOT/'data/kant-enacted-standing-basis-v1.json').read_text(encoding='utf-8')))
    statements, doc['statements'] = doc['statements'], []
    text = definitions()
    text += definition('hzbe', params(SETTINGS), k('rfv', *args(SETTINGS), 'p cb', 'p cf', 'p dg', 'p f3', 'p f2'), 'h[a a] e')
    targets = [v(n) for n in ('issuer', 'person', 'role', 'action', 'teaching')]
    text += definition('hzbf', DUTY, k('h7a', *targets, TRUE, v('context')))
    text += definition('hzbg', DUTY, k('rdq', *targets, TRUE, v('context'), 'p h7a', 'p h7b'))
    public = [v(n) for n in ('person', 'speech', 'scholar', 'audience', 'channel', 'subject', 'criticism', 'context', 'authority')]
    text += definition('hzbh', DUTY+' '+PUBLIC, both(k('hzbf', *map(v, DUTY_NAMES.split())),
        op('u', op('e', v('action'), v('speech'))), k('h7c', *public)))
    doc = parse(format_graph(doc, 'compact')+text); doc['statements'] = statements
    basis.update(version='kant-prescribed-teaching-basis-v1', document='examples/v014/kant-prescribed-teaching.noema')
    basis['definitions'].update(MEANINGS | {
        'hzbe': '組織・役割・基準・二つの受け手範囲・対象・発話・基準列・奉仕と採用の関係を固定し、rfvを既存の役割分類cb、委任cf、生起dg、提示者f3、伝達f2へ接続する。',
        'hzbf': '同じ出所・本人・役割・活動へ、指定したteaching記述の成立が要求される。作例ではhzbeの閉じた適用を渡す。要求があるだけで講義済み・基準への適合・内容の真理を認定しない。',
        'hzbg': 'hzbfの要求があり、その同じ本人・活動への記述が現在不成立である。未履行を示すが、故意・拒否・責任・制裁を付けない。',
        'hzbh': 'hzbfの要求と、同じ本人による別活動の公的使用への積極的な許可が併存する。許可側で同じ出所による禁止がないことを要求する。実際の発言や、無制限の自由・学識者の使命までは意味しない。',
    })
    basis['unresolved'] += LIMITS + [
        'u0012の聖職者の教示義務へ部分接続する。学生と会衆は受け手範囲として渡し、教会のSymbolを採用された基準とその検査列へ結ぶ。教理・教会・宗教・聖職者という名詞の一般的な構成説明と、教理内容の完全な翻訳は未完。',
        '基準列による適合は明示した部分モデルであり、教義への適合の唯一の必要十分条件とはしない。原文が基準を有限列に列挙したという主張を追加しない。',
        'hzbfは任意の対象記述を受け取れる。教示の読みはhzbeを引用して固定した作例に限る。別記述へ同じ義務を移すことや、現在の教示内容を自動的に義務化することはしない。',
        '本人が完全に確信していないという後続箇所に向け、教示と真理・同意を区別できる。確信の程度、良心、真理の可能性、内的宗教との無矛盾、辞職の条件は未記述。',
        '受任条件から義務を説明するdenn、組織の名による発言、公的批判の慎重さ・善意・改革提案・使命、全文の意味一致は未完。既存15件の著者主張を保持する。',
    ]
    audit_basis(doc, basis)
    return format_graph(doc, 'compact')+'\n', basis


def core_composed():
    text, basis = source_composed(); doc = parse(text)
    selected = extract_document(doc, roots=['hzbe', 'hzbf', 'hzbg', 'hzbh'], statement_indices=[])
    projected = extract_basis(doc, basis, selected, version='prescribed-teaching-core-basis-v1', document_path='examples/v014/prescribed-teaching-core.noema')
    return format_graph(selected.document, 'compact')+'\n', projected


BUILDERS = ((generic_composed, 'prescribed-teaching'), (source_composed, 'kant-prescribed-teaching'), (core_composed, 'prescribed-teaching-core'))


def main():
    for builder, stem in BUILDERS:
        text, basis = builder()
        for name, body in ((basis['document'], text), ('data/'+stem+'-basis-v1.json', json.dumps(basis, ensure_ascii=False, indent=2)+'\n')):
            path = ROOT/name
            if path.exists():
                if path.read_text(encoding='utf-8') != body: raise ValueError('Stored teaching differs: '+name)
            else:
                with path.open('x', encoding='utf-8', newline='\n') as stream: stream.write(body)
        print(stem, len(text), 'characters')


if __name__ == '__main__': main()
