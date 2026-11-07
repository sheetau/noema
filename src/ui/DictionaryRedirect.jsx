import {useEffect} from 'react';
import Head from 'next/head';
import {route} from '../site/web.mjs';
export default function DictionaryRedirect({locale}) {
  const target=route(locale)+'#dictionary';
  useEffect(()=>{location.replace(route(locale)+location.search+'#dictionary');},[locale]);
  return <><Head><title>Noema dictionary</title><meta name="robots" content="noindex"/></Head><a href={target}>{locale==='ja'?'共通辞書へ':'Open the shared dictionary'}</a></>;
}
