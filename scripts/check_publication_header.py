"""Check named publication metadata and independent numbering scopes."""
import argparse
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
from noema.constructed import parse,format_graph
from noema.constructed_semantics import evaluate_document
from noema.meaning_catalog import load_catalog
from noema.identifiers import load_annotations
from noema.semantic_reviews import digest,selection_binding,validate_hashes
from noema.script import transcribe
from scripts import check_projected_classification as prior
from scripts.compose_subject_bound_departure import closure
from scripts.compose_publication_header import ROOT,PARENT,PARENT_BASIS,FULL,LIBRARY,BASIS,ANNOTATIONS,build,num

REPORT=ROOT/'reports/publication-header-v1.json'
ROOTS=('hzml','hzmm','hzmn','hzmo')
DOMAIN=prior.previous.DOMAIN+('current_issue','december','header_display','issue_numbers','article_numbers')
SCENES=prior.previous.previous.previous.SCENES+('header',)
FALSE={
 'baseline':(), 'missing_name':(0,), 'missing_display':(0,), 'wrong_series':(0,), 'name_is_series':(0,), 'september_issue':(0,),
 'missing_year':(1,), 'year_1783':(1,), 'duplicate_year':(1,), 'wrong_display_year':(1,),
 'missing_month':(2,), 'month_9':(2,), 'duplicate_month':(2,), 'wrong_display_month':(2,),
 'issue_9':(2,), 'issue_wrong_scheme':(2,), 'reversed_issue_parents':(2,), 'other_issue_year':(2,), 'duplicate_issue':(2,),
 'article_2':(3,), 'article_wrong_scheme':(3,), 'other_article_issue':(3,), 'duplicate_article':(3,), 'missing_article':(3,),
}


@lru_cache(maxsize=2)
def document(combined=False):
    # Cache parsing only. Every semantic evaluation remains uncached, and each
    # report invocation starts a new process with pinned source bytes.
    doc=parse((ROOT/FULL).read_text(encoding='utf-8'))
    roots=([*prior.previous.previous.previous.SYMBOLS,'hzlt','hzlz','hzmd'] if combined else [])+list(ROOTS)
    doc['declarations']=closure(doc,roots)
    doc['statements']=doc['statements'][18:31] if combined else doc['statements'][27:31]
    return doc


@lru_cache(maxsize=1)
def prior_document():return prior.document(True)


def unknown(*args):raise ValueError('Unknown publication metadata')


