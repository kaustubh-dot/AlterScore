import { getSessionStorage, readStorageItem, removeStorageItem, writeStorageItem } from './safeStorage.js';

export const TRIAL_RESULT_STORAGE_KEY = 'alterscore_trial_result';
export const TRIAL_RESULT_VERSION = 4;

const INITIAL_LIQUIDITY = 21_000;
const COST_BUDGET = 6_000;
const INITIAL_STATE = Object.freeze({
  cashAvailable: 12_000,
  requiredPaymentsDue: 30_000,
  requiredPaymentsMet: 0,
  confirmedInflows: 24_000,
  essentialExpenses: 9_000,
  emergencyBuffer: 9_000,
  newBorrowing: 0,
  borrowingCost: 0,
  avoidableCost: 0,
  latePayments: 0,
  unfundedCommitments: 6_000,
});

const money = (value) => `₹${value.toLocaleString('en-IN')}`;
const update = (state, changes) => ({ ...state, ...changes });
const receive = (state, amount) => update(state, {
  cashAvailable: state.cashAvailable + amount,
  confirmedInflows: state.confirmedInflows - amount,
});
const payRequiredFromCash = (state, amount) => update(state, {
  cashAvailable: state.cashAvailable - amount,
  requiredPaymentsMet: state.requiredPaymentsMet + amount,
});
const payRequiredFromBuffer = (state, amount) => update(state, {
  emergencyBuffer: state.emergencyBuffer - amount,
  requiredPaymentsMet: state.requiredPaymentsMet + amount,
});
const borrow = (state, amount, cost) => update(state, {
  cashAvailable: state.cashAvailable + amount,
  newBorrowing: state.newBorrowing + amount,
  borrowingCost: state.borrowingCost + cost,
});
const spendLiquidity = (state, amount) => {
  const funded = Math.min(amount, state.cashAvailable + state.emergencyBuffer);
  const fromCash = Math.min(state.cashAvailable, funded);
  return update(state, {
    cashAvailable: state.cashAvailable - fromCash,
    emergencyBuffer: state.emergencyBuffer - (funded - fromCash),
  });
};
const fundEssential = (state, amount, plannedDeferral = 0) => {
  const shortfall = Math.max(0, amount - state.cashAvailable - state.emergencyBuffer);
  return update(spendLiquidity(state, amount), {
    essentialExpenses: 0,
    unfundedCommitments: state.unfundedCommitments + plannedDeferral + shortfall,
  });
};

function metrics(state) {
  const unmetRequiredPayments = state.requiredPaymentsDue - state.requiredPaymentsMet;
  const liquidResources = state.cashAvailable + state.emergencyBuffer;
  return {
    unmetRequiredPayments,
    unencumberedLiquidity: Math.max(0, liquidResources - unmetRequiredPayments),
    remainingPlanNeed: unmetRequiredPayments + state.essentialExpenses + state.unfundedCommitments,
  };
}

