"""Derive a quotable action template and connect it to the partial permission claim."""
from copy import deepcopy
import json

from noema.grammar import parse as old_parse, format_graph as old_format
from noema.specialization import specialize_definition
from noema.extraction import _references
from noema.constructed import parse, format_graph, promote
from noema.constructed_discourse import normalize_document
from scripts.compose_constructed_purposes import ROOT, PARENT as LEGACY, DEFINITIONS as PURPOSES
from scripts.compose_public_divergent_judgments import FRAME
from scripts.compose_quantified_permissions import CLAIM, REFERENCES
from scripts.compose_origin_clock import definition, v
from scripts.compose_limits import call as k, app, both, op, quant
from scripts.compose_situated_criticism import params
from scripts.compose_described_norms import DESCRIPTION

PARENT = 'examples/v015/kant-quantified-permissions.noema'
SOURCE = 'examples/v016/kant-constructed-actions.noema'
CORE = 'examples/v016/constructed-actions-core.noema'
BASIS = 'data/constructed-actions-basis-v1.json'
INPUTS = [(name, type_ if name in ('owncriterion', 'standardcriterion') else 'i[' + type_ + ']')
          for name, type_ in FRAME if name not in ('message', 'goal')]
SELECTORS = [(name, 'h[a d] ' + type_) for name, type_ in INPUTS]
ELIGIBLE = [('person', 'a'), ('activity', 'a'), ('target', DESCRIPTION), ('anchor', 'd'),
    ('frames', 'h[a a a d] c'), ('roles', 'h[a d] a')] + SELECTORS
FIELD_SYMBOLS = {name: 'hzkfield' + chr(ord('a') + i) for i, (name, _) in enumerate(INPUTS)}


def action_template():
    """Abstract code and denotation separately from a verified static specialization.

    This authoring transform executes no model. Quoted placeholder references
    become description parameters; executable references become function parameters.
    The constructor later supplies each pair from the very same description.
    """
    doc = old_parse((ROOT / LEGACY).read_text(encoding='utf-8')); doc['statements'] = []
    placeholders = {'jtemplateown': ('templateownfn', 'templateowncode'),
                    'jtemplatestandard': ('templatestandardfn', 'templatestandardcode')}
    extra = ''.join('r ' + name + '[j[a]] e.' for name in placeholders)
    doc = old_parse(old_format(doc, 'compact') + extra)
    bindings = {index: {'kind': 'quote', 'body': {'kind': 'function_ref',
        'symbol': 'jtemplateown' if name == 'owncriterion' else 'jtemplatestandard'}}
        for index, (name, _) in enumerate(FRAME) if name in ('owncriterion', 'standardcriterion')}
    specialized = specialize_definition(doc, 'hzgy', 'jtemplatetarget', bindings)
    original = specialized.document['declarations'][-1]
    replacements = {'quoted': 0, 'executed': 0}
    def abstract(node):
        if isinstance(node, list):
            return [abstract(item) for item in node]
        if not isinstance(node, dict):
            return node
        if node.get('kind') == 'quote':
            body = node['body']
            if body.get('kind') == 'function_ref' and body['symbol'] in placeholders:
                replacements['quoted'] += 1
                return {'kind': 'variable', 'name': placeholders[body['symbol']][1]}
            if _references(node) & set(placeholders):
                raise ValueError('Placeholder occurs inside an unsupported quoted expression')
            return deepcopy(node)
        if node.get('kind') in ('function_ref', 'call') and node['symbol'] in placeholders:
            replacements['executed'] += 1
            variable = {'kind': 'variable', 'name': placeholders[node['symbol']][0]}
            return variable if node['kind'] == 'function_ref' else {
                'kind': 'apply', 'function': variable, 'arguments': abstract(node['arguments'])}
        return {key: abstract(value) for key, value in node.items()}
    prefix = []
    for index in (1, 2):
        type_ = doc['declarations'][next(i for i, d in enumerate(doc['declarations']) if d['name'] == 'hzgy')]['parameters'][index]['sort']
        pair = placeholders['jtemplateown' if index == 1 else 'jtemplatestandard']
        prefix.extend([{'name': pair[0], 'sort': deepcopy(type_['result'])}, {'name': pair[1], 'sort': deepcopy(type_)}])
    template = {**deepcopy(original), 'name': 'rqd', 'parameters': prefix + deepcopy(original['parameters']),
                'body': abstract(original['body'])}
    if _references(template) & set(placeholders):
        raise ValueError('Template retains placeholder symbols')
    return template, dict(disquotations_removed=specialized.disquotations_removed,
        expanded_definitions=specialized.expanded_definitions, replacements=replacements)


def construction_definitions():
    message = k('rqa', v('owncriterion'))
    purpose = k('rqb', v('recipient'), v('subject'), message)
    arguments = [v('owncriterion'), 'o r[' + v('owncriterion') + ']',
                 v('standardcriterion'), 'o r[' + v('standardcriterion') + ']']
    for name, _ in FRAME:
        if name in ('owncriterion', 'standardcriterion'):
            continue
        arguments.append('o r[' + (message if name == 'message' else purpose) + ']' if name in ('message', 'goal') else v(name))
    text = definition('rqe', params(INPUTS), 'o a[r[p rqd]][' + ' '.join(arguments) + ']', DESCRIPTION)
    text += definition('rqf', params([('target', DESCRIPTION)] + INPUTS), op('e', v('target'), k('rqe', *(v(name) for name, _ in INPUTS))))
    fields = {name: app(v(name), v('frame'), v('anchor')) for name, _ in INPUTS}
    match = k('rqf', v('target'), *(fields[name] for name, _ in INPUTS))
    role_matches = op('e', 's[' + fields['role'] + ']', app(v('roles'), v('person'), v('anchor')))
    body = quant('g', 'frame', 'a', both(app(v('frames'), v('person'), v('activity'), v('frame'), v('anchor')), role_matches, match))
    return text + definition('rqg', params(ELIGIBLE), body)