def model(doc,variant='baseline',combined=False):
    old=prior.model(prior_document()) if combined else {}
    issue='monthly_issue' if variant=='september_issue' else 'current_issue'
    name='monthly_series' if variant=='name_is_series' else 'monthly_name'
    refs=dict(hzme=issue,hzmf='header',hzmg='december',hzmh='header_display',hzmj='issue_numbers',hzmk='article_numbers',
        hzkh=name,hzkg='monthly_series',hzkf='monthly_issue',hzjf='year',hzix='calendar',hzik='document')
    values=dict(old);values.update({n:lambda v=v:v for n,v in refs.items()})
    own={
        'dg':lambda act,ctx:variant!='missing_display' and (act,ctx)==('header_display','header'),
        'hzih':lambda act,label,series,ctx:variant!='missing_name' and (act,label,series,ctx)==('header_display',name,'monthly_series','header'),
        'hzka':lambda item,series,ctx:(item,series,ctx)==(issue,'other' if variant=='wrong_series' else 'monthly_series','header'),
        'hzjw':lambda text,item,ctx:variant!='missing_article' and (text,item,ctx)==('document',issue,'header'),
    }
    def years(cal,period,number,ctx):
        if variant=='unknown_year' and ctx=='header':return unknown()
        return variant!='missing_year' and (cal,number,ctx)==('calendar',Fraction(1783 if variant=='year_1783' else 1784),'header') and period in (
            ('year','other') if variant=='duplicate_year' else ('year',))
    def months(cal,year,period,number,ctx):
        if variant=='unknown_month' and ctx=='header':return unknown()
        return variant!='missing_month' and (cal,year,number,ctx)==('calendar','year',Fraction(9 if variant=='month_9' else 12),'header') and period in (
            ('december','other') if variant=='duplicate_month' else ('december',))
    def dates(item,period,ctx):
        return (item,ctx)==(issue,'header') and period in (
            'other' if variant=='wrong_display_year' else 'year',
            'other' if variant=='wrong_display_month' else 'december')
    own.update(hzir=years,hzlm=months,hzjy=dates)
    for symbol,fn in own.items():
        if symbol in old:
            previous=old[symbol]
            # Context partitioning avoids consulting an unrelated interpreter
            # branch and keeps header-only mutations out of the footnote.
            values[symbol]=lambda *args,fn=fn,previous=previous:fn(*args) if args[-1]=='header' else previous(*args)
        else:values[symbol]=fn
    def assigned(scheme,item,parents,number,ctx):
        if variant=='unknown_number':return unknown()
        if ctx!='header':return False
        issue_scope=('year','monthly_series') if variant=='reversed_issue_parents' else ('monthly_series','other') if variant=='other_issue_year' else ('monthly_series','year')
        issue_rows=(issue,'other') if variant=='duplicate_issue' else (issue,)
        article_rows=('document','other') if variant=='duplicate_article' else ('document',)
        return ((scheme,parents.items,number)==('article_numbers' if variant=='issue_wrong_scheme' else 'issue_numbers',issue_scope,Fraction(9 if variant=='issue_9' else 12)) and item in issue_rows) or (
            (scheme,parents.items,number)==('issue_numbers' if variant=='article_wrong_scheme' else 'article_numbers',('other' if variant=='other_article_issue' else issue,),Fraction(2 if variant=='article_2' else 1)) and item in article_rows)
    values['hzmi']=assigned
    return {d['name']:values[d['name']] for d in doc['declarations'] if d['kind']=='primitive'}


def evaluate(doc,values):
    return [r['value'] for r in evaluate_document(doc,individuals=DOMAIN,situations=SCENES,primitives=values,
        max_steps=4000000,memoize_definitions=False,memoize_expressions=False)]


def generic_checks():
    doc=parse((ROOT/LIBRARY).read_text(encoding='utf-8')+
        'r jscheme[] a.r jitem[] a.r jparent[] a.r jctx[] d.r jassigned[a a j[a] b d] c.'+
        'q[k rqso[k jscheme[] k jitem[] l[a][k jparent[]] '+num(1)+' k jctx[] p jassigned]].')
    for present,duplicate,other_scheme,other_scope in product((False,True),repeat=4):
        rows=set()
        if present:rows.add(('article_numbers','document',('current_issue',)))
        if duplicate:rows.add(('article_numbers','other',('current_issue',)))
        if other_scheme:rows.add(('issue_numbers','other',('current_issue',)))
        if other_scope:rows.add(('article_numbers','other',('monthly_issue',)))
        values=dict(jscheme=lambda:'article_numbers',jitem=lambda:'document',jparent=lambda:'current_issue',jctx=lambda:'header',
            jassigned=lambda scheme,item,scope,number,ctx:(scheme,item,scope.items) in rows and number==1 and ctx=='header')
        assert evaluate(doc,values)==[present and not duplicate]
    return 16


def checks():
    doc=document();rows={}
    for variant,indices in FALSE.items():
        actual=evaluate(doc,model(doc,variant));assert actual==[i not in indices for i in range(4)],(variant,actual)
        rows[variant]=actual
    for variant in ('unknown_year','unknown_month','unknown_number'):
        try:evaluate(doc,model(doc,variant))
        except ValueError as error:assert 'Unknown' in str(error)
        else:raise AssertionError(variant)
    joined={};combined=document(True)
    for variant in ('baseline','missing_name','year_1783','month_9','issue_9','article_2','other_article_issue'):
        actual=evaluate(combined,model(combined,variant,True))
        assert actual==[True]*9+rows[variant],(variant,actual)
        joined[variant]=actual
    return dict(source_contrasts=rows,combined_thirteen_statement_contrasts=joined,
        unknown_inputs_refused=3,numbering_combinations=generic_checks(),semantic_evaluation_uncached=True)


