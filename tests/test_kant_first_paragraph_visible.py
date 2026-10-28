"""Check the complete paragraph with actual references and opaque quotations."""
import json
import pytest
from copy import deepcopy
from scripts import check_kant_first_paragraph_visible as check
from scripts.shared_modality import renamed,call
from noema.constructed_semantics import evaluate_document
import test_kant_title_author_visible as parent

NODES=('first','second','third','latin','german','conclusion')
DOMAIN=('use','designation','author','document','title','signature','quotedwhole','reader','other',*NODES)


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=('body','closing','other'),
        primitives=values,max_steps=1000000,memoize_definitions=False,memoize_expressions=False)]


def model(doc,variant='baseline'):
    values=parent.model(doc);voc=check.vocabulary();inverse={v:k for k,v in check.mapping().items()}
    syntax=lambda code:renamed(json.loads(code.syntax),inverse)
    def sentence(context,paragraph,index):
        if context!='closing' or paragraph!=1 or index not in (1,2,3,4):raise ValueError('Unknown paragraph sentence')
        return ('first','second','third','quotedwhole')[int(index)-1]
    def span(document,first,a,last,b,context):
        if (document,first,last,context)!=('document','quotedwhole','quotedwhole','closing'):raise ValueError('Unknown paragraph span')
        known={(1,2):'latin',(3,10):'german',(11,16):'conclusion'}
        if (a,b) not in known:raise ValueError('Unknown paragraph span')
        return known[a,b]
    def context(author,point):return (author,point)==('other' if variant=='other_author' else 'author','other' if variant=='other_context' else 'body')
    def definition(node,author,code,point):
        return context(author,point) and syntax(code)==dict(kind='function_ref',symbol={'first':'bi','second':'bf'}.get(node))
    def quoted(node,author,code,point):
        selected={'latin':'hzsi','german':'bn'}
        if variant=='swapped_quotes':selected={'latin':'bn','german':'hzsi'}
        return context(author,point) and syntax(code)==call(selected.get(node),call('ao'))
    def claimed(node,author,code,point):
        if variant=='missing_condition' and node=='third' or variant=='missing_conclusion' and node=='conclusion':return False
        return context(author,point) and syntax(code)==call({'third':'rqrk','conclusion':'hzsk'}.get(node))
    def before(a,b,point):
        return point=='body' and a in NODES and b in NODES and (NODES.index(a)>NODES.index(b) if variant=='reverse_order' else NODES.index(a)<NODES.index(b))
    reference=check.profile.QuotedAddresseeReferences({('document','latin','closing'):'reader'})
    handlers=dict(sentencereference=sentence,sentencetokenspanreference=span,quotedaddresseereference=reference.reference,
        presentspropertydefinition=definition,quotesutterance=quoted,assertsdescribedcontent=claimed,textbefore=before,
        authorexplainsby=lambda author,a,b,point:context(author,point) and (a,b)==(('german','latin') if variant=='reverse_explanation' else ('latin','german')),
        presentedpremiseconsequence=lambda author,premises,node,point:context(author,point) and node=='conclusion'
            and [x for x in DOMAIN if premises(x)]==list(NODES[:-1]))
    values.update({voc._symbols[n]:f for n,f in handlers.items()})
    return values


def test_all_source_bodies_and_parent_statements_are_preserved():
    doc=check.restored()['document'];assert check.backprojection(doc)==check.source_excerpt()
    assert len(check.source_excerpt()['declarations'])==99 and len(doc['statements'])==4
    assert doc['statements'][:3]==check.previous.document()['statements']
    definitions={d['name']:d for d in doc['declarations']}
    for name in ('ao','wb','wc','wd','we','wf','wg'):
        assert definitions[check.names()[name]]['kind']=='definition'
    assert check.bridge()['visible_statement_indices']==[0,1,3]


def test_whole_paragraph_preserves_quotation_order_and_attribution():
    doc=check.restored()['document']
    for variant in ('baseline','other_author','other_context','swapped_quotes','missing_condition',
                    'missing_conclusion','reverse_order','reverse_explanation'):
        assert evaluate(doc,model(doc,variant))==[True,True,True,variant=='baseline'],variant


def test_unknown_sentence_span_and_presentation_are_rejected():
    doc=check.restored()['document'];voc=check.vocabulary()
    for name in ('sentencereference','sentencetokenspanreference','presentspropertydefinition','quotesutterance',
                 'assertsdescribedcontent','textbefore','authorexplainsby','presentedpremiseconsequence'):
        values=model(doc);values[voc._symbols[name]]=parent.forbidden
        with pytest.raises(ValueError,match='Unspecified'):evaluate(doc,values)


def test_quoted_addressee_is_resolved_only_when_explicitly_used():
    original=check.restored()['document'];values=model(original);symbol=check.vocabulary()._symbols['quotedaddresseereference']
    values[symbol]=parent.forbidden
    assert evaluate(original,values)==[True]*4
    doc=deepcopy(original)
    doc['statements'].append(dict(kind='ask',body=dict(kind='equal',arguments=[call(check.names()['ao']),call(check.names()['wa'])])))
    assert evaluate(doc,model(doc))==[True,True,True,True,False]
    with pytest.raises(ValueError,match='Unspecified'):evaluate(doc,values)
