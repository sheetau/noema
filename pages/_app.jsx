import 'lenis/dist/lenis.css';
import '../public/style.css';
import {PageScroll} from '../src/ui/ScrollArea';
export default function App({Component, pageProps}) {
  return <PageScroll><Component {...pageProps}/></PageScroll>;
}