def structure():
    old,new=load_catalog(ROOT,PARENT_BASIS),load_catalog(ROOT,BASIS)
    assert new.document['statements'][:-4]==old.document['statements'] and len(new.document['statements'])==31
    assert new.document['declarations'][:-12]==old.document['declarations']
    for n,e in old.entries.items():assert new.entries[n]==e,n
    for i in (16,17):assert selection_binding(old,[i])==selection_binding(new,[i])
    annotations=load_annotations(ROOT,BASIS,ANNOTATIONS)
    expected=load_annotations(ROOT,PARENT_BASIS,'data/projected-classification-identifiers-v1.json').show()['entries']
    next(e for e in expected if e['symbol']=='hzkh')['forms'].append(dict(text='Berlinische Monatsschrift',language='de',role='edition_heading'))
    assert annotations.show()['entries']==expected
    for form in ('Berlinische Monatsschrift','Berlinischen Monatsschrift'):
        assert [m['symbol'] for m in annotations.find(form,'de')['matches']]==['hzkh']
    return dict(previous_statements_preserved=27,new_primitive_relations=1,new_references=6,new_definitions=5,
        generic_characters=len((ROOT/LIBRARY).read_text(encoding='utf-8')),
        added_characters=len((ROOT/FULL).read_text(encoding='utf-8'))-len((ROOT/PARENT).read_text(encoding='utf-8')),
        previous_meanings_and_review_bindings_preserved=True,heading_name_form_added_without_new_designation=True)


def build_report():
    for name,text in build().items():assert (ROOT/name).read_text(encoding='utf-8')==text
    for name in (FULL,LIBRARY):
        doc=parse((ROOT/name).read_text(encoding='utf-8'))
        for notation in ('compact','full'):
            text=format_graph(doc,notation);assert parse(text)==parse(transcribe(text,alphabet='v2'))==doc
    prior_report=json.loads((ROOT/'reports/projected-classification-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,prior_report['source_sha256'])
    evidence=json.loads((ROOT/'data/publication-header-evidence-v1.json').read_text(encoding='utf-8'));validate_hashes(ROOT,evidence['source_sha256'])
    inventory=json.loads((ROOT/'artifacts/written-units-v1/kant-1784.json').read_text(encoding='utf-8'))
    segments=[]
    for i,symbol in enumerate(ROOTS,1):
        u=next(u for u in inventory['units'] if u['id']==f'kant-1784:u{i:04}')
        segments.append(dict(unit=u['id'],unit_sha256=u['text_sha256'],range=[0,len(u['text'])],source=u['text'],status='partial_header_metadata',definitions=[symbol],remaining=['Whole-unit review judgments are registered separately.']))
    paths=set(prior_report['source_sha256'])|set(evidence['source_sha256'])|set(build())|set(load_catalog(ROOT,BASIS).source_sha256)|{
        'reports/projected-classification-v1.json','data/publication-header-evidence-v1.json','scripts/compose_publication_header.py',
        'scripts/check_publication_header.py','scripts/check_calendar_dateline.py','tests/test_publication_header.py','docs/publication-header-v1.md'}
    return dict(status='publication_header_formal_checks_under_stated_reading',document=FULL,checks=checks(),structure=structure(),roundtrips=True,
        alignment=dict(segments=segments),verified_full_units={'kant-1784':0,'einstein-1905':0},
        source_sha256={p:digest((ROOT/p).read_bytes()) for p in sorted(paths)})


def main():
    cli=argparse.ArgumentParser();cli.add_argument('--verify-only',action='store_true');args=cli.parse_args();report=build_report()
    if args.verify_only:assert json.loads(REPORT.read_text(encoding='utf-8'))==report
    else:
        with REPORT.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Publication header and numbering scopes checked separately from issuance dates')


if __name__=='__main__':main()
