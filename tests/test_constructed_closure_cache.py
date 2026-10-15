import pytest
from noema.constructed import parse,promote
from noema.constructed_semantics import evaluate_document as historical
from noema.constructed_closure_semantics import evaluate_document
from scripts.check_runtime_quotation import ROUTES,route_document,CHAIN,TRUE


def run(doc,model,*,enabled=True,**options):
    if isinstance(doc,str):doc=parse(doc)
    return evaluate_document(doc,individuals=('alice','bob','carol'),situations=('before','after'),primitives=model,
        memoize_definitions=True,memoize_expressions=True,memoize_closures=enabled,**options)


def test_reuse_depends_on_free_values_not_unrelated_quantifier_bindings():
    text='''p:r aa[h[a] c] c.r ac[] a.
d ab[fn h[a] c unused a] c[k aa[v fn]].
q[f x a[f y a[e[k ab[i[z a][e[v z][v x]] v y]][e[v x][k ac[]]]]]].'''
    def measure(enabled):
        calls=[]
        def apply(fn):calls.append(fn);return fn('alice')
        return run(text,{'aa':apply,'ac':lambda:'alice'},enabled=enabled),calls
    old,oldcalls=measure(False);new,newcalls=measure(True)
    assert old==new==[{'kind':'ask','value':True}]
    assert len(oldcalls)==9 and len(newcalls)==3
    assert [f('alice') for f in newcalls]==[True,False,False]


def test_nested_captures_distinct_functions_and_models_remain_distinct():
    text='''p:r aa[a a] c.r ab[a] c.r ac[a] c.r ad[] a.
d ba[x a] h[a] h[a] c[i[y a][i[z a][w[k aa[v x v z]][k aa[v y v z]]]]].
d bb[fn h[a] c] c[c[v fn][k ad[]]].
q[f x a[f y a[f z a[z[c[c[k ba[v x]][v y]][v z]][w[k aa[v x v z]][k aa[v y v z]]]]]]].
q[k bb[p ab]].q[k bb[p ac]].'''
    for accepted in (False,True):
        model={'aa':lambda a,b:a==b,'ab':lambda a:accepted,'ac':lambda a:not accepted,'ad':lambda:'alice'}
        assert run(text,model)==run(text,model,enabled=False)==[
            {'kind':'ask','value':True},{'kind':'ask','value':accepted},{'kind':'ask','value':not accepted}]


@pytest.mark.parametrize('route',ROUTES)
@pytest.mark.parametrize('ceiling',range(3))
@pytest.mark.parametrize('target',(None,0,1,2))
def test_higher_order_routes_keep_creation_and_invocation_ceilings(route,ceiling,target):
    doc=promote(route_document(route,ceiling,target));model={'touch':lambda:True}
    if route=='callback':model['bridge']=lambda fn:fn()
    if target is None or target<ceiling:
        assert run(doc,model)==run(doc,model,enabled=False)==[{'kind':'ask','value':True}]
    else:
        for enabled in (False,True):
            with pytest.raises(ValueError,match='Runtime quotation ceiling'):run(doc,model,enabled=enabled)


def test_warming_a_closure_outside_a_quote_does_not_reuse_its_unrestricted_ceiling_inside():
    text=CHAIN.replace('o:','p:',1)+'d probe[] c[s[k aa[]]].'
    text+='d template[] i[h[h[] c] c][r[i[fn h[] c][c[v fn][]]]].'
    text+='q[k probe[]].q[c[s[k template[]]][p probe]].'
    calls=[]
    with pytest.raises(ValueError,match='Runtime quotation ceiling'):
        run(text,{'touch':lambda:calls.append(True) is None})
    assert calls==[True]


def test_quotes_are_opaque_and_required_errors_are_not_suppressed():
    def forbidden():raise ValueError('Required evaluation')
    assert run('p:r aa[] c.q[e[r[k aa[]]][r[k aa[]]]].',{'aa':forbidden})==[{'kind':'ask','value':True}]
    with pytest.raises(ValueError,match='Required evaluation'):run('p:r aa[] c.q[s[r[k aa[]]]].',{'aa':forbidden})
    with pytest.raises(ValueError,match='Required evaluation'):
        run('p:r aa[] c.q[y[u['+TRUE+']][k aa[]]].',{'aa':forbidden})


def test_default_keeps_historical_execution_and_strict_options_and_budgets():
    doc=parse('p:r aa[a] c.q[f x a[f y a[k aa[v x]]]].')
    results=[]
    for engine in (historical,evaluate_document):
        calls=[]
        result=engine(doc,individuals=('alice','bob'),situations=('now',),primitives={'aa':lambda x:calls.append(x) is None})
        results.append((result,calls))
    assert results[0]==results[1] and len(results[0][1])==4
    with pytest.raises(ValueError,match='closure memoization option'):run('p:q['+TRUE+'].',{},enabled=1)
    with pytest.raises(ValueError,match='step budget'):run('p:q['+TRUE+'].',{},max_steps=1)


def test_unsupported_domains_still_fail_instead_of_sampling():
    with pytest.raises(ValueError,match='Cannot finitely quantify'):
        run('p:q[f x i[c][e[v x][v x]]].',{})
