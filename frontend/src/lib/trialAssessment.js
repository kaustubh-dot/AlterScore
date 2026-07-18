import { getSessionStorage, readStorageItem, removeStorageItem, writeStorageItem } from './safeStorage.js';

export const TRIAL_RESULT_STORAGE_KEY = 'alterscore_trial_result';
export const TRIAL_RESULT_VERSION = 2;

const QUALITY_LABELS = ['High-risk choice', 'Fragile choice', 'Mixed choice', 'Sound choice', 'Strong evidence'];

export const TRIAL_QUESTIONS = Object.freeze([
  {
    id: 'cash-flow',
    domain: 'Financial knowledge',
    weight: 0.16,
    prompt: 'You receive ₹30,000 this month. Essential expenses are ₹18,000 and required repayments are ₹5,000. How much is genuinely available after both?',
    principle: 'Cash-flow arithmetic',
    guidance: 'Separate essential spending and fixed obligations before treating money as available.',
    options: [
      { label: '₹12,000', quality: 1, analysis: 'This subtracts essentials but overlooks the required repayment.', protects: 'Essential spending', risks: 'Missing a fixed obligation' },
      { label: '₹7,000', quality: 4, analysis: 'This accounts for both essentials and the required repayment.', protects: 'Obligation coverage and liquidity visibility', risks: 'No material calculation gap' },
      { label: '₹25,000', quality: 0, analysis: 'This subtracts only the repayment and treats essential costs as optional.', protects: 'The repayment only', risks: 'A severe cash shortfall' },
      { label: '₹5,000', quality: 2, analysis: 'This recognises the repayment but mistakes it for the remaining balance.', protects: 'Awareness of debt', risks: 'Underestimating usable cash' },
    ],
  },
  {
    id: 'borrowing-cost',
    domain: 'Financial knowledge',
    weight: 0.18,
    prompt: 'Two loans fund the same purchase. Which comparison gives the clearest first view of affordability?',
    principle: 'Total borrowing cost',
    guidance: 'Compare total repayment, fees, rate, and term before relying on the monthly instalment.',
    options: [
      { label: 'Choose the lowest monthly payment', quality: 1, analysis: 'A low instalment can hide a longer term and a higher total cost.', protects: 'Short-term monthly cash flow', risks: 'Paying substantially more over time' },
      { label: 'Compare total repayment and fees for equivalent terms', quality: 4, analysis: 'This puts interest, fees, and duration on a comparable basis.', protects: 'Cost efficiency and affordability', risks: 'Requires checking the full loan schedule' },
      { label: 'Choose whichever lender approves first', quality: 0, analysis: 'Approval speed says nothing about affordability or total cost.', protects: 'Speed', risks: 'High-cost or unsuitable borrowing' },
      { label: 'Compare interest rates only', quality: 2, analysis: 'The rate matters, but fees and term can still change the actual cost.', protects: 'Part of the cost comparison', risks: 'Missing fees and duration effects' },
    ],
  },
  {
    id: 'emergency-buffer',
    domain: 'Financial resilience',
    weight: 0.19,
    prompt: 'You have ₹15,000 saved, irregular income, and no overdue bills. An investment promises high returns but locks the money for a year. What is the most resilient response?',
    principle: 'Liquidity before avoidable risk',
    guidance: 'Protect an accessible emergency reserve before locking scarce savings into higher-risk products.',
    options: [
      { label: 'Invest all ₹15,000 before the offer ends', quality: 0, analysis: 'This removes the only liquid buffer while income is uncertain.', protects: 'Potential return', risks: 'Borrowing for the next essential shock' },
      { label: 'Keep an accessible buffer and invest only a genuine surplus', quality: 4, analysis: 'This balances resilience with the opportunity to invest.', protects: 'Liquidity and future flexibility', risks: 'A smaller immediate investment' },
      { label: 'Keep all savings accessible and review investing after income stabilises', quality: 3, analysis: 'This is cautious and preserves liquidity, though it postpones learning or gradual investing.', protects: 'Maximum short-term resilience', risks: 'Opportunity cost' },
      { label: 'Borrow for emergencies if one happens', quality: 1, analysis: 'This treats expensive future borrowing as the safety net.', protects: 'The investment amount', risks: 'Debt escalation during a shock' },
    ],
  },
  {
    id: 'due-date',
    domain: 'Decision judgement',
    weight: 0.22,
    prompt: 'A required payment is due tomorrow, but your salary arrives in three days. What do you do first?',
    principle: 'Early obligation management',
    guidance: 'Confirm the shortfall, contact the provider before the due date, and document any arrangement.',
    options: [
      { label: 'Ignore it until the salary arrives', quality: 0, analysis: 'Silence removes the chance to agree terms before the payment is late.', protects: 'Immediate effort', risks: 'Fees, escalation, and loss of options' },
      { label: 'Take the first instant loan offered', quality: 1, analysis: 'This covers the date but may replace a short timing gap with expensive debt.', protects: 'The immediate due date', risks: 'High borrowing cost and repeat shortfalls' },
      { label: 'Contact the provider now and document a short arrangement', quality: 4, analysis: 'Early contact preserves options without automatically adding new debt.', protects: 'Obligation coverage and cost control', risks: 'The provider may still apply limited terms' },
      { label: 'Pay part without contacting the provider', quality: 2, analysis: 'A partial payment shows intent, but it may not prevent late status without an agreement.', protects: 'Some obligation coverage', risks: 'Unclear treatment of the remaining balance' },
    ],
  },
  {
    id: 'branch-outcome',
    domain: 'Decision judgement',
    weight: 0.25,
    principle: 'Recovery under changing constraints',
    guidance: 'Balance urgent obligations with enough retained liquidity to avoid immediately borrowing again.',
    branchFrom: 'due-date',
    variants: {
      managed: {
        pathLabel: 'Negotiated path · stage 2',
        prompt: 'The provider accepts a three-day extension. An unexpected ₹10,000 also arrives today. How do you use it?',
        options: [
          { label: 'Reserve the required payment, keep a basic buffer, then review any surplus', quality: 4, analysis: 'This honours the arrangement and preserves enough liquidity for another essential shock.', protects: 'The commitment and future resilience', risks: 'Less money available for discretionary use' },
          { label: 'Pay the full ₹10,000 immediately even though less is due', quality: 3, analysis: 'This strongly protects the obligation but can leave no buffer for the next disruption.', protects: 'Debt reduction', risks: 'A new liquidity shortfall' },
          { label: 'Invest all ₹10,000 because the extension creates time', quality: 0, analysis: 'The extension changes timing, not the obligation or need for liquidity.', protects: 'Potential return', risks: 'Breaking the agreed payment plan' },
          { label: 'Spend half and decide about the payment later', quality: 1, analysis: 'This consumes flexibility before a known obligation is secured.', protects: 'Immediate discretionary wants', risks: 'Late payment and renewed borrowing' },
        ],
      },
      recovery: {
        pathLabel: 'Pressure path · stage 2',
        prompt: 'The payment is now late and a costly short-term loan has been offered. An unexpected ₹10,000 arrives. What is the strongest recovery move?',
        options: [
          { label: 'Clear the urgent overdue amount, avoid the new loan, and retain a small buffer', quality: 4, analysis: 'This reduces immediate harm while preserving enough liquidity to avoid another instant loan.', protects: 'Obligation coverage, cost control, and resilience', risks: 'Only a modest buffer remains' },
          { label: 'Use all ₹10,000 on the overdue amount', quality: 3, analysis: 'This reduces the obligation quickly but may leave the next essential cost unfunded.', protects: 'Maximum debt reduction', risks: 'Returning to high-cost borrowing' },
          { label: 'Take the loan and keep the ₹10,000 untouched', quality: 1, analysis: 'This preserves cash but adds avoidable cost when funds are already available.', protects: 'Visible cash balance', risks: 'Unnecessary interest and fees' },
          { label: 'Ignore the overdue amount and invest the ₹10,000', quality: 0, analysis: 'This leaves a certain urgent cost unresolved for an uncertain return.', protects: 'Potential return', risks: 'Escalating arrears and borrowing cost' },
        ],
      },
    },
  },
]);

