export {default} from '../src/ui/LandingPage';
export async function getStaticProps() {
  const {pageData} = await import('../src/page.mjs');
  return {props:pageData('en')};
}