const TRIAL_STAGES = Object.freeze([
  {
    id: 'collection-action',
    label: 'Collection decision',
    principle: 'Convert forecasts into verified cash before committing funds.',
    build: (state) => ({
      prompt: `You have ${money(state.cashAvailable)} operating cash, a ${money(state.emergencyBuffer)} reserve, and ${money(state.confirmedInflows)} still receivable. A ${money(metrics(state).unmetRequiredPayments)} payment is due. Which collection action do you take first?`,
      options: [
        { id: 'routine', label: 'Use routine follow-up and collect ₹6,000 now.', analysis: 'Preserves margin, but leaves more of the due payment dependent on an uncollected receivable.', protects: 'Cost efficiency', risks: 'A larger near-term cash shortfall', apply: (current) => receive(current, 6_000) },
        { id: 'reconcile', label: 'Reconcile disputed invoices and collect ₹12,000 now.', analysis: 'Improves verified liquidity without paying a settlement concession.', protects: 'Liquidity and cost control', risks: 'Only half the receivable is realised now', apply: (current) => receive(current, 12_000) },
        { id: 'accelerate', label: 'Concede ₹1,000 and collect ₹18,000 now.', analysis: 'Secures the most immediate cash, while permanently reducing cost efficiency by the concession.', protects: 'Near-term liquidity', risks: 'A certain ₹1,000 cost', apply: (current) => update(receive(current, 18_000), { avoidableCost: current.avoidableCost + 1_000 }) },
      ],
    }),
  },
  {
    id: 'shortfall-response',
    label: 'Funding decision',
    principle: 'Meet obligations without creating a larger liquidity or borrowing problem.',
    build: (state) => ({
      prompt: `Your collection choice leaves ${money(state.cashAvailable)} in cash, ${money(state.confirmedInflows)} receivable, and ${money(metrics(state).unmetRequiredPayments)} still due. Which funding response best fits this state?`,
      options: [
        { id: 'cash-payment', label: 'Apply ₹10,000 of operating cash to the payment.', analysis: 'Reduces the obligation directly, but also removes cash needed for essential operations.', protects: 'Immediate obligation coverage', risks: 'Lower operating liquidity', apply: (current) => payRequiredFromCash(current, 10_000) },
        { id: 'buffer-payment', label: 'Apply ₹8,000 from the emergency reserve.', analysis: 'Keeps operating cash available, but weakens protection against the next shock.', protects: 'Operating continuity', risks: 'Lower emergency resilience', apply: (current) => payRequiredFromBuffer(current, 8_000) },
        { id: 'bridge', label: 'Draw a ₹10,000 bridge facility costing ₹3,000.', analysis: 'Adds liquidity but does not itself settle the required payment, and consumes half of the scenario’s cost budget.', protects: 'Immediate cash capacity', risks: 'New debt and ₹3,000 cost', apply: (current) => borrow(current, 10_000, 3_000) },
      ],
    }),
  },
  {
    id: 'payment-arrangement',
    label: 'Payment decision',
    principle: 'Balance documented payment progress with enough liquidity to execute the remaining plan.',
    build: (state) => ({
      prompt: `At the due date, the path you created has ${money(state.cashAvailable)} cash, a ${money(state.emergencyBuffer)} reserve, and ${money(metrics(state).unmetRequiredPayments)} unpaid. What arrangement do you put to the counterparty?`,
      options: [
        { id: 'accelerated-payment', label: `Apply ${money(Math.min(Math.round(state.cashAvailable * 0.75), metrics(state).unmetRequiredPayments))} now and retain one-quarter of operating cash.`, analysis: 'Makes the strongest immediate payment while retaining a defined operating balance for the next essential shock.', protects: 'Obligation coverage', risks: 'A substantial liquidity draw', apply: (current) => payRequiredFromCash(current, Math.min(Math.round(current.cashAvailable * 0.75), metrics(current).unmetRequiredPayments)) },
        { id: 'balanced-payment', label: `Apply ${money(Math.min(Math.round(state.cashAvailable * 0.45), metrics(state).unmetRequiredPayments))} now and document the remaining schedule.`, analysis: 'Balances measurable payment progress with liquidity for the known essential-cost exposure.', protects: 'Payment progress and plan flexibility', risks: 'A larger unpaid balance than the accelerated option', apply: (current) => payRequiredFromCash(current, Math.min(Math.round(current.cashAvailable * 0.45), metrics(current).unmetRequiredPayments)) },
        { id: 'extension-payment', label: `Apply ${money(Math.min(Math.round(state.cashAvailable * 0.2), metrics(state).unmetRequiredPayments))} and take a seven-day extension costing ₹500.`, analysis: 'Retains most cash today, but records a late event and a certain avoidable cost while making only limited payment progress.', protects: 'Short-term operating liquidity', risks: 'Delay penalty and weaker obligation coverage', apply: (current) => update(payRequiredFromCash(current, Math.min(Math.round(current.cashAvailable * 0.2), metrics(current).unmetRequiredPayments)), { latePayments: current.latePayments + 1, avoidableCost: current.avoidableCost + 500 }) },
      ],
    }),
  },
  {
    id: 'essential-shock',
    label: 'Resilience decision',
    principle: 'Absorb essential costs without hiding them or double-counting available funds.',
    build: (state) => ({
      prompt: `A critical operating repair makes the full ${money(state.essentialExpenses)} essential-cost provision payable now. Your path leaves ${money(state.cashAvailable)} cash and a ${money(state.emergencyBuffer)} reserve. How do you fund it?`,
      options: [
        { id: 'fund-essential', label: `Apply up to ${money(state.essentialExpenses)} from available cash, then the reserve; carry any uncovered amount explicitly.`, analysis: 'Uses available liquidity without inventing funds. Any shortfall remains visible as an unfunded commitment.', protects: 'State integrity and cost efficiency', risks: 'Less liquidity and a possible residual commitment', apply: (current) => fundEssential(current, current.essentialExpenses) },
        { id: 'defer-essential', label: 'Apply up to ₹6,000 now and carry at least ₹3,000 with a ₹600 delay cost.', analysis: 'Retains some liquidity today while keeping both the planned deferral and any additional cash shortfall inside the plan need.', protects: 'Near-term liquidity', risks: 'An unfunded commitment, late event, and avoidable cost', apply: (current) => update(fundEssential(current, 6_000, 3_000), { latePayments: current.latePayments + 1, avoidableCost: current.avoidableCost + 600 }) },
        { id: 'finance-essential', label: 'Finance the ₹9,000 repair at a ₹2,700 cost and preserve current liquidity.', analysis: 'Completes the repair without drawing current cash, but the emergency financing charge consumes almost half of the scenario’s cost budget.', protects: 'Visible cash and reserve', risks: 'New borrowing and materially reduced cost efficiency', apply: (current) => update(current, { essentialExpenses: 0, newBorrowing: current.newBorrowing + 9_000, borrowingCost: current.borrowingCost + 2_700 }) },
      ],
    }),
  },
  {
    id: 'supplier-opportunity',
    label: 'Opportunity decision',
    principle: 'Evaluate a growth opportunity against the state created by every prior decision.',
    prepare: (state) => receive(state, state.confirmedInflows),
    build: (state) => ({
      prompt: `The remaining receivable now settles. You have ${money(state.cashAvailable)} cash, ${money(metrics(state).unmetRequiredPayments)} still unpaid, and ${money(state.unfundedCommitments)} in other commitments. A supplier slot needs ₹5,000 and confirms a ₹20,000 future inflow. What do you do?`,
      options: [
        { id: 'supplier-cash', label: 'Fund the ₹5,000 slot from operating cash.', analysis: 'Adds a confirmed future inflow at a direct liquidity cost, without adding debt.', protects: 'Future plan feasibility', risks: 'Less cash against the remaining obligation', apply: (current) => update(current, { cashAvailable: current.cashAvailable - 5_000, confirmedInflows: current.confirmedInflows + 20_000 }) },
        { id: 'supplier-decline', label: 'Decline the slot and preserve current liquidity.', analysis: 'Avoids new cost and commitment, but gives up a confirmed inflow that may strengthen the remaining plan.', protects: 'Immediate liquidity and cost control', risks: 'Foregone future cash', apply: (current) => current },
        { id: 'supplier-borrow', label: 'Borrow the ₹5,000 deposit at a ₹900 cost.', analysis: 'Preserves current cash and captures the inflow, but adds borrowing solely to fund the opportunity.', protects: 'Current liquidity and future inflow', risks: 'Additional financing cost', apply: (current) => update(current, { newBorrowing: current.newBorrowing + 5_000, borrowingCost: current.borrowingCost + 900, confirmedInflows: current.confirmedInflows + 20_000 }) },
      ],
    }),
  },
]);

