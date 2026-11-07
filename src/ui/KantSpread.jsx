import {getContent} from '../content.mjs';
import {asset} from '../site/web.mjs';
import {ScrollArea} from './ScrollArea';
import english from '../../public/specimens/kant-english.json';

export default function KantSpread({locale, onOpen}) {
  const c = getContent(locale);
  return <figure className="kant-comparison" aria-label={c.kantComparisonTitle}>
    <ScrollArea className="kant-viewport" id="kant-spread" both label={c.kantComparisonTitle}>
      <div className="kant-spread">
        <article className="kant-leaf" lang="en" aria-label="Opening four paragraphs: English translation by John Richardson, 1798">
          <div className="kant-paper kant-english">
            {english.paragraphs.map(p => <p key={p.unit}>{p.text}</p>)}
          </div>
        </article>
        <div className="kant-leaf">
          <button className="kant-paper kant-noema" type="button" aria-label={c.kantComparisonEnlarge} aria-haspopup="dialog" onClick={onOpen}>
            <img className="ink" src={asset('specimens/kant-four-paragraphs.svg')} width="4460" height="6300" loading="lazy" alt={c.kantComparisonAlt}/>
          </button>
        </div>
      </div>
    </ScrollArea>
  </figure>;
}
