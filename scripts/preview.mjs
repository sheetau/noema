import {access} from 'node:fs/promises';
import {resolve} from 'node:path';
import {root} from '../src/site/config.mjs';
import {createStaticServer, listen} from './server.mjs';
try {
  await access(resolve(root,'out/index.html'));
  await listen(createStaticServer(resolve(root,'out')));
} catch (error) {
  console.error(error.code === 'ENOENT' ? 'Run npm run build before npm run preview.' : error.message);
  process.exitCode = 1;
}
