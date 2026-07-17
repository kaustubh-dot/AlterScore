import { FRONTEND_RELEASE_SHA } from './releaseMetadata.js';
import {
  getSessionStorage as getSafeSessionStorage,
  removeStorageItem,
  writeStorageItem,
} from './safeStorage.js';

export const V2_CONTRACT = Object.freeze({
  contract_version: '2.0',
  assessment_version: 'india-en-3.0.0',
  scoring_policy_version: 'readiness-rubric-1.1.0',
});

export const V2_RESULT_STORAGE_KEY = 'alterscore_v2_signed_result';
export const V2_RESULT_TTL_MS = 24 * 60 * 60 * 1000;
export const PUBLIC_ASSESSMENT_ITEM_COUNT = 24;

const OPAQUE_ID_PATTERN = /^(?<prefix>req|attempt|result|item|behavior_option|behavior|scenario|option)_[A-Za-z0-9_-]{32,}$/;
const ATTEMPT_TOKEN_PATTERN = /^at1\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]{43}$/;
const RESULT_SIGNATURE_PATTERN = /^hmac-sha256-v1:[A-Za-z0-9_-]{43}$/;
const EXPLANATION_DIGEST_PATTERN = /^sha256:[0-9a-f]{64}$/;
const UTC_SECOND_TIMESTAMP_PATTERN = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/;
const BEHAVIOR_LABELS = new Set(['Never', 'Rarely', 'Sometimes', 'Often', 'Always', 'Not applicable']);
const STATE_FIELDS = Object.freeze([
  'cash_available',
  'required_payments_due',
  'required_payments_met',
  'confirmed_inflows',
  'essential_expenses',
  'emergency_buffer',
  'new_borrowing',
  'borrowing_cost',
  'avoidable_cost',
  'late_payments',
  'unfunded_commitments',
]);
const DIMENSION_FIELDS = Object.freeze([
  'obligation_coverage',
  'liquidity_retention',
  'cost_efficiency',
  'plan_feasibility',
]);
const OBJECTIVE_VALUE_NAMES = Object.freeze({
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
});
const SCORE_RESPONSE_KEYS = new Set([
  'contract_version', 'assessment_version', 'scoring_policy_version', 'request_id', 'release_sha',
  'result_id', 'attempt_id', 'issued_at', 'expires_at', 'integrity_status',
  'financial_decision_index', 'legacy_demo_score', 'objective_score', 'judgment_score',
  'behavior_profile', 'limitations', 'result_signature', 'explanation_digest', 'explanation',
]);
const DETAILED_RESULT_KEYS = new Set([
  'contract_version', 'assessment_version', 'scoring_policy_version', 'request_id', 'release_sha',
  'result_id', 'attempt_id', 'issued_at', 'expires_at', 'integrity_status',
  'financial_decision_index', 'legacy_demo_score', 'objective_score', 'judgment_score',
  'limitations', 'result_signature', 'explanation_digest', 'explanation',
]);
const SIGNED_SUMMARY_KEYS = new Set([
  'contract_version', 'assessment_version', 'scoring_policy_version', 'request_id', 'release_sha',
  'result_id', 'attempt_id', 'issued_at', 'expires_at', 'integrity_status',
  'financial_decision_index', 'legacy_demo_score', 'objective_score', 'judgment_score',
  'limitations', 'result_signature', 'explanation_digest',
]);

function isRecord(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function hasExactVersions(value) {
  return isRecord(value)
    && value.contract_version === V2_CONTRACT.contract_version
    && value.assessment_version === V2_CONTRACT.assessment_version
    && value.scoring_policy_version === V2_CONTRACT.scoring_policy_version;
}

function hasRequiredString(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function hasExactKeys(value, keys) {
  if (!isRecord(value)) return false;
  const valueKeys = Object.keys(value);
  return valueKeys.length === keys.size && valueKeys.every((key) => keys.has(key));
}

function hasOpaqueId(value, expectedPrefix) {
  if (!hasRequiredString(value)) return false;
  const matched = value.match(OPAQUE_ID_PATTERN);
  return matched?.groups?.prefix === expectedPrefix;
}

function parseCanonicalTimestamp(value) {
  if (typeof value !== 'string' || !UTC_SECOND_TIMESTAMP_PATTERN.test(value)) return null;
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) return null;
  return new Date(timestamp).toISOString().replace('.000Z', 'Z') === value ? timestamp : null;
}

function hasTimestampLifecycle(value, requiredDurationMs) {
  const issuedAt = parseCanonicalTimestamp(value.issued_at);
  const expiresAt = parseCanonicalTimestamp(value.expires_at);
  if (issuedAt === null || expiresAt === null || expiresAt <= issuedAt) return false;
  return requiredDurationMs === undefined || expiresAt - issuedAt === requiredDurationMs;
}

function isScoreHundredths(value) {
  return Number.isInteger(value) && value >= 0 && value <= 10_000;
}

function scoreToHundredths(value) {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > 100) return null;
  const hundredths = Math.round(value * 100);
  return Math.abs(value * 100 - hundredths) < 1e-8 ? hundredths : null;
}

