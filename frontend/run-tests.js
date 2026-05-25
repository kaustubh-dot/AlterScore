import { runQuestionsTests } from "./src/data/questions.test.js";
import { runScorePayloadTests } from "./src/services/scorePayload.test.js";
import { runApiTests } from "./src/services/api.test.js";

console.log("=========================================");
console.log(" AlterScore Frontend Unit Test Suite     ");
console.log("=========================================");

async function main() {
  try {
    runQuestionsTests();
    runScorePayloadTests();
    await runApiTests();
    console.log("🎉 SUCCESS: All frontend tests completed successfully!");
    console.log("=========================================\n");
    process.exit(0);
  } catch (error) {
    console.error("❌ FAILURE: Test run failed with an exception:");
    console.error(error);
    console.log("=========================================\n");
    process.exit(1);
  }
}

main();
