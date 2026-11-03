"""Join self-delimiting native items and read them from one geometry flow."""
import json
from scripts import kant_public_fragment as writing
from scripts.kant_incremental_dictionary import Reader
from scripts.kant_lexical_context import use_context
from scripts.kant_public_lexicon import read_word
from scripts.kant_interleaved_layout import compile_stream
from scripts.kant_item_rows import split_rows,shifted
from scripts.balanced_circle_script import LARGE,PITCH,near


def _freeze_words(stream,context,index):
    for event in stream:
        event['path']=[index,*event['path']]
        if event.get('word') is not None:
            event['word_length']=len(context.parts[event['word']])
        sides=[]
        for side in writing.event_sides(event):
            if isinstance(side,str):
                side=[dict(token=t,side=None,depth=event['depth']+1,path=event['path'][1:],
                           **({'word':side} if i==0 and side in context.parts else {}))
                      for i,t in enumerate(context.parts.get(side,(side,)))]
            _freeze_words(side,context,index)
            sides.append(side)
        event['side']=sides[0] if sides else None
        if len(sides)>1:event['extra_sides']=sides[1:]


def item_events(records,reader,**options):
    pending=reader.fork();stream=[];ranges=[]
    for index,item in enumerate(records):
        context=pending.context
        with use_context(context):events=writing.events(item,full_names=True,**options)
        _freeze_words(events,context,index)
        ranges.append((len(stream),len(stream)+len(events),context))
        stream+=events
        pending.register(item)
    if not stream:raise ValueError('Item run requires at least one item')
    if writing.event_count(stream)>512:raise ValueError('Item run exceeds 512 events; split at a complete item')
    # Old seams remain valid. Only add the stops required across item ends,
    # using the dictionary that exists when the respective word is read.
    tokens=[e['token'] for e in stream]
    stops={i for i,e in enumerate(stream) if e.get('lexical_seam')}
    sides={i for i,e in enumerate(stream) if e['side'] is not None}
    for start,end,context in reversed(ranges):
        with use_context(context):
            for i in range(end-1,start-1,-1):
                expected=stream[i].get('word')
                if expected is None:continue
                finish=i+stream[i]['word_length']
                actual=read_word(tokens,i,stops=stops,sides=sides)
                if actual==(expected,finish):continue
                if actual[1]<=finish:raise ValueError('Item word cannot be delimited by a suffix boundary')
                stops.add(finish)
                if read_word(tokens,i,stops=stops,sides=sides)!=(expected,finish):
                    raise ValueError('Item boundary did not disambiguate word')
    for i in stops:stream[i]['lexical_seam']=True
    return stream,pending


def compile_run(records,*,reader=None,contacts=True,**options):
    stream,pending=item_events(records,reader if reader is not None else Reader(),**options)
    drawing=compile_stream(stream,contacts=contacts)
    return drawing,pending


def read_row(shapes,reader):
    circles=[s for s in shapes if s['kind']=='circle']
    if not circles:raise ValueError('Page row has no circles')
    large=[s['y'] for s in circles if near(s['r'],LARGE)]
    if large:
        if any(not near(y,large[0]) for y in large):raise ValueError('Page row has inconsistent central rails')
        baselines=[large[0]]
    else:
        low=min(s['y'] for s in circles);baselines=[low-PITCH,low,low+PITCH]
    decoded={};errors=[]
    for baseline in baselines:
        try:pending,items=writing.decode_run(shifted(shapes,PITCH-baseline),reader=reader)
        except ValueError as error:errors.append(str(error));continue
        decoded[json.dumps(items,sort_keys=True,separators=(',',':'))]=pending
    if not decoded:raise ValueError('No readable item run: '+('; '.join(errors)))
    if len(decoded)!=1:raise ValueError('Ambiguous item run reading')
    return next(iter(decoded.values()))


def decode_page(shapes,*,seed=None,include_spellings=False):
    reader=Reader(seed)
    for row in split_rows(shapes):reader=read_row(row,reader)
    return reader.result(include_spellings)
