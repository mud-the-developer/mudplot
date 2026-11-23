import { RootProvider } from 'fumadocs-ui/provider/next';
import './global.css';

const korean = {
  'Close Sidebar(aria-label)': '사이드바 닫기',
  'Close Sidebar(sidebar)(aria-label)': '사이드바 닫기',
  'Collapse Sidebar(sidebar)(aria-label)': '사이드바 접기',
  'Hide Sidebar(sidebar)': '사이드바 숨기기',
  'Open Sidebar(sidebar)(aria-label)': '사이드바 열기',
  'Show Sidebar(sidebar)': '사이드바 표시',
  'Light(theme switcher)(aria-label)': '밝은 테마',
  'Dark(theme switcher)(aria-label)': '어두운 테마',
  'System(theme switcher)(aria-label)': '시스템 테마',
  'Toggle Theme(theme switcher)(aria-label)': '테마 전환',
  'Skip to Content(skip link)': '본문으로 건너뛰기',
  'On this page(table of contents)': '이 페이지의 내용',
  'No Headings(table of contents)': '제목 없음',
  'Previous Page(pagination)': '이전 페이지',
  'Next Page(pagination)': '다음 페이지',
};

export function Document({ lang = 'en', children }) {
  return (
    <html lang={lang} suppressHydrationWarning>
      <body>
        <RootProvider
          i18n={lang === 'ko' ? { translations: korean } : undefined}
          search={{ enabled: false }}
          theme={{ defaultTheme: 'light', hotKey: false }}
        >
          {children}
        </RootProvider>
      </body>
    </html>
  );
}
