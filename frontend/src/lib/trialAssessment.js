import { getSessionStorage, readStorageItem, removeStorageItem, writeStorageItem } from './safeStorage';

export const TRIAL_RESULT_STORAGE_KEY = 'alterscore_trial_result';

export const TRIAL_QUESTIONS = Object.freeze([
  {
    id: 'cash-flow',
    domain: 'Financial knowledge',
    prompt: 'You receive ₹30,000 this month. Essential expenses are ₹18,000 and required repayments are ₹5,000. How much remains?',
    choices: ['₹5,000', '₹7,000', '₹12,000', '₹13,000'],
    answer: 1,
    explanation: '₹30,000 − ₹18,000 − ₹5,000 leaves ₹7,000 after essentials and required repayments.',
    guidance: 'Practise subtracting both essential spending and fixed obligations when estimating usable cash.',
  },
  {
    id: 'borrowing-cost',
    domain: 'Financial knowledge',
    prompt: 'Which loan is usually the better comparison before borrowing?',
    choices: ['The one with the lowest monthly payment only', 'The one approved fastest', 'The one with the lowest total repayment for comparable terms', 'The one with the longest term'],
    answer: 2,
    explanation: 'Total repayment captures interest and fees across the term; a smaller instalment can still cost more overall.',
    guidance: 'Compare total repayment, fees, rate, and term—not the monthly instalment alone.',
  },
  {
    id: 'emergency-buffer',
    domain: 'Financial knowledge',
    prompt: 'What is the clearest purpose of an emergency fund?',
    choices: ['To fund routine shopping', 'To cover unexpected essential costs without expensive borrowing', 'To maximise short-term investment returns', 'To increase a credit limit'],
    answer: 1,
    explanation: 'An emergency buffer protects essential obligations when an unplanned cost or income interruption occurs.',
    guidance: 'Build a separate, accessible buffer for essential surprises before taking avoidable investment risk.',
  },
  {
    id: 'due-date',
    domain: 'Decision judgement',
    prompt: 'A required payment is due tomorrow, but your salary arrives in three days. What is the strongest first action?',
    choices: ['Ignore the due date', 'Take the first instant loan offered', 'Contact the provider early and discuss a documented arrangement', 'Spend the available cash on a non-essential purchase'],
    answer: 2,
    explanation: 'Early contact can preserve options and reduce avoidable penalties without immediately adding high-cost debt.',
    guidance: 'Act before a due date: confirm the shortfall, contact the provider, and document any arrangement.',
  },
  {
    id: 'unexpected-cash',
    domain: 'Decision judgement',
    prompt: 'You receive an unexpected ₹10,000 while carrying costly overdue debt and no emergency buffer. What is the most balanced response?',
    choices: ['Spend all of it immediately', 'Use it only for a speculative investment', 'Address urgent overdue debt and retain part as a basic buffer', 'Commit it to a new recurring expense'],
    answer: 2,
    explanation: 'Reducing urgent costly debt while retaining some liquidity balances obligation coverage with resilience.',
    guidance: 'Prioritise urgent obligations while keeping enough liquidity to avoid immediately borrowing again.',
  },
]);

export function scoreTrialAssessment(answers) {
  const feedback = TRIAL_QUESTIONS.map((question, index) => ({
    id: question.id,
    domain: question.domain,
    prompt: question.prompt,
    selected: question.choices[answers[question.id]],
    correct: question.choices[question.answer],
    isCorrect: answers[question.id] === question.answer,
    explanation: question.explanation,
    guidance: question.guidance,
    number: index + 1,
  }));
  const correctCount = feedback.filter((item) => item.isCorrect).length;
  const score = correctCount * 20;
  const domainScores = ['Financial knowledge', 'Decision judgement'].map((name) => {
    const items = feedback.filter((item) => item.domain === name);
    return { name, score: Math.round((items.filter((item) => item.isCorrect).length / items.length) * 100) };
  });
  const band = score >= 80 ? 'Strong foundation' : score >= 60 ? 'Developing foundation' : 'Needs focused review';
  const recommendations = feedback.filter((item) => !item.isCorrect).map((item) => item.guidance).slice(0, 3);

  return {
    kind: 'trial',
    score,
    correctCount,
    total: TRIAL_QUESTIONS.length,
    band,
    domainScores,
    feedback,
    recommendations: recommendations.length > 0
      ? recommendations
      : ['Continue with the full assessment for broader scenarios, calibrated scoring, and a server-signed result.'],
  };
}

export function isTrialResult(value) {
  return value?.kind === 'trial'
    && Number.isInteger(value.score)
    && value.score >= 0
    && value.score <= 100
    && value.total === TRIAL_QUESTIONS.length
    && Array.isArray(value.domainScores)
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
    return isTrialResult(result) ? result : null;
  } catch {
    return null;
  }
}

export function clearStoredTrialResult() {
  removeStorageItem(getSessionStorage(), TRIAL_RESULT_STORAGE_KEY);
}
