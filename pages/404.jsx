import Head from 'next/head';
import {route} from '../src/site/web.mjs';
export default function NotFound(){return <main className="container error-page"><Head><title>404 — Noema</title></Head><p>404</p><h1>Page not found</h1><a className="text-link" href={route('ja')}>日本語 ↗</a><a className="text-link" href={route('en')}>English ↗</a></main>;}
