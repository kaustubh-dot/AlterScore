// AlterScore v2 Question Bank
// 14 questions: 5 reasoning + 7 behavioral scenarios + 1 honesty trap + 1 open-text
// Scenario options include pre-coded feature values for backend mapping.

export const SECTIONS = [
  {
    id: "A",
    title: "Financial Reasoning",
    kicker: "Numeracy, financial literacy, and cognitive reflection",
    icon: "Calculator",
  },
  {
    id: "B",
    title: "Decision Scenarios",
    kicker: "Real financial situations — what would you actually do?",
    icon: "Scale",
  },
  {
    id: "C",
    title: "Your Story",
    kicker: "A moment that shaped how you handle money",
    icon: "BookOpen",
  },
];

// ---------------------------------------------------------------------------
// SECTION A — Financial Reasoning (5 questions)
// Objective, correct-answer questions. Ungameable. Keep as-is.
// ---------------------------------------------------------------------------

export const QUESTIONS = [
  {
    id: "numeracy_q1",
    section: "A",
    type: "number",
    question: "You borrow Rs. 6,000 at 2.5% monthly interest. How much do you owe after 4 months?",
    hint: "Round to the nearest Rs. 10.",
    prefix: "Rs.",
    correctAnswer: 6600,
    isRiskQuestion: false,
    isTrap: false,
  },
  {
    id: "numeracy_q2",
    section: "A",
    type: "number",
    question: "A wholesaler gives you 20% off on a Rs. 1,400 purchase. What do you pay?",
    prefix: "Rs.",
    correctAnswer: 1120,
    isRiskQuestion: false,
    isTrap: false,
  },
  {
    id: "financial_literacy_q1",
    section: "A",
    type: "mcq",
    question:
      "Inflation is running at 9%. Your savings account earns 6% per year. What is happening to the real value of your savings?",
    options: [
      "Increasing because any interest is good",
      "Decreasing because inflation is outpacing returns",
      "Staying the same because interest offsets inflation",
      "It depends only on the bank",
    ],
    correctIndex: 1,
    isRiskQuestion: false,
    isTrap: false,
  },
  {
    id: "CRT_q1",
    section: "A",
    type: "number",
    question:
      "A bat and a ball together cost Rs. 110. The bat costs Rs. 100 more than the ball. How much does the ball cost?",
    hint: "Take your time. Most people answer this from instinct first.",
    prefix: "Rs.",
    correctAnswer: 5,
    isRiskQuestion: false,
    isTrap: false,
  },
  {
    id: "CRT_q2",
    section: "A",
    type: "number",
    question:
      "A lily pad patch doubles in size every day. It fills an entire lake in 48 days. How many days does it take to fill half the lake?",
    suffix: "days",
    correctAnswer: 47,
    isRiskQuestion: false,
    isTrap: false,
  },

  // ---------------------------------------------------------------------------
  // SECTION B — Behavioral Decision Scenarios (8 questions)
  // Scenario options carry pre-coded feature values for backend mapping.
  // Each option: { text, featureSignals: { featureName: value [0.0–1.0] } }
  // The consistency trap (S8) mirrors S1 in semantic intent.
  // Two honesty-trap Likerts are embedded here (not labeled as a separate section).
  // ---------------------------------------------------------------------------

  {
    id: "scenario_s1",
    section: "B",
    type: "scenario",
    question:
      "Your supplier is offering a 15% bulk discount on stock — but only if you pay within 2 days. Your next EMI is due in 5 days, and paying both would wipe out your buffer entirely.",
    isRiskQuestion: false,
    isTrap: false,
    options: [
      {
        id: "s1_a",
        text: "Take the supplier deal — the discount more than covers the short-term pressure",
        featureSignals: {
          primary: { feature: "future_orientation", value: 0.7 },
          secondary: { feature: "conscientiousness_score", value: 0.3 },
        },
      },
      {
        id: "s1_b",
        text: "Skip the deal — protecting the EMI comes first, no exceptions",
        featureSignals: {
          primary: { feature: "conscientiousness_score", value: 1.0 },
          secondary: { feature: "future_orientation", value: 0.5 },
        },
      },
      {
        id: "s1_c",
        text: "Negotiate with the supplier — can I pay half now and half next week?",
        featureSignals: {
          primary: { feature: "conscientiousness_score", value: 0.8 },
          secondary: { feature: "future_orientation", value: 0.8 },
        },
      },
      {
        id: "s1_d",
        text: "Ask a trusted contact to bridge the gap and repay them within the week",
        featureSignals: {
          primary: { feature: "social_capital_score", value: 0.8 },
          secondary: { feature: "conscientiousness_score", value: 0.6 },
        },
      },
    ],
  },

  {
    id: "scenario_s2",
    section: "B",
    type: "scenario",
    question:
      "A key client owes you Rs. 12,000 and has gone silent for 3 weeks. Your own rent is due in 10 days and you're cutting it close.",
    isRiskQuestion: false,
    isTrap: false,
    options: [
      {
        id: "s2_a",
        text: "Call them repeatedly until I get a response — I need that money",
        featureSignals: {
          primary: { feature: "locus_of_control", value: 0.8 },
          secondary: { feature: "resilience_score", value: 0.6 },
        },
      },
      {
        id: "s2_b",
        text: "Send a clear written message giving them a firm deadline before escalating",
        featureSignals: {
          primary: { feature: "locus_of_control", value: 1.0 },
          secondary: { feature: "conscientiousness_score", value: 0.9 },
        },
      },
      {
        id: "s2_c",
        text: "Reach out to someone in my network who might spot me until the client pays",
        featureSignals: {
          primary: { feature: "social_capital_score", value: 0.9 },
          secondary: { feature: "locus_of_control", value: 0.6 },
        },
      },
      {
        id: "s2_d",
        text: "Wait a bit longer — pushing too hard might damage the relationship",
        featureSignals: {
          primary: { feature: "locus_of_control", value: 0.2 },
          secondary: { feature: "resilience_score", value: 0.3 },
        },
      },
    ],
  },

  {
    id: "scenario_s3",
    section: "B",
    type: "scenario",
    question:
      "You receive Rs. 8,000 unexpectedly — a client paid an overdue invoice you had nearly written off. You have no urgent debts. What do you do with it?",
    isRiskQuestion: false,
    isTrap: false,
    options: [
      {
        id: "s3_a",
        text: "Keep it in cash — you never know when an emergency will come",
        featureSignals: {
          primary: { feature: "future_orientation", value: 0.5 },
          secondary: { feature: "loss_aversion_score", value: 0.7 },
        },
      },
      {
        id: "s3_b",
        text: "Put most of it into savings or a small investment, keep a small buffer",
        featureSignals: {
          primary: { feature: "future_orientation", value: 1.0 },
          secondary: { feature: "conscientiousness_score", value: 0.9 },
        },
      },
      {
        id: "s3_c",
        text: "Use it to clear a small debt early even though it's not overdue yet",
        featureSignals: {
          primary: { feature: "conscientiousness_score", value: 1.0 },
          secondary: { feature: "future_orientation", value: 0.8 },
        },
      },
      {
        id: "s3_d",
        text: "Treat myself and the family — this kind of windfall is rare",
        featureSignals: {
          primary: { feature: "future_orientation", value: 0.1 },
          secondary: { feature: "conscientiousness_score", value: 0.2 },
        },
      },
    ],
  },

  {
    id: "scenario_s4",
    section: "B",
    type: "scenario",
    question:
      "Your small business has been losing Rs. 1,500 a month for 4 months. You've tried adjustments, but the trend hasn't reversed yet.",
    isRiskQuestion: false,
    isTrap: false,
    options: [
      {
        id: "s4_a",
        text: "Close it now and cut further losses — it's better to preserve what's left",
        featureSignals: {
          primary: { feature: "loss_aversion_score", value: 0.3 },
          secondary: { feature: "resilience_score", value: 0.4 },
        },
      },
      {
        id: "s4_b",
        text: "Give it a fixed window — say 2 more months — with a clear decision point",
        featureSignals: {
          primary: { feature: "resilience_score", value: 0.9 },
          secondary: { feature: "conscientiousness_score", value: 0.9 },
        },
      },
      {
        id: "s4_c",
        text: "Double down with more investment — I believe this can turn around",
        featureSignals: {
          primary: { feature: "future_orientation", value: 0.6 },
          secondary: { feature: "loss_aversion_score", value: 0.1 },
        },
      },
      {
        id: "s4_d",
        text: "Pivot the business model rather than closing or investing more",
        featureSignals: {
          primary: { feature: "resilience_score", value: 1.0 },
          secondary: { feature: "locus_of_control", value: 0.9 },
        },
      },
    ],
  },

  {
    id: "scenario_s5",
    section: "B",
    type: "scenario",
    question:
      "A neighbour you know reasonably well asks if you can lend them Rs. 3,000. You have it, but it's your emergency buffer. They say they'll return it in two weeks.",
    isRiskQuestion: false,
    isTrap: false,
    options: [
      {
        id: "s5_a",
        text: "Lend it — relationships matter and two weeks isn't long",
        featureSignals: {
          primary: { feature: "social_capital_score", value: 0.9 },
          secondary: { feature: "reciprocity_norm", value: 1.0 },
        },
      },
      {
        id: "s5_b",
        text: "Offer a smaller amount I can genuinely afford to lose",
        featureSignals: {
          primary: { feature: "honesty_score", value: 0.9 },
          secondary: { feature: "social_capital_score", value: 0.7 },
        },
      },
      {
        id: "s5_c",
        text: "Say I don't have it right now — I can't risk my emergency buffer",
        featureSignals: {
          primary: { feature: "conscientiousness_score", value: 0.8 },
          secondary: { feature: "honesty_score", value: 0.6 },
        },
      },
      {
        id: "s5_d",
        text: "Ask what the money is for before deciding",
        featureSignals: {
          primary: { feature: "honesty_score", value: 1.0 },
          secondary: { feature: "locus_of_control", value: 0.8 },
        },
      },
    ],
  },

  // Honesty trap: embedded naturally among scenarios — not in a labeled section
  {
    id: "honesty_trap_q1",
    section: "B",
    type: "likert",
    question: "I have never told even a small lie in my entire life.",
    scale: ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"],
    isRiskQuestion: false,
    isTrap: true,
  },

  {
    id: "scenario_s6",
    section: "B",
    type: "scenario",
    question:
      "Your family expects you to contribute Rs. 15,000 to a wedding celebration. Doing so would mean pausing your planned savings for 2 months.",
    isRiskQuestion: false,
    isTrap: false,
    options: [
      {
        id: "s6_a",
        text: "Contribute what they're expecting — family obligations come first",
        featureSignals: {
          primary: { feature: "locus_of_control", value: 0.2 },
          secondary: { feature: "future_orientation", value: 0.3 },
        },
      },
      {
        id: "s6_b",
        text: "Contribute a smaller amount I can genuinely afford without breaking my plan",
        featureSignals: {
          primary: { feature: "conscientiousness_score", value: 0.9 },
          secondary: { feature: "locus_of_control", value: 0.7 },
        },
      },
      {
        id: "s6_c",
        text: "Have an honest conversation with the family about my current financial situation",
        featureSignals: {
          primary: { feature: "honesty_score", value: 1.0 },
          secondary: { feature: "locus_of_control", value: 0.9 },
        },
      },
      {
        id: "s6_d",
        text: "Stick to my savings plan — I can't let social expectations derail my finances",
        featureSignals: {
          primary: { feature: "locus_of_control", value: 1.0 },
          secondary: { feature: "future_orientation", value: 0.9 },
        },
      },
    ],
  },

  // S8 — CONSISTENCY TRAP: mirrors S1 (EMI vs. opportunity).
  // Reframed with different context and amounts. Cross-check divergence
  // vs. S1 response generates scenario_consistency_score in backend.
  {
    id: "scenario_s8",
    section: "B",
    type: "scenario",
    question:
      "You hear about a 2-day flash sale from your supplier — 12% off on an order that could keep you stocked for 3 months. But your account is tight and you'd have little left for unexpected costs.",
    hint: "There's no right or wrong answer — choose what genuinely feels most like you.",
    isRiskQuestion: false,
    isTrap: true, // marks it as a consistency check, not displayed to user
    consistencyPair: "scenario_s1",
    options: [
      {
        id: "s8_a",
        text: "Go for it — the savings are real and the math makes sense",
        featureSignals: {
          primary: { feature: "future_orientation", value: 0.7 },
          secondary: { feature: "conscientiousness_score", value: 0.3 },
        },
        // mirrors s1_a
        consistencyMatch: "s1_a",
      },
      {
        id: "s8_b",
        text: "Hold off — I never buy when my buffer is this low",
        featureSignals: {
          primary: { feature: "conscientiousness_score", value: 1.0 },
          secondary: { feature: "future_orientation", value: 0.5 },
        },
        // mirrors s1_b
        consistencyMatch: "s1_b",
      },
      {
        id: "s8_c",
        text: "Buy a smaller portion of the order, keeping a meaningful buffer",
        featureSignals: {
          primary: { feature: "conscientiousness_score", value: 0.8 },
          secondary: { feature: "future_orientation", value: 0.8 },
        },
        // mirrors s1_c
        consistencyMatch: "s1_c",
      },
      {
        id: "s8_d",
        text: "See if someone can front the money while I repay them within the week",
        featureSignals: {
          primary: { feature: "social_capital_score", value: 0.8 },
          secondary: { feature: "conscientiousness_score", value: 0.6 },
        },
        // mirrors s1_d
        consistencyMatch: "s1_d",
      },
    ],
  },

  // ---------------------------------------------------------------------------
  // SECTION C — Open Text (1 question)
  // NLP pipeline: sentiment, agency, problem-solving, embeddings
  // ---------------------------------------------------------------------------

  {
    id: "q27_resilience_text",
    section: "C",
    type: "text",
    question:
      "Tell us about a time your finances were under real pressure — what happened, and how did you handle it?",
    hint: "Write 2–5 sentences. Be specific about what you did, not just how you felt.",
    minWords: 10,
    maxLength: 1000,
    isRiskQuestion: false,
    isTrap: false,
  },
];

// ---------------------------------------------------------------------------
// Constants and helpers
// ---------------------------------------------------------------------------

export const CORE_QUESTION_COUNT = QUESTIONS.length;

export function getSectionById(sectionId) {
  return SECTIONS.find((section) => section.id === sectionId);
}

export function getSectionQuestions(sectionId) {
  return QUESTIONS.filter((question) => question.section === sectionId);
}

/** Returns true if a question uses the scenario interaction type. */
export function isScenarioQuestion(question) {
  return question.type === "scenario";
}

/** Returns the consistency pair question ID for a given scenario, if any. */
export function getConsistencyPair(questionId) {
  const question = QUESTIONS.find((q) => q.id === questionId);
  return question?.consistencyPair ?? null;
}
