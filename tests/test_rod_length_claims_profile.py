from copy import deepcopy
from fractions import Fraction
from itertools import product
import json
import pytest
from noema.constructed_semantics import FunctionValue,evaluate_document
from noema.meaning_catalog import _references
from scripts import check_einstein_rod_length_claims as check
from scripts import rod_length_claims_profile as profile
from scripts.rod_methods_profile import RodMethodsVocabulary
from scripts.shared_modality import call,op
from scripts.name_presentation_profile import scalar_text


def forbidden(*args):raise AssertionError('Unselected or quoted content executed')
def cut(n):return FunctionValue(('number',),'truth',lambda q:q<n)
def handlers(doc):return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
def context(doc,**kwargs):return handlers(doc)|{check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE,**kwargs).items()}
def ask(body):return dict(kind='ask',body=body)
def run(doc,h,individuals=None):return [r['value'] for r in evaluate_document(doc,individuals=individuals or tuple(set(check.BASE.values())|{'other','setting','frame','rb'}),situations=check.SITUATIONS,primitives=h)]
def abstract(d):
    if d['kind']=='definition':d['parameters']=[p['sort'] for p in d['parameters']]
    d['kind']='primitive';d.pop('body',None)


def fixture(target,boundaries):
    doc=deepcopy(check.restored()['document']);n=check.names();m=check.mapping()
    for d in doc['declarations']:
        if d['name'] in {m[k] for k in boundaries}:abstract(d)
    ds={d['name']:d for d in doc['declarations']};seen=set()
    def visit(name):
        if name in seen:return
        seen.add(name)
        for ref in _references(ds[name].get('body')):visit(ref)
    visit(n[target]);doc['declarations']=[d for d in doc['declarations'] if d['name'] in seen];doc['statements']=[]
    return doc


def test_profile_preserves_all_previous_words_and_reuses_four_old_contracts():
    old=RodMethodsVocabulary();new=check.vocabulary()
    assert len(old._words)==664 and len(new._words)==668
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new.document()[field][n]==d for n,d in old.document()[field].items())
    assert set(profile.SOURCE_RELATIONS)=={'eisl7','zb','zc','zd'} and len(profile.CONTRACTS)==4


def test_visible_document_preserves_parent_and_complete_selected_source():
    doc=check.restored()['document'];assert doc==check.document()
    old=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations']) and doc['statements'][:46]==old['statements']
    assert (len(doc['declarations']),len(doc['statements']),len(check.source_excerpt()['declarations']))==(916,50,247)
    assert check.backprojection(doc)==check.source_excerpt()


def test_original_positions_names_and_both_initial_length_symbols():
    b=check.bridge();assert check.author.read(check.BRIDGE)==b
    assert b['source_statement_indices']==[93,94] and b['sentence_positions']==dict(zg=[22,1],zh=[23,1])
    assert b['sentence_ranges']=={'einstein-1905:u0032':[[0,195]],'einstein-1905:u0033':[[0,239]]}
    assert [r['id'] for r in b['math']]==['M0049','M0050']
    assert all(r['binding']=='ya; initial rest length from u0029' for r in b['math'])
    assert b['designation_positions']==dict(eisma=['zg',1],eismb=['zh',1])
    assert '(bewegten)' in b['annotations']['eismb']['forms'][0]['text']
    assert b['later_context']['completed_here'] is False


def test_attribution_and_presentation_keep_necessity_forecast_and_unexecuted_quotes():
    for rows,size in ((check.diagnostics(),9),(check.presentation_diagnostics(),17)):
        assert len(rows)==size and rows[0]['values']==[True,True]
        assert all(not all(r['values']) for r in rows[1:])
    calls=check.presentation_diagnostics()[0]['calls']
    assert next(r['arguments'][4] for r in calls if r['relation']=='zd')==[['call','eion'],['call','eiot']]
    assert next(r['arguments'][2:4] for r in calls if r['relation']=='zc')==[['call','eion'],['call','eiqh']]