function isSafeInteger(value) {
  return typeof value === 'number' && Number.isSafeInteger(value);
}

function isNonNegativeSafeInteger(value) {
  return isSafeInteger(value) && value >= 0;
}

function gcd(left, right) {
  let a = left < 0n ? -left : left;
  let b = right < 0n ? -right : right;
  while (b !== 0n) {
    const remainder = a % b;
    a = b;
    b = remainder;
  }
  return a;
}

function reduceFraction(numerator, denominator) {
  if (denominator <= 0n) return null;
  const divisor = gcd(numerator, denominator);
  return {
    numerator: numerator / divisor,
    denominator: denominator / divisor,
  };
}

function parseFraction(value) {
  if (typeof value !== 'string' || value.length > 200) return null;
  const match = value.match(/^(\d+)\/(\d+)$/);
  if (!match || match[2].startsWith('0')) return null;
  try {
    const numerator = BigInt(match[1]);
    const denominator = BigInt(match[2]);
    const reduced = reduceFraction(numerator, denominator);
    return reduced && reduced.numerator === numerator && reduced.denominator === denominator
      ? reduced
      : null;
  } catch {
    return null;
  }
}

function addFractions(left, right) {
  return reduceFraction(
    left.numerator * right.denominator + right.numerator * left.denominator,
    left.denominator * right.denominator,
  );
}

function fractionFromDecimalHundredths(hundredths, numerator, denominator) {
  return reduceFraction(
    BigInt(hundredths) * BigInt(numerator),
    100n * BigInt(denominator),
  );
}

function halfUpRound(fraction) {
  const quotient = fraction.numerator / fraction.denominator;
  const remainder = fraction.numerator % fraction.denominator;
  return Number(quotient + (remainder * 2n >= fraction.denominator ? 1n : 0n));
}

function hasOptions(item, expectedCount) {
  return Array.isArray(item.options)
    && item.options.length === expectedCount
    && item.options.every((option) => (
      hasExactKeys(option, new Set(['option_id', 'label']))
      && hasOpaqueId(option.option_id, item.item_type === 'behavior_profile' ? 'behavior_option' : 'option')
      && hasRequiredString(option.label)
    ))
    && new Set(item.options.map((option) => option.option_id)).size === item.options.length;
}

function isScoredItem(item) {
  if (!isRecord(item) || !hasOpaqueId(item.presentation_id, 'item') || item.required !== true) {
    return false;
  }

  if (item.item_type === 'objective') {
    return hasExactKeys(item, new Set(['presentation_id', 'item_type', 'prompt', 'response_kind', 'required']))
      && item.response_kind === 'integer'
      && hasRequiredString(item.prompt);
  }

  if (item.item_type === 'static_sjt') {
    return hasExactKeys(item, new Set(['presentation_id', 'item_type', 'prompt', 'response_kind', 'required', 'options']))
      && item.response_kind === 'single_choice'
      && hasRequiredString(item.prompt)
      && hasOptions(item, 4);
  }

  if (item.item_type === 'branching') {
    return hasExactKeys(item, new Set(['presentation_id', 'item_type', 'scenario_presentation_id', 'stage_index', 'prompt', 'response_kind', 'required', 'options']))
      && item.response_kind === 'single_choice'
      && hasOpaqueId(item.scenario_presentation_id, 'scenario')
      && Number.isInteger(item.stage_index)
      && item.stage_index >= 1
      && item.stage_index <= 3
      && hasRequiredString(item.prompt)
      && hasOptions(item, 3);
  }

  return false;
}

