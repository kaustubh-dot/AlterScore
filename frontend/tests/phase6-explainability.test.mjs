import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import { join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { isV2Explanation, isV2ScoreResponse } from '../src/lib/assessmentV2.js';
import { FRONTEND_RELEASE_SHA } from '../src/lib/releaseMetadata.js';

const frontendRoot = join(dirname(fileURLToPath(import.meta.url)), '..');
const versions = {
  contract_version: '2.0',
  assessment_version: 'india-en-3.0.0',
  scoring_policy_version: 'readiness-rubric-1.1.0',
};

function id(prefix, suffix) {
  return `${prefix}_${String(suffix).padEnd(32, 'x')}`;
}

const OBJECTIVE_CASES = [
  { concept: 'cash_flow', values: [['opening_cash', 100, 'INR'], ['inflow', 50, 'INR'], ['expenses', 20, 'INR']], answer: 130 },
  { concept: 'simple_interest', values: [['principal', 1000, 'INR'], ['annual_rate_percent', 5, '%'], ['term_years', 2, 'years']], answer: 100 },
  { concept: 'borrowing_cost_comparison', values: [['principal', 1000, 'INR'], ['term_years', 2, 'years'], ['offer_a_rate_percent', 5, '%'], ['offer_a_fee', 10, 'INR'], ['offer_b_rate_percent', 6, '%'], ['offer_b_fee', 20, 'INR'], ['offer_a_total_repayment', 1100, 'INR'], ['offer_b_total_repayment', 1300, 'INR']], answer: 200 },
  { concept: 'discount_price', values: [['marked_price', 1000, 'INR'], ['discount_rate_percent', 10, '%'], ['discount', 100, 'INR']], answer: 900 },
  { concept: 'inflation_price', values: [['current_price', 1000, 'INR'], ['inflation_rate_percent', 5, '%']], answer: 1050 },
  { concept: 'due_date_shortfall', values: [['due_amount', 500, 'INR'], ['available_amount', 350, 'INR']], answer: 150 },
  { concept: 'repayment_total', values: [['principal', 1000, 'INR'], ['annual_rate_percent', 5, '%'], ['term_years', 2, 'years'], ['fee', 25, 'INR'], ['interest', 100, 'INR']], answer: 1125 },
  { concept: 'emergency_buffer', values: [['monthly_essential_costs', 500, 'INR'], ['buffer_months', 3, 'months']], answer: 1500 },
];

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

function makeScenario(index, score = 80) {
  const startingState = makeState(index * 100);
  let before = startingState;
  const timeline = [1, 2, 3].map((stage) => {
    const delta = Object.fromEntries(STATE_FIELDS.map((field) => [field, 0]));
    delta.cash_available = stage * 10;
    const after = { ...before, cash_available: before.cash_available + delta.cash_available };
    const entry = {
      stage_index: stage,
      presentation_id: id('item', `scenario_${index}_stage_${stage}`),
      selected_option_label: `Selected decision ${stage}`,
      state_before: before,
      state_delta: delta,
      state_after: after,
    };
    before = after;
    return entry;
  });
  return {
    scenario_presentation_id: id('scenario', `scenario_${index}`),
    starting_state: startingState,
    timeline,
    terminal_state: before,
    dimensions: {
      obligation_coverage: score,
      liquidity_retention: score,
      cost_efficiency: score,
      plan_feasibility: score,
    },
    score_basis: 'feasible_range_normalized',
    scenario_score: score,
  };
}

function makeResult({ perfect = false, weakScenario = false } = {}) {
  const objectiveItems = OBJECTIVE_CASES.map((item, index) => {
    const isCorrect = perfect || index >= 2;
    return {
      presentation_id: id('item', `objective_${index}`),
      concept: item.concept,
      issued_values: item.values.map(([name, value, unit]) => ({ name, value, unit })),
      submitted_answer: isCorrect ? item.answer : item.answer + 1,
      correct_answer: item.answer,
      is_correct: isCorrect,
      worked_calculation: `${item.answer} INR worked calculation = ${item.answer} INR`,
      concept_explanation: `Use the issued ${item.concept.replaceAll('_', ' ')} quantities before acting.`,
    };
  });
  const scenarios = [makeScenario(0, weakScenario ? 50 : 80), makeScenario(1, 80)];
  const objectiveScore = perfect ? 100 : 75;
  const objectiveContribution = perfect ? '55/1' : '165/4';
  const weightedTotal = perfect ? '3433/40' : '2883/40';
  const index = perfect ? 86 : 72;
  const legacy = perfect ? 773 : 696;
  const recommendations = [];
  if (!perfect) {
    recommendations.push({
      recommendation: 'Review the first objective calculation and check each quantity before acting.',
      evidence_type: 'objective',
      evidence_ids: [objectiveItems[0].presentation_id],
    });
    if (weakScenario) {
      recommendations.push({
        recommendation: 'Review the first simulation decisions, especially the terminal liquidity dimension.',
        evidence_type: 'branching',
        evidence_ids: [scenarios[0].scenario_presentation_id],
      });
    }
  } else {
    recommendations.push({
      recommendation: 'Maintain the current approach by checking total costs, timing, required payments, and emergency buffers before acting.',
      evidence_type: 'maintenance',
      evidence_ids: [],
    });
  }

  return {
    ...versions,
    request_id: id('req', 'result'),
    release_sha: FRONTEND_RELEASE_SHA,
    result_id: id('result', 'explainability'),
    attempt_id: id('attempt', 'explainability'),
    issued_at: '2026-07-15T10:00:00Z',
    expires_at: '2026-07-16T10:00:00Z',
    integrity_status: 'verified_attempt',
    financial_decision_index: index,
    legacy_demo_score: legacy,
    objective_score: objectiveScore,
    judgment_score: 68.5,
    behavior_profile: Array.from({ length: 6 }, (_, index) => ({
      presentation_id: id('behavior', index),
      selected_value: 'Sometimes',
    })),
    limitations: ['Educational readiness rubric only.'],
    result_signature: `hmac-sha256-v1:${'A'.repeat(43)}`,
    explanation_digest: `sha256:${'a'.repeat(64)}`,
    explanation: {
      formula: {
        objective_score: objectiveScore,
        judgment_score: 68.5,
        objective_weight: '0.55',
        judgment_weight: '0.45',
        objective_contribution_exact: objectiveContribution,
        judgment_contribution_exact: '1233/40',
        weighted_total_exact: weightedTotal,
        financial_decision_index: index,
        legacy_demo_score: legacy,
      },
      objective_items: objectiveItems,
      static_sjt_items: Array.from({ length: 4 }, (_, index) => ({
        presentation_id: id('item', `static_${index}`),
        selected_option_label: `Selected action ${index}`,
        principle: 'protect required payments',
        protects: 'This protects timing and obligations.',
        risks: 'The action should still be checked for cost trade-offs.',
        stronger_principle: 'Stronger principle: protect required payments',
      })),
      branching_scenarios: scenarios,
      recommendations,
    },
  };
}

test('accepts all frozen explainability sections with every canonical objective concept', () => {
  const result = makeResult();
  assert.equal(isV2ScoreResponse(result), true);
  assert.equal(isV2Explanation(result.explanation, result), true);
  assert.equal(result.explanation.objective_items.length, 8);
  assert.equal(result.explanation.static_sjt_items.length, 4);
  assert.equal(result.explanation.branching_scenarios.length, 2);

  const expectedAnswers = [130, 100, 200, 900, 1050, 150, 1125, 1500];
  result.explanation.objective_items.forEach((item, index) => {
    assert.equal(item.correct_answer, expectedAnswers[index]);
    assert.equal(item.is_correct, item.submitted_answer === item.correct_answer);
    assert.match(item.worked_calculation, new RegExp(`= ${expectedAnswers[index]} INR$`));
  });
});

test('accepts a calibrated path score that differs from the raw dimension composite', () => {
  const result = makeResult();
  const scenario = result.explanation.branching_scenarios[0];
  scenario.dimensions = {
    obligation_coverage: 36,
    liquidity_retention: 42,
    cost_efficiency: 55,
    plan_feasibility: 48,
  };
  assert.equal(scenario.score_basis, 'feasible_range_normalized');
  assert.equal(isV2ScoreResponse(result), true);
});

test('rejects unreconciled formula fractions, hidden SJT fields, and broken branching continuity', () => {
  const unreduced = structuredClone(makeResult());
  unreduced.explanation.formula.objective_contribution_exact = '330/8';
  assert.equal(isV2ScoreResponse(unreduced), false);

  const forgedJudgmentContribution = structuredClone(makeResult());
  forgedJudgmentContribution.explanation.formula.judgment_contribution_exact = '617/20';
  forgedJudgmentContribution.explanation.formula.weighted_total_exact = '721/10';
  assert.equal(isV2ScoreResponse(forgedJudgmentContribution), false);

  const hiddenRubric = structuredClone(makeResult());
  hiddenRubric.explanation.static_sjt_items[0].rubric_points = 3;
  assert.equal(isV2ScoreResponse(hiddenRubric), false);

  const brokenTimeline = structuredClone(makeResult());
  brokenTimeline.explanation.branching_scenarios[0].timeline[1].state_before.cash_available += 1;
  assert.equal(isV2ScoreResponse(brokenTimeline), false);

  const unorderedTimeline = structuredClone(makeResult());
  [unorderedTimeline.explanation.branching_scenarios[0].timeline[0], unorderedTimeline.explanation.branching_scenarios[0].timeline[1]]
    = [unorderedTimeline.explanation.branching_scenarios[0].timeline[1], unorderedTimeline.explanation.branching_scenarios[0].timeline[0]];
  assert.equal(isV2ScoreResponse(unorderedTimeline), false);

  const invalidScoreBasis = structuredClone(makeResult());
  invalidScoreBasis.explanation.branching_scenarios[0].score_basis = 'raw_dimension_composite';
  assert.equal(isV2ScoreResponse(invalidScoreBasis), false);

  const outOfRangeScenarioScore = structuredClone(makeResult());
  outOfRangeScenarioScore.explanation.branching_scenarios[0].scenario_score = 101;
  assert.equal(isV2ScoreResponse(outOfRangeScenarioScore), false);
});

test('uses exact half-up rounding at an index boundary', () => {
  const boundary = makeResult({ perfect: true });
  boundary.explanation.formula.judgment_contribution_exact = '9/2';
  boundary.explanation.formula.weighted_total_exact = '119/2';
  boundary.explanation.formula.judgment_score = 10;
  boundary.judgment_score = 10;
  boundary.financial_decision_index = 60;
  boundary.legacy_demo_score = 630;
  boundary.explanation.formula.financial_decision_index = 60;
  boundary.explanation.formula.legacy_demo_score = 630;
  assert.equal(isV2ScoreResponse(boundary), true);
});

test('accepts the server exact judgment fraction when its decimal-2 display reconciles', () => {
  const serverRounded = makeResult({ perfect: true });
  serverRounded.judgment_score = 33.47;
  serverRounded.explanation.formula.judgment_score = 33.47;
  serverRounded.explanation.formula.judgment_contribution_exact = '5929559/393680';
  serverRounded.explanation.formula.weighted_total_exact = '27581959/393680';
  serverRounded.financial_decision_index = 70;
  serverRounded.legacy_demo_score = 685;
  serverRounded.explanation.formula.financial_decision_index = 70;
  serverRounded.explanation.formula.legacy_demo_score = 685;
  assert.equal(isV2ScoreResponse(serverRounded), true);
});

test('recommendations cite actual weaknesses and perfect profiles receive maintenance guidance', () => {
  assert.equal(isV2ScoreResponse(makeResult({ perfect: true })), true);

  const forged = structuredClone(makeResult());
  forged.explanation.recommendations[0].evidence_ids = [forged.explanation.objective_items[2].presentation_id];
  assert.equal(isV2ScoreResponse(forged), false);

  const forgedMaintenance = structuredClone(makeResult());
  forgedMaintenance.explanation.recommendations = [{
    recommendation: 'Maintain everything.',
    evidence_type: 'maintenance',
    evidence_ids: [],
  }];
  assert.equal(isV2ScoreResponse(forgedMaintenance), false);

  const forgedBranching = structuredClone(makeResult({ weakScenario: true }));
  forgedBranching.explanation.recommendations[1].evidence_ids = [id('scenario', 'not-issued')];
  assert.equal(isV2ScoreResponse(forgedBranching), false);

  const healthyBranching = structuredClone(makeResult());
  healthyBranching.explanation.recommendations = [{
    recommendation: 'Review the simulation.',
    evidence_type: 'branching',
    evidence_ids: [healthyBranching.explanation.branching_scenarios[0].scenario_presentation_id],
  }];
  assert.equal(isV2ScoreResponse(healthyBranching), false);

  assert.equal(isV2ScoreResponse(makeResult({ perfect: true, weakScenario: true })), false);

  const missingRecommendations = structuredClone(makeResult());
  missingRecommendations.explanation.recommendations = [];
  assert.equal(isV2ScoreResponse(missingRecommendations), false);
});

test('rejects duplicate concepts and an objective score that disagrees with shown correctness', () => {
  const duplicateConcept = structuredClone(makeResult());
  duplicateConcept.explanation.objective_items[1] = {
    ...duplicateConcept.explanation.objective_items[0],
    presentation_id: id('item', 'duplicate_concept'),
  };
  assert.equal(isV2ScoreResponse(duplicateConcept), false);

  const wrongObjectiveScore = structuredClone(makeResult());
  wrongObjectiveScore.explanation.objective_items.forEach((item) => {
    item.submitted_answer = item.correct_answer;
    item.is_correct = true;
  });
  assert.equal(isV2ScoreResponse(wrongObjectiveScore), false);
});

test('result presentation exposes all explanation sections without hidden scoring authorities', async () => {
  const results = await readFile(join(frontendRoot, 'src/pages/Results.jsx'), 'utf8');
  const assessment = await readFile(join(frontendRoot, 'src/pages/Assessment.jsx'), 'utf8');
  const css = await readFile(join(frontendRoot, 'src/pages/Results.css'), 'utf8');

  for (const required of [
    'formula.weighted_total_exact', 'objective_items', 'issued_values', 'worked_calculation',
    'static_sjt_items', 'selected_option_label', 'branching_scenarios', 'state_delta',
    'terminal_state', 'dimensions', 'recommendations', 'evidence-links',
    'behaviorProfile', 'Your reflection profile', 'removed from browser history',
  ]) assert.match(results, new RegExp(required.replaceAll('.', '\\.'), 'i'));
  assert.match(assessment, /toV2DetailedResult/);
  assert.match(assessment, /state: \{ result: detailedResult, behaviorProfile \}/);
  assert.match(assessment, /Choose Not applicable if you prefer not to self-report/);
  assert.match(css, /prefers-reduced-motion/);
  assert.match(css, /max-width: 640px/);

  for (const forbidden of ['option_id', 'rubric_points', 'responses', 'attempt_token', 'SHAP', 'repayment_probability']) {
    assert.equal(results.includes(forbidden), false, `forbidden result authority: ${forbidden}`);
  }
});