export const TRIAL_QUESTIONS = Object.freeze(TRIAL_STAGES.map(({ id, label }) => ({ id, label })));

function resolveStage(index, state) {
  const stage = TRIAL_STAGES[index];
  const stateBefore = stage.prepare ? stage.prepare(state) : state;
  return { ...stage, ...stage.build(stateBefore), stateBefore };
}

function replayUntil(index, answers) {
  let state = { ...INITIAL_STATE };
  for (let stageIndex = 0; stageIndex < index; stageIndex += 1) {
    const stage = resolveStage(stageIndex, state);
    const option = stage.options.find((candidate) => candidate.id === answers[stage.id]);
    if (!option) break;
    state = option.apply(stage.stateBefore);
  }
  return state;
}

export function getTrialQuestion(index, answers = {}) {
  const stage = resolveStage(index, replayUntil(index, answers));
  return { ...stage, state: stateSummary(stage.stateBefore) };
}

function clamp01(value) {
  return Math.max(0, Math.min(1, value));
}

function terminalScore(state) {
  const stateMetrics = metrics(state);
  const dimensions = {
    obligationCoverage: 100 * clamp01(state.requiredPaymentsMet / state.requiredPaymentsDue),
    liquidityRetention: 100 * clamp01(stateMetrics.unencumberedLiquidity / INITIAL_LIQUIDITY),
    costEfficiency: 100 * clamp01(1 - ((state.borrowingCost + state.avoidableCost) / COST_BUDGET)),
    planFeasibility: stateMetrics.remainingPlanNeed === 0
      ? 100
      : (100 * clamp01((stateMetrics.unencumberedLiquidity + state.confirmedInflows) / stateMetrics.remainingPlanNeed)) / (1 + state.latePayments),
  };
  const raw = (0.4 * dimensions.obligationCoverage)
    + (0.25 * dimensions.liquidityRetention)
    + (0.2 * dimensions.costEfficiency)
    + (0.15 * dimensions.planFeasibility);
  return { raw, dimensions };
}

