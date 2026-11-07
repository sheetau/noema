import {fileURLToPath} from 'node:url';

export const root = fileURLToPath(new URL('../../', import.meta.url));
export const base = (process.env.NEXT_PUBLIC_BASE_PATH ?? process.env.BASE_PATH ?? '/noema').replace(/\/$/, '');
if (base && !/^\/[a-zA-Z0-9_-]+(?:\/[a-zA-Z0-9_-]+)*$/.test(base)) {
  throw new Error('BASE_PATH must be empty or a URL path such as /noema.');
}
export const site = Object.freeze({
  name: 'Noema', edition: '1.0', released: '2026-11-05',
  origin: 'https://sheetau.github.io', repository: 'https://github.com/sheetau/noema',
  locales: ['en', 'ja'],
});
export const route = (locale, path = '', prefix = base) => `${prefix}/${locale === 'ja' ? 'ja/' : ''}${path}`;
export const docLink = path => `${site.repository}/blob/main/${path}`;
