"""Construct exact personal message and review-purpose descriptions, without evaluation."""
import json
from pathlib import Path

from noema.grammar import parse as old_parse
from noema.extraction import extract_document
from noema.constructed import parse, format_graph, promote

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'examples/v014/kant-unrestricted-others.noema'
EXAMPLE = 'examples/v016/personal-message-purpose.noema'
DEFINITIONS = '''
d rqa[criterion i[h[j[a]] e]] i[h[a] f][o a[r[i[meaning h[j[a]] e][i[subject a][j s[c[v meaning][l[a][v subject]]]]]]][v criterion]].
d rqb[recipient i[a] subject i[a] message i[h[a] f]] i[e][o a[r[p hzx]][v recipient v subject o r[v message]]].
d rqc[criterion i[h[j[a]] e] recipient i[a] subject i[a] message i[h[a] f] purpose i[e]] c[w[e[v message][k rqa[v criterion]]][e[v purpose][k rqb[v recipient v subject v message]]]].
'''
EXTRA = '''
r jown[j[a]] e.r jother[j[a]] e.r jrecipient[] a.r jsubject[] a.
r jselect[a i[h[j[a]] e] i[h[j[a]] e]] i[h[j[a]] e].
r jinspect[a i[h[j[a]] e] i[h[a] f] i[e]] c.
d jqcriterion[person a] i[h[j[a]] e][k jselect[v person r[p jown] r[p jother]]].
d jqmessage[person a] i[h[a] f][k rqa[k jqcriterion[v person]]].
d jqpurpose[person a] i[e][k rqb[r[k jrecipient[]] r[k jsubject[]] k jqmessage[v person]]].
s[f person a[k jinspect[v person k jqcriterion[v person] k jqmessage[v person] k jqpurpose[v person]]]].
'''


def build_example():
    parent = old_parse((ROOT / PARENT).read_text(encoding='utf-8'))
    core = extract_document(parent, roots=['hzx'], statement_indices=[]).document
    return format_graph(parse(format_graph(promote(core), 'compact') + DEFINITIONS + EXTRA), 'compact') + '\n'


def main():
    path = ROOT / EXAMPLE
    text = build_example()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding='utf-8') != text:
            raise ValueError('Stored personal-purpose example differs')
    else:
        with path.open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
    print(EXAMPLE, len(text), 'characters')


if __name__ == '__main__':
    main()
