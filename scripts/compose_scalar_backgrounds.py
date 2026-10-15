"""Keep a scalar comparison background separate from the foreground content."""
import json

from noema.constructed import parse, format_graph
from scripts.compose_origin_clock import ROOT, definition, v
from scripts.compose_limits import call as k, app, op, both
from scripts.compose_situated_criticism import params
from scripts.compose_described_norms import TRUE

LIBRARY = 'examples/v016/scalar-backgrounds.noema'
EXAMPLE = 'examples/v016/scalar-backgrounds-example.noema'
PERMISSIONS = 'examples/v016/scalar-permissions-example.noema'
BASIS = 'data/scalar-backgrounds-basis-v1.json'
PC = 'i b[e]'
CC = 'i c[e]'
PAIR = 'h[h[' + CC + ' ' + CC + '] ' + CC + '] ' + CC
ORDER = 'h[a ' + PC + ' ' + PC + ' d] c'
BACKGROUND = [('focus', PC), ('alternatives', 'j[' + PC + ']'), ('observer', 'a'), ('anchor', 'd'), ('ranking', ORDER)]
INPUTS = [(n, ('i b[' if n in ('focus', 'alternatives') else 'i[') + t + ']') for n, t in BACKGROUND]
BG_FUNCTION = 'h[' + ' '.join(t for _, t in BACKGROUND) + '] e'
ACTION_CODE = 'i[h[a a] e]'
FRAME = 'i b[h[' + ACTION_CODE + '] e]'


def every(sequence, variable, body):
    state = 'state' + variable
    return 'q[' + sequence + '][' + TRUE + '][i[' + state + ' c ' + variable + ' ' + PC + '][' + both(v(state), body) + ']]'


def definitions():
    text = definition('rst', 'foreground ' + CC + ' background ' + CC,
        'i[select h[' + CC + ' ' + CC + '] ' + CC + '][' + app(v('select'), v('foreground'), v('background')) + ']', PAIR)
    for name, selected in (('rsu', 'foreground'), ('rsv', 'background')):
        selector = 'i[foreground ' + CC + ' background ' + CC + '][v ' + selected + ']'
        text += definition(name, 'package ' + PAIR, app(v('package'), selector), CC)
    negate = 'r c[i[content e][b point[u[t[v content][v point]]]]]'
    negated = 'o a[' + negate + '][' + k('rsu', v('package')) + ']'
    text += definition('rsw', 'package ' + PAIR, k('rst', negated, k('rsv', v('package'))), PAIR)
    for name, projection in (('rsx', 'rsu'), ('rsy', 'rsv')):
        text += definition(name, 'package ' + PAIR + ' point d', op('t', 's[' + k(projection, v('package')) + ']', v('point')))
    text += definition('rsz', 'package ' + PAIR,
        'o a[r c[i[content e][j q[v content]]]][' + k('rsu', v('package')) + ']', 'i c[f]')
    ranked = lambda left, right: app(v('ranking'), v('observer'), v(left), v(right), v('anchor'))
    irreflexive = every(v('alternatives'), 'item', op('u', ranked('item', 'item')))
    transitive = every(v('alternatives'), 'first', every(v('alternatives'), 'second', every(v('alternatives'), 'third',
        op('y', both(ranked('first', 'second'), ranked('second', 'third')), ranked('first', 'third')))))
    text += definition('rta', params(BACKGROUND[1:]), both(irreflexive, transitive))
    full = 'm[l[' + PC + '][v focus]][v alternatives]'
    extreme = every(v('alternatives'), 'other', both(op('u', op('e', v('focus'), v('other'))), ranked('focus', 'other')))
    text += definition('rtb', params(BACKGROUND), both(op('u', op('e', 'd[v alternatives]', 'n p a b')),
        k('rta', full, v('observer'), v('anchor'), v('ranking')), extreme))
    additive = 'q[v alternatives][u[' + TRUE + ']][i[found c alternative ' + PC + '][' + op('x', v('found'), op('t', 's[v alternative]', v('point'))) + ']]'
    text += definition('rtc', 'alternatives j[' + PC + '] point d', additive)
    scalar = k('rtb', *(v(n) for n, _ in BACKGROUND))
    text += definition('rtd', params(BACKGROUND), 'b point[' + scalar + ']', 'e')
    text += definition('rte', params(BACKGROUND), 'b point[' + both(scalar, k('rtc', v('alternatives'), v('point'))) + ']', 'e')
    foreground = 'o a[r c[i[value ' + PC + '][s[v value]]]][v focus]'
    background = 'o a[v background][' + ' '.join(v(n) for n, _ in INPUTS) + ']'
    text += definition('rtf', 'background i c[' + BG_FUNCTION + '] ' + params(INPUTS), k('rst', foreground, background), PAIR)
    for name, background_symbol in (('rtg', 'rtd'), ('rth', 'rte')):
        text += definition(name, params(INPUTS), k('rtf', 'r c[p ' + background_symbol + ']', *(v(n) for n, _ in INPUTS)), PAIR)
    text += definition('rti', 'frame ' + FRAME + ' target ' + ACTION_CODE,
        'o a[v frame][o r[v target]]', PC)
    mapped = 'q[v targets][l[' + PC + '][]][i[state j[' + PC + '] target ' + ACTION_CODE + '][m[v state][l[' + PC + '][' + k('rti', v('frame'), v('target')) + ']]]]'
    text += definition('rtj', 'frame ' + FRAME + ' targets j[' + ACTION_CODE + ']', mapped, 'j[' + PC + ']')
    append = 'r b[i[prefix j[' + PC + '] item ' + PC + '][m[v prefix][l[' + PC + '][v item]]]]'
    quoted = 'q[v contents][r b[l[' + PC + '][]]][i[state i b[j[' + PC + ']] item ' + PC + '][o a[' + append + '][v state o r[v item]]]]'
    text += definition('rtk', 'contents j[' + PC + ']', quoted, 'i b[j[' + PC + ']]')
    fields = 'frame ' + FRAME + ' focus ' + ACTION_CODE + ' alternatives j[' + ACTION_CODE + '] ' + params(INPUTS[2:])
    text += definition('rtl', fields, k('rth', 'o r[' + k('rti', v('frame'), v('focus')) + ']',
        k('rtk', k('rtj', v('frame'), v('alternatives'))), v('observer'), v('anchor'), v('ranking')), PAIR)
    return text


