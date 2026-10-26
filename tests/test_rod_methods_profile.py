from copy import deepcopy
from fractions import Fraction
import pytest
from noema.constructed_semantics import FunctionValue,evaluate_document
from scripts import check_einstein_rod_methods as check
from scripts import rod_methods_profile as profile
from scripts.rod_experiment_profile import RodExperimentVocabulary
from scripts.shared_modality import call,op
from scripts.name_presentation_profile import scalar_text


def forbidden(*args):raise AssertionError('Unselected or quoted content executed')
def cut(n):return FunctionValue(('number',),'truth',lambda q:q<n)
def handlers(doc):return {d['name']:forbidden for d in doc['declarations'] if d['kind']=='primitive'}
def context(doc):return handlers(doc)|{check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(check.BASE).items()}
def ask(body):return dict(kind='ask',body=body)
def run(doc,h):return [r['value'] for r in evaluate_document(doc,individuals=tuple(set(check.BASE.values())|{'other','setting','frame','rb','unit'}),situations=check.SITUATIONS,primitives=h)]
def abstract(d):
    if d['kind']=='definition':d['parameters']=[p['sort'] for p in d['parameters']]
    d['kind']='primitive';d.pop('body',None)


def test_profile_reuses_previous_contracts_and_adds_only_four_existing_relations():
    old=RodExperimentVocabulary();new=check.vocabulary()
    assert len(old._words)==660 and len(new._words)==664
    for field in ('entries','compounds','definitions','primitives'):
        assert all(new.document()[field][n]==d for n,d in old.document()[field].items())
    assert set(profile.SOURCE_RELATIONS)=={'eisl3','eisl4','eisl5','xz'}
    assert len(profile.CONTRACTS)==4


def test_visible_document_preserves_parent_and_exact_source_closure():
    doc=check.restored()['document'];assert doc==check.document()
    old=check.previous.document();ds={d['name']:d for d in doc['declarations']}
    assert all(ds[d['name']]==d for d in old['declarations'])
    assert doc['statements'][:43]==old['statements']
    assert (len(doc['declarations']),len(doc['statements']),len(check.source_excerpt()['declarations']))==(886,46,180)
    assert check.backprojection(doc)==check.source_excerpt()


def test_source_boundaries_reuse_forward_references_and_separate_naming_sentence():
    b=check.bridge();assert check.author.read(check.BRIDGE)==b
    assert b['source_statement_indices']==[91,92]
    assert b['sentence_positions']==dict(xw=[20,1],xx=[21,1],methodbnaming=[21,2])
    assert b['sentence_ranges']=={'einstein-1905:u0030':[[0,243]],'einstein-1905:u0031':[[0,238],[239,420]]}
    assert [r['id'] for r in b['math']]==['M0048']
    assert b['designation_positions']=={'eisl6':['methodbnaming',1]}
    assert b['annotations']['eisl6']['forms'][0]['text']=='Länge des Stabes'
    assert check.names()['xw']==check.previous.names()['xw']
    assert check.names()['xx']==check.previous.names()['xx']


def test_attribution_and_presentation_preserve_roles_scope_and_quoted_order():
    for rows,size in ((check.diagnostics(),10),(check.presentation_diagnostics(),16)):
        assert len(rows)==size and rows[0]['values']==[True,True]
        assert all(not all(r['values']) for r in rows[1:])
    trace=check.presentation_diagnostics()[0]['calls']
    permission=next(r for r in trace if r['relation']=='eisl5')
    assert permission['arguments'][4]==[['function_ref','eip2'],['function_ref','eip6']]


def test_native_sentence_and_designation_references_bind_distinct_targets():
    doc=deepcopy(check.restored()['document']);n=check.names()
    doc['declarations'].append(dict(kind='primitive',name='expected',parameters=[],result='individual'))
    for old in ('xw','xx','methodbnaming','eisl6'):
        doc['statements']=[ask(op('equal',call(n[old]),call('expected')))]
        h=context(doc)|dict(expected=lambda:check.BASE[old]);assert run(doc,h)==[True]
        h['expected']=lambda:'other';assert run(doc,h)==[False]


@pytest.mark.parametrize('field',range(4))
def test_designation_rejects_every_unknown_reference_component(field):
    h=check.context_handlers(check.BASE)['designationreference']
    key=[check.BASE['eirf'],check.BASE['methodbnaming'],1,check.BASE['ri']]
    assert h(*key)==check.BASE['eisl6']
    key[field]=2 if field==2 else 'unknown'
    with pytest.raises(ValueError):h(*key)


