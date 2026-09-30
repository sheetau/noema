import pytest

from noema.finite_semantics import evaluate_document
from noema.grammar import parse


def run(text, primitives, *, enabled=True, domain=('first','second','third'), **kwargs):
    return evaluate_document(parse(text),individuals=domain,situations=('before','after'),
        primitives=primitives,memoize_expressions=enabled,**kwargs)


def test_repeated_subexpressions_depend_only_on_their_free_variables():
    text='''n:r aa[a] c.r ab[a] c.
q[f x a[f y a[w[e[k aa[v x]][k aa[v x]]][e[k ab[v y]][k ab[v y]]]]]].'''
    def measured(enabled):
        calls=[]
        def first(value):calls.append(('first',value));return value=='first'
        def second(value):calls.append(('second',value));return value=='second'
        result=run(text,{'aa':first,'ab':second},enabled=enabled)
        return result,calls
    ordinary,ordinary_calls=measured(False)
    cached,cached_calls=measured(True)
    assert ordinary==cached==[{'kind':'ask','value':True}]
    assert len(ordinary_calls)==36 and len(cached_calls)==12
    assert set(ordinary_calls)==set(cached_calls)


def test_lexical_captures_and_distinct_function_arguments_are_not_merged():
    text='''n:r aa[a a] c.r ab[a] c.r ac[a] c.r ad[] a.
d ba[x a] h[a] c[i[y a][k aa[v x v y]]].
d bb[fn h[a] c] c[c[v fn][k ad[]]].
q[f x a[f y a[z[c[k ba[v x]][v y]][k aa[v x v y]]]]].
q[k bb[p ab]].q[k bb[p ac]].'''
    primitives={'aa':lambda a,b:a==b,'ab':lambda a:True,'ac':lambda a:False,'ad':lambda:'first'}
    assert run(text,primitives)==run(text,primitives,enabled=False)==[
        {'kind':'ask','value':True},{'kind':'ask','value':True},{'kind':'ask','value':False}]


def test_content_binders_keep_each_situation_and_models_stay_isolated():
    text='''n:r aa[a d] c.r ab[] a.r ac[] d.
d ba[x a] e[b scene[k aa[v x v scene]]].
q[t[k ba[k ab[]]][k ac[]]].'''
    for scene in ('before','after'):
        for accepted in (False,True):
            primitives={'aa':lambda person,s:s=='before' and accepted,'ab':lambda:'first','ac':lambda:scene}
            assert run(text,primitives)==run(text,primitives,enabled=False)==[
                {'kind':'ask','value':scene=='before' and accepted}]


def test_nested_function_capture_retains_outer_parameters():
    text='''n:r aa[a a] c.
d ba[x a] h[a] h[a] c[i[y a][i[z a][w[k aa[v x v z]][k aa[v y v z]]]]].
q[f x a[f y a[f z a[z[c[c[k ba[v x]][v y]][v z]][w[k aa[v x v z]][k aa[v y v z]]]]]]].'''
    model={'aa':lambda a,b:a==b}
    assert run(text,model)==run(text,model,enabled=False)==[{'kind':'ask','value':True}]


def test_sequence_fold_bindings_and_question_answers_remain_exact():
    text='''n:r aa[b b] b.
d ba[values j[b] start b] b[q[v values][v start][i[state b item b][k aa[v state v item]]]].
q[e[k ba[l[b][n p b b n p c b] n p d b]][n p g b]].
q[e[k ba[l[b][n p b b n p c b] n p e b]][n p h b]].
q[j v[i[x a y a][e[v x][v y]]]].'''
    model={'aa':lambda a,b:a+b}
    result=run(text,model)
    assert result==run(text,model,enabled=False)
    assert result[:2]==[{'kind':'ask','value':True}]*2
    assert result[2]['answers']==[['first','first'],['second','second'],['third','third']]


def test_quotation_is_not_executed_and_disquotation_remains_checked():
    text='''n:r aa[] c.q[e[r[k aa[]]][r[k aa[]]]].'''
    def forbidden():raise AssertionError('Quotation was evaluated')
    assert run(text,{'aa':forbidden})==[{'kind':'ask','value':True}]
    with pytest.raises(AssertionError,match='Quotation was evaluated'):
        run('n:r aa[] c.q[s[r[k aa[]]]].',{'aa':forbidden})


@pytest.mark.parametrize('text',[
    'n:q[y[e[n p a b][n p b b]][f x b[e[v x][v x]]]].',
    'n:q[f x j[a][e[v x][v x]]].',
    'n:q[f x i[c][e[v x][v x]]].',
])
def test_unsupported_domains_are_not_skipped_or_sampled(text):
    for enabled in (False,True):
        with pytest.raises(ValueError,match='Cannot finitely quantify'):
            run(text,{},enabled=enabled)


def test_type_errors_budgets_and_strict_option_type_still_apply():
    with pytest.raises(ValueError,match='wrong result sort'):
        run('n:r aa[] c.q[k aa[]].',{'aa':lambda:'bad'})
    with pytest.raises(ValueError,match='step budget'):
        run('n:q[e[n p a b][n p a b]].',{},max_steps=1)
    with pytest.raises(ValueError,match='expression memoization option'):
        run('n:q[e[n p a b][n p a b]].',{},enabled=1)


def test_boolean_branches_remain_eager_and_default_does_not_reuse_calls():
    text='n:r aa[] c.q[y[e[n p a b][n p b b]][k aa[]]].'
    for enabled in (False,True):
        def invalid():raise ValueError('Required branch still evaluated')
        with pytest.raises(ValueError,match='Required branch still evaluated'):
            run(text,{'aa':invalid},enabled=enabled)
    doc=parse('n:r aa[a] c.q[f x a[f y a[k aa[v x]]]].')
    calls=[]
    def fact(person):calls.append(person);return True
    evaluate_document(doc,individuals=('first','second'),situations=('text',),primitives={'aa':fact})
    assert len(calls)==4