def append_constructors(doc):
    doc = deepcopy(doc)
    template, evidence = action_template()
    doc['declarations'].append(template)
    return parse(format_graph(doc, 'compact') + PURPOSES + construction_definitions()), evidence


def build_documents():
    parent = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    doc = promote(parent); statements, doc['statements'] = doc['statements'], []
    doc, evidence = append_constructors(doc)
    text = 'r hzkframe[a a a d] c.'
    for name, type_ in INPUTS:
        text += 'r ' + FIELD_SYMBOLS[name] + '[a d] ' + type_ + '.'
    fields = {name: 'p ' + FIELD_SYMBOLS[name] for name, _ in INPUTS}
    fields.update(person=v('person'), activity=v('activity'), target=v('target'), anchor=v('anchor'),
        frames='p hzkframe', roles=k(REFERENCES['roles']))
    text += definition('hzkeligible', params(ELIGIBLE[:4]), k('rqg', *(fields[name] for name, _ in ELIGIBLE)))
    arguments = {name: k(REFERENCES[name]) for name in REFERENCES}
    arguments.update(activities='p hzkeligible', anchor=v('context'), required='p h7a', permitted='p h7b')
    text += definition('hzkclaim', '', 'b context[' + k('rpu', *(arguments[name] for name, _ in CLAIM)) + ']', 'e')
    text += definition('hzkattribution', '', k('hzjn', k('hzjo'), k('wa'), 'r b[k hzkclaim[]]', k('hzjp'), k('wh')))
    doc = parse(format_graph(doc, 'compact') + text + 's[k hzkattribution[]].')
    doc['statements'] = statements[:-1] + doc['statements']
    by_name = {d['name']: d for d in doc['declarations']}
    pending, kept = _references(doc['statements'][-1:]), set()
    while pending:
        symbol = pending.pop()
        if symbol in kept:
            continue
        kept.add(symbol); pending.update(_references(by_name[symbol]) - kept)
    core = normalize_document({**doc, 'declarations': [d for d in doc['declarations'] if d['name'] in kept], 'statements': doc['statements'][-1:]})
    return {SOURCE: format_graph(doc, 'compact') + '\n', CORE: format_graph(core, 'compact') + '\n'}, evidence


def basis(documents, evidence):
    return dict(status='partial_constructed_action_eligibility_not_completed_translation', document=SOURCE,
        parent_document=PARENT, parent_basis='data/quantified-permissions-basis-v1.json', template_derivation=evidence,
        definitions=dict(rqd='hzgyを、基準の実行関数と同じ基準の記述を別引数とする、脱引用のない行為関数へ抽象化したもの。',
            rqe='同じ本人側基準と標準基準の記述から、実行関数と記述値の両方を渡す。主張rqaと目的rqbも内部で作り、閉じた行為記述を構成する。',
            rqf='対象記述が同じ入力から構成した行為記述に構文として一致する。任意の同義記述を認定するものではない。',
            rqg='本人・活動に選んだ枠のうち、対象記述が構成結果と一致し、構成で用いる公的役割が許可側の役割と一致する枠がある。',
            hzkeligible='rqgを文書の枠選択・各項目の記述・既存の役割指定へ接続する。',
            hzkclaim='既存rpuの資格条件をhzkeligibleへ変更する。他の対象者・義務・比較候補・権限側・役割・文脈の指定は保持する。',
            hzkattribution='改訂した内容を既存の著者・発話箇所・原文範囲・文脈へ帰属する。原文との意味一致を証明したものではない。'),
        fields={FIELD_SYMBOLS[name]: dict(role=name, signature=['individual', 'situation'], description_type=type_,
            meaning_ja='指定枠と基準文脈に対応する' + name + 'の閉じた記述。コードを実行せず行為記述へ組み込む。') for name, type_ in INPUTS},
        selection=dict(symbol='hzkframe', meaning_ja='本人・活動・枠・基準文脈の選択関係。判断や提示の成立そのものを原始述語で認定しない。'),
        unresolved=['枠の選択が対象となるすべての公的提示を尽くすかは未確認。構文一致は任意の同義表現より厳しい。',
            '一枠では一論点の提示を扱う。複数判断・洞察を一つの提示としてまとめる一般化は未完。',
            '基準コードと関数の一致はrqeの構成で保証する。rqdを直接任意の引数で呼ぶだけでは保証されない。',
            '静的特殊化の同値性は、値の等しさを尊重する全域的で純粋な解釈を前提とする。評価順序・資源消費の同一性は主張しない。',
            '人口・役割・君主への照応・職務範囲・比較候補の同定、なおさらの論証、原文全体の意味確認は未完。',
            '全記述域の評価は有限評価器では行わない。0.16は標準版に未採用で、原文対応範囲へ新規加算しない。'])


def main():
    documents, evidence = build_documents()
    files = documents | {BASIS: json.dumps(basis(documents, evidence), ensure_ascii=False, indent=2) + '\n'}
    for name, body in files.items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != body:
                raise ValueError('Existing constructed-action artifact differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(body)
        print(name, len(body), 'characters')


if __name__ == '__main__':
    main()