function allTerminalScores(index = 0, state = INITIAL_STATE) {
  if (index === TRIAL_STAGES.length) return [terminalScore(state).raw];
  const stage = resolveStage(index, state);
  return stage.options.flatMap((option) => allTerminalScores(index + 1, option.apply(stage.stateBefore)));
}

const ATTAINABLE_SCORES = allTerminalScores();
const ATTAINABLE_MIN = Math.min(...ATTAINABLE_SCORES);
const ATTAINABLE_MAX = Math.max(...ATTAINABLE_SCORES);

function bestReachableScore(index, state) {
  if (index === TRIAL_STAGES.length) return terminalScore(state).raw;
  const stage = resolveStage(index, state);
  return Math.max(...stage.options.map((option) => bestReachableScore(index + 1, option.apply(stage.stateBefore))));
}

function stateSummary(state) {
  const stateMetrics = metrics(state);
  return {
    cashAvailable: state.cashAvailable,
    emergencyBuffer: state.emergencyBuffer,
    paymentRemaining: stateMetrics.unmetRequiredPayments,
    confirmedInflows: state.confirmedInflows,
    planNeed: stateMetrics.remainingPlanNeed,
    costToDate: state.borrowingCost + state.avoidableCost,
  };
}

function changedState(before, after) {
  const labels = {
    cashAvailable: 'Operating cash', requiredPaymentsMet: 'Required payments met', confirmedInflows: 'Confirmed inflows', essentialExpenses: 'Essential costs remaining', emergencyBuffer: 'Emergency reserve', newBorrowing: 'New borrowing', borrowingCost: 'Borrowing cost', avoidableCost: 'Avoidable cost', latePayments: 'Late-payment events', unfundedCommitments: 'Unfunded commitments',
  };
  return Object.entries(labels).flatMap(([key, label]) => {
    const difference = after[key] - before[key];
    if (!difference) return [];
    const value = key === 'latePayments' ? `${difference > 0 ? '+' : ''}${difference}` : `${difference > 0 ? '+' : '−'}${money(Math.abs(difference))}`;
    return [{ label, value }];
  });
}

const DIMENSION_LABELS = {
  obligationCoverage: 'Obligation coverage',
  liquidityRetention: 'Liquidity retention',
  costEfficiency: 'Cost efficiency',
  planFeasibility: 'Plan feasibility',
};

const DIMENSION_GUIDANCE = {
  obligationCoverage: 'Increase verified payment coverage before taking on discretionary commitments.',
  liquidityRetention: 'Protect unencumbered cash and reserve after allowing for unpaid obligations.',
  costEfficiency: 'Reduce avoidable concessions, late costs, and borrowing used only to preserve visible cash.',
  planFeasibility: 'Keep enough verified liquidity and confirmed inflows to fund the remaining plan without repeated delay.',
};