export function getTrialQuestion(index, answers = {}) {
  const question = TRIAL_QUESTIONS[index];
  if (!question?.variants) return question;
  const branch = answers[question.branchFrom] === 2 ? 'managed' : 'recovery';
  return { ...question, ...question.variants[branch], branch };
}

export function scoreTrialAssessment(answers) {
  const scored = TRIAL_QUESTIONS.map((_, index) => {
    const question = getTrialQuestion(index, answers);
    const selected = question.options[answers[question.id]];
    if (!selected) throw new Error('Complete every trial decision before scoring.');
    const benchmark = question.options.reduce((best, option) => option.quality > best.quality ? option : best);
    return { question, selected, benchmark };
  });
  const score = Math.round(scored.reduce((total, item) => total + (item.selected.quality / 4) * item.question.weight, 0) * 100);
  const domains = ['Financial knowledge', 'Financial resilience', 'Decision judgement'];
  const domainScores = domains.map((name) => {
    const items = scored.filter((item) => item.question.domain === name);
    const domainWeight = items.reduce((total, item) => total + item.question.weight, 0);
    const earned = items.reduce((total, item) => total + (item.selected.quality / 4) * item.question.weight, 0);
    return { name, score: Math.round((earned / domainWeight) * 100) };
  });
  const feedback = scored.map(({ question, selected, benchmark }, index) => ({
    id: question.id,
    number: index + 1,
    domain: question.domain,
    pathLabel: question.pathLabel || null,
    prompt: question.prompt,
    selected: selected.label,
    benchmark: benchmark.label,
    quality: selected.quality,
    rating: QUALITY_LABELS[selected.quality],
    principle: question.principle,
    analysis: selected.analysis,
    protects: selected.protects,
    risks: selected.risks,
    guidance: question.guidance,
  }));
  const recommendations = scored
    .filter((item) => item.selected.quality < 3)
    .sort((a, b) => (b.question.weight * (4 - b.selected.quality)) - (a.question.weight * (4 - a.selected.quality)))
    .map((item) => item.question.guidance)
    .slice(0, 3);

  return {
    kind: 'trial',
    version: TRIAL_RESULT_VERSION,
    score,
    band: score >= 85 ? 'Strong foundation' : score >= 70 ? 'Sound foundation' : score >= 50 ? 'Developing foundation' : 'Priority review',
    domainScores,
    feedback,
    recommendations: recommendations.length ? recommendations : ['Use the full assessment to test the same principles across longer simulations and a calibrated server-signed rubric.'],
  };
}

export function isTrialResult(value) {
  return value?.kind === 'trial'
    && value.version === TRIAL_RESULT_VERSION
    && Number.isInteger(value.score)
    && value.score >= 0
    && value.score <= 100
    && Array.isArray(value.domainScores)
    && value.domainScores.length === 3
    && Array.isArray(value.feedback)
    && value.feedback.length === TRIAL_QUESTIONS.length
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
