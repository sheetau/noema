"""Replace opaque obedience with scoped requirements and their fulfillment."""
import json
from copy import deepcopy

from noema.constructed import parse, format_graph
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both, quant
from scripts.compose_situated_criticism import params
from scripts.compose_described_norms import RULE, DESCRIPTION
from scripts.compose_choice_permissions import EXAMPLE as PARENT, PC, MC

LIBRARY = 'examples/v016/scoped-obedience.noema'
EXAMPLE = 'examples/v016/scoped-obedience-example.noema'
BASIS = 'data/scoped-obedience-basis-v1.json'
INHERITED = 'examples/v014/unrestricted-others.noema'
FIELDS = [('source','a'),('person','a'),('anchor','d'),('rolescope','h[a] c'),('items','h[a] c'),
          ('roles','h[a] a'),('actions','h[a] a'),('descriptions','h[a] ' + DESCRIPTION),('signs','h[a] c'),('required',RULE)]
CODES = [(n,'i['+t+']') for n,t in FIELDS]

def av(fields): return [v(n) for n,_ in fields]

def definitions():
    previous = [v('person'),v('anchor'),v('rolescope'),v('items'),'i[item a][v source]',
                v('roles'),v('actions'),v('descriptions'),v('signs'),v('required'),v('point')]
    text = definition('rtw',params(FIELDS+[('point','d')]),k('rpm',*previous))
    required = app(v('required'),v('source'),v('person'),v('role'),v('activity'),v('description'),v('sign'),v('anchor'))
    match = both(app(v('items'),v('item')),*[op('e',app(v(fn),v('item')),v(field)) for fn,field in
        [('roles','role'),('actions','activity'),('descriptions','description'),('signs','sign')]])
    coverage = op('y',both(app(v('rolescope'),v('role')),required),quant('g','item','a',match))
    for name,sort in reversed([('role','a'),('activity','a'),('description',DESCRIPTION),('sign','c')]):
        coverage = quant('f',name,sort,coverage)
    text += definition('rtx',params(FIELDS),coverage)
    text += definition('rty',params(FIELDS),'b point['+both(k('rtx',*av(FIELDS)),k('rtw',*av(FIELDS),v('point')))+']','e')
    text += definition('rtz',params(CODES),'o a[r b[p rty]]['+' '.join(av(CODES))+']',PC)
    return text

def example_refs():
    return ['k jdsource[]','k joperson[]','k jdanchor[]','p joscope','p joitems','p joroles',
            'p joactions','p jocodes','p josigns','p jorequired']

def build():
    base = parse((ROOT / PARENT).read_text(encoding='utf-8'))
    old = parse((ROOT / INHERITED).read_text(encoding='utf-8'))
    doc = dict(base,declarations=[d for d in old['declarations'] if d['name'] in ('rpl','rpm')],statements=[])
    library = parse(format_graph(doc,'compact')+definitions())
    revised=deepcopy(base)
    revised['statements']=[]
    revised['declarations']=[d for d in revised['declarations'] if d['name'] not in ('jdobeys','jdobedience','jdquoted')]
    revised['declarations'] += library['declarations']
    text=format_graph(revised,'compact')
    for name,fields,result in [
        ('joperson','','a'),('joscope','a','c'),('joitems','a','c'),('joroles','a','a'),('joactions','a','a'),('josigns','a','c'),
        ('jorequired','a a a a '+DESCRIPTION+' c d','c'),('jofirst','a a d','c'),('josecond','a a d','c'),
        ('jochoose','a '+DESCRIPTION+' '+DESCRIPTION,DESCRIPTION),('jolater','','d')]:
        text += 'r '+name+'['+fields+'] '+result+'.'
    text += definition('joa','person a activity a','b point[k jofirst[v person v activity v point]]','e')
    text += definition('job','person a activity a','b point[k josecond[v person v activity v point]]','e')
    text += definition('jocodes','item a','k jochoose[v item r[p joa] r[p job]]',DESCRIPTION)
    refs=example_refs()
    text += definition('jdobedience','',k('rty',*refs),'e')
    text += definition('joobediencecode','',k('rtz',*['r['+x+']' for x in refs]),PC)
    text += definition('jdquoted','',k('rtv','r b[k jdpolicy[]]','k joobediencecode[]'),'j['+MC+']')
    literal='l['+MC+'][r b[c[i[content e][j s[v content]]][k jdpolicy[]]] r b[c[i[content e][j m[v content]]][c[p rty]['+' '.join(refs)+']]]]'
    text += 'q[e[k jdquoted[]]['+literal+']].'
    text += 'q['+k('rtw',*refs,'k jdanchor[]')+'].'
    text += 'q['+k('rtw',*refs,'k jolater[]')+'].'
    text += 'q['+k('rtx',*refs)+'].'
    text += 'q[t[k jdobedience[]][k jolater[]]].'
    text += 'q[e[k joobediencecode[]][r b[c[p rty]['+' '.join(refs)+']]]].'
    return {LIBRARY:format_graph(library,'compact')+'\n',EXAMPLE:format_graph(parse(text),'compact')+'\n'}

