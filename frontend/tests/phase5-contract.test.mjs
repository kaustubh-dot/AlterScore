import assert from 'node:assert/strict';
import { readdir, readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import {
  V2_CONTRACT,
  V2_RESULT_STORAGE_KEY,
  V2_RESULT_TTL_MS,
  buildScoreSubmission,
  getAssessmentSteps,
  getStoredSignedResult,
  isV2DetailedResult,
  isCurrentV2SignedResultSummary,
  isV2ScoreResponse,
  isV2SignedResultSummary,
  parseIntegerAnswer,
  saveSignedResult,
  toV2DetailedResult,
  toSignedResultSummary,
  validateAllResponses,
  validateFormResponse,
  validateStepResponse,
} from '../src/lib/assessmentV2.js';
import { FRONTEND_RELEASE_SHA } from '../src/lib/releaseMetadata.js';
import { normalizeApiBaseUrl } from '../src/lib/api.js';
import {
  getApiErrorCode,
  getRetryAfterSeconds,
  isAttemptLifecycleError,
} from '../src/utils/apiErrors.js';

const here = dirname(fileURLToPath(import.meta.url));
const frontendRoot = join(here, '..');

async function collectFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) files.push(...await collectFiles(path));
    else files.push(path);
  }
  return files;
}

class MemoryStorage {
  #values = new Map();

  getItem(key) {
    return this.#values.get(key) ?? null;
  }

  setItem(key, value) {
    this.#values.set(key, String(value));
  }

  removeItem(key) {
    this.#values.delete(key);
  }
}

function opaqueIdentifier(prefix, suffix) {
  return `${prefix}_${String(suffix).padEnd(32, 'x')}`;
}

function option(prefix, index, behavior = false) {
  return {
    option_id: opaqueIdentifier(behavior ? 'behavior_option' : 'option', `${prefix}_${index}`),
    label: `Issued option ${index}`,
  };
}

function makeForm() {
  const items = [
    ...Array.from({ length: 4 }, (_, index) => ({
      presentation_id: opaqueIdentifier('item', `objective_${index}`),
      item_type: 'objective',
      prompt: `Objective prompt ${index}`,
      response_kind: 'integer',
      required: true,
    })),
    ...Array.from({ length: 4 }, (_, index) => ({
      presentation_id: opaqueIdentifier('item', `sjt_${index}`),
      item_type: 'static_sjt',
      prompt: `Judgement prompt ${index}`,
      response_kind: 'single_choice',
      required: true,
      options: Array.from({ length: 4 }, (_, optionIndex) => option(`sjt_${index}`, optionIndex)),
    })),
    ...Array.from({ length: 6 }, (_, index) => ({
      presentation_id: opaqueIdentifier('item', `branch_${index}`),
      item_type: 'branching',
      scenario_presentation_id: opaqueIdentifier('scenario', Math.floor(index / 3)),
      stage_index: (index % 3) + 1,
      prompt: `Branch stage ${index}`,
      response_kind: 'single_choice',
      required: true,
      options: Array.from({ length: 3 }, (_, optionIndex) => option(`branch_${index}`, optionIndex)),
    })),
    ...Array.from({ length: 4 }, (_, index) => ({
      presentation_id: opaqueIdentifier('item', `objective_tail_${index}`),
      item_type: 'objective',
      prompt: `Objective tail prompt ${index}`,
      response_kind: 'integer',
      required: true,
    })),
  ];

  return {
    ...V2_CONTRACT,
    request_id: opaqueIdentifier('req', 'test'),
    release_sha: FRONTEND_RELEASE_SHA,
    attempt_id: opaqueIdentifier('attempt', 'test'),
    attempt_token: `at1.${'b'.repeat(40)}.${'c'.repeat(43)}`,
    issued_at: '2026-07-15T10:00:00Z',
    expires_at: '2026-07-15T10:45:00Z',
    integrity_status: 'issued',
    items,
    behavior_profile_items: Array.from({ length: 6 }, (_, index) => ({
      presentation_id: opaqueIdentifier('behavior', index),
      item_type: 'behavior_profile',
      prompt: `Behavior prompt ${index}`,
      response_kind: 'single_choice',
      required: true,
      options: ['Never', 'Rarely', 'Sometimes', 'Often', 'Always', 'Not applicable']
        .map((label, optionIndex) => ({ ...option(`behavior_${index}`, optionIndex, true), label })),
    })),
    narrative: {
      enabled: true,
      prompt: 'Optional reflection',
      max_length: 1000,
    },
  };
}

