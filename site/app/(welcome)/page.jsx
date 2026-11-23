import Link from 'next/link';
import { repoUrl } from '../../content.mjs';

export default function Welcome() {
  return (
    <main className="welcome">
      <section className="welcome-panel" aria-labelledby="welcome-title">
        <p className="welcome-kicker">DOCUMENTATION</p>
        <h1 id="welcome-title">mudplot</h1>
        <p className="welcome-intro">Scientific plotting for Python.</p>
        <p className="welcome-detail">Build publication figures with Matplotlib and save an editable FigureSpec.</p>
        <nav className="welcome-links" aria-label="Documentation languages">
          <Link href="/en/" className="welcome-primary">English documentation <span aria-hidden="true">→</span></Link>
          <Link href="/ko/" lang="ko" hrefLang="ko">한국어 문서 <span aria-hidden="true">→</span></Link>
        </nav>
        <a className="welcome-repo" href={repoUrl}>View source on GitHub</a>
      </section>
    </main>
  );
}
