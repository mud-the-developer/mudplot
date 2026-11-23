import { execFileSync } from 'node:child_process';
import { copyFile, lstat, mkdir, readFile, realpath, rename, writeFile } from 'node:fs/promises';
import { dirname, posix, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import GithubSlugger from 'github-slugger';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import rehypeStringify from 'rehype-stringify';
import remarkGfm from 'remark-gfm';
import remarkParse from 'remark-parse';
import remarkRehype from 'remark-rehype';
import { unified } from 'unified';
import { visit } from 'unist-util-visit';
import { groups, languages, overview, repoUrl } from '../content.mjs';

const site = fileURLToPath(new URL('..', import.meta.url));
const root = await realpath(resolve(site, '..'));
const base = process.env.DOCS_BASE_PATH || '';
if (base && !/^\/[\w.-]+(?:\/[\w.-]+)*$/.test(base)) {
  throw new Error('DOCS_BASE_PATH must start with a slash and have no trailing slash');
}
const tracked = new Set(execFileSync('git', ['ls-files', '-z'], { cwd: root, encoding: 'utf8' }).split('\0'));
const pages = languages.flatMap((lang, i) => [
  { lang, slug: 'index', file: overview[i + 1], url: `/${lang}/` },
  ...groups.flatMap(({ slug: group, pages }) => pages.flatMap(([id, ...files]) => (
    files[i] ? [{ lang, slug: `${group}/${id}`, file: files[i], url: `/${lang}/${group}/${id}/` }] : []
  ))),
]);
const byFile = new Map();
for (const page of pages) {
  if (!byFile.has(page.file)) byFile.set(page.file, []);
  byFile.get(page.file).push(page);
}
const assets = new Set();
const plot = /^docs\/images\/(?:[\w-]+\/)*[\w-]+(?:\.(?:png|svg|pdf)|\.mplot\.json)$/;
const internal = /(?:^|\/)(?:review_evidence|REVIEW_[^/]+|review-map\.md|WORK_SNAPSHOT[^/]*|V[12]_[^/]*|mudplot_review_checklist[^/]*|scientific_quality\/report\.json|visual_quality\.json)(?:\/|$)/i;
const source = /^(?:README(?:\.ko)?\.md|LICENSE|(?:CONTRIBUTING|ROADMAP)(?:\.ko)?\.md|docs\/VISUAL_REVIEW\.html|(?:dashboard|mudplot-editor)\/README(?:\.ko)?\.md|(?:examples|mudplot|scripts)\/(?:[\w.-]+\/)*[\w.-]+\.py|schemas\/[\w.-]+\.json)$/;
const safeFile = async (file) => {
  const path = resolve(root, file);
  if (!path.startsWith(root + sep) || await realpath(path) !== path) {
    throw new Error(`Documentation cannot read a path outside its source tree or through a symlink: ${file}`);
  }
  return path;
};

function publicUrl(value, page, image) {
  if (typeof value !== 'string' || !value) throw new Error(`Missing link in ${page.file}`);
  if (value.startsWith('#')) return value;
  if (/^https:\/\//i.test(value) || /^http:\/\//i.test(value) || /^mailto:/i.test(value)) {
    if (image) throw new Error(`Document images must be local plot assets: ${page.file}`);
    if (value.startsWith(`${repoUrl}/`) && internal.test(new URL(value).pathname)) return undefined;
    return value;
  }
  if (/^(?:[a-z][a-z\d+.-]*:|\/|\\)/i.test(value)) {
    throw new Error(`Unsupported URL ${value} in ${page.file}`);
  }
  const [, raw, suffix] = /^([^?#]*)(.*)$/.exec(value);
  const target = posix.join(posix.dirname(page.file), decodeURIComponent(raw));
  if (internal.test(target)) return undefined;
  if (plot.test(target) && tracked.has(target)) {
    assets.add(target);
    return `${base}/plots/${target.slice('docs/images/'.length)}${suffix}`;
  }
  if (!image) {
    const choices = byFile.get(target);
    const mapped = choices?.find(({ lang }) => lang === page.lang) ?? choices?.[0];
    if (mapped) return `${base}${mapped.url}${suffix}`;
    if (source.test(target) && tracked.has(target)) return `${repoUrl}/blob/main/${target}${suffix}`;
  }
  throw new Error(`Unmapped ${image ? 'image' : 'link'} ${value} (${target}) in ${page.file}`);
}

const schema = {
  ...defaultSchema,
  tagNames: [...defaultSchema.tagNames, 'details', 'summary'],
  attributes: { ...defaultSchema.attributes, img: [...defaultSchema.attributes.img, 'width', 'height'] },
};
const text = (node) => node.value ?? node.children?.map(text).join('') ?? '';
const parser = unified().use(remarkParse).use(remarkGfm)
  .use(remarkRehype, { allowDangerousHtml: true }).use(rehypeRaw).use(rehypeSanitize, schema)
  .use(rehypeStringify);

async function render(page) {
  const tree = await parser.run(parser.parse(await readFile(await safeFile(page.file), 'utf8')));
  const titleIndex = tree.children.findIndex((node) => node.tagName === 'h1');
  if (titleIndex === -1) throw new Error(`Missing title in ${page.file}`);
  const [heading] = tree.children.splice(titleIndex, 1);
  const title = text(heading);
  const slugger = new GithubSlugger();
  const toc = [];
  visit(tree, 'element', (node) => {
    if (/^h[1-6]$/.test(node.tagName)) {
      const name = text(node);
      const id = slugger.slug(name);
      node.properties.id = id;
      node.properties.className = ['scroll-m-24'];
      const depth = Number(node.tagName[1]);
      if (depth <= 4) toc.push({ title: name, url: `#${id}`, depth });
    }
    if (node.tagName === 'a' && node.properties.href) {
      const href = publicUrl(node.properties.href, page, false);
      if (href === undefined) {
        node.tagName = 'span';
        delete node.properties.href;
      } else node.properties.href = href;
    }
    if (node.tagName === 'img' && node.properties.src) {
      node.properties.src = publicUrl(node.properties.src, page, true);
      if (!node.properties.src) throw new Error(`Internal image in ${page.file}`);
      node.properties.loading = 'lazy';
    }
  });
  return [page.lang, page.slug, { title, toc, html: parser.stringify(tree) }];
}

const generated = await Promise.all(pages.map(render));
const generatedDir = resolve(site, '.generated');
const exported = resolve(site, 'out');
for (const dir of [generatedDir, resolve(site, '.next'), exported]) {
  const details = await lstat(dir).catch((error) => {
    if (error.code !== 'ENOENT') throw error;
  });
  if (details && !details.isDirectory()) throw new Error(`Not a build directory: ${dir}`);
}
await mkdir(generatedDir, { recursive: true });
const payload = resolve(generatedDir, `pages-${process.pid}.json`);
await writeFile(payload, JSON.stringify(generated), { flag: 'wx' });
await rename(payload, resolve(generatedDir, 'pages.json'));
console.log(`Prepared ${generated.length} documentation pages and ${assets.size} referenced plot assets.`);

execFileSync(process.execPath, [resolve(site, 'node_modules/next/dist/bin/next'), 'build'], {
  cwd: site,
  stdio: 'inherit',
});

// Next recreates out/ on every export. Reserve only this new subtree, never
// copy into public/ and never remove assets from the source checkout.
const plots = resolve(exported, 'plots');
await mkdir(plots);
for (const file of [...assets].sort()) {
  const dest = resolve(plots, file.slice('docs/images/'.length));
  await mkdir(dirname(dest), { recursive: true });
  await copyFile(await safeFile(file), dest);
}
