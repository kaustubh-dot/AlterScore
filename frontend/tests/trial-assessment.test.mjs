import test from 'node:test';
import assert from 'node:assert/strict';

import {
  getTrialQuestion,
  isTrialResult,
  scoreTrialAssessment,
  TRIAL_QUESTIONS,
} from '../src/lib/trialAssessment.js';

test('uses weighted response quality instead of equal twenty-point questions', () => {
  const answers = {
    'cash-flow': 1,
    'borrowing-cost': 3,
    'emergency-buffer': 2,
    'due-date': 3,
    'branch-outcome': 1,
  };
  const result = scoreTrialAssessment(answers);

  assert.equal(result.version, 2);
  assert.equal(result.domainScores.length, 3);
  assert.equal(result.feedback.length, TRIAL_QUESTIONS.length);
  assert.notEqual(result.score % 20, 0);
  assert.equal(Object.hasOwn(result, 'correctCount'), false);
  assert.equal(isTrialResult(result), true);
});

test('branches the final scenario from the earlier due-date decision', () => {
  const managed = getTrialQuestion(4, { 'due-date': 2 });
  const recovery = getTrialQuestion(4, { 'due-date': 1 });

  assert.equal(managed.branch, 'managed');
  assert.equal(recovery.branch, 'recovery');
  assert.notEqual(managed.prompt, recovery.prompt);
});

test('retains a meaningful perfect benchmark while rejecting old quiz results', () => {
  const result = scoreTrialAssessment({
    'cash-flow': 1,
    'borrowing-cost': 1,
    'emergency-buffer': 1,
    'due-date': 2,
    'branch-outcome': 0,
  });

  assert.equal(result.score, 100);
  assert.equal(result.band, 'Strong foundation');
  assert.equal(result.feedback.every((item) => item.rating === 'Strong evidence'), true);
  assert.equal(isTrialResult({ ...result, version: 1 }), false);
});
