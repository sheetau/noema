"""Binding contrasts and retained explanation checks on recovered bodies."""
from copy import deepcopy
from types import FunctionType
from scripts import check_kant_title_author_visible as check
from scripts import check_explanatory_question as original
import test_kant_title_author_visible as structure

RESULTS={}
RECOVERED_DEFINITIONS_SEEN=set()


def test_every_author_role_and_question_reference_is_bound():
    doc=check.restored()['document'];vocabulary=check.vocabulary();rows={}
    for relation,width,index in [('actionoccurrence',2,1),('nameapplies',4,1),
                                 ('authordisplay',4,1),('presentspropertyquestion',4,0)]:
        for slot in range(width):
            if relation=='presentspropertyquestion' and slot==2:continue
            values=structure.model(doc);symbol=vocabulary._symbols[relation];baseline=values[symbol]
            def changed(*args,slot=slot,baseline=baseline):
                changed=list(args);changed[slot]='other'
                return baseline(*changed)
            values[symbol]=changed
            result=structure.evaluate(doc,values)
            expected=[True,True,True];expected[index]=False
            assert result==expected,(relation,slot,result)
            rows[relation+':'+str(slot)]=result
    RESULTS['binding_contrasts']=rows


def test_original_explanation_candidate_checks_use_recovered_definitions():
    recovered=check.backprojection(check.restored()['document'])
    definitions={d['name']:d for d in recovered['declarations'] if d['kind']=='definition'}
    def fixture():
        doc=deepcopy(original.fixture())
        for i,declaration in enumerate(doc['declarations']):
            name=declaration['name']
            if name in definitions:
                assert definitions[name]==declaration,('Historical candidate body changed',name)
                doc['declarations'][i]=deepcopy(definitions[name])
                RECOVERED_DEFINITIONS_SEEN.add(name)
        return doc
    namespace=dict(vars(original));namespace['fixture']=fixture
    function=FunctionType(original.candidate_checks.__code__,namespace,
        original.candidate_checks.__name__,original.candidate_checks.__defaults__,original.candidate_checks.__closure__)
    result=function()
    assert {'rqwd','rqqp'}<=RECOVERED_DEFINITIONS_SEEN
    assert result==check.read('reports/explanatory-question-v1.json')['candidate']
    RESULTS['original_candidate_checks']=result
    RESULTS['recovered_candidate_definitions']=sorted(RECOVERED_DEFINITIONS_SEEN)