function makeAnswers(form) {
  const answers = { narrative: 'A short optional reflection.' };
  for (const item of form.items) {
    answers[item.presentation_id] = item.item_type === 'objective'
      ? '17'
      : item.options[0].option_id;
  }
  for (const item of form.behavior_profile_items) answers[item.presentation_id] = item.options[1].option_id;
  return answers;
}

const OBJECTIVE_VALUE_NAMES = {
  cash_flow: ['opening_cash', 'inflow', 'expenses'],
  simple_interest: ['principal', 'annual_rate_percent', 'term_years'],
  borrowing_cost_comparison: [
    'principal', 'term_years', 'offer_a_rate_percent', 'offer_a_fee',
    'offer_b_rate_percent', 'offer_b_fee', 'offer_a_total_repayment', 'offer_b_total_repayment',
  ],
  discount_price: ['marked_price', 'discount_rate_percent', 'discount'],
  inflation_price: ['current_price', 'inflation_rate_percent'],
  due_date_shortfall: ['due_amount', 'available_amount'],
  repayment_total: ['principal', 'annual_rate_percent', 'term_years', 'fee', 'interest'],
  emergency_buffer: ['monthly_essential_costs', 'buffer_months'],
};

const STATE_FIELDS = [
  'cash_available', 'required_payments_due', 'required_payments_met', 'confirmed_inflows',
  'essential_expenses', 'emergency_buffer', 'new_borrowing', 'borrowing_cost',
  'avoidable_cost', 'late_payments', 'unfunded_commitments',
];

function makeState(seed = 0) {
  return {
    cash_available: 1000 + seed,
    required_payments_due: 500,
    required_payments_met: 250,
    confirmed_inflows: 300,
    essential_expenses: 200,
    emergency_buffer: 100,
    new_borrowing: 0,
    borrowing_cost: 0,
    avoidable_cost: 0,
    late_payments: 0,
    unfunded_commitments: 0,
  };
}

function zeroDelta() {
  return Object.fromEntries(STATE_FIELDS.map((field) => [field, 0]));
}

function makeScenario(index, scenarioScore = 80) {
  const startingState = makeState(index * 100);
  let before = startingState;
  const timeline = [1, 2, 3].map((stage) => {
    const delta = zeroDelta();
    delta.cash_available = stage * 10;
    const after = { ...before, cash_available: before.cash_available + delta.cash_available };
    const entry = {
      stage_index: stage,
      presentation_id: opaqueIdentifier('item', `scenario_${index}_stage_${stage}`),
      selected_option_label: `Issued decision ${stage}`,
      state_before: before,
      state_delta: delta,
      state_after: after,
    };
    before = after;
    return entry;
  });
  return {
    scenario_presentation_id: opaqueIdentifier('scenario', `scenario_${index}`),
    starting_state: startingState,
    timeline,
    terminal_state: before,
    dimensions: {
      obligation_coverage: scenarioScore,
      liquidity_retention: scenarioScore,
      cost_efficiency: scenarioScore,
      plan_feasibility: scenarioScore,
    },
    score_basis: 'feasible_range_normalized',
    scenario_score: scenarioScore,
  };
}

function makeExplanation() {
  return {
    formula: {
      objective_score: 75,
      judgment_score: 68.5,
      objective_weight: '0.55',
      judgment_weight: '0.45',
      objective_contribution_exact: '165/4',
      judgment_contribution_exact: '1233/40',
      weighted_total_exact: '2883/40',
      financial_decision_index: 72,
      legacy_demo_score: 696,
    },
    objective_items: Object.entries(OBJECTIVE_VALUE_NAMES).map(([concept, names], index) => ({
      presentation_id: opaqueIdentifier('item', `objective_explanation_${index}`),
      concept,
      issued_values: names.map((name, valueIndex) => ({ name, value: valueIndex + 10, unit: 'INR' })),
      submitted_answer: index < 2 ? 31 : 30,
      correct_answer: 30,
      is_correct: index >= 2,
      worked_calculation: '10 + 20 = 30 INR',
      concept_explanation: `The ${concept} calculation checks the quantities before acting.`,
    })),
    static_sjt_items: Array.from({ length: 4 }, (_, index) => ({
      presentation_id: opaqueIdentifier('item', `static_explanation_${index}`),
      selected_option_label: `Selected action ${index}`,
      principle: 'protect required payments',
      protects: 'This protects timing and obligations.',
      risks: 'The trade-off should still be checked.',
      stronger_principle: 'Stronger principle: protect required payments',
    })),
    branching_scenarios: [makeScenario(0), makeScenario(1)],
    recommendations: [{
      recommendation: 'Review the first calculation before acting.',
      evidence_type: 'objective',
      evidence_ids: [opaqueIdentifier('item', 'objective_explanation_0')],
    }],
  };
}

