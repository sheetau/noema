"""Native parameter binding and explicit two-valued vector models."""
from copy import deepcopy
from fractions import Fraction
import json
from noema.constructed_discourse import normalize_document
from noema.constructed_semantics import evaluate_document,FunctionValue,SequenceValue
from scripts.shared_cut_products import CUT
from scripts.shared_vectors import require
from scripts.shared_modality import call
from scripts.check_shared_real_cuts import num,apply


def truth_sorts(value):
    if value==CUT:return 'truth'
    if isinstance(value,dict):return {k:truth_sorts(v) for k,v in value.items()}
    if isinstance(value,list):return [truth_sorts(v) for v in value]
    return value


class Model:
    """Native values are constant predicates, not valid real cuts.

    In the explicit finite projection values instead have sort truth, allowing
    enumeration of four vectors over two components. No numbers are sampled.
    """
    def __init__(self,document,*,finite=False,individuals=('x','y')):
        self.document=normalize_document(truth_sorts(document) if finite else document)
        self.finite=finite;self.individuals=individuals

    def lift(self,sort,value):
        if sort==CUT:
            require(type(value) is bool,'Native diagnostic scalar must be Boolean')
            return FunctionValue(('number',),'truth',lambda point:value)
        if isinstance(sort,str):return Fraction(value) if sort=='number' else value
        if sort['kind']=='sequence':
            return SequenceValue(tuple(self.lift(sort['element'],v) for v in value),json.dumps(sort['element'],sort_keys=True,separators=(',',':')))
        require(sort['kind']=='function' and callable(value),'Expected a diagnostic function')
        def invoke(*arguments):
            decoded=[self.lower(t,a) for t,a in zip(sort['parameters'],arguments,strict=True)]
            return self.lift(sort['result'],value(*decoded))
        return FunctionValue(tuple(sort['parameters']),sort['result'],invoke)

    def lower(self,sort,value):
        if sort==CUT:return value(Fraction(0))
        if isinstance(sort,str):return value
        if sort['kind']=='sequence':return tuple(self.lower(sort['element'],v) for v in value.items)
        def invoke(*arguments):
            encoded=[self.lift(t,a) for t,a in zip(sort['parameters'],arguments,strict=True)]
            return self.lower(sort['result'],value(*encoded))
        return invoke

    def check(self,name,values,probe=None):
        doc=deepcopy(self.document);target=next(d for d in doc['declarations'] if d['name']==name)
        handlers={};args=[]
        for i,(p,value) in enumerate(zip(target['parameters'],values,strict=True)):
            label='diagnosticargument'+chr(97+i);sort=p['sort'];lifted=self.lift(sort,value)
            doc['declarations'].append(dict(kind='primitive',name=label,parameters=[],result=sort))
            handlers[label]=lambda value=lifted:value;args.append(call(label))
        body=call(name,*args)
        if probe is not None:
            doc['declarations'].append(dict(kind='primitive',name='diagnosticprobe',parameters=[],result='individual'))
            handlers['diagnosticprobe']=lambda:probe
            body=apply(body,call('diagnosticprobe'))
            if not self.finite:body=apply(body,num(0))
        doc['statements']=[dict(kind='ask',body=body)]
        return evaluate_document(doc,individuals=self.individuals,situations=('now',),primitives=handlers,max_steps=1000000)[0]['value']


def vector(x,y):return lambda component:dict(x=x,y=y)[component]
def matrix(xx,xy,yx,yy):return lambda row,column:{('x','x'):xx,('x','y'):xy,('y','x'):yx,('y','y'):yy}[row,column]
def xor(a,b):return a!=b
def conjunction(a,b):return a and b
def equal(a,b):return a==b
def valid(value):return True
def identity(point):return point
def shifted(point):return vector(not point('x'),point('y'))
def nonlinear(point):return vector(point('x') and point('y'),point('y'))


