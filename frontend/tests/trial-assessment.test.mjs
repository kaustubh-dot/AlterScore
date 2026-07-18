import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import {
  getTrialQuestion,
  isTrialResult,
  scoreTrialAssessment,
  TRIAL_QUESTIONS,
} from '../src/lib/trialAssessment.js';

const representativePath = {
  'collection-action': 'reconcile',
  'shortfall-response': 'cash-payment',
  'payment-arrangement': 'balanced-payment',
  'essential-shock': 'fund-essential',
  'supplier-opportunity': 'supplier-cash',
};

test('uses the main branching dimensions and feasible-range normalization', () => {
  const result = scoreTrialAssessment(representativePath);

  assert.equal(result.version, 4);
  assert.equal(result.scoreBasis, 'Limited-evidence preview');
  assert.equal(result.calibration, '70% feasible-range path score + 30% neutral evidence anchor');
  assert.deepEqual(result.domainScores.map((item) => item.name), [
    'Obligation coverage',
    'Liquidity retention',
    'Cost efficiency',
    'Plan feasibility',
  ]);
  assert.equal(result.feedback.length, TRIAL_QUESTIONS.length);
  assert.equal(Object.hasOwn(result, 'correctCount'), false);
  assert.equal(isTrialResult(result), true);
});

test('every decision changes the state inherited by the next stage', () => {
  const collectionA = getTrialQuestion(1, { 'collection-action': 'routine' });
  const collectionB = getTrialQuestion(1, { 'collection-action': 'accelerate' });
  assert.notEqual(collectionA.state.cashAvailable, collectionB.state.cashAvailable);

  const fundingA = getTrialQuestion(2, { 'collection-action': 'reconcile', 'shortfall-response': 'cash-payment' });
  const fundingB = getTrialQuestion(2, { 'collection-action': 'reconcile', 'shortfall-response': 'bridge' });
  assert.notEqual(fundingA.state.paymentRemaining, fundingB.state.paymentRemaining);
  assert.notEqual(fundingA.state.costToDate, fundingB.state.costToDate);

  const arrangementA = getTrialQuestion(3, { ...representativePath, 'payment-arrangement': 'accelerated-payment' });
  const arrangementB = getTrialQuestion(3, { ...representativePath, 'payment-arrangement': 'extension-payment' });
  assert.notEqual(arrangementA.state.cashAvailable, arrangementB.state.cashAvailable);

  const resilienceA = getTrialQuestion(4, { ...representativePath, 'essential-shock': 'fund-essential' });
  const resilienceB = getTrialQuestion(4, { ...representativePath, 'essential-shock': 'finance-essential' });
  assert.notEqual(resilienceA.state.cashAvailable, resilienceB.state.cashAvailable);
  assert.notEqual(resilienceA.state.costToDate, resilienceB.state.costToDate);
});

test('calibrates all 243 reachable paths and rejects legacy trial results', () => {
  const results = [];
  const visit = (index, answers) => {
    if (index === TRIAL_QUESTIONS.length) {
      results.push(scoreTrialAssessment(answers));
      return;
    }
    const question = getTrialQuestion(index, answers);
    assert.equal(Object.values(question.state).every((value) => Number.isFinite(value) && value >= 0), true);
    question.options.forEach((option) => visit(index + 1, { ...answers, [question.id]: option.id }));
  };
  visit(0, {});

  assert.equal(results.length, 243);
  assert.equal(Math.min(...results.map((result) => result.score)), 15);
  assert.equal(Math.max(...results.map((result) => result.score)), 85);
  assert.equal(results.filter((result) => result.score >= 85).length, 2);
  assert.equal(results.every((result) => Object.values(result.terminalState).every((value) => Number.isFinite(value) && value >= 0)), true);
  assert.equal(isTrialResult({ ...results[0], version: 3 }), false);
});

test('clears stale trial results and keeps missing trial state out of the full-result path', () => {
  const trialPage = readFileSync(new URL('../src/pages/TrialAssessment.jsx', import.meta.url), 'utf8');
  const resultsPage = readFileSync(new URL('../src/pages/Results.jsx', import.meta.url), 'utf8');

  assert.match(trialPage, /useEffect\(\(\) => \{\s*clearStoredTrialResult\(\);\s*\}, \[\]\);/);
  assert.ok(resultsPage.indexOf('if (trialMode)') < resultsPage.indexOf('if (!result)'));
  assert.match(resultsPage, /No current trial result/);
});