function isBehaviorItem(item) {
  return hasExactKeys(item, new Set(['presentation_id', 'item_type', 'prompt', 'response_kind', 'required', 'options']))
    && hasOpaqueId(item.presentation_id, 'behavior')
    && item.item_type === 'behavior_profile'
    && item.response_kind === 'single_choice'
    && item.required === true
    && hasRequiredString(item.prompt)
    && hasOptions(item, 6)
    && item.options.map((option) => option.label).every((label) => BEHAVIOR_LABELS.has(label))
    && new Set(item.options.map((option) => option.label)).size === BEHAVIOR_LABELS.size;
}

export function validateFormResponse(form) {
  if (!isRecord(form)) return 'The assessment form was empty.';
  if (!hasExactKeys(form, new Set([
    'contract_version', 'assessment_version', 'scoring_policy_version', 'request_id', 'release_sha',
    'attempt_id', 'attempt_token', 'issued_at', 'expires_at', 'integrity_status', 'items',
    'behavior_profile_items', 'narrative',
  ]))) {
    return 'The assessment form contains unsupported fields.';
  }
  if (!hasExactVersions(form)) return 'This assessment version is not supported.';
  if (!hasOpaqueId(form.request_id, 'req') || !hasRequiredString(form.release_sha)
    || !hasOpaqueId(form.attempt_id, 'attempt')
    || typeof form.attempt_token !== 'string'
    || form.attempt_token.length < 80
    || form.attempt_token.length > 500
    || !ATTEMPT_TOKEN_PATTERN.test(form.attempt_token)
    || form.integrity_status !== 'issued'
    || !hasTimestampLifecycle(form)) {
    return 'The assessment form did not include a usable attempt.';
  }
  if (!Array.isArray(form.items) || form.items.length !== 18) {
    return 'The assessment form did not include the expected scored items.';
  }
  if (!form.items.every(isScoredItem)) {
    return 'The assessment form contains an unsupported scored item.';
  }

  const scoredIds = form.items.map((item) => item.presentation_id);
  if (new Set(scoredIds).size !== scoredIds.length) {
    return 'The assessment form contains duplicate item identifiers.';
  }

  const scoredCounts = form.items.reduce((counts, item) => {
    counts[item.item_type] = (counts[item.item_type] || 0) + 1;
    return counts;
  }, {});
  if (scoredCounts.objective !== 8 || scoredCounts.static_sjt !== 4 || scoredCounts.branching !== 6) {
    return 'The assessment form does not match the frozen item architecture.';
  }
  const branchingScenarios = form.items
    .filter((item) => item.item_type === 'branching')
    .reduce((scenarios, item) => {
      const stages = scenarios.get(item.scenario_presentation_id) || [];
      stages.push(item.stage_index);
      scenarios.set(item.scenario_presentation_id, stages);
      return scenarios;
    }, new Map());
  if (branchingScenarios.size !== 2
    || [...branchingScenarios.values()].some((stages) => (
      stages.length !== 3 || new Set(stages).size !== 3 || ![1, 2, 3].every((stage) => stages.includes(stage))
    ))) {
    return 'The assessment form does not contain two complete decision simulations.';
  }

  if (!Array.isArray(form.behavior_profile_items) || form.behavior_profile_items.length !== 6) {
    return 'The assessment form did not include the expected behavior items.';
  }
  if (!form.behavior_profile_items.every(isBehaviorItem)) {
    return 'The assessment form contains an unsupported behavior item.';
  }

  const behaviorIds = form.behavior_profile_items.map((item) => item.presentation_id);
  if (new Set(behaviorIds).size !== behaviorIds.length
    || behaviorIds.some((id) => scoredIds.includes(id))) {
    return 'The assessment form contains duplicate item identifiers.';
  }

  if (!hasExactKeys(form.narrative, new Set(['enabled', 'prompt', 'max_length']))
    || typeof form.narrative.enabled !== 'boolean'
    || !hasRequiredString(form.narrative.prompt)
    || form.narrative.max_length !== 1000) {
    return 'The assessment form contains unsupported narrative settings.';
  }

  return null;
}

