import {Html, Head, Main, NextScript} from 'next/document';
import {asset} from '../src/site/web.mjs';
export default function Document(props) {
  return <Html lang={props.__NEXT_DATA__?.props?.pageProps?.locale ?? 'en'}><Head>
    <link rel="icon" href={asset('favicon.ico')} type="image/x-icon" sizes="16x16 24x24 32x32 48x48 64x64 128x128 256x256"/>
    <meta name="theme-color" content="#000000"/><meta name="color-scheme" content="dark"/>
    <link rel="preload" href={asset('fonts/helvetica-now-text.ttf')} as="font" type="font/ttf" crossOrigin="anonymous"/>
    <style dangerouslySetInnerHTML={{__html:`@font-face{font-family:"Helvetica Now Text";src:url("${asset('fonts/helvetica-now-text.ttf')}") format("truetype");font-weight:100 900;font-display:swap}@font-face{font-family:"M PLUS 1 Code";src:url("${asset('fonts/m-plus-1-code-full.woff2')}") format("woff2");font-weight:100 900;font-display:swap}`}}/>
  </Head><body id="top"><Main/><NextScript/></body></Html>;
}
