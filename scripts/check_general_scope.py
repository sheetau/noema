"""Cross-domain quantifier-scope contrasts with two roles and two witnesses each."""
import json
from noema.constructed import format_graph
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document
from scripts.shared_modality import v, call, op
from scripts.shared_time import q
from scripts.two_work_inventory import ROOT, sha
from scripts.general_language_release import save_text

LIBRARY='examples/v016/general-scope-contrasts-v1.noema'
BASIS='data/general-scope-contrasts-v1.json'


def document():
    ds=[dict(kind='primitive',name=n,parameters=ps,result=result) for n,ps,result in
        [('person',['individual'],'truth'),('object',['individual'],'truth'),
         ('related',['individual','individual','situation'],'truth'),('context',[],'situation')]]
    relation=call('related',v('reader'),v('item'),call('context'))
    has=q('exists','item','individual',op('and',call('object',v('item')),relation))
    each=q('forall','reader','individual',op('implies',call('person',v('reader')),has))
    common=q('exists','item','individual',op('and',call('object',v('item')),
        q('forall','reader','individual',op('implies',call('person',v('reader')),relation))))
    nobody=q('forall','reader','individual',op('implies',call('person',v('reader')),op('not',has)))
    return normalize_document(dict(schema_version='0.16',lexicon_version='0.16',declarations=ds,
        statements=[dict(kind='ask',body=x) for x in (each,common,op('not',each),nobody)]))


MODELS=[('different-witnesses',[('p','x'),('q','y')],[True,False,False,False]),
        ('one-person',[('p','x')],[False,False,True,False]),
        ('no-witness',[],[False,False,True,True]),
        ('shared-witness',[('p','x'),('q','x')],[True,True,False,False])]


def values(pairs,*,context='now',transpose=False):
    interpretation=dict(person=lambda x:x in ('p','q'),object=lambda x:x in ('x','y'),context=lambda:context,
        related=lambda person,item,world:((item,person) if transpose else (person,item)) in pairs and world=='now')
    return [r['value'] for r in evaluate_document(document(),individuals=('p','q','x','y'),situations=('now','later'),primitives=interpretation)]


def prepare():
    save_text(LIBRARY,format_graph(document(),'compact')+'\n')
    save_text(BASIS,json.dumps(dict(statement_order=['各人に関係する対象がある','全員に共通して関係する対象がある','対象を持たない人がいる','全員が対象を持たない'],
        interpretations=[dict(topic='読書',person='読者の全範囲',object='本の全範囲',related='同じ時点までに本人がその本を読んだ'),
                         dict(topic='配送',person='配達担当者の全範囲',object='配送先の全範囲',related='同じ時点までに本人がその配送先へ届けた')],
        model_domain=['p','q','x','y'],models=[dict(name=n,relations=pairs,expected=expected) for n,pairs,expected in MODELS],
        contract='person/objectは役割ごとの全範囲、relatedはperson→object→situationの順。結果から範囲を選ばない。語義ごとに入力解釈を固定する。',
        boundary='同じ構文を読書と配送の二つの明示解釈で使う。実在の読者や配送記録についての事実認定ではない。'),ensure_ascii=False,indent=2)+'\n')


def build_report():
    rows=[]
    for topic in ('reading','delivery'):
        for n,pairs,expected in MODELS:
            result=values(pairs);assert result==expected
            rows.append(dict(topic=topic,model=n,values=result))
    assert values(MODELS[-1][1],transpose=True)==[False,False,True,True]
    assert values(MODELS[-1][1],context='later')==[False,False,True,True]
    paths=[LIBRARY,BASIS,'scripts/check_general_scope.py','scripts/shared_modality.py','scripts/shared_time.py',
           'noema/constructed.py','noema/constructed_discourse.py','noema/constructed_semantics.py']
    return dict(schema='noema-general-scope-1',interpretations=rows,role_reversal_rejected=True,context_shift_distinguished=True,
                source_sha256={p:sha(p) for p in paths},boundary='4対象・2状況の識別例。任意の領域での完全性証明ではない。')
