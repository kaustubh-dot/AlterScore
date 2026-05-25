import {
  coerceAnswerValue,
  getTimeOfDay,
  computeTypingSpeed,
  getRiskBand,
  formatCurrencyRange,
  buildAnswersPayload,
  buildBehavioralPayload
} from "./scorePayload.js";

export function runScorePayloadTests() {
  console.log("▶ Running scorePayload.js tests...");

  // Test 1: coerceAnswerValue
  const numQ = { type: "number" };
  const textQ = { type: "text", maxLength: 20 };
  const mcqQ = { type: "mcq" };

  if (coerceAnswerValue(numQ, "123") !== 123) throw new Error("Number coercion failed");
  if (coerceAnswerValue(numQ, "abc") !== "") throw new Error("NaN number coercion should return empty string");
  if (coerceAnswerValue(textQ, "a".repeat(30)) !== "a".repeat(20)) throw new Error("Text clipping failed");
  if (coerceAnswerValue(mcqQ, "2") !== 2) throw new Error("Generic coercion failed");
  console.log("  ✓ coerceAnswerValue converts inputs accurately");

  // Test 2: getTimeOfDay
  const morningDate = new Date(); morningDate.setHours(9);
  const nightDate = new Date(); nightDate.setHours(2);
  if (getTimeOfDay(morningDate) !== "morning") throw new Error("getTimeOfDay failed for morning");
  if (getTimeOfDay(nightDate) !== "night") throw new Error("getTimeOfDay failed for night");
  console.log("  ✓ getTimeOfDay resolves categories correctly");

  // Test 3: computeTypingSpeed
  const text = "Hello world from AlterScore"; // 4 words
  const responseTimeMs = 60000; // 1 minute
  const speed = computeTypingSpeed(text, responseTimeMs);
  if (speed !== 5.4) { // standard English word definition is length / 5 -> 27 / 5 = 5.4
    throw new Error(`Typing speed calculation failed: expected 5.4, got ${speed}`);
  }
  console.log("  ✓ computeTypingSpeed performs accurate mathematical formulas");

  // Test 4: getRiskBand
  if (getRiskBand(820).label !== "Excellent") throw new Error("getRiskBand mapping failed for Excellent");
  if (getRiskBand("poor").label !== "Poor") throw new Error("getRiskBand string mapping failed for poor");
  if (getRiskBand(600).color !== "#ffad33") throw new Error("getRiskBand color association failed");
  console.log("  ✓ getRiskBand maps labels and colors correctly");

  // Test 5: formatCurrencyRange
  const eligibility = { amount_min: 5000, amount_max: 25000 };
  if (formatCurrencyRange(eligibility) !== "Rs. 5,000 - Rs. 25,000") {
    throw new Error(`formatCurrencyRange failed: got ${formatCurrencyRange(eligibility)}`);
  }
  console.log("  ✓ formatCurrencyRange conforms to local formatting");

  console.log("✓ All scorePayload.js tests PASSED!\n");
}
