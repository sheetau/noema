import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {dictionaryFile} from './dictionary-data.mjs';
const dictionaries = Object.fromEntries(['ja','en'].map(locale => {
  const catalog = JSON.parse(readFileSync(join(process.cwd(),'public',dictionaryFile(locale)),'utf8'));
  catalog.entries.sort((a,b)=>a.name.localeCompare(b.name,'en'));
  return [locale,catalog];
}));
export const dictionary = dictionaries.ja;
export const englishDictionary = dictionaries.en;
export function pageData(locale) {
  const catalog = dictionaries[locale];
  return {locale,initialEntries:catalog.entries.slice(0,60),counts:catalog.counts,source:catalog.source};
}