def test_new_coordinates_are_exact_positive_integers_and_do_not_alias_first_sentence():
    h=check.context_handlers(check.BASE);ctx=check.BASE['ri']
    assert h['sentencereference'](ctx,Fraction(21),Fraction(2))==check.BASE['methodbnaming']
    assert h['sentencereference'](ctx,21,1)==check.BASE['xx']
    for bad in (True,2.0,Fraction(3,2),0,-1):
        with pytest.raises(ValueError):h['sentencereference'](ctx,21,bad)
        with pytest.raises(ValueError):h['designationreference'](check.BASE['eirf'],check.BASE['methodbnaming'],bad,ctx)
    with pytest.raises(ValueError):h['sentencereference']('unknown',21,2)


def test_printed_designation_preserves_exact_unicode_without_claiming_its_meaning():
    doc=deepcopy(check.restored()['document']);doc['statements']=doc['statements'][-1:]
    expected=('eisl6','de','Länge des Stabes','body');seen=[]
    def form(name,language,text,ctx):
        row=(name,scalar_text(language),scalar_text(text),ctx);seen.append(row);return row==expected
    h=context(doc);h[check.vocabulary()._symbols['printedform']]=form
    assert run(doc,h)==[True] and seen==[expected]
    for changed in ('eisl6','ri'):
        values=check.BASE|{changed:'front' if changed=='ri' else 'other'}
        h.update({check.vocabulary()._symbols[k]:f for k,f in check.context_handlers(values).items()})
        h[check.vocabulary()._symbols['printedform']]=form
        assert run(doc,h)==[False]


def test_native_localization_body_binds_both_endpoint_records_and_same_specified_time():
    # Keep the native eip5 body; abstract its already-reviewed physical premises.
    # Changing one slot at a time diagnoses binding, not the full real domain.
    doc=deepcopy(check.restored()['document']);n=check.names();m=check.mapping()
    for d in doc['declarations']:
        if d['name'] in (n['eipk'],n['eip4']):abstract(d)
    doc['statements']=[ask(call(n['eip5'],call(n['yf'])))]
    for failed in (None,'eipk','eip4','first','last'):
        seen=[]
        def locate(observer,endpoint,event,clock,place,frame,unit,time,ctx):
            row=(observer,endpoint,event,clock,place,frame,unit,time(Fraction(0)),time(Fraction(1)),ctx)
            seen.append(row)
            expected=[('xk','xn','xp','xr','xt','frame','rb',True,False,'methodb'),
                      ('xk','xo','xq','xs','xu','frame','rb',True,False,'methodb')]
            assert row in expected
            return failed!=('first' if endpoint=='xn' else 'last')
        h=context(doc)|{n[k]:(lambda *args,k=k:k!=failed) for k in ('eipk','eip4')}
        h[m['eisl4']]=locate
        assert run(doc,h)==[failed is None]
        if failed is None:assert len(seen)==2


def test_native_method_a_and_hypothetical_comparison_keep_value_frame_and_setting():
    doc=deepcopy(check.restored()['document']);n=check.names();m=check.mapping()
    boundaries=('sbi','eipy','eipz')
    for d in doc['declarations']:
        if d['name'] in {m[k] for k in boundaries}:abstract(d)
    doc['declarations'].append(dict(kind='primitive',name='candidate',parameters=[],result=profile.CUT))
    for target,frame,used in [('eip2','xl',boundaries),('eip3','frame',('eipz',))]:
        doc['statements']=[ask(call(n[target],call('candidate'),call(n['ye'])))]
        for threshold in (0,1):
            for failed in (None,*used):
                seen=[]
                def boundary(name,args):
                    seen.append(name)
                    if name=='eipy':assert args==('methoda',)
                    else:
                        assert [args[0](Fraction(q)) for q in (0,1)]==[q<threshold for q in (0,1)]
                        assert args[1:]==((frame,'methoda') if name=='eipz' else ('methoda',))
                    return name!=failed
                h=context(doc)|dict(candidate=lambda:cut(threshold))
                h.update({m[k]:(lambda *args,k=k:boundary(k,args)) for k in boundaries})
                assert run(doc,h)==[failed is None]
                if failed is None:assert seen==list(used)


def test_changed_method_definition_or_name_binding_cannot_reuse_evidence():
    for old in (*check.NEW_DEFINITIONS,'methodbnaming','eisl6'):
        doc=deepcopy(check.document());ds={d['name']:d for d in doc['declarations']}
        ds[check.names()[old]]['body']=dict(kind='truth',value=True)
        with pytest.raises(ValueError,match='Changed migration'):check.backprojection(doc)