def test_native_role_references_bind_naming_passages_and_later_argument_without_evaluation():
    doc=deepcopy(check.restored()['document']);n=check.names()
    doc['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
    for old in (*check.SENTENCES,*check.DESIGNATIONS,*check.ROLE_ASSIGNMENTS):
        doc['statements']=[ask(op('equal',call(n[old]),call('expected')))]
        h=context(doc)|dict(expected=lambda:check.BASE[old]);assert run(doc,h)==[True]
        h['expected']=lambda:'other';assert run(doc,h)==[False]
    # Roles may mention the designation and quoted method, never their own referent.
    ds={d['name']:d for d in doc['declarations']};done=set()
    def visit(name,stack):
        assert name not in stack,'Cyclic reference'
        if name in done:return
        for ref in _references(ds[name].get('body')):visit(ref,stack|{name})
        done.add(name)
    for old in check.ROLE_ASSIGNMENTS:visit(n[old],set())


@pytest.mark.parametrize('field',range(4))
def test_native_roles_reject_every_unknown_key(field):
    doc=deepcopy(check.document());n=check.names()
    for old,(anchor,_) in check.ROLE_ASSIGNMENTS.items():
        roles=check.role_model(check.BASE)
        key=(check.BASE['eirf'],check.BASE[anchor],check.canonical(dict(kind='function_ref',symbol=check.reference_roles()[old])),check.BASE['ri'])
        value=roles.pop(key);bad=list(key);bad[field]='unknown';roles[tuple(bad)]=value
        doc['statements']=[ask(op('equal',call(n[old]),call(n[old])))]
        with pytest.raises(ValueError,match='Unknown temporal reference'):run(doc,context(doc,roles=roles))


def test_native_role_bodies_preserve_the_naming_and_later_relations():
    doc=deepcopy(check.restored()['document']);n=check.names();m=check.mapping();inverse={v:k for k,v in m.items()}
    doc['declarations'].append(dict(kind='primitive',name='candidate',parameters=[],result='individual'))
    for old,role in check.reference_roles().items():
        relation='eisci' if old=='zi' else 'eisl7';facts=check.presentation_facts()[relation]
        doc['statements']=[ask(call(role,call('candidate'),call(n['ri'])))]
        for candidate in (check.BASE[old],'other'):
            seen=[]
            def accept(*args):
                args=list(args)
                if relation=='eisl7':
                    for slot in (3,4):
                        expr=json.loads(args[slot].syntax);args[slot]=(expr['kind'],inverse[expr['symbol']])
                seen.append(tuple(args));return tuple(args) in facts
            h=context(doc)|dict(candidate=lambda:candidate);h[m[relation]]=accept
            assert run(doc,h)==[candidate==check.BASE[old]] and seen[0][0]==candidate


def test_designations_preserve_exact_unicode_and_do_not_alias_the_previous_label():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][-2:]
    expected={(old,'de',text,'body') for old,text in check.FORMS.items()};seen=[]
    def form(name,language,text,ctx):
        row=(name,scalar_text(language),scalar_text(text),ctx);seen.append(row);return row in expected
    h=context(doc);h[check.vocabulary()._symbols['printedform']]=form
    assert run(doc,h)==[True,True] and set(seen)==expected
    for old in check.DESIGNATIONS:
        values=check.BASE|{old:'eisl6'}
        h.update({check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(values).items()})
        h[check.vocabulary()._symbols['printedform']]=form
        assert run(doc,h)==([False,True] if old=='eisma' else [True,False])
    refs=check.context_handlers(check.BASE)
    for old,(node,item) in check.DESIGNATIONS.items():
        key=[check.BASE['eirf'],check.BASE[node],item,check.BASE['ri']]
        for field in range(4):
            bad=list(key);bad[field]=2 if field==2 else 'unknown'
            with pytest.raises(ValueError):refs['designationreference'](*bad)


def project_carrier(node):
    if node==profile.CUT:return 'individual'
    if isinstance(node,dict):return {k:project_carrier(v) for k,v in node.items()}
    if isinstance(node,list):return [project_carrier(v) for v in node]
    return node


