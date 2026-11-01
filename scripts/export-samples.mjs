import { writeFile } from 'node:fs/promises';
import { examples, introductory } from '../src/examples.mjs';
await writeFile(new URL('../src/samples.json', import.meta.url), JSON.stringify([...examples, introductory].map(({id, source})=>({id, source})), null, 2)+'\n');
