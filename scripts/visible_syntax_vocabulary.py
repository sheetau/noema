"""Shared typed vocabulary and a fixed public grammar-glyph table."""
from copy import deepcopy
from importlib.resources import files
import json
import re

from noema.constructed_discourse import sort
from scripts.visible_lexical_script import Lexicon, _glyph, _shape_set, require, DIRECTIONS
from scripts.visible_word_forms import Word, symbol
from scripts.balanced_circle_script import LARGE, MEDIUM, PITCH, nucleus, geometry_check

FAMILIES = {
    'utterance': ('nested', 0), 'logic': ('nested', 2),
    'binding': ('offset', 4), 'quotation': ('offset', 6),
    'type': ('offset-left', 0), 'application': ('offset-left', 2),
    'number': ('offset-left', 6), 'sequence': ('offset', 2),
}
# A named classification and direction, never a row number or hash.
KEYWORDS = {
    'assert': ('utterance', 0), 'ask': ('utterance', 6),
    'perform': ('utterance', 4), 'suppose': ('utterance', 2),
    'direct': ('utterance', 7), 'document': ('utterance', 1),
    'import': ('utterance', 3), 'definition': ('utterance', 5),
    'not': ('logic', 0), 'and': ('logic', 6), 'or': ('logic', 2),
    'implies': ('logic', 4), 'iff': ('logic', 7), 'equal': ('logic', 5),
    'forall': ('binding', 0), 'exists': ('binding', 6),
    'variable': ('binding', 4), 'content': ('binding', 2), 'evaluate': ('binding', 7),
    'quote': ('quotation', 0), 'disquote': ('quotation', 6),
    'quoted_lift': ('quotation', 4), 'message': ('quotation', 2),
    'message_content': ('quotation', 7), 'question': ('quotation', 5),
    'answer_matches': ('quotation', 1),
    'individual': ('type', 0), 'number': ('type', 6), 'truth': ('type', 2),
    'situation': ('type', 4), 'content_type': ('type', 7), 'message_type': ('type', 5),
    'function_type': ('type', 1), 'sequence_type': ('type', 3), 'description_type': ('type', None),
    'call': ('application', 0), 'function_ref': ('application', 6),
    'apply': ('application', 2), 'quoted_apply': ('application', 4), 'lambda': ('application', 7),
    'nonnegative': ('number', 0), 'negative': ('number', 6),
    'sequence': ('sequence', 0), 'length': ('sequence', 6),
    'position': ('sequence', 2), 'concat': ('sequence', 4), 'fold': ('sequence', 7),
}


def family_glyph(name):
    pair, direction = FAMILIES[name]
    return nucleus(0., PITCH, LARGE, pair, direction, companion=MEDIUM)


def modifier_glyph(direction):
    return nucleus(0., PITCH, MEDIUM, None, direction,
                   mode='none' if direction is None else 'radius')


class Vocabulary(Lexicon):
    """General typed entries with inherited, unchanged lexical forms."""

    def __init__(self, document=None):
        if document is None:
            source=json.loads(files('noema').joinpath('resources/visible-vocabulary-v1.json').read_text(encoding='utf-8'))
            require(source['schema']=='noema-visible-vocabulary-1' and source['edition']==1
                    and source['base']=='visible-lexicon-v1.json', 'Unknown vocabulary edition')
            base=Lexicon().document()
            require(not set(base['entries']) & set(source['extensions']), 'Root redefinition')
            document=dict(schema='noema-visible-vocabulary-1',edition=1,
                          entries={**base['entries'],**source['extensions']})
        data=deepcopy(document)
        require(isinstance(data,dict) and set(data)=={'schema','edition','entries'}
                and data['schema']=='noema-visible-vocabulary-1' and data['edition']==1,
                'Invalid shared vocabulary')
        require(isinstance(data['entries'],dict) and data['entries'], 'Empty shared vocabulary')
        names,signatures={},set()
        for name,entry in data['entries'].items():
            require(isinstance(name,str) and re.fullmatch('[a-z2-7]+',name),'Invalid shared name')
            require(isinstance(entry,dict) and set(entry)=={'parameters','result','roles','meaning',
                    'context','contrast','form','aliases'},'Invalid shared entry')
            require(isinstance(entry['parameters'],list),'Invalid parameter types')
            for t in [*entry['parameters'],entry['result']]: sort(t,'0.16')
            for key in ('roles','context','contrast','aliases'):
                require(isinstance(entry[key],list) and all(isinstance(v,str) and v.strip() for v in entry[key]),
                        'Invalid shared '+key)
            require(len(entry['roles'])==len(entry['parameters']) and entry['contrast']
                    and isinstance(entry['meaning'],str) and entry['meaning'].strip(), 'Missing shared meaning/roles')
            form=entry['form']
            require(isinstance(form,dict) and set(form)=={'size','companion','ray'}
                    and form['size'] in ('medium','large')
                    and form['companion'] in ('none','small-concentric','small-east-rim')
                    and (form['ray'] is None or form['ray'] in DIRECTIONS), 'Invalid shared form')
            glyph=_glyph(form)
            geometry_check(glyph['shapes'],glyph['paths'])
            signature=_shape_set(glyph['shapes'])
            require(signature not in signatures,'Shared lexical shape collision')
            signatures.add(signature)
            for alias in [name,*entry['aliases']]:
                require(re.fullmatch('[a-z2-7]+',alias) and alias not in names,'Duplicate shared name')
                names[alias]=name
        self._document,self._names=data,names

    def declaration(self,name):
        canonical,entry=self.resolve(name)
        return dict(kind='primitive',name=symbol(Word('root',(canonical,)),self),
                    parameters=entry['parameters'],result=entry['result'])