export function scoreTrialAssessment(answers) {
  let state = { ...INITIAL_STATE };
  const timeline = TRIAL_STAGES.map((_, index) => {
    const stage = resolveStage(index, state);
    const selected = stage.options.find((option) => option.id === answers[stage.id]);
    if (!selected) throw new Error('Complete every trial decision before scoring.');
    const optionPotentials = stage.options.map((option) => ({ option, score: bestReachableScore(index + 1, option.apply(stage.stateBefore)) }));
    const best = optionPotentials.reduce((current, candidate) => candidate.score > current.score ? candidate : current);
    const selectedPotential = optionPotentials.find((candidate) => candidate.option.id === selected.id).score;
    const weakestPotential = Math.min(...optionPotentials.map((candidate) => candidate.score));
    const retainedPotential = best.score === weakestPotential ? 100 : (100 * (selectedPotential - weakestPotential)) / (best.score - weakestPotential);
    const stateAfter = selected.apply(stage.stateBefore);
    state = stateAfter;
    return {
      id: stage.id,
      number: index + 1,
      pathLabel: stage.label,
      prompt: stage.prompt,
      selected: selected.label,
      benchmark: best.option.label,
      quality: retainedPotential >= 92 ? 4 : retainedPotential >= 70 ? 3 : retainedPotential >= 45 ? 2 : retainedPotential >= 20 ? 1 : 0,
      rating: retainedPotential >= 92 ? 'Strong path choice' : retainedPotential >= 70 ? 'Sound path choice' : retainedPotential >= 45 ? 'Mixed path choice' : retainedPotential >= 20 ? 'Fragile path choice' : 'High-cost path choice',
      retainedPotential: Math.round(retainedPotential),
      principle: stage.principle,
      analysis: selected.analysis,
      protects: selected.protects,
      risks: selected.risks,
      impact: changedState(stage.stateBefore, stateAfter),
    };
  });
  const terminal = terminalScore(state);
  const scenarioScore = Math.round(100 * clamp01((terminal.raw - ATTAINABLE_MIN) / (ATTAINABLE_MAX - ATTAINABLE_MIN)));
  const score = Math.round((0.7 * scenarioScore) + 15);
  const domainScores = Object.entries(terminal.dimensions).map(([key, value]) => ({ name: DIMENSION_LABELS[key], score: Math.round(value) }));
  const recommendations = Object.entries(terminal.dimensions)
    .sort((a, b) => a[1] - b[1])
    .slice(0, 2)
    .map(([key]) => DIMENSION_GUIDANCE[key]);

  return {
    kind: 'trial',
    version: TRIAL_RESULT_VERSION,
    score,
    band: score >= 85 ? 'Strong path' : score >= 70 ? 'Sound path' : score >= 50 ? 'Developing path' : 'High-pressure path',
    scoreBasis: 'Limited-evidence preview',
    formula: '40% obligation coverage + 25% liquidity retention + 20% cost efficiency + 15% plan feasibility',
    calibration: '70% feasible-range path score + 30% neutral evidence anchor',
    scenarioScore,
    domainScores,
    feedback: timeline,
    terminalState: stateSummary(state),
    recommendations,
  };
}

export function isTrialResult(value) {
  return value?.kind === 'trial'
    && value.version === TRIAL_RESULT_VERSION
    && Number.isInteger(value.score)
    && value.score >= 15
    && value.score <= 85
    && Number.isInteger(value.scenarioScore)
    && value.scenarioScore >= 0
    && value.scenarioScore <= 100
    && Array.isArray(value.domainScores)
    && value.domainScores.length === 4
    && Array.isArray(value.feedback)
    && value.feedback.length === TRIAL_QUESTIONS.length
    && value.terminalState
    && Array.isArray(value.recommendations);
}

export function saveTrialResult(result) {
  if (!isTrialResult(result)) return false;
  return writeStorageItem(getSessionStorage(), TRIAL_RESULT_STORAGE_KEY, JSON.stringify(result));
}

export function getStoredTrialResult() {
  const raw = readStorageItem(getSessionStorage(), TRIAL_RESULT_STORAGE_KEY);
  if (!raw) return null;
  try {
    const result = JSON.parse(raw);
    if (isTrialResult(result)) return result;
    removeStorageItem(getSessionStorage(), TRIAL_RESULT_STORAGE_KEY);
    return null;
  } catch {
    removeStorageItem(getSessionStorage(), TRIAL_RESULT_STORAGE_KEY);
    return null;
  }
}

export function clearStoredTrialResult() {
  removeStorageItem(getSessionStorage(), TRIAL_RESULT_STORAGE_KEY);
}