export function getAssessmentSteps(form) {
  if (!form) return [];

  const scoredSteps = form.items.map((item) => ({
    id: item.presentation_id,
    kind: 'scored',
    item,
  }));
  const behaviorSteps = form.behavior_profile_items.map((item) => ({
    id: item.presentation_id,
    kind: 'behavior',
    item,
  }));
  const narrativeStep = form.narrative.enabled
    ? [{ id: 'narrative', kind: 'narrative', item: form.narrative }]
    : [];

  return [...scoredSteps, ...behaviorSteps, ...narrativeStep];
}

export function parseIntegerAnswer(value) {
  const normalized = String(value ?? '').trim();
  if (!/^-?\d+$/.test(normalized)) return null;
  const parsed = Number(normalized);
  return Number.isSafeInteger(parsed) ? parsed : null;
}

export function validateStepResponse(step, value) {
  if (!step) return 'The current assessment item is unavailable.';

  if (step.kind === 'narrative') {
    if (value === undefined || value === null || value === '') return null;
    if (typeof value !== 'string') return 'Enter a written response or leave it blank.';
    if (value.length > step.item.max_length) {
      return `Keep the written response under ${step.item.max_length} characters.`;
    }
    return null;
  }

  if (step.item.item_type === 'objective') {
    return parseIntegerAnswer(value) === null ? 'Enter a whole number.' : null;
  }

  if (typeof value !== 'string' || !step.item.options.some((option) => option.option_id === value)) {
    return 'Select one of the issued options.';
  }

  return null;
}

export function validateAllResponses(form, answers) {
  const steps = getAssessmentSteps(form);
  for (let index = 0; index < steps.length; index += 1) {
    const error = validateStepResponse(steps[index], answers[steps[index].id]);
    if (error) return { index, message: error };
  }
  return null;
}

export function buildScoreSubmission(form, answers) {
  const validation = validateAllResponses(form, answers);
  if (validation) {
    const error = new Error(validation.message);
    error.code = 'invalid_client_response';
    throw error;
  }

  const responses = {};
  for (const item of form.items) {
    responses[item.presentation_id] = item.item_type === 'objective'
      ? parseIntegerAnswer(answers[item.presentation_id])
      : answers[item.presentation_id];
  }

  const behaviorProfile = {};
  for (const item of form.behavior_profile_items) {
    behaviorProfile[item.presentation_id] = answers[item.presentation_id];
  }

  return {
    ...V2_CONTRACT,
    responses,
    behavior_profile: behaviorProfile,
    narrative: form.narrative.enabled ? (answers.narrative || null) : null,
  };
}

function hasSafeState(state, delta = false) {
  const keys = new Set(STATE_FIELDS);
  return hasExactKeys(state, keys)
    && STATE_FIELDS.every((field) => delta
      ? isSafeInteger(state[field])
      : isNonNegativeSafeInteger(state[field]))
    && (delta || state.required_payments_met <= state.required_payments_due);
}

function statesEqual(left, right) {
  return Boolean(left && right) && STATE_FIELDS.every((field) => left[field] === right[field]);
}

function stateAfterDelta(state, delta) {
  const next = {};
  for (const field of STATE_FIELDS) {
    const value = state[field] + delta[field];
    if (!Number.isSafeInteger(value)) return null;
    next[field] = value;
  }
  return next;
}