function makeResult(expiresAt = '2026-07-16T10:00:00Z') {
  return {
    ...V2_CONTRACT,
    request_id: opaqueIdentifier('req', 'test'),
    release_sha: FRONTEND_RELEASE_SHA,
    result_id: opaqueIdentifier('result', 'test'),
    attempt_id: opaqueIdentifier('attempt', 'test'),
    issued_at: '2026-07-15T10:00:00Z',
    expires_at: expiresAt,
    integrity_status: 'verified_attempt',
    financial_decision_index: 72,
    legacy_demo_score: 696,
    objective_score: 75,
    judgment_score: 68.5,
    behavior_profile: Array.from({ length: 6 }, (_, index) => ({
      presentation_id: opaqueIdentifier('behavior', index),
      selected_value: 'Sometimes',
    })),
    limitations: ['Educational readiness rubric only.'],
    result_signature: `hmac-sha256-v1:${'A'.repeat(43)}`,
    explanation_digest: `sha256:${'a'.repeat(64)}`,
    explanation: makeExplanation(),
  };
}

test('accepts the frozen form architecture and preserves server order', () => {
  const form = makeForm();
  assert.equal(validateFormResponse(form), null);
  const steps = getAssessmentSteps(form);
  assert.equal(steps.length, 25);
  assert.equal(steps[0].id, form.items[0].presentation_id);
  assert.equal(steps[17].id, form.items[17].presentation_id);
  assert.equal(steps[18].id, form.behavior_profile_items[0].presentation_id);
  assert.equal(steps.at(-1).kind, 'narrative');
});

test('rejects version mismatches and malformed item architecture', () => {
  const versionMismatch = { ...makeForm(), assessment_version: 'wrong-version' };
  assert.match(validateFormResponse(versionMismatch), /version/i);

  const malformed = makeForm();
  malformed.items[0] = { ...malformed.items[0], response_kind: 'single_choice' };
  assert.match(validateFormResponse(malformed), /unsupported scored item/i);
});

test('rejects malformed opaque form shapes before rendering or submission', () => {
  const duplicateOptions = makeForm();
  duplicateOptions.items[4].options[1] = { ...duplicateOptions.items[4].options[0] };
  assert.match(validateFormResponse(duplicateOptions), /unsupported scored item/i);

  const collapsedScenario = makeForm();
  for (const item of collapsedScenario.items.filter((entry) => entry.item_type === 'branching')) {
    item.scenario_presentation_id = opaqueIdentifier('scenario', 'one');
  }
  assert.match(validateFormResponse(collapsedScenario), /two complete decision simulations/i);

  const leakedField = makeForm();
  leakedField.items[0].correctAnswer = 42;
  assert.match(validateFormResponse(leakedField), /unsupported scored item/i);
});

test('validates numeric answers without recreating hidden bounds', () => {
  assert.equal(parseIntegerAnswer('17'), 17);
  assert.equal(parseIntegerAnswer(''), null);
  assert.equal(parseIntegerAnswer('17.5'), null);
  assert.equal(parseIntegerAnswer('1e3'), null);
  assert.equal(parseIntegerAnswer('9007199254740992'), null);

  const form = makeForm();
  const objectiveStep = getAssessmentSteps(form)[0];
  assert.match(validateStepResponse(objectiveStep, ''), /whole number/i);
  assert.equal(validateStepResponse(objectiveStep, '17'), null);
});

test('builds exact opaque-ID submission maps for branching and behavior items', () => {
  const form = makeForm();
  const answers = makeAnswers(form);
  assert.equal(validateAllResponses(form, answers), null);
  const submission = buildScoreSubmission(form, answers);

  assert.deepEqual(Object.keys(submission), [
    'contract_version',
    'assessment_version',
    'scoring_policy_version',
    'responses',
    'behavior_profile',
    'narrative',
  ]);
  assert.deepEqual(Object.keys(submission.responses), form.items.map((item) => item.presentation_id));
  assert.deepEqual(Object.keys(submission.behavior_profile), form.behavior_profile_items.map((item) => item.presentation_id));
  assert.equal(submission.responses[form.items[0].presentation_id], 17);
  assert.equal(submission.responses[form.items[6].presentation_id], form.items[6].options[0].option_id);
  assert.equal(Object.prototype.hasOwnProperty.call(submission, 'attempt_token'), false);
  assert.equal(JSON.stringify(submission).includes('at1.'), false);
});

