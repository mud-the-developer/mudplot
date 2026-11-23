import { loader } from 'fumadocs-core/source';
import data from './.generated/pages.json';
import { groups, languages } from './content.mjs';

export const sources = Object.fromEntries(languages.map((lang, i) => {
  const files = data.flatMap(([pageLang, slug, page]) => pageLang === lang
    ? [{ type: 'page', path: `${slug}.md`, data: page }]
    : []);
  files.push({
    type: 'meta', path: 'meta.json', data: { pages: ['index', ...groups.map(({ slug }) => slug)] },
  });
  for (const { slug, titles, pages } of groups) {
    files.push({
      type: 'meta', path: `${slug}/meta.json`,
      data: { title: titles[i], pages: pages.filter((row) => row[i + 1]).map(([id]) => id) },
    });
  }
  return [lang, loader({ files }, { baseUrl: `/${lang}` })];
}));
