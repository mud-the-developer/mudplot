import { DocsLayout } from 'fumadocs-ui/layouts/docs';
import { notFound } from 'next/navigation';
import { languages, repoUrl } from '../../content.mjs';
import { sources } from '../../source.mjs';
import { Document } from '../document';

export const dynamicParams = false;
export const metadata = { title: { default: 'mudplot', template: '%s · mudplot' } };

export function generateStaticParams() {
  return languages.map((lang) => ({ lang }));
}

export default async function LanguageLayout({ children, params }) {
  const { lang } = await params;
  if (!languages.includes(lang)) notFound();
  return (
    <Document lang={lang}>
      <DocsLayout
        tree={sources[lang].getPageTree()}
        nav={{ title: 'mudplot', url: `/${lang}/` }}
        githubUrl={repoUrl}
        searchToggle={{ enabled: false }}
        tabs={false}
      >
        {children}
      </DocsLayout>
    </Document>
  );
}
