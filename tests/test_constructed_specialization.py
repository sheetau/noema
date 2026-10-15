from copy import deepcopy
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_specialization import specialize_definition
from noema.constructed_semantics import evaluate_document


def quote(symbol):return dict(kind='quote',body=dict(kind='call',symbol=symbol,arguments=[]),rank=0)


def run(doc):
    return [r['value'] for r in evaluate_document(doc,individuals=('one','two'),situations=('now',),
        primitives={'aa':lambda:'one','ab':lambda:'two'})]


@pytest.mark.parametrize('names',[(),('aa',),('aa','ab'),('ab','aa','ab')])
def test_literal_fold_preserves_order_duplicates_and_empty_accumulator(names):
    doc=parse('p:r aa[] a.r ab[] a.d ac[items j[i[a]]] j[a][q[v items][l[a][]][i[values j[a] item i[a]][m[v values][l[a][s[v item]]]]]].')
    before=deepcopy(doc)
    binding=dict(kind='sequence',element=deepcopy(doc['declarations'][2]['parameters'][0]['sort']['element']),items=[quote(n) for n in names])
    result=specialize_definition(doc,'ac','ad',{0:binding})
    assert doc==before and result.literal_fold_steps==len(names) and result.disquotations_removed==len(names)
    inputs='l[i[a]]['+' '.join('r[k '+n+'[]]' for n in names)+']'
    expected='l[a]['+' '.join('k '+n+'[]' for n in names)+']'
    candidate=parse(format_graph(result.document,'compact')+'q[e[k ac['+inputs+']][k ad[]]].q[e[k ad[]]['+expected+']].')
    assert run(candidate)==[True,True]


def test_function_reference_fold_step_can_be_specialized_without_erasing_quote_identity():
    doc=parse('p:r aa[] a.r ab[] a.d ac[x a] a[v x].d ad[] a[k aa[]].'
        'd ae[acc c item i[a]] c[w[v acc][e[s[v item]][k aa[]]]].'
        'd af[items j[i[a]]] c[q[v items][e[n p a b][n p a b]][p ae]].')
    element=doc['declarations'][-1]['parameters'][0]['sort']['element']
    result=specialize_definition(doc,'af','ag',{0:dict(kind='sequence',element=element,items=[quote('aa')])})
    assert result.disquotations_removed==1
    assert run(parse(format_graph(result.document,'compact')+'q[k ag[]].'))==[True]


def test_bound_literal_and_inline_binders_cannot_capture_callers_variables():
    doc=parse('p:r aa[] a.r ab[] a.d ac[x a value i[a]] c[f y a[e[v x][s[v value]]]].'
        'd ad[x a y a z a value i[a]] c[k ac[v z v value]].')
    result=specialize_definition(doc,'ad','ae',{3:quote('aa')})
    candidate=parse(format_graph(result.document,'compact')+'q[f x a[f y a[k ae[v x v y k aa[]]]]].q[f z a[k ae[k aa[] k aa[] v z]]].')
    assert run(candidate)==[True,False]


@pytest.mark.parametrize('binding',[{}, {0:dict(kind='call',symbol='aa',arguments=[])}])
def test_unknown_description_is_not_guessed_or_executed(binding):
    doc=parse('p:r aa[] i[a].d ab[value i[a]] a[s[v value]].')
    with pytest.raises(ValueError,match='not statically'):specialize_definition(doc,'ab','ac',binding)


def test_unknown_sequence_cannot_make_dynamic_disquotation_quotable():
    doc=parse('p:d aa[items j[i[a]]] j[a][q[v items][l[a][]][i[acc j[a] item i[a]][m[v acc][l[a][s[v item]]]]]].')
    with pytest.raises(ValueError,match='not statically'):specialize_definition(doc,'aa','ab',{})


@pytest.mark.parametrize('body',[
    'r aa[] a.d ab[value i b[a]] a[s[v value]].',
    'r aa[] a.d ab[] a[s[r b[k aa[]]]].',
])
def test_higher_rank_disquotation_is_never_demoted(body):
    doc=parse('p:'+body)
    with pytest.raises(ValueError,match='Higher-rank'):specialize_definition(doc,'ab','ac',{})


@pytest.mark.parametrize('bindings',[{False:quote('aa')},{-1:quote('aa')},{1:quote('aa')},
    {0:dict(kind='variable',name='outside')},{0:dict(kind='number',numerator=1,denominator=1)}])
def test_invalid_positions_open_or_wrong_typed_bindings_fail(bindings):
    doc=parse('p:r aa[] a.d ab[value i[a]] a[s[v value]].')
    with pytest.raises(ValueError):specialize_definition(doc,'ab','ac',bindings)


def test_budget_names_unapplied_evaluator_and_old_editions_remain_restricted():
    doc=parse('p:r aa[] a.d ab[value i[a]] a[s[v value]].d ac[] h[i[a]] a[p ab].')
    for source,target,bindings,budget in [('aa','ad',{},1000),('ab','aa',{},1000),('ab','ad',{0:quote('aa')},1),
            ('ab','ad',{0:quote('aa')},0),('ac','ad',{},1000)]:
        with pytest.raises(ValueError):specialize_definition(doc,source,target,bindings,max_nodes=budget)
    legacy=deepcopy(doc);legacy['schema_version']='0.14'
    with pytest.raises(ValueError):specialize_definition(legacy,'ab','ad',{0:quote('aa')})


def test_unrelated_ranked_definitions_and_original_statements_are_preserved():
    doc=parse('p:r aa[] a.r ab[] a.d ac[value i[a]] a[s[v value]].d ad[] i b[a][r b[k aa[]]].q[e[k aa[]][k aa[]]].')
    result=specialize_definition(doc,'ac','ae',{0:quote('aa')})
    assert result==specialize_definition(doc,'ac','ae',{0:quote('aa')})
    assert result.document['declarations'][:-1]==doc['declarations'] and result.document['statements']==doc['statements']
    parse(format_graph(result.document,'compact')+'q[e[r[p ae]][r[p ae]]].')
