import { DocsBody, DocsPage, DocsTitle } from 'fumadocs-ui/layouts/docs/page';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { sources } from '../../../source.mjs';

export const dynamicParams = false;

export function generateStaticParams({ params: { lang } }) {
  return sources[lang].getPages().map(({ slugs }) => ({ slug: slugs }));
}

function getPage(lang, slug) {
  const page = sources[lang]?.getPage(slug);
  if (!page) notFound();
  return page;
}

export async function generateMetadata({ params }) {
  const { lang, slug } = await params;
  return { title: getPage(lang, slug).data.title };
}

export default async function Page({ params }) {
  const { lang, slug } = await params;
  const page = getPage(lang, slug);
  const other = lang === 'en' ? 'ko' : 'en';
  const destination = sources[other].getPage(slug)?.url ?? `/${other}/`;
  const label = other === 'ko' ? '한국어' : 'English';
  return (
    <DocsPage toc={page.data.toc} tableOfContent={{ enabled: page.data.toc.length > 0 }}>
      <header className="doc-heading">
        <DocsTitle>{page.data.title}</DocsTitle>
        <Link className="language-link" href={destination} lang={other} hrefLang={other}>{label}</Link>
      </header>
      <DocsBody className="mudplot-markdown" dangerouslySetInnerHTML={{ __html: page.data.html }} />
    </DocsPage>
  );
}