def native_diagnostics(document):
    model=Model(document);rows=[];components=('x','y')
    def check(label,name,args,expected,probe=None):
        actual=model.check(name,args,probe)
        require(actual==expected,'Native vector binding diagnostic failed: '+label)
        rows.append(dict(name=label,target=name,probe=probe,expected=expected,actual=actual))
    for label,items,expected in [('empty',(),False),('singleton',('x',),True),('distinct',components,True),
        ('duplicate',('x','x'),False),('separated_duplicate',('x','y','x'),False)]:
        check(label,'vectorcomponents',[items],expected)
    for label,point,expected in [('all_valid',vector(True,True),True),('invalid_x',vector(False,True),False),('invalid_y',vector(True,False),False)]:
        check(label,'vectorvalid',[components,point,lambda value:value],expected)
    for label,left,right,relation,expected in [
        ('same_values_different_functions',vector(True,False),vector(True,False),equal,True),
        ('different_x',vector(True,False),vector(False,False),equal,False),
        ('different_y',vector(True,False),vector(True,True),equal,False),
        ('explicit_comparison_is_not_implicit_equality',vector(True,False),vector(False,True),lambda a,b:True,True)]:
        check(label,'vectorcompare',[components,left,right,relation],expected)
    for component,expected in [('x',True),('y',False)]:
        check('ordered_operation_'+component,'vectorcombine',[vector(True,False),vector(False,True),lambda a,b:a and not b],expected,component)
    mat=matrix(True,True,False,True);zero=vector(False,False);point=vector(True,False)
    for component,expected in [('x',True),('y',False)]:
        check('matrix_row_column_'+component,'vectoraffinevalue',[components,mat,zero,point,xor,conjunction],expected,component)
    check('component_specific_offset','vectoraffinevalue',[components,mat,vector(False,True),point,xor,conjunction],True,'y')
    check('empty_fold_returns_offset','vectoraffinevalue',[(),mat,vector(False,True),point,xor,conjunction],True,'y')
    check('duplicate_component_is_counted_twice','vectoraffinevalue',[('x','x'),mat,zero,point,xor,conjunction],False,'x')
    for label,order,expected in [('declared_fold_order',components,False),('reversed_fold_order',tuple(reversed(components)),True)]:
        check(label,'vectoraffinevalue',[order,mat,vector(True,True),point,lambda a,b:not a and b,conjunction],expected,'x')
    check('coefficient_precedes_input','vectoraffinevalue',[components,mat,zero,point,lambda a,b:a or b,lambda a,b:a and not b],True,'x')
    first=zero;second=vector(True,False);displacement=vector(False,True)
    for label,transform,good,expected in [('affine_equal_increments',shifted,valid,True),
        ('nonlinear_increments_differ',nonlinear,valid,False),('invalid_values_rejected',shifted,lambda value:False,False)]:
        check(label,'vectorequalincrement',[components,first,second,displacement,transform,good,equal,xor,xor],expected)
    check('zero_displacement_does_not_prove_affinity','vectorequalincrement',[components,first,second,zero,nonlinear,valid,equal,xor,xor],True)
    return rows


def finite_diagnostics(document):
    model=Model(document,finite=True);rows=[];components=('x','y');all_points=lambda point:True;empty=lambda point:False
    def check(label,name,args,expected):
        actual=model.check(name,args)
        require(actual==expected,'Finite vector model failed: '+label)
        rows.append(dict(name=label,target=name,expected=expected,actual=actual))
    for label,domain,transform,good,expected in [
        ('identity_uniform',all_points,identity,valid,True),('translated_uniform',all_points,shifted,valid,True),
        ('nonlinear_not_uniform',all_points,nonlinear,valid,False),('empty_not_uniform',empty,identity,valid,False),
        ('no_valid_displacement_is_vacuous',all_points,identity,lambda value:False,True)]:
        check(label,'vectoruniform',[components,domain,transform,good,equal,xor,xor],expected)
    identity_matrix=matrix(True,False,False,True);zero=vector(False,False)
    def affine(domain,transform,mat,offset,good=valid):return [components,domain,transform,mat,offset,good,equal,xor,conjunction]
    check('fixed_identity_matrix','vectoraffine',affine(all_points,identity,identity_matrix,zero),True)
    check('fixed_offset','vectoraffine',affine(all_points,shifted,identity_matrix,vector(True,False)),True)
    check('wrong_offset','vectoraffine',affine(all_points,identity,identity_matrix,vector(True,False)),False)
    asymmetric=matrix(True,True,False,True);transposed=matrix(True,False,True,True)
    transform=lambda p:vector(xor(p('x'),p('y')),p('y'))
    check('asymmetric_matrix','vectoraffine',affine(all_points,transform,asymmetric,zero),True)
    check('transposed_matrix_rejected','vectoraffine',affine(all_points,transform,transposed,zero),False)
    fitting=matrix(False,False,False,True)
    check('three_points_fit_same_matrix','vectoraffine',affine(lambda p:not(p('x') and p('y')),nonlinear,fitting,zero),True)
    check('fourth_point_breaks_same_matrix','vectoraffine',affine(all_points,nonlinear,fitting,zero),False)
    check('empty_not_affine','vectoraffine',affine(empty,identity,identity_matrix,zero),False)
    only_true=lambda p:p('x') and p('y');constant=lambda p:vector(True,True);true_vector=vector(True,True)
    def guarded(mat,offset):return [components,only_true,constant,mat,offset,lambda value:value,equal,lambda a,b:a or b,conjunction]
    check('all_coefficients_valid','vectoraffine',guarded(matrix(True,True,True,True),true_vector),True)
    for row in components:
        for column in components:
            mat=lambda r,c,row=row,column=column:not(r==row and c==column)
            check('invalid_matrix_'+row+column,'vectoraffine',guarded(mat,true_vector),False)
    for component in components:
        check('invalid_offset_'+component,'vectoraffine',guarded(matrix(True,True,True,True),lambda c:c!=component),False)
    return rows
