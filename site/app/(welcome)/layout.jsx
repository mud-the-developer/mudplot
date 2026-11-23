import { Document } from '../document';

export const metadata = { title: 'mudplot documentation' };

export default function WelcomeLayout({ children }) {
  return <Document>{children}</Document>;
}