function isExplanationFormula(formula, result) {
  if (!hasExactKeys(formula, new Set([
    'objective_score', 'judgment_score', 'objective_weight', 'judgment_weight',
    'objective_contribution_exact', 'judgment_contribution_exact', 'weighted_total_exact',
    'financial_decision_index', 'legacy_demo_score',
  ]))) return false;
  if (formula.objective_weight !== '0.55' || formula.judgment_weight !== '0.45') return false;

  const objectiveHundredths = scoreToHundredths(formula.objective_score);
  const judgmentHundredths = scoreToHundredths(formula.judgment_score);
  if (objectiveHundredths === null || judgmentHundredths === null
    || objectiveHundredths !== scoreToHundredths(result.objective_score)
    || judgmentHundredths !== scoreToHundredths(result.judgment_score)) return false;

  const objectiveContribution = parseFraction(formula.objective_contribution_exact);
  const judgmentContribution = parseFraction(formula.judgment_contribution_exact);
  const weightedTotal = parseFraction(formula.weighted_total_exact);
  if (!objectiveContribution || !judgmentContribution || !weightedTotal) return false;

  const expectedObjectiveContribution = fractionFromDecimalHundredths(objectiveHundredths, 55, 100);
  if (objectiveContribution.numerator !== expectedObjectiveContribution.numerator
    || objectiveContribution.denominator !== expectedObjectiveContribution.denominator) return false;

  // The scorer keeps this contribution as an exact fraction from the
  // unrounded judgment score, while the public judgment score is decimal-2.
  // Reconstruct that public display with the scorer's half-up policy instead
  // of treating the displayed decimal as the hidden source precision.
  const judgmentDisplayHundredths = halfUpRound(reduceFraction(
    judgmentContribution.numerator * 10_000n,
    judgmentContribution.denominator * 45n,
  ));
  if (judgmentDisplayHundredths !== judgmentHundredths) return false;

  const expectedWeightedTotal = addFractions(objectiveContribution, judgmentContribution);
  if (weightedTotal.numerator !== expectedWeightedTotal.numerator
    || weightedTotal.denominator !== expectedWeightedTotal.denominator) return false;

  if (!isSafeInteger(formula.financial_decision_index)
    || formula.financial_decision_index < 0
    || formula.financial_decision_index > 100
    || formula.financial_decision_index !== result.financial_decision_index
    || halfUpRound(weightedTotal) !== formula.financial_decision_index) return false;

  const expectedLegacyScore = 300 + Math.floor((11 * formula.financial_decision_index + 1) / 2);
  return isSafeInteger(formula.legacy_demo_score)
    && formula.legacy_demo_score >= 300
    && formula.legacy_demo_score <= 850
    && formula.legacy_demo_score === result.legacy_demo_score
    && formula.legacy_demo_score === expectedLegacyScore;
}

function isObjectiveExplanation(item) {
  if (!hasExactKeys(item, new Set([
    'presentation_id', 'concept', 'issued_values', 'submitted_answer', 'correct_answer',
    'is_correct', 'worked_calculation', 'concept_explanation',
  ])) || !hasOpaqueId(item.presentation_id, 'item') || !hasRequiredString(item.concept)) return false;
  const expectedNames = OBJECTIVE_VALUE_NAMES[item.concept];
  if (!expectedNames || !Array.isArray(item.issued_values) || item.issued_values.length !== expectedNames.length) return false;
  if (!item.issued_values.every((issued) => (
    hasExactKeys(issued, new Set(['name', 'value', 'unit']))
      && hasRequiredString(issued.name)
      && isSafeInteger(issued.value)
      && hasRequiredString(issued.unit)
  ))) return false;
  const names = item.issued_values.map((issued) => issued.name);
  return new Set(names).size === names.length
    && expectedNames.every((name) => names.includes(name))
    && isSafeInteger(item.submitted_answer)
    && isSafeInteger(item.correct_answer)
    && typeof item.is_correct === 'boolean'
    && item.is_correct === (item.submitted_answer === item.correct_answer)
    && hasRequiredString(item.worked_calculation)
    && hasRequiredString(item.concept_explanation);
}

function isStaticSjtExplanation(item) {
  return hasExactKeys(item, new Set([
    'presentation_id', 'selected_option_label', 'principle', 'protects', 'risks', 'stronger_principle',
  ]))
    && hasOpaqueId(item.presentation_id, 'item')
    && ['selected_option_label', 'principle', 'protects', 'risks', 'stronger_principle']
      .every((field) => hasRequiredString(item[field]));
}

function isDimensionMap(dimensions) {
  return hasExactKeys(dimensions, new Set(DIMENSION_FIELDS))
    && DIMENSION_FIELDS.every((field) => scoreToHundredths(dimensions[field]) !== null);
}