test('handles v2 lifecycle errors and retry metadata without exposing raw data', () => {
  const error = {
    response: {
      status: 409,
      data: { error: { code: 'attempt_consumed', details: { retryable: true, new_form_required: true } } },
    },
  };
  assert.equal(getApiErrorCode(error), 'attempt_consumed');
  assert.equal(isAttemptLifecycleError(error), true);
  assert.equal(getRetryAfterSeconds({
    response: { status: 429, data: { error: { code: 'rate_limited', details: { retry_after_seconds: 7 } } } },
  }), 7);
});

test('retains a bounded signed explanation projection without raw submission or behavior data', () => {
  const storage = new MemoryStorage();
  const now = Date.parse('2026-07-15T10:00:00Z');
  const result = {
    ...makeResult('2026-07-16T10:00:00Z'),
    behavior_profile: Array.from({ length: 6 }, (_, index) => ({
      presentation_id: opaqueIdentifier('behavior', index),
      selected_value: 'Always',
    })),
  };
  assert.equal(isV2ScoreResponse(result), true);
  const detailed = toV2DetailedResult(result);
  assert.equal(isV2DetailedResult(detailed), true);
  const summary = toSignedResultSummary(result);
  assert.equal(isV2SignedResultSummary(summary), true);
  assert.equal(isCurrentV2SignedResultSummary(summary, now), true);
  assert.equal(summary.objective_score, 7500);
  assert.equal(summary.judgment_score, 6850);
  assert.equal(saveSignedResult(result, now, storage), false);
  assert.equal(saveSignedResult(detailed, now, storage), true);
  assert.equal(JSON.parse(storage.getItem(V2_RESULT_STORAGE_KEY)).result.result_signature.startsWith('hmac-sha256-v1:'), true);
  assert.equal(storage.getItem(V2_RESULT_STORAGE_KEY).includes('attempt_token'), false);
  assert.equal(storage.getItem(V2_RESULT_STORAGE_KEY).includes('"behavior_profile":'), false);
  assert.equal(storage.getItem(V2_RESULT_STORAGE_KEY).includes('"explanation":'), true);
  assert.equal(storage.getItem(V2_RESULT_STORAGE_KEY).includes('"correct_answer":'), true);
  assert.equal(storage.getItem(V2_RESULT_STORAGE_KEY).includes('"narrative":'), false);
  assert.deepEqual(getStoredSignedResult(now + V2_RESULT_TTL_MS - 1, storage), detailed);
  assert.equal(getStoredSignedResult(now + V2_RESULT_TTL_MS, storage), null);
  assert.equal(storage.getItem(V2_RESULT_STORAGE_KEY), null);
});

test('cleans malformed or expired signed-summary cache entries instead of rendering them', () => {
  const storage = new MemoryStorage();
  storage.setItem(V2_RESULT_STORAGE_KEY, JSON.stringify({ result: { credit_score: 800 } }));
  assert.equal(getStoredSignedResult(Date.now(), storage), null);
  assert.equal(storage.getItem(V2_RESULT_STORAGE_KEY), null);

  const now = Date.parse('2026-07-15T10:00:00Z');
  const expired = toSignedResultSummary({
    ...makeResult('2026-07-15T10:00:00Z'),
    issued_at: '2026-07-14T10:00:00Z',
  });
  assert.equal(isCurrentV2SignedResultSummary(expired, now), false);
  assert.equal(saveSignedResult(expired, now, storage), false);
  assert.equal(storage.getItem(V2_RESULT_STORAGE_KEY), null);

  const staleRelease = toSignedResultSummary({
    ...makeResult('2026-07-16T10:00:00Z'),
    release_sha: '0'.repeat(40),
  });
  assert.equal(isV2SignedResultSummary(staleRelease), false);
  assert.equal(saveSignedResult(staleRelease, now, storage), false);
  assert.equal(storage.getItem(V2_RESULT_STORAGE_KEY), null);

  const malformed = toSignedResultSummary(makeResult());
  delete malformed.limitations;
  storage.setItem(V2_RESULT_STORAGE_KEY, JSON.stringify({
    stored_at: now,
    expires_at: Date.parse(malformed.expires_at),
    result: malformed,
  }));
  assert.equal(getStoredSignedResult(now, storage), null);
  assert.equal(storage.getItem(V2_RESULT_STORAGE_KEY), null);
});

