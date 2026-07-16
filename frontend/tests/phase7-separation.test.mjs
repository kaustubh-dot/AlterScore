import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const frontendRoot = path.resolve(here, '..');
const read = (relativePath) => fs.readFileSync(path.join(frontendRoot, relativePath), 'utf8');

test('Research Lab is static, direct-link-only, and preserves the public boundary', () => {
  const app = read('src/App.jsx');
  const lab = read('src/pages/ResearchLab.jsx').toLowerCase();

  assert.match(app, /ResearchLab/);
  assert.match(app, /path="\/research"/);
  assert.doesNotMatch(app, /path="\/admin"/);
  for (const phrase of ['synthetic', 'fairness', 'auc', 'generated data', 'does not score public assessments']) {
    assert.match(lab, new RegExp(phrase));
  }
  for (const forbidden of ['api.js', 'assessmentv2', 'questions.js', 'sessionstorage']) {
    assert.doesNotMatch(lab, new RegExp(forbidden, 'i'));
  }
});

test('legacy client question data is absent from the active frontend graph', () => {
  const sourceFiles = [];
  const walk = (directory) => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const fullPath = path.join(directory, entry.name);
      if (entry.isDirectory()) walk(fullPath);
      else if (/\.(js|jsx|mjs)$/.test(entry.name)) sourceFiles.push(fullPath);
    }
  };
  walk(path.join(frontendRoot, 'src'));
  const combined = sourceFiles.map((filePath) => fs.readFileSync(filePath, 'utf8')).join('\n');
  assert.doesNotMatch(combined, /data[\\/]questions\.js/);
  assert.doesNotMatch(combined, /VITE_ADMIN_PASSCODE/);
});

test('frontend package keeps the research dependency surface out of serving', () => {
  const packageJson = JSON.parse(read('package.json'));
  const dependencies = Object.keys(packageJson.dependencies || {});
  for (const forbidden of ['recharts', 'xgboost', 'shap', 'torch', 'tensorflow']) {
    assert.ok(!dependencies.includes(forbidden), `${forbidden} must not be a frontend dependency`);
  }
});
