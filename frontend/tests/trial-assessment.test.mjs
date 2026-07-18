import test from 'node:test';
import assert from 'node:assert/strict';

import {
  getTrialQuestion,
  isTrialResult,
  scoreTrialAssessment,
  TRIAL_QUESTIONS,
} from '../src/lib/trialAssessment.js';

const representativePath = {
  'collection-action': 'reconcile',
  'shortfall-response': 'cash-payment',
  'payment-arrangement': 'good-faith',
  'essential-shock': 'fund-essential',
  'supplier-opportunity': 'supplier-cash',
};

test('uses the main branching dimensions and feasible-range normalization', () => {
  const result = scoreTrialAssessment(representativePath);

  assert.equal(result.version, 3);
  assert.equal(result.scoreBasis, 'Feasible-range normalized');
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

  const arrangementA = getTrialQuestion(3, { ...representativePath, 'payment-arrangement': 'all-cash' });
  const arrangementB = getTrialQuestion(3, { ...representativePath, 'payment-arrangement': 'extension' });
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
    question.options.forEach((option) => visit(index + 1, { ...answers, [question.id]: option.id }));
  };
  visit(0, {});

  assert.equal(results.length, 243);
  assert.equal(Math.min(...results.map((result) => result.score)), 0);
  assert.equal(Math.max(...results.map((result) => result.score)), 100);
  assert.ok(results.filter((result) => result.score === 100).length < 10);
  assert.equal(isTrialResult({ ...results[0], version: 2 }), false);
});