test('rejects insecure configured API transport before a bearer token can be attached', () => {
  assert.equal(normalizeApiBaseUrl('https://scoring.example.test'), 'https://scoring.example.test/api');
  assert.equal(normalizeApiBaseUrl('https://scoring.example.test/api'), 'https://scoring.example.test/api');
  assert.equal(normalizeApiBaseUrl('http://localhost:8000'), 'http://localhost:8000/api');
  assert.equal(normalizeApiBaseUrl('http://127.0.0.1:8000/api'), 'http://127.0.0.1:8000/api');
  assert.equal(normalizeApiBaseUrl('http://scoring.example.test'), null);
  assert.equal(normalizeApiBaseUrl('not a URL'), null);
});

test('keeps the required accessibility and StrictMode lifecycle seams in the UI', async () => {
  const assessment = await readFile(join(frontendRoot, 'src/pages/Assessment.jsx'), 'utf8');
  const processing = await readFile(join(frontendRoot, 'src/pages/Processing.jsx'), 'utf8');
  const results = await readFile(join(frontendRoot, 'src/pages/Results.jsx'), 'utf8');
  const landing = await readFile(join(frontendRoot, 'src/pages/Landing.jsx'), 'utf8');
  const app = await readFile(join(frontendRoot, 'src/App.jsx'), 'utf8');
  const notFound = await readFile(join(frontendRoot, 'src/pages/NotFound.jsx'), 'utf8');

  assert.match(assessment, /role="progressbar"/);
  assert.match(assessment, /role="radiogroup"/);
  assert.match(assessment, /aria-invalid/);
  assert.match(assessment, /questionHeadingRef/);
  assert.match(assessment, /validateAllResponses/);
  assert.match(assessment, /fetchV2AssessmentForm/);
  assert.match(assessment, /Step \{currentIndex \+ 1\} of \{steps\.length\}/);
  assert.match(processing, /AbortController/);
  assert.match(processing, /record\.started/);
  assert.match(processing, /isAttemptLifecycleError/);
  assert.match(processing, /onFreshAttempt/);
  assert.match(results, /saveSignedResult/);
  assert.match(results, /clearSignedResult/);
  assert.match(landing, /required items/);
  assert.match(landing, /optional reflection/);
  assert.match(app, /<Route path="\*" element=\{<NotFound \/>\} \/>/);
  assert.match(notFound, /<main className="not-found-page" aria-labelledby="not-found-title">/);
  assert.match(notFound, /Return home/);
  assert.match(notFound, /Start assessment/);
  assert.doesNotMatch(assessment, /data\/questions/);
  assert.doesNotMatch(landing, /data\/questions/);
});

test('production bundle contains only the v2 assessment transport and no legacy authority', async (t) => {
  const dist = join(frontendRoot, 'dist');
  let files;
  try {
    files = await collectFiles(dist);
  } catch {
    if (process.env.CI === 'true') {
      assert.fail('Production bundle is required before the CI secrecy scan.');
    }
    t.skip('Run npm run build before the emitted-bundle scan.');
    return;
  }

  const emitted = (await Promise.all(files.map((file) => readFile(file, 'utf8')))).join('\n');
  for (const forbidden of [
    'correctAnswer', 'correctIndex', 'featureSignals', 'credit_score',
    'repayment_probability', 'percentile', 'shap_value', 'counterfactual_actions',
    'improvement_tips', 'text_quality', 'session_id', 'VITE_ADMIN_PASSCODE',
    'VITE_API_KEY', 'VITE_SIGNING_SECRET', 'VITE_ATTEMPT_TOKEN', 'VITE_PASSWORD',
    'rubric_points', 'generation_rule', 'objective_01', 'static_sjt_01',
    'scenario_emi_supplier', 'answer_key',
  ]) {
    assert.equal(emitted.includes(forbidden), false, `forbidden bundle token: ${forbidden}`);
  }
  assert.equal(/['"]\/(?:api\/)?score['"]/.test(emitted), false);
  assert.match(emitted, /v2\/assessment\/form/);
  assert.match(emitted, /v2\/assessment\/score/);
});