def test_quantified_comparison_requires_one_value_not_one_representation():
    # Finite carrier projection of the real Native quantifiers, not a real-domain proof.
    n=check.names();m=check.mapping();domain=('base','alias','different');numbers=dict(base=5,alias=5,different=4)
    for target,method,setting,equal in [('eiqh','eip2','ye',True),('eiqi','eip6','yf',False)]:
        native=fixture(target,('ya','ye','yf','eip2','eip6','sbg','sca'))
        native['statements']=[ask(dict(kind='evaluate',content=call(n[target]),situation=dict(kind='call',symbol='testcontext',arguments=[])))]
        native['declarations'].append(dict(kind='primitive',name='testcontext',parameters=[],result='situation'))
        doc=project_carrier(native)
        for bits in product((False,True),repeat=3):
            selected={x for x,b in zip(domain,bits) if b};values={numbers[x] for x in selected}
            for valid,correct_setting in product((False,True),repeat=2):
                h=handlers(doc)|{n['ya']:lambda:'base',n[setting]:lambda:check.BASE[setting] if correct_setting else 'front',
                    m['sbg']:lambda x:valid or numbers[x]!=5,m['sca']:lambda x,y:numbers[x]==numbers[y],
                    n[method]:lambda x,s:x in selected and s==check.BASE[setting],'testcontext':lambda:'body'}
                expected=valid and correct_setting and len(values)==1 and ((next(iter(values))==5)==equal)
                assert run(doc,h,domain)==[expected]
        h=handlers(native)|{n['ya']:lambda:cut(1),n[setting]:lambda:check.BASE[setting],n[method]:lambda *args:True,m['sbg']:lambda *args:True,m['sca']:lambda *args:True,'testcontext':lambda:'body'}
        with pytest.raises(ValueError,match='Cannot finitely quantify the rational number domain'):run(native,h)


def test_native_candidate_condition_keeps_validity_measurement_and_comparison_slots():
    doc=fixture('sbx',());n=check.names();target=next(d for d in doc['declarations'] if d['name']==n['sbx'])
    slots=('slota','slotb','slotc','slotd','slote')
    for name,p in zip(slots,target['parameters'],strict=True):doc['declarations'].append(dict(kind='primitive',name=name,parameters=[],result=p['sort']))
    doc['statements']=[ask(call(n['sbx'],*[call(name) for name in slots]))]
    for valid_candidate,valid_base,measured,compared in product((False,True),repeat=4):
        # Two explicit cuts are distinguished only for this binding diagnostic.
        which=lambda value:bool(value(Fraction(0)))
        h=dict(slota=lambda:cut(0),slotb=lambda:cut(1),
            slotc=lambda:FunctionValue((profile.CUT,),'truth',lambda x:measured and not which(x)),
            slotd=lambda:FunctionValue((profile.CUT,),'truth',lambda x:valid_base if which(x) else valid_candidate),
            slote=lambda:FunctionValue((profile.CUT,profile.CUT),'truth',lambda x,y:compared and not which(x) and which(y)))
        assert run(doc,h)==[all((valid_candidate,valid_base,measured,compared))]


def test_native_question_accepts_candidates_without_asserting_a_unique_answer():
    doc=fixture('eiqj',('eip6','yf'));n=check.names();d=next(d for d in doc['declarations'] if d['name']==n['eiqj'])
    doc['declarations'].append(dict(kind='primitive',name='capture',parameters=[d['result']],result='truth'))
    doc['statements']=[ask(call('capture',call(n['eiqj'])))]
    for selected in (set(),{False},{False,True}):
        for setting in ('methodb','front'):
            captured=[]
            def capture(q):captured.append(q);return True
            h=handlers(doc)|{n['yf']:lambda:setting,n['eip6']:lambda value,s:s=='methodb' and bool(value(Fraction(0))) in selected,'capture':capture}
            assert run(doc,h)==[True]
            for i in (0,1):assert captured[0].function(cut(i))==(setting=='methodb' and bool(i) in selected)


def test_changed_composition_roles_or_names_cannot_reuse_prior_evidence():
    for old in (*check.NEW_DEFINITIONS,*check.ROLE_HELPERS,*check.ROLE_ASSIGNMENTS,*check.DESIGNATIONS):
        doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']}
        ds[check.names()[old]]['body']=dict(kind='truth',value=True)
        with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)