def basis():
    return dict(status='scoped_source_requirement_fulfillment_and_closed_directive_content',parent=PARENT,
        definitions={
            'rtw':'選択した全記録について、指定出所・本人・役割・活動・記述・極性の要求が基準文脈に存在し、同じ記述が評価状況でその極性を満たす。役割の範囲も検査する。',
            'rtx':'同じ出所・本人・基準文脈の、指定役割範囲に属する全活動・全記述・両極性の要求が記録に含まれる。選択した出所以外の要求を混ぜない。',
            'rty':'要求記録の網羅性rtxと、記録の妥当性・履行rtwを合わせた内容。要求の成立と履行の評価状況を分ける。',
            'rtz':'rtyの引数の閉じた記述から内容記述を構成する。命令の実行も、全記述域の列挙も行わない。',
            'jdobedience':'作例の同じ出所・本人・基準文脈と要求記録をrtyへ結ぶ。従来の不透明なjdobeys入力を使わない。',
            'joobediencecode':'同じ引数をrtzで閉じた内容記述にし、rtvの二番目の指令に渡す。'},
        parameters={
            'source/person/anchor':'要求の出所・受け手・要求を照合する基準文脈。評価状況で要求が新設・免除されても、既に指定した要求をすり替えない。',
            'rolescope':'服従について扱う立場の範囲。政府・職務・制度上の立場の一般的説明は別に必要。',
            'items/roles/actions/descriptions/signs':'要求を記録する各項目とその役割・活動・閉じた行為記述・肯否。出所と本人は共通の引数に固定する。',
            'required':'同じ出所・本人・役割・行為記述・極性・基準文脈の要求関係。正当性、本人の同意、現実の実行は含めない。'},
        limitations=[
            'ここで表すのは指定した要求への全面的な適合である。要求を理由として従う意図、心理的服従、正当な権威への服従一般の必要十分条件とはしない。',
            '記録の網羅性は全ての型に合う行為記述へ量化する。有限評価器は全記述域を拒否し、有限の記述だけの診断例を全域の証明とはしない。',
            '空の記録が適合するのは対象範囲に要求が存在しない場合である。記録から命令を消すだけではrtxを満たさない。',
            '実行と不実行の両方が要求される場合は、両方を記録しても履行できない。優先順位・例外・正当性の解決規則は加えない。',
            '内容の引用・指令の引用から、引用者の賛同や要求の実行を導かない。許可と服従を同じ真偽にまとめない。',
            '作例は一人への要求を記述する。カントの複数の聞き手、論じる行為の具体化、ただしの関係、上位の発話可能条件と本文帰属は未接続。'])

def main():
    for name,body in (build()|{BASIS:json.dumps(basis(),ensure_ascii=False,indent=2)+'\n'}).items():
        path=ROOT/name
        if path.exists(): assert path.read_text(encoding='utf-8')==body,name
        else:
            with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(body)
        print(name,len(body))

if __name__=='__main__':main()
