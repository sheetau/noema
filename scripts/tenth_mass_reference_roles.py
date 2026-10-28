"""Closed roles for the mass-convention group's remaining contextual references."""
from scripts.shared_reference import definition
from scripts.shared_modality import call,v,op

I='individual';S='situation';T='truth'
ROLE_ASSIGNMENTS={'zrcsubject':'massmotionsubjectrole','zrcrole':'masscomparerrole','eiszk':'massordinarystandardrole'}
REFERENCE_ANCHORS={n:'eiszm' for n in ROLE_ASSIGNMENTS}
def quote(body):return dict(kind='quote',body=body)
def qf(name):return quote(dict(kind='function_ref',symbol=name))
def exists(name,body):return dict(kind='exists',variable=name,sort=I,body=body)


def definitions():
    account=dict(kind='content',variable='world',body=exists('law',op('and',
        call('vd',v('law'),v('world')),
        call('eisxn',v('law'),call('eisxh'),call('ra'),v('world')))))
    participant=exists('left',exists('right',call('en3',v('person'),v('activity'),v('left'),v('right'),v('world'))))
    role_params=[('candidate',I),('context',S)]
    return [
        definition('massmotionaccount',[],'content',account),
        definition('masscomparisonparticipant',[('person',I),('activity',I),('world',S)],T,participant),
        definition(ROLE_ASSIGNMENTS['zrcsubject'],role_params,T,
            call('theoreticalinquirytopic',v('candidate'),quote(call('ek36')),quote(call('massmotionaccount')),v('context'))),
        definition(ROLE_ASSIGNMENTS['zrcrole'],role_params,T,
            call('methodologicalactivityrole',v('candidate'),qf('masscomparisonparticipant'),v('context'))),
        definition(ROLE_ASSIGNMENTS['eiszk'],role_params,T,
            call('ordinaryprocedurestandard',v('candidate'),qf('en4'),v('context'))),
    ]


MEANINGS={
    'massmotionaccount':'同じ導入粒子eisxh・系raの運動法則として検討する範囲を、既存vdとeisxnで指定する内容。特定の式への適合や法則の真理は含めない。',
    'masscomparisonparticipant':'既存en3の二理論の共同証人を保ち、同じ人・活動・適用状況について比較を担う関係を得る。比較要求や通常程度基準には依存しない。',
    'massmotionsubjectrole':'同じ粒子の設定ek36と運動法則の範囲massmotionaccountを引用して、電子運動の理論的探究領域を同定する。特定の理論や三加速度式の真を要求しない。',
    'masscomparerrole':'同じ比較参加関係を引用して、比較を行う者という方法上の立場を同定する。個人や実際の職位への参照とはしない。',
    'massordinarystandardrole':'注意深い吟味の旧本文en4そのものを引用し、その通常程度の文脈基準を同定する。程度を強めたen5や要求en6から基準を逆に定めない。',
}


def build_report():
    """Check full source dependency closure with references replaced by their roles."""
    import hashlib
    from copy import deepcopy
    from noema.constructed import parse,format_graph
    from noema.constructed_discourse import normalize_document
    from noema.meaning_catalog import _references
    from scripts.check_manuscript_context import catalogs
    from scripts.activity_role_visible_profile import ROOT,CONTRACTS
    from scripts.seventh_section_visible_profile_contracts import CONTRACTS as inquiry_contracts
    from scripts.temporal_discourse_profile import EXTRA
    catalog=catalogs()['einstein-1905']
    declarations={d['name']:deepcopy(d) for d in catalog.document['declarations']}
    contracts=CONTRACTS|{'theoreticalinquirytopic':inquiry_contracts['theoreticalinquirytopic'],
                         'describedreference':EXTRA['describedreference']}
    for n,r in contracts.items():
        assert n not in declarations,n
        declarations[n]=dict(kind='primitive',name=n,parameters=r['parameters'],result=r['result'])
    for d in definitions():
        assert d['name'] not in declarations,d['name']
        declarations[d['name']]=d
    for old,role in ROLE_ASSIGNMENTS.items():
        assert declarations[old]['kind']=='primitive' and declarations[old]['parameters']==[] and declarations[old]['result']==I
        declarations[old]=definition(old,[],I,call('describedreference',call('eirf'),
            call(REFERENCE_ANCHORS[old]),qf(role),call('ri')))
    seen=set();active=set();order=[]
    def visit(name):
        assert name not in active,('Cyclic contextual reference',name)
        if name in seen:return
        active.add(name)
        for ref in sorted(_references(declarations[name].get('body'))):visit(ref)
        active.remove(name);seen.add(name);order.append(name)
    for name in ROLE_ASSIGNMENTS:visit(name)
    document=normalize_document(dict(schema_version='0.16',lexicon_version='0.16',
        declarations=[declarations[n] for n in order],statements=[]))
    assert parse(format_graph(document))==document
    assert not {'en5','en6','eiszk','zrcrole'}.intersection(_references(definitions()[0]['body']))
    def closure(name):
        result=set()
        def collect(n):
            if n in result:return
            result.add(n)
            for ref in _references(declarations[n].get('body')):collect(ref)
        collect(name);return result
    assert not {'en5','en6','eiszk','zrcrole'}.intersection(closure('massmotionaccount'))
    assert not {'en5','en6','eiszk','zrcrole'}.intersection(closure('masscomparisonparticipant'))
    assert not {'en5','en6','eiszk','zrcrole'}.intersection(closure('en4'))
    paths=set(catalog.source_sha256)|{catalog.document_path,'data/work-state.json',
        'scripts/tenth_mass_reference_roles.py','tests/test_tenth_mass_reference_roles.py',
        'scripts/activity_role_visible_profile.py','scripts/seventh_section_visible_profile_contracts.py',
        'scripts/temporal_discourse_profile.py','.noema-project/tenth-mass-text-boundaries-v1.json'}
    return dict(schema='noema-tenth-mass-reference-roles-check-1',
        status='closed_roles_typechecked_with_full_source_dependencies',roles=ROLE_ASSIGNMENTS,
        anchors=REFERENCE_ANCHORS,definitions=definitions(),meanings=MEANINGS,
        source_dependency_count=len(order),dependency_order=order,cyclic_references=False,
        strengthened_requirement_used_to_define_standard=False,document_integration_credit=0,
        limitations=['Source dependencies and quotation types are checked; the complete visible Native connector and actual SVG decoding remain required.',
                     'Finite binding diagnostics are not a proof over all possible theories, activities or physical models.'],
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(paths)})
