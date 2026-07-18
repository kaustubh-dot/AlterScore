import { getSessionStorage, readStorageItem, removeStorageItem, writeStorageItem } from './safeStorage.js';

export const TRIAL_RESULT_STORAGE_KEY = 'alterscore_trial_result';
export const TRIAL_RESULT_VERSION = 3;

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
  const fromCash = Math.min(state.cashAvailable, amount);
  return update(state, {
    cashAvailable: state.cashAvailable - fromCash,
    emergencyBuffer: state.emergencyBuffer - (amount - fromCash),
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
        { id: 'bridge', label: 'Draw a ₹12,000 bridge facility costing ₹1,800.', analysis: 'Adds liquidity but does not itself settle the required payment, and introduces a certain financing cost.', protects: 'Immediate cash capacity', risks: 'New debt and ₹1,800 cost', apply: (current) => borrow(current, 12_000, 1_800) },
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
        { id: 'all-cash', label: `Apply ${money(Math.min(state.cashAvailable, metrics(state).unmetRequiredPayments))} — all available operating cash up to the unpaid amount.`, analysis: 'Maximises payment progress now, but can leave essential operating costs dependent on the reserve.', protects: 'Obligation coverage', risks: 'A concentrated liquidity draw', apply: (current) => payRequiredFromCash(current, Math.min(current.cashAvailable, metrics(current).unmetRequiredPayments)) },
        { id: 'good-faith', label: 'Make a documented ₹6,000 good-faith payment and retain the balance.', analysis: 'Preserves more liquidity, while leaving a larger balance exposed to later collection risk.', protects: 'Plan flexibility', risks: 'Lower immediate obligation coverage', apply: (current) => payRequiredFromCash(current, Math.min(6_000, metrics(current).unmetRequiredPayments)) },
        { id: 'extension', label: 'Take a seven-day extension with a ₹500 follow-up cost.', analysis: 'Preserves cash today but records a late event and a certain avoidable cost.', protects: 'Short-term liquidity', risks: 'Delay penalty and weaker plan feasibility', apply: (current) => update(current, { latePayments: current.latePayments + 1, avoidableCost: current.avoidableCost + 500 }) },
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
        { id: 'fund-essential', label: `Pay the full ${money(state.essentialExpenses)} from available cash, then the reserve if needed.`, analysis: 'Closes the essential need without new debt, but draws directly on remaining liquidity.', protects: 'Plan completion and cost efficiency', risks: 'Less cash and reserve after the repair', apply: (current) => update(spendLiquidity(current, current.essentialExpenses), { essentialExpenses: 0 }) },
        { id: 'defer-essential', label: 'Pay ₹6,000 now and carry ₹3,000 as an unfunded commitment.', analysis: 'Retains some liquidity today, but the deferred amount remains inside the plan need.', protects: 'Near-term liquidity', risks: 'A new unfunded commitment', apply: (current) => update(spendLiquidity(current, 6_000), { essentialExpenses: 0, unfundedCommitments: current.unfundedCommitments + 3_000 }) },
        { id: 'finance-essential', label: 'Finance the ₹9,000 repair at a ₹1,350 cost and preserve current liquidity.', analysis: 'Completes the repair without drawing current cash, in exchange for material borrowing cost.', protects: 'Visible cash and reserve', risks: 'New borrowing and reduced cost efficiency', apply: (current) => update(current, { essentialExpenses: 0, newBorrowing: current.newBorrowing + 9_000, borrowingCost: current.borrowingCost + 1_350 }) },
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
  const score = Math.round(100 * clamp01((terminal.raw - ATTAINABLE_MIN) / (ATTAINABLE_MAX - ATTAINABLE_MIN)));
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
    scoreBasis: 'Feasible-range normalized',
    formula: '40% obligation coverage + 25% liquidity retention + 20% cost efficiency + 15% plan feasibility',
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
    && value.score >= 0
    && value.score <= 100
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