def library():
    return parse('p:' + definitions())


def example():
    text = 'r jdforeground[d] c.r jdfirst[d] c.r jdsecond[d] c.r jdview[] a.r jdanchor[] d.r jdranking[' + ORDER[2:ORDER.rfind(']')] + '] c.'
    for name, primitive in (('jdfocus', 'jdforeground'), ('jdone', 'jdfirst'), ('jdtwo', 'jdsecond')):
        text += definition(name, '', 'b point[' + k(primitive, v('point')) + ']', 'e')
    inputs = ['r b[r b[k jdfocus[]]]', 'r b[l[' + PC + '][r b[k jdone[]] r b[k jdtwo[]]]]',
              'r[k jdview[]]', 'r[k jdanchor[]]', 'r[p jdranking]']
    text += definition('jdpackage', '', k('rth', *inputs), PAIR)
    text += definition('jdnegated', '', k('rsw', k('jdpackage')), PAIR)
    text += 'q[k rsy[k jdpackage[] k jdanchor[]]].q[k rsx[k jdpackage[] k jdanchor[]]].'
    text += 'q[k rsy[k jdnegated[] k jdanchor[]]].q[k rsx[k jdnegated[] k jdanchor[]]].'
    text += 'l[s[k rsz[k jdpackage[]]]].'
    return parse(format_graph(library(), 'compact') + text)


def permission_example():
    doc = library()
    source = parse((ROOT / 'examples/v016/kant-prior-criticism.noema').read_text(encoding='utf-8'))
    doc['declarations'].append(next(d for d in source['declarations'] if d['name'] == 'rdm'))
    text = ''.join('r jd' + name + '[] a.' for name in ('ruler', 'person', 'role', 'act', 'author'))
    text += 'r jdanchor[] d.r jdordinary[a a d] c.r jdcritique[a a d] c.'
    text += 'r jdrequired[a a a a ' + ACTION_CODE + ' c d] c.r jdallowed[a a a a ' + ACTION_CODE + ' c d] c.'
    text += 'r jdranking[' + ORDER[2:ORDER.rfind(']')] + '] c.'
    ordinary = 'k jdordinary[v person v activity v point]'
    text += definition('jdplain', 'person a activity a', 'b point[' + ordinary + ']', 'e')
    text += definition('jdcompound', 'person a activity a', 'b point[' + both(ordinary, 'k jdcritique[v person v activity v point]') + ']', 'e')
    text += definition('jdpermission', 'target ' + ACTION_CODE, 'b point[k rdm[k jdruler[] k jdperson[] k jdrole[] k jdact[] v target ' + TRUE + ' v point p jdrequired p jdallowed]]', 'e')
    text += definition('jdpackage', '', 'k rtl[r b[p jdpermission] r[p jdcompound] l[' + ACTION_CODE + '][r[p jdplain]] r[k jdauthor[]] r[k jdanchor[]] r[p jdranking]]', PAIR)
    queries = [k('rsy', k('jdpackage'), k('jdanchor')), k('rsx', k('jdpackage'), k('jdanchor')),
               k('rsx', k('rsw', k('jdpackage')), k('jdanchor'))]
    text += ''.join('q[' + query + '].' for query in queries)
    return parse(format_graph(doc, 'compact') + text)


