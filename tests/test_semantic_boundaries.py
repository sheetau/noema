import pytest
from copy import deepcopy
from scripts.check_semantic_boundaries import *


def test_every_typed_binding_field_is_preserved_without_evaluation():
    extra=[primitive('fixturea',[],I),primitive('fixtureb',[],I),primitive('fixtureleft',[I,N],C),primitive('fixtureright',[I,N],C)]
    left=quote(ref('fixtureleft'));right=quote(ref('fixtureright'))
    package=call('boundcontentindividualnumber',left,call('fixturea'),num(20))
    fields=[(left,call('fixturea'),num(20)),(right,call('fixturea'),num(20)),
            (left,call('fixtureb'),num(20)),(left,call('fixturea'),num(21))]
    d=make(extra,[call('boundcontentmatchesindividualnumber',package,*xs) for xs in fields])
    assert values(d,dict(fixturea=lambda:'a',fixtureb=lambda:'b',fixtureleft=unknown,fixtureright=unknown))==[True,False,False,False]


def test_infinite_number_quantification_is_not_silently_sampled():
    body=call('missingvaluenumber',truth(True),truth(True),lam([('x',N)],truth(False)))
    d=make([], [body])
    with pytest.raises(ValueError,match='rational number domain'):values(d,{})


@pytest.mark.parametrize('slot',range(3))
def test_reported_support_cannot_borrow_another_source_claim_or_context(slot):
    extra=[primitive('fixturea',[],I),primitive('fixtureclaim',[],C),primitive('fixtureworld',[],S),
           primitive('fixturesupport',[I,DC,S],T)]
    d=make(extra,[call('reportedsupport',seq(I,[call('fixturea')]),quote(call('fixtureclaim')),call('fixtureworld'),ref('fixturesupport'))])
    wanted=['a','fixtureclaim','now'];wanted[slot]=['b','anotherclaim','later'][slot]
    m=dict(fixturea=lambda:'a',fixtureclaim=unknown,fixtureworld=lambda:'now',
        fixturesupport=lambda a,d,s:[a,json.loads(d.syntax)['symbol'],s]==wanted)
    assert values(d,m)==[False]


def test_inconsistent_belief_reports_do_not_assert_both_contents():
    extra=[primitive('fixturea',[],I),primitive('fixtureworld',[],S),primitive('fixturefact',[],T),
           *dependencies(['nonfactivecontentbelief'])]
    positive=dict(kind='content',variable='world',body=call('fixturefact'))
    negative=dict(kind='content',variable='world',body=neg(call('fixturefact')))
    bodies=[call('nonfactivecontentbelief',call('fixturea'),quote(x),call('fixtureworld')) for x in (positive,negative)]
    bodies+=[ev(positive,call('fixtureworld')),ev(negative,call('fixtureworld'))]
    d=make(extra,bodies)
    assert values(d,dict(fixturea=lambda:'a',fixtureworld=lambda:'now',fixturefact=lambda:True,
                        nonfactivecontentbelief=lambda person,description,world:True))==[True,True,True,False]


def test_dangling_reference_and_multiple_equations_are_not_valid_graphs():
    extra=[primitive('fixturenodes',[I],T),primitive('fixturepositive',[I,I],T),primitive('fixturenegative',[I,I],T),
           primitive('fixturegrounded',[I],T),primitive('fixturegiven',[I],T)]
    params=[ref('fixture'+n) for n in ('nodes','positive','negative','grounded','given')]
    d=make(extra,[call('truthgraphvalid',*params)])
    m=dict(fixturenodes=lambda x:x=='a',fixturepositive=lambda a,b:(a,b)==('a','b'),
           fixturenegative=lambda *xs:False,fixturegrounded=lambda x:False,fixturegiven=lambda x:True)
    assert values(d,m)==[False]
    m.update(fixturenodes=lambda x:True,fixturepositive=lambda a,b:a=='a')
    assert values(d,m)==[False]


def test_unbounded_process_can_be_stated_without_a_finite_horizon():
    # With a nonempty individual domain, lengths of arbitrary finite sequences
    # define exactly the nonnegative integer indices, without a maximum length.
    natural=definition('examplenatural',[('n',N)],T,q('exists','items',Q(I),
        eq(dict(kind='length',sequence=v('items')),v('n'))))
    step=app('edge',app('path',v('n')),app('path',call('rationaladd',v('n'),num(1))))
    path=definition('exampleunbounded',[('edge',REL),('path',F([N],I))],T,
        q('forall','n',N,op('implies',call('examplenatural',v('n')),step)))
    d=make([natural,path],[])
    from noema.constructed import format_graph
    from scripts.two_work_fastparse import parse_source
    assert parse_source(format_graph(d,'compact'))==d