function isBranchingExplanation(item) {
  if (!hasExactKeys(item, new Set([
    'scenario_presentation_id', 'starting_state', 'timeline', 'terminal_state', 'dimensions', 'score_basis', 'scenario_score',
  ])) || !hasOpaqueId(item.scenario_presentation_id, 'scenario')
    || !hasSafeState(item.starting_state)
    || !Array.isArray(item.timeline) || item.timeline.length !== 3
    || !hasSafeState(item.terminal_state)
    || !isDimensionMap(item.dimensions)
    || item.score_basis !== 'feasible_range_normalized'
    || scoreToHundredths(item.scenario_score) === null) return false;

  if (!item.timeline.every((entry, index) => entry.stage_index === index + 1)) return false;
  const timeline = item.timeline;
  if (!timeline.every((entry, index) => (
    hasExactKeys(entry, new Set([
      'stage_index', 'presentation_id', 'selected_option_label', 'state_before', 'state_delta', 'state_after',
    ]))
      && entry.stage_index === index + 1
      && hasOpaqueId(entry.presentation_id, 'item')
      && hasRequiredString(entry.selected_option_label)
      && hasSafeState(entry.state_before)
      && hasSafeState(entry.state_delta, true)
      && hasSafeState(entry.state_after)
      && statesEqual(stateAfterDelta(entry.state_before, entry.state_delta), entry.state_after)
  ))) return false;
  if (!statesEqual(item.starting_state, timeline[0].state_before)
    || !statesEqual(timeline[0].state_after, timeline[1].state_before)
    || !statesEqual(timeline[1].state_after, timeline[2].state_before)
    || !statesEqual(timeline[2].state_after, item.terminal_state)) return false;
  return new Set(item.timeline.map((entry) => entry.stage_index)).size === 3;
}

function isRecommendation(item, objectiveItems, branchingScenarios) {
  if (!hasExactKeys(item, new Set(['recommendation', 'evidence_type', 'evidence_ids']))
    || !hasRequiredString(item.recommendation)
    || !['objective', 'branching', 'maintenance'].includes(item.evidence_type)
    || !Array.isArray(item.evidence_ids)
    || !item.evidence_ids.every(hasRequiredString)
    || new Set(item.evidence_ids).size !== item.evidence_ids.length) return false;

  const missedObjectiveIds = new Set(objectiveItems.filter((entry) => !entry.is_correct).map((entry) => entry.presentation_id));
  const weakScenarioIds = new Set(branchingScenarios
    .filter((entry) => scoreToHundredths(entry.scenario_score) < 6000)
    .map((entry) => entry.scenario_presentation_id));
  if (item.evidence_type === 'maintenance') {
    return item.evidence_ids.length === 0 && missedObjectiveIds.size === 0 && weakScenarioIds.size === 0;
  }
  if (item.evidence_ids.length === 0) return false;
  const expectedIds = item.evidence_type === 'objective' ? missedObjectiveIds : weakScenarioIds;
  return item.evidence_ids.every((id) => expectedIds.has(id));
}

export function isV2Explanation(explanation, result) {
  if (!isRecord(explanation) || !hasExactKeys(explanation, new Set([
    'formula', 'objective_items', 'static_sjt_items', 'branching_scenarios', 'recommendations',
  ]))) return false;
  if (!isExplanationFormula(explanation.formula, result)
    || !Array.isArray(explanation.objective_items) || explanation.objective_items.length !== 8
    || !explanation.objective_items.every(isObjectiveExplanation)
    || new Set(explanation.objective_items.map((item) => item.presentation_id)).size !== 8
    || new Set(explanation.objective_items.map((item) => item.concept)).size !== 8
    || Object.keys(OBJECTIVE_VALUE_NAMES).some((concept) => !explanation.objective_items
      .some((item) => item.concept === concept))
    || !Array.isArray(explanation.static_sjt_items) || explanation.static_sjt_items.length !== 4
    || !explanation.static_sjt_items.every(isStaticSjtExplanation)
    || new Set(explanation.static_sjt_items.map((item) => item.presentation_id)).size !== 4
    || !Array.isArray(explanation.branching_scenarios) || explanation.branching_scenarios.length !== 2
    || !explanation.branching_scenarios.every(isBranchingExplanation)
    || new Set(explanation.branching_scenarios.map((item) => item.scenario_presentation_id)).size !== 2
    || !Array.isArray(explanation.recommendations)) return false;

  const allScoredIds = new Set([
    ...explanation.objective_items.map((item) => item.presentation_id),
    ...explanation.static_sjt_items.map((item) => item.presentation_id),
    ...explanation.branching_scenarios.flatMap((scenario) => scenario.timeline.map((entry) => entry.presentation_id)),
  ]);
  if (allScoredIds.size !== 8 + 4 + 6) return false;
  const objectiveHundredths = scoreToHundredths(result.objective_score);
  const correctObjectiveCount = explanation.objective_items.filter((item) => item.is_correct).length;
  if (objectiveHundredths !== correctObjectiveCount * 1250) return false;
  const hasWeakness = correctObjectiveCount < 8
    || explanation.branching_scenarios.some((scenario) => scoreToHundredths(scenario.scenario_score) < 6000);
  if (hasWeakness && explanation.recommendations.length === 0) return false;
  return explanation.recommendations.every((recommendation) => (
    isRecommendation(recommendation, explanation.objective_items, explanation.branching_scenarios)
  ));
}

