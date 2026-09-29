"""Loss-accounted source segmentation. This does not translate or interpret text."""
from dataclasses import dataclass, field
from html.parser import HTMLParser
import hashlib
import re

from .semantics import require


@dataclass(eq=False)
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    start: int = 0
    end: int = 0
    text: str = ''

    def walk(self):
        yield self
        for child in self.children:
            yield from child.walk()


class Tree(HTMLParser):
    VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.html = html
        self.lines = [0]
        self.lines.extend(m.end() for m in re.finditer('\n', html))
        self.root = Node('root')
        self.stack = [self.root]
        self.feed(html)
        self.close()
        require(len(self.stack) == 1, 'Unclosed source HTML elements')

    def absolute_position(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs), start=self.absolute_position())
        self.stack[-1].children.append(node)
        if tag in self.VOID:
            node.end = node.start + len(self.get_starttag_text())
        else:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            node = self.stack.pop()
            node.end = node.start + len(self.get_starttag_text())

    def handle_endtag(self, tag):
        # HTML void elements sometimes have explicit closing tags.
        if tag in self.VOID:
            return
        require(self.stack[-1].tag == tag, f'Mismatched source HTML close: {tag} after {self.stack[-1].tag}')
        self.stack.pop().end = self.html.index('>', self.absolute_position()) + 1

    def handle_data(self, text):
        self.stack[-1].children.append(Node('#text', start=self.absolute_position(), text=text))


def compact(text):
    return re.sub(r'\s+', ' ', text).strip()


def plain(node):
    return ''.join(n.text for n in node.walk() if n.tag == '#text')


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


BLOCKS = {'p', 'div', 'center', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'ol', 'ul', 'dl', 'dt', 'dd', 'table', 'tr', 'td', 'th'}


def segment(html, work):
    require(work in ('einstein-1905', 'kant-1784'), 'Unknown source configuration')
    tree = Tree(html)
    candidates = [n for n in tree.root.walk() if n.tag == 'div'
                  and n.attrs.get('style', '').startswith('display:table; text-align:justify;')]
    require(len(candidates) == 1, 'Ambiguous source work boundary')
    root = candidates[0]
    require(not any(n.tag in ('img', 'svg', 'video', 'audio', 'table', 'script', 'style') for n in root.walk()),
            'Unsupported non-text source content requires explicit extraction')
    units, math, annotations = [], [], []
    pieces, current_math, current_annotations, current_nodes = [], [], [], []
    ownership, page = {}, None
    category = 'frontmatter'

    def own(node, owner):
        for child in node.walk():
            if child.tag == '#text' and compact(child.text):
                require(id(child) not in ownership, 'Source text assigned twice')
                ownership[id(child)] = owner

    def flush():
        nonlocal pieces, current_math, current_annotations, current_nodes, category
        text = compact(''.join(pieces))
        if text:
            if work == 'einstein-1905' and text.startswith('Daß die Elektrodynamik'):
                category = 'body'
            if work == 'kant-1784' and text.startswith('Aufklärung ist der Ausgang'):
                category = 'body'
            if text == 'Anmerkungen (Wikisource)':
                require(work == 'kant-1784', 'Unexpected editorial boundary')
                category = 'editorial'
            kind = category
            if category != 'editorial':
                if text.startswith('*)') or any(n.tag == 'li' and n.attrs.get('id', '').startswith('cite_note-') for n in current_nodes):
                    kind = 'author_note'
                elif text.startswith(('§ ', 'I. Kinematischer', 'II. Elektrodynamischer')):
                    kind = 'heading'
                elif current_math and not re.sub(r'\[M\d+\]|[\s.,;:()]+', '', text):
                    kind = 'equation'
            ident = f'{work}:u{len(units) + 1:04d}'
            for node in current_nodes:
                if node.tag == '#text':
                    own(node, ident)
            units.append({'id': ident, 'kind': kind, 'text': text, 'text_sha256': digest(text),
                          'source_ids': [n.attrs['id'] for n in current_nodes if 'id' in n.attrs],
                          'page_at_end': page, 'math_ids': current_math, 'annotation_ids': current_annotations,
                          'facsimile_review': 'pending'})
        pieces, current_math, current_annotations, current_nodes = [], [], [], []

    def visit(node):
        nonlocal page
        classes = node.attrs.get('class', '').split()
        if node.tag == 'math':
            ident = f'M{len(math) + 1:04d}'
            raw = html[node.start:node.end]
            require(raw.startswith('<math') and raw.endswith('</math>'), 'Incomplete MathML')
            math.append({'id': ident, 'mathml': raw, 'sha256': digest(raw), 'source_start': node.start, 'source_end': node.end})
            own(node, ident)
            pieces.append('[' + ident + ']')
            current_math.append(ident)
            return
        annotation_kind = ('page' if 'pagenum' in classes or 'PageNumber' in classes else
                           'reference' if 'reference' in classes else
                           'backlink' if 'mw-cite-backlink' in classes else None)
        if annotation_kind:
            ident = f'A{len(annotations) + 1:04d}'
            if annotation_kind == 'page':
                page = node.attrs.get('id')
            annotations.append({'id': ident, 'kind': annotation_kind, 'source_id': node.attrs.get('id'),
                                'source_start': node.start, 'source_end': node.end,
                                'text': compact(plain(node)), 'targets': [n.attrs['href'] for n in node.walk() if 'href' in n.attrs]})
            own(node, ident)
            current_annotations.append(ident)
            return
        if node.tag in BLOCKS:
            flush()
            current_nodes.append(node)
        if node.tag == '#text':
            pieces.append(node.text)
            current_nodes.append(node)
        elif node.tag == 'br':
            pieces.append('\n')
        else:
            for child in node.children:
                visit(child)
        if node.tag in BLOCKS:
            flush()

    visit(root)
    flush()
    nonblank = [n for n in root.walk() if n.tag == '#text' and compact(n.text)]
    require(set(map(id, nonblank)) == set(ownership), 'Unassigned source text')
    require(sum(n.tag == 'math' for n in root.walk()) == len(math), 'Lost or nested MathML')
    require(any(u['kind'] == 'body' for u in units), 'Author body start not found')
    source_ids = {ident for u in units for ident in u['source_ids']}
    require(all(target[1:] in source_ids for a in annotations if a['kind'] == 'reference'
                for target in a['targets'] if target.startswith('#cite_note-')), 'Unresolved source note reference')
    return {'work': work, 'root_range': [root.start, root.end], 'root_sha256': digest(html[root.start:root.end]),
            'units': units, 'math': math, 'annotations': annotations,
            'audit': {'nonblank_text_nodes': len(nonblank), 'assigned_text_nodes': len(ownership),
                      'math_elements': len(math), 'source_accounting_exact': True,
                      'facsimile_review': 'pending', 'semantic_coverage': 'not_started'}}
