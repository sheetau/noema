import {readFileSync} from 'node:fs';
import {join} from 'node:path';
export const dictionary = JSON.parse(readFileSync(join(process.cwd(),'public/data/dictionary.json'),'utf8'));
dictionary.entries.sort((a,b)=>a.name.localeCompare(b.name,'en'));
export function pageData(locale) {
  return {locale,initialEntries:dictionary.entries.slice(0,60),counts:dictionary.counts,source:dictionary.source};
}