function hasV2ResultCore(result) {
  return hasExactVersions(result)
    && hasOpaqueId(result.request_id, 'req')
    && result.release_sha === FRONTEND_RELEASE_SHA
    && hasOpaqueId(result.result_id, 'result')
    && hasOpaqueId(result.attempt_id, 'attempt')
    && hasTimestampLifecycle(result, V2_RESULT_TTL_MS)
    && Number.isInteger(result.financial_decision_index)
    && result.financial_decision_index >= 0
    && result.financial_decision_index <= 100
    && Number.isInteger(result.legacy_demo_score)
    && result.legacy_demo_score >= 300
    && result.legacy_demo_score <= 850
    && scoreToHundredths(result.objective_score) !== null
    && scoreToHundredths(result.judgment_score) !== null
    && hasLimitations(result.limitations)
    && typeof result.result_signature === 'string'
    && RESULT_SIGNATURE_PATTERN.test(result.result_signature)
    && typeof result.explanation_digest === 'string'
    && EXPLANATION_DIGEST_PATTERN.test(result.explanation_digest)
    && isV2Explanation(result.explanation, result)
    && result.integrity_status === 'verified_attempt';
}

export function isV2ScoreResponse(result) {
  return hasExactKeys(result, SCORE_RESPONSE_KEYS)
    && hasV2ResultCore(result)
    && Array.isArray(result.behavior_profile)
    && result.behavior_profile.length === 6
    && result.behavior_profile.every((item) => (
      hasExactKeys(item, new Set(['presentation_id', 'selected_value']))
      && hasOpaqueId(item.presentation_id, 'behavior')
      && BEHAVIOR_LABELS.has(item.selected_value)
    ))
    && new Set(result.behavior_profile.map((item) => item.presentation_id)).size === result.behavior_profile.length;
}

export function isV2DetailedResult(result) {
  return hasExactKeys(result, DETAILED_RESULT_KEYS) && hasV2ResultCore(result);
}

function hasLimitations(limitations) {
  return Array.isArray(limitations)
    && limitations.length > 0
    && limitations.every(hasRequiredString)
    && new Set(limitations).size === limitations.length;
}

export function isV2SignedResultSummary(result) {
  return hasExactKeys(result, SIGNED_SUMMARY_KEYS)
    && hasExactVersions(result)
    && hasOpaqueId(result.request_id, 'req')
    && result.release_sha === FRONTEND_RELEASE_SHA
    && hasOpaqueId(result.result_id, 'result')
    && hasOpaqueId(result.attempt_id, 'attempt')
    && hasTimestampLifecycle(result, V2_RESULT_TTL_MS)
    && result.integrity_status === 'verified_attempt'
    && Number.isInteger(result.financial_decision_index)
    && result.financial_decision_index >= 0
    && result.financial_decision_index <= 100
    && Number.isInteger(result.legacy_demo_score)
    && result.legacy_demo_score >= 300
    && result.legacy_demo_score <= 850
    && isScoreHundredths(result.objective_score)
    && isScoreHundredths(result.judgment_score)
    && hasLimitations(result.limitations)
    && typeof result.result_signature === 'string'
    && RESULT_SIGNATURE_PATTERN.test(result.result_signature)
    && typeof result.explanation_digest === 'string'
    && EXPLANATION_DIGEST_PATTERN.test(result.explanation_digest);
}

export function isCurrentV2SignedResultSummary(result, now = Date.now()) {
  const currentTime = Number.isFinite(now) ? now : Date.now();
  const expiresAt = isV2SignedResultSummary(result) ? parseCanonicalTimestamp(result.expires_at) : null;
  return expiresAt !== null && currentTime < expiresAt;
}