def build():
    return {LIBRARY: format_graph(library(), 'compact') + '\n', EXAMPLE: format_graph(example(), 'compact') + '\n',
            PERMISSIONS: format_graph(permission_example(), 'compact') + '\n'}


def basis():
    return dict(status='explicit_scalar_background_pair_not_full_presupposition_theory', library=LIBRARY, example=EXAMPLE,
        permission_example=PERMISSIONS,
        definitions=dict(rst='主張内容と背景内容の閉じた記述を区別して保持する二項の組。選択関数を受ける通常のNoema関数で表す。',
            rsu='主張内容の記述を取り出す。', rsv='背景内容の記述を取り出す。',
            rsw='主張内容だけを否定した記述へ変換し、背景の記述をそのまま保持する。',
            rsx='主張内容を指定状況で評価する。背景の成立を前提に真偽を補わない。',
            rsy='背景内容を指定状況で評価する。背景不成立を主張内容の否定へ変換しない。',
            rsz='主張内容の肯否を問う発話の記述を作る。元の組は背景を保持するが、返した発話型そのものに背景を埋め込む操作ではない。',
            rta='明示した記述列上で、同じ視点と基準文脈の比較関係が非反射的・推移的であることを検査する。全順序は要求しない。',
            rtb='焦点の記述以外の比較対象列が非空で、焦点を加えた範囲でrtaが成立し、焦点が全比較対象より指定尺度で上位にある。',
            rtc='比較対象のうち少なくとも一つの内容が指定状況で成立する。焦点内容の真偽を検査しない。',
            rtd='指定視点・基準文脈の尺度条件だけを背景内容にする。',
            rte='rtdの尺度条件に、比較対象の少なくとも一つが評価状況で成立する追加条件を併記した背景。',
            rtf='同じ焦点の記述から主張内容と背景の引数を構成する。構成時に内容を実行しない。',
            rtg='尺度条件だけを背景にした組を構成する。', rth='尺度条件と追加条件を背景にした組を構成する。',
            rti='同じ閉じた枠へ一つの行為記述を適用した内容記述を作る。行為自体は実行しない。',
            rtj='行為記述の列の各要素へ同じ枠を適用し、比較内容の列を作る。',
            rtk='内容記述の列を、同じ順序・重複を保った列の閉じた記述にする。',
            rtl='同じ枠に焦点の行為記述と全比較対象をそれぞれ適用し、その内容でrthの組を作る。'),
        references=[dict(url='https://semprag.org/index.php/sp/article/view/sp.9.2', author='Yael Greenberg', year=2016,
            title='A novel problem for the likelihood-based semantics of even', use='確率・起こりにくさだけを尺度の唯一の定義としない設計上の注意。論文の理論全体を実装したものではない。')],
        limitations=[
            '背景と主張を保持する表現であり、自然言語の前提投射・受容・修復・談話更新の一般理論ではない。背景が偽なら、その背景が満たされないことを別に報告する。',
            '尺度は同じ視点と基準文脈に依存する入力。起こりにくさ、意外性、注目すべき程度などを一律に確率へ還元しない。尺度の妥当性と比較対象の選定根拠は別に説明する。',
            '比較対象列は焦点自身を含めない。空の列や自己比較から極端性を認定しない。重複は保存するが比較の重みにはしない。',
            '記述は構文によって識別する。同じ内容の別名を自動では統合せず、意味的に不適切な代替の選定まで構文検査で排除できるとはしない。',
            'rtlは同じ枠の一つの行為記述引数だけを差し替える。枠がその引数を無視する場合や、語用論的に無関係な代替を選ぶ場合まで適切な焦点と認定するものではない。',
            '追加条件を持つ組と持たない組を区別する。全言語・全用法のevenやsogarへ一律の追加前提を要求しない。',
            '否定・質問について検査するのは明示した操作の振る舞いである。複合文全般の投射、否定の異なる作用範囲、背景そのものへの異議申し立ての談話効果は未完。',
            'カント本文の焦点位置・尺度・視点の確定と著者帰属への接続は未完。新しい原文対応範囲や意味確認済み区間を追加しない。'])


def main():
    for name, text in (build() | {BASIS: json.dumps(basis(), ensure_ascii=False, indent=2) + '\n'}).items():
        path = ROOT / name
        if path.exists():
            if path.read_text(encoding='utf-8') != text:
                raise ValueError('Stored scalar background differs: ' + name)
        else:
            with path.open('x', encoding='utf-8', newline='\n') as stream:
                stream.write(text)
        print(name, len(text), 'characters')


if __name__ == '__main__':
    main()
