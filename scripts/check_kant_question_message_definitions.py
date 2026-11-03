"""Saved equivalence, question and message definitions; expression inventory."""
from copy import deepcopy
from functools import lru_cache
import ast,hashlib,json,time
from noema import constructed_discourse as native
from scripts.kant_page_public_context import ROOT,BRIDGE
from scripts.check_kant_function_definition_body import DICTIONARY,BASELINE
from scripts.kant_lexical_context import LexicalContext
from scripts.shared_modality import renamed
from scripts import kant_public_fragment as writing
from scripts.visible_syntax_geometry import to_svg,from_svg
from scripts.check_kant_multiple_arguments import measure,syntax_hash
from scripts.check_kant_questions_messages import pins as prior_pins
from scripts.kant_structural_trial import prepare as trial,report

ORIGINALS=('ev','hzs5','rqqp','rqwd')
OUT=ROOT/'output/kant-question-message-definitions'
RUN=ROOT/'.noema-project/runs/kant-question-message-definitions-v1'


def expression_inventory():
    """Check source branches, not semantic coverage or arbitrary layout success."""
    def function(path,name):
        return next(n for n in ast.walk(ast.parse((ROOT/path).read_text(encoding='utf-8')))
                    if isinstance(n,ast.FunctionDef) and n.name==name)
    def kinds(node,sets):
        result=set()
        for c in ast.walk(node):
            if not isinstance(c,ast.Compare) or not isinstance(c.left,ast.Name) or c.left.id!='kind':continue
            if len(c.ops)!=1 or not isinstance(c.ops[0],(ast.Eq,ast.In)):continue
            right=c.comparators[0]
            if isinstance(right,ast.Constant) and isinstance(right.value,str):result.add(right.value)
            elif isinstance(right,(ast.Tuple,ast.List,ast.Set)):
                if any(not isinstance(x,ast.Constant) or not isinstance(x.value,str) for x in right.elts):
                    raise ValueError('Unknown constructor membership test')
                result.update(x.value for x in right.elts)
            elif isinstance(right,ast.Name) and right.id in sets:result.update(sets[right.id])
            elif (isinstance(right,ast.Call) and isinstance(right.func,ast.Attribute)
                  and right.func.attr=='values' and isinstance(right.func.value,ast.Name)
                  and right.func.value.id in sets and not right.args and not right.keywords):
                result.update(sets[right.func.value.id])
            else:raise ValueError('Unclassified native constructor test: '+ast.unparse(c))
        return result
    accepted=kinds(function('noema/constructed_discourse.py','visit'),
                   {'LOGIC':native.LOGIC.values(),'QUANTIFIERS':native.QUANTIFIERS.values()})
    emitted=kinds(function('scripts/kant_public_fragment.py','split'),
                  {'SEQUENCE_FIELDS':writing.SEQUENCE_FIELDS,'APPLICATIONS':writing.APPLICATIONS})
    if accepted!=emitted:raise ValueError('Native expression branch gap: '+str((accepted-emitted,emitted-accepted)))
    return dict(native_expression_kinds=sorted(accepted),writer_expression_kinds=sorted(emitted),
                scope='Source-branch inventory only; statements, declarations and arbitrary geometry are not certified')


def relevant(value):
    if isinstance(value,list):return set().union(*(relevant(v) for v in value))
    if not isinstance(value,dict):return set()
    kind=value.get('kind')
    own={kind} if kind in ('iff','message','message_content','answer_matches') or kind=='question' and 'function' in value else set()
    return own|set().union(*(relevant(v) for v in value.values()))


@lru_cache(maxsize=1)
def inputs():
    prior=json.loads((ROOT/BASELINE).read_text(encoding='utf-8'))
    for name in (DICTIONARY,BRIDGE):
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=prior['source_sha256'][name]:
            raise ValueError('Saved definition input changed: '+name)
    published=json.loads((ROOT/DICTIONARY).read_text(encoding='utf-8'))
    bridge=json.loads((ROOT/BRIDGE).read_text(encoding='utf-8'));rows=[]
    for original in ORIGINALS:
        source=next(d for d in bridge['source_declarations'] if d['name']==original)
        declaration=next(d for d in published['native']['declarations'] if d['name']==bridge['mapping'][original])
        if renamed(source,bridge['mapping'])!=declaration:raise ValueError('Definition differs from its source/name bridge')
        body=deepcopy(declaration['body']);equation=declaration['result']!='truth'
        if equation:
            reference=dict(kind='call',symbol=declaration['name'],arguments=[dict(kind='variable',name=p['name']) for p in declaration['parameters']])
            body=dict(kind='equal',arguments=[body,reference])
        for p in reversed(declaration['parameters']):body=dict(kind='forall',variable=p['name'],sort=p['sort'],body=body)
        rows.append((declaration,dict(kind='assert',body=body),equation))
    return published,rows


def cases():return [(key,'既存定義 '+key+' の同値・質問・発話',row[1]) for key,row in zip(ORIGINALS,inputs()[1])]


@lru_cache(maxsize=4)
def checked(index):
    published,rows=inputs();declaration,source,equation=rows[index]
    started=time.perf_counter()
    drawing=writing.compile_statement(source,lexicon=LexicalContext.from_published(published),multiple=True)
    svg=to_svg(drawing['shapes'])
    recovered=writing.decode(list(reversed(from_svg(svg))),lexicon=LexicalContext.from_published(published))
    if recovered!=source:raise ValueError('Definition scope changed')
    body=recovered['body']
    for p in declaration['parameters']:
        if (body['kind'],body['variable'],body['sort'])!=('forall',p['name'],p['sort']):
            raise ValueError('Definition parameter changed')
        body=body['body']
    if equation:body=body['arguments'][0]
    if body!=declaration['body']:raise ValueError('Definition body changed')
    key,label,_=cases()[index]
    return dict(key=key,label=label,source=source,svg=svg,width=drawing['width'],seconds=time.perf_counter()-started,
        original_symbol=key,public_symbol=declaration['name'],declaration_sha256=syntax_hash(declaration),
        body_sha256=syntax_hash(body),syntax_sha256=syntax_hash(source),new_constructors=sorted(relevant(body)),
        diagnostic_equation=equation,branch_limits=drawing.get('branch_limits',[]),
        unbranched_paths=drawing.get('unbranched_paths',[]),**measure(svg))


def pins():
    result=prior_pins()
    for name in (DICTIONARY,BASELINE,BRIDGE,'reports/kant-questions-messages-v1.json',
                 'scripts/check_kant_question_message_definitions.py','tests/test_kant_question_message_definitions.py'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return dict(sorted(result.items()))


def prepare():
    expression_inventory()
    trial(out=OUT,run_path=RUN,pins=pins,cases=cases,checked=checked,preserved=lambda _:None,preserved_count=0,
        schema='kant-question-message-definitions-1',version=writing.VERSION,title='既存定義の同値・質問・発話を読む',
        intro='保存された定義本体を元の引数範囲で閉じ、同値・質問・発話を図形から読み戻します。',
        limits=['Four saved native definitions; wrappers are structural diagnostics, not declaration writing or new semantic assertions',
                'No saved answer_matches or message_content definition is claimed; independent cases cover those constructors',
                'Statement scopes, declarations, full-page integration and visual approval remain incomplete'])


def build_report():return dict(report(OUT,pins),expression_inventory=expression_inventory())
