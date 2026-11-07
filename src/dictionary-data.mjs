const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
export const labels = {
  ja:{primitive:'基本宣言', definition:'合成定義', 'shared-core':'共通基礎', 'shared-extension':'共通拡張', 'domain-contract':'分野・文脈条件つき', 'source-selector':'作品内参照補助'},
  en:{primitive:'Primitive', definition:'Definition', 'shared-core':'Shared core', 'shared-extension':'Shared extension', 'domain-contract':'Domain / context contract', 'source-selector':'Source selector'},
};
function type(value) {
  if (typeof value === 'string') return value;
  if (value?.sort) return type(value.sort);
  return JSON.stringify(value);
}
export function entryDetailHTML(entry, locale) {
  const ja = locale === 'ja', l = labels[locale];
  const list = (title, items) => items?.length ? `<div><dt>${title}</dt><dd>${items.map(escape).join(' · ')}</dd></div>` : '';
  return `<p class="word-spelling">${escape(entry.spelling.join(' · '))}</p><p lang="ja">${escape(entry.meaning)}</p><dl class="word-detail">
<div><dt>${ja ? '型' : 'Type'}</dt><dd><code>(${entry.parameters.map(type).map(escape).join(', ')}) → ${escape(type(entry.result))}</code></dd></div>
${list(ja ? '引数の順序' : 'Argument order', entry.roles)}${list(ja ? '文脈' : 'Context', entry.context)}${list(ja ? '区別する読み' : 'Contrasts', entry.contrast)}
<div><dt>${ja ? '構成・利用範囲' : 'Kind and scope'}</dt><dd>${l[entry.kind]} · ${l[entry.portability]}</dd></div>
<div><dt>${ja ? '正式な名前' : 'Native name'}</dt><dd><code>${escape(entry.symbol)}</code></dd></div>
</dl><div class="entry-sources">${entry.sources.map((p,i)=>`<a class="text-link" href="https://github.com/sheetau/noema/blob/main/${escape(p)}">${ja ? '出典' : 'Source'} ${i+1} ↗</a>`).join('')}</div>`;
}

export function filterEntries(entries, {query = '', kind = '', scope = ''} = {}) {
  const terms = query.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const result = entries.filter(e => (!kind || e.kind === kind) && (!scope || e.portability === scope) &&
    terms.every(term => [e.name, e.symbol, e.meaning, ...e.spelling, ...e.roles, ...e.context, ...e.contrast].join(' ').toLocaleLowerCase().includes(term)));
  // An exact word name should precede the many spellings containing that root.
  if (terms.length) {
    const text = terms.join(' ');
    const rank = e => e.name.toLowerCase() === text || e.symbol.toLowerCase() === text ? 0 : e.name.toLowerCase().startsWith(text) ? 1 : e.name.toLowerCase().includes(text) ? 2 : 3;
    result.sort((a,b)=>rank(a)-rank(b));
  }
  return result;
}
