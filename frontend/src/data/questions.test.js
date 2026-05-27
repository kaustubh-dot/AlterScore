import { QUESTIONS, SECTIONS, CORE_QUESTION_COUNT, getSectionQuestions, getSectionById } from "./questions.js";

export function runQuestionsTests() {
  console.log("▶ Running questions.js tests...");

  // Test 1: Questions count
  if (QUESTIONS.length < CORE_QUESTION_COUNT) {
    throw new Error(`Expected at least ${CORE_QUESTION_COUNT} questions, got ${QUESTIONS.length}`);
  }
  console.log("  ✓ Total questions count is correct");

  // Test 2: Valid categories and sections
  for (const q of QUESTIONS) {
    if (!q.id) throw new Error("Question found without an id");
    if (!q.section) throw new Error(`Question ${q.id} found without a section`);
    if (!q.type) throw new Error(`Question ${q.id} found without a type`);
    if (!["number", "mcq", "likert", "binary_choice", "text", "scenario"].includes(q.type)) {
      throw new Error(`Question ${q.id} has invalid type: ${q.type}`);
    }
  }
  console.log("  ✓ All questions have valid IDs, types, and sections");

  // Test 3: getSectionQuestions works
  const sectionAQuestions = getSectionQuestions("A");
  if (sectionAQuestions.length === 0) {
    throw new Error("getSectionQuestions('A') returned zero questions");
  }
  for (const q of sectionAQuestions) {
    if (q.section !== "A") {
      throw new Error(`Expected question ${q.id} to be in section A, got ${q.section}`);
    }
  }
  console.log(`  ✓ getSectionQuestions helper operates correctly (${sectionAQuestions.length} questions in section A)`);

  // Test 4: getSectionById works
  const sectionB = getSectionById("B");
  if (!sectionB || sectionB.title !== "Decision Scenarios") {
    throw new Error("getSectionById('B') failed to retrieve correct section definition");
  }
  console.log("  ✓ getSectionById helper resolves titles correctly");

  console.log("✓ All questions.js tests PASSED!\n");
}