export function isCurrentV2DetailedResult(result, now = Date.now()) {
  const currentTime = Number.isFinite(now) ? now : Date.now();
  const expiresAt = isV2DetailedResult(result) ? parseCanonicalTimestamp(result.expires_at) : null;
  return expiresAt !== null && currentTime < expiresAt;
}

export function toV2DetailedResult(result) {
  if (!isV2ScoreResponse(result)) return null;
  return {
    contract_version: result.contract_version,
    assessment_version: result.assessment_version,
    scoring_policy_version: result.scoring_policy_version,
    request_id: result.request_id,
    release_sha: result.release_sha,
    result_id: result.result_id,
    attempt_id: result.attempt_id,
    issued_at: result.issued_at,
    expires_at: result.expires_at,
    integrity_status: result.integrity_status,
    financial_decision_index: result.financial_decision_index,
    legacy_demo_score: result.legacy_demo_score,
    objective_score: result.objective_score,
    judgment_score: result.judgment_score,
    limitations: [...result.limitations],
    result_signature: result.result_signature,
    explanation_digest: result.explanation_digest,
    explanation: result.explanation,
  };
}

export function toSignedResultSummary(result) {
  if (!isV2ScoreResponse(result)) return null;
  return {
    contract_version: result.contract_version,
    assessment_version: result.assessment_version,
    scoring_policy_version: result.scoring_policy_version,
    request_id: result.request_id,
    release_sha: result.release_sha,
    result_id: result.result_id,
    attempt_id: result.attempt_id,
    issued_at: result.issued_at,
    expires_at: result.expires_at,
    integrity_status: result.integrity_status,
    financial_decision_index: result.financial_decision_index,
    legacy_demo_score: result.legacy_demo_score,
    objective_score: scoreToHundredths(result.objective_score),
    judgment_score: scoreToHundredths(result.judgment_score),
    limitations: [...result.limitations],
    result_signature: result.result_signature,
    explanation_digest: result.explanation_digest,
  };
}

function getSessionStorage(storage) {
  if (storage) return storage;
  return getSafeSessionStorage();
}

export function saveSignedResult(result, now = Date.now(), storage) {
  const targetStorage = getSessionStorage(storage);
  if (!targetStorage) return false;
  const storedAt = Number.isFinite(now) ? now : Date.now();
  if (!isCurrentV2DetailedResult(result, storedAt) && !isCurrentV2SignedResultSummary(result, storedAt)) {
    clearSignedResult(targetStorage);
    return false;
  }

  const expiresAt = parseCanonicalTimestamp(result.expires_at);
  return writeStorageItem(targetStorage, V2_RESULT_STORAGE_KEY, JSON.stringify({
    stored_at: storedAt,
    expires_at: expiresAt,
    result,
  }));
}

export function clearSignedResult(storage) {
  const targetStorage = getSessionStorage(storage);
  removeStorageItem(targetStorage, V2_RESULT_STORAGE_KEY);
}

export function getStoredSignedResult(now = Date.now(), storage) {
  const targetStorage = getSessionStorage(storage);
  if (!targetStorage) return null;

  try {
    const stored = JSON.parse(targetStorage.getItem(V2_RESULT_STORAGE_KEY) || 'null');
    if (!hasExactKeys(stored, new Set(['stored_at', 'expires_at', 'result']))
      || (!isCurrentV2DetailedResult(stored.result, now) && !isCurrentV2SignedResultSummary(stored.result, now))) {
      clearSignedResult(targetStorage);
      return null;
    }
    const expiresAt = Number(stored.expires_at);
    const storedAt = Number(stored.stored_at);
    const serverExpiresAt = parseCanonicalTimestamp(stored.result.expires_at);
    if (!Number.isFinite(expiresAt) || !Number.isFinite(storedAt)
      || storedAt > now
      || expiresAt !== serverExpiresAt
      || now >= expiresAt) {
      clearSignedResult(targetStorage);
      return null;
    }
    return stored.result;
  } catch {
    clearSignedResult(targetStorage);
    return null;
  }
}

export function getStepLabel(step) {
  if (!step) return 'Assessment item';
  if (step.kind === 'narrative') return 'Optional reflection';
  if (step.kind === 'behavior') return 'Unscored self-reflection';
  if (step.item.item_type === 'objective') return 'Financial knowledge';
  if (step.item.item_type === 'static_sjt') return 'Decision judgement';
  return `Decision simulation · stage ${step.item.stage_index}`;
}
