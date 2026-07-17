import assert from 'node:assert/strict';
import { readdir, readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import {
  FRONTEND_RELEASE_SHA,
  RELEASE_METADATA,
  isMatchingReleaseMetadata,
} from '../src/lib/releaseMetadata.js';

const frontendRoot = join(dirname(fileURLToPath(import.meta.url)), '..');

async function collectFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...await collectFiles(path));
    } else {
      files.push(path);
    }
  }
  return files;
}

test('frontend release metadata is frozen and rejects mismatched backend releases', () => {
  assert.deepEqual(RELEASE_METADATA, {
    contract_version: '2.0',
    assessment_version: 'india-en-3.0.0',
    scoring_policy_version: 'readiness-rubric-1.1.0',
  });
  assert.equal(FRONTEND_RELEASE_SHA, 'local');
  assert.equal(isMatchingReleaseMetadata({ ...RELEASE_METADATA, release_sha: 'local' }), true);
  assert.equal(isMatchingReleaseMetadata({ ...RELEASE_METADATA, release_sha: 'other-release' }), false);
  assert.equal(isMatchingReleaseMetadata({ ...RELEASE_METADATA, release_sha: 'local', extra: true }), true);
});

test('assessment transport preflights liveness and checks release metadata on form and score', async () => {
  const api = await readFile(join(frontendRoot, 'src/lib/api.js'), 'utf8');
  const errors = await readFile(join(frontendRoot, 'src/utils/apiErrors.js'), 'utf8');
  assert.match(api, /fetchV2Live/);
  assert.match(api, /assertMatchingRelease/);
  assert.match(api, /api\.get\('\/live'/);
  assert.match(api, /api\.get\('\/v2\/assessment\/form'/);
  assert.match(api, /api\.post\('\/v2\/assessment\/score'/);
  assert.match(api, /release_mismatch/);
  assert.match(errors, /release_mismatch/);
});

test('production frontend configuration requires the release SHA from the deployment environment', async () => {
  const productionEnv = await readFile(join(frontendRoot, '.env.production'), 'utf8');
  const exampleEnv = await readFile(join(frontendRoot, '..', '.env.example'), 'utf8');
  const releaseGate = await readFile(join(frontendRoot, 'verify-release-sha.mjs'), 'utf8');
  const packageJson = JSON.parse(await readFile(join(frontendRoot, 'package.json'), 'utf8'));
  assert.match(productionEnv, /VITE_RELEASE_SHA/);
  assert.match(exampleEnv, /VITE_RELEASE_SHA=local/);
  assert.match(releaseGate, /40-character lowercase Git SHA/);
  assert.match(packageJson.scripts.build, /verify:release/);
});

test('the CI release SHA is embedded in the emitted production bundle', async () => {
  const expected = process.env.VITE_RELEASE_SHA?.trim();
  if (!expected) return;
  let files;
  try {
    files = await collectFiles(join(frontendRoot, 'dist'));
  } catch {
    assert.fail('Production bundle is required before the release SHA scan.');
  }
  const emitted = (await Promise.all(files.map((file) => readFile(file, 'utf8')))).join(String.fromCharCode(10));
  assert.equal(emitted.includes(expected), true, 'release SHA is absent from the production bundle');
});
