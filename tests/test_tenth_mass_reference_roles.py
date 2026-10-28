"""Check quotation isolation and every slot of the comparison participant role."""
from copy import deepcopy
import json
import pytest
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document,DescriptionValue
from noema.constructed_discourse import description_sort
from scripts import activity_role_visible_profile as profile
from scripts import tenth_mass_reference_roles as roles
from scripts.shared_modality import call,v
from scripts.seventh_section_visible_profile_contracts import CONTRACTS as INQUIRY_CONTRACTS

def primitive(name,parameters,result):return dict(kind='primitive',name=name,parameters=parameters,result=result)
def document(declarations,body):
    ordered=[d for d in declarations if d['kind']=='primitive']+[d for d in declarations if d['kind']!='primitive']
    return dict(schema_version='0.16',lexicon_version='0.16',declarations=ordered,statements=[dict(kind='ask',body=body)])
def forbidden(*args):raise AssertionError('A quoted procedure or unrelated contract was executed')


@pytest.mark.parametrize('old,relation,target,sort',[
    ('zrcrole','methodologicalactivityrole','masscomparisonparticipant',profile.ACTIVITY),
    ('eiszk','ordinaryprocedurestandard','en4',profile.PROCEDURE),
])
def test_role_keeps_candidate_context_and_closed_description_without_execution(old,relation,target,sort):
    role=next(d for d in roles.definitions() if d['name']==roles.ROLE_ASSIGNMENTS[old])
    decls=[primitive(relation,profile.CONTRACTS[relation]['parameters'],'truth'),
           primitive(target,sort['parameters'],sort['result']),role,
           primitive('chosen',[],'individual'),primitive('context',[],'situation')]
    doc=parse(format_graph(document(decls,call(role['name'],call('chosen'),call('context')))))
    seen=[]
    def relation_value(candidate,description,context):
        assert isinstance(description,DescriptionValue) and description.rank==0
        assert json.loads(description.result_type)==sort
        assert json.loads(description.syntax)['symbol']==target
        seen.append((candidate,context))
        return candidate=='candidate' and context=='world'
    for candidate,context,expected in [('candidate','world',True),('other','world',False),('candidate','otherworld',False)]:
        handlers={relation:relation_value,target:forbidden,'chosen':lambda:candidate,'context':lambda:context}
        assert evaluate_document(doc,individuals=['candidate','other'],situations=['world','otherworld'],primitives=handlers)[0]['value']==expected
    assert seen==[('candidate','world'),('other','world'),('candidate','otherworld')]


def test_participant_preserves_every_source_argument_slot_in_small_domain():
    participant=next(d for d in roles.definitions() if d['name']=='masscomparisonparticipant')
    declarations=[primitive('en3',['individual']*4+['situation'],'truth'),participant,
                  primitive('person',[],'individual'),primitive('activity',[],'individual'),primitive('world',[],'situation')]
    expected=('personvalue','activityvalue','leftvalue','rightvalue','worldvalue')
    def check(row):
        doc=parse(format_graph(document(row,call('masscomparisonparticipant',call('person'),call('activity'),call('world')))))
        return evaluate_document(doc,individuals=['personvalue','activityvalue','leftvalue','rightvalue'],situations=['worldvalue'],
            primitives={'en3':lambda *args:args==expected,'person':lambda:'personvalue',
                        'activity':lambda:'activityvalue','world':lambda:'worldvalue'})[0]['value']
    assert check(declarations)
    for slot in range(4):
        changed=deepcopy(declarations)
        args=changed[1]['body']['body']['body']['arguments']
        args[slot]=call('person') if slot!=0 else call('activity')
        assert not check(changed),slot
    # The fifth slot must remain the supplied world rather than another situation.
    changed=deepcopy(declarations)
    changed.append(primitive('alternate',[],'situation'))
    changed[1]['body']['body']['body']['arguments'][4]=call('alternate')
    doc=parse(format_graph(document(changed,call('masscomparisonparticipant',call('person'),call('activity'),call('world')))))
    assert not evaluate_document(doc,individuals=['personvalue','activityvalue','leftvalue','rightvalue'],situations=['worldvalue','otherworld'],
        primitives={'en3':lambda *args:args==expected,'person':lambda:'personvalue','activity':lambda:'activityvalue',
                    'world':lambda:'worldvalue','alternate':lambda:'otherworld'})[0]['value']


def test_subject_role_keeps_setting_and_law_range_separate_without_asserting_them():
    role=next(d for d in roles.definitions() if d['name']==roles.ROLE_ASSIGNMENTS['zrcsubject'])
    relation='theoreticalinquirytopic'
    declarations=[primitive(relation,INQUIRY_CONTRACTS[relation]['parameters'],'truth'),
        primitive('ek36',[],'content'),primitive('massmotionaccount',[],'content'),role,
        primitive('chosen',[],'individual'),primitive('context',[],'situation')]
    def inquiry(candidate,setting,account,context):
        for description in (setting,account):
            assert isinstance(description,DescriptionValue) and description.rank==0
            assert json.loads(description.result_type)=='content'
        return (candidate,json.loads(setting.syntax)['symbol'],json.loads(account.syntax)['symbol'],context)==(
            'candidate','ek36','massmotionaccount','world')
    for swap,candidate,context in [(False,'candidate','world'),(True,'candidate','world'),
                                   (False,'other','world'),(False,'candidate','otherworld')]:
        changed=deepcopy(declarations)
        if swap:
            args=changed[3]['body']['arguments'];args[1],args[2]=args[2],args[1]
        doc=parse(format_graph(document(changed,call(role['name'],call('chosen'),call('context')))))
        result=evaluate_document(doc,individuals=['candidate','other'],situations=['world','otherworld'],
            primitives={relation:inquiry,'ek36':forbidden,'massmotionaccount':forbidden,
                        'chosen':lambda:candidate,'context':lambda:context})
        assert result[0]['value']==(not swap and candidate=='candidate' and context=='world')
