export const base = process.env.NEXT_PUBLIC_BASE_PATH ?? '/noema';
export const asset = file => `${base}/${file}`;
export const repository = 'https://github.com/sheetau/noema';
export const origin = 'https://sheetau.github.io';
export const route = locale => `${base}/${locale === 'ja' ? 'ja/' : ''}`;
export const docLink = path => `${repository}/blob/main/${path}`;
export const guideLink = (topic, locale) => docLink(`docs/${locale === 'ja' ? 'ja' : 'guide'}/${topic}.md`);
