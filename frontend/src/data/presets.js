export const PRESET_PROFILES = [
  {
    id: "strong",
    name: "High Literacy / Strong Applicant",
    description: "Accurate math/financial literacy, patient time-preferences, consistent choices, and high deliberation.",
    answers: {
      numeracy_q1: 6600,
      numeracy_q2: 1120,
      financial_literacy_q1: 1,
      CRT_q1: 5,
      CRT_q2: 47,
      scenario_s1: "s1_a",
      scenario_s2: "s2_b",
      scenario_s3: "s3_c",
      scenario_s4: "s4_a",
      scenario_s5: "s5_b",
      scenario_s6: "s6_a",
      honesty_trap_q1: 2,
      scenario_s8: "s8_a",
      open_response_text: "During a sudden business inventory crisis, we lost key supply contacts. I immediately drafted a contingency budget, cut discretionary overhead, and built direct relations with two local distributors. We recovered operations in three weeks and kept all payments fully on time."
    },
    behavioral: {
      avg_response_time_ms: 4800.0,
      answer_change_rate: 0.037,
      session_duration_sec: 195.0,
      dropout_count: 0,
      scroll_hesitation_score: 0.037,
      risk_response_speed_ratio: 0.92,
      time_of_day: "afternoon",
      device_type: "desktop",
      typing_speed_wpm: 68.0
    }
  },
  {
    id: "average",
    name: "Average Applicant",
    description: "Standard financial skills, moderate patience, mixed math scores, normal response speed.",
    answers: {
      numeracy_q1: 6600,
      numeracy_q2: 1120,
      financial_literacy_q1: 1,
      CRT_q1: 10,
      CRT_q2: 24,
      scenario_s1: "s1_c",
      scenario_s2: "s2_c",
      scenario_s3: "s3_b",
      scenario_s4: "s4_b",
      scenario_s5: "s5_c",
      scenario_s6: "s6_b",
      honesty_trap_q1: 3,
      scenario_s8: "s8_c",
      open_response_text: "I had a sudden emergency when my laptop broke and I needed it for client projects. I was able to borrow some money from my family to buy a replacement and then worked extra hours the next month to repay them fully."
    },
    behavioral: {
      avg_response_time_ms: 3200.0,
      answer_change_rate: 0.111,
      session_duration_sec: 220.0,
      dropout_count: 1,
      scroll_hesitation_score: 0.148,
      risk_response_speed_ratio: 1.05,
      time_of_day: "morning",
      device_type: "tablet",
      typing_speed_wpm: 42.0
    }
  },
  {
    id: "hesitant",
    name: "Hesitant Applicant",
    description: "Highly uncertain responder. Frequently changes choices and hovers back and forth.",
    answers: {
      numeracy_q1: 6600,
      numeracy_q2: 1120,
      financial_literacy_q1: 1,
      CRT_q1: 5,
      CRT_q2: 47,
      scenario_s1: "s1_c",
      scenario_s2: "s2_a",
      scenario_s3: "s3_a",
      scenario_s4: "s4_c",
      scenario_s5: "s5_d",
      scenario_s6: "s6_c",
      honesty_trap_q1: 2,
      scenario_s8: "s8_c",
      open_response_text: "Our small team experienced a major client churn event last winter. We debated whether to take emergency debt or defer wages. I spent a long time reviewing operational metrics and renegotiating lease delays. We successfully re-stabilized."
    },
    behavioral: {
      avg_response_time_ms: 9500.0,
      answer_change_rate: 0.444,
      session_duration_sec: 480.0,
      dropout_count: 3,
      scroll_hesitation_score: 0.592,
      risk_response_speed_ratio: 2.15,
      time_of_day: "night",
      device_type: "mobile",
      typing_speed_wpm: 24.0
    }
  },
  {
    id: "manipulated",
    name: "Manipulated / Inconsistent Applicant",
    description: "Flags honesty traps and fails repeat consistency audits. Extremely fast timing.",
    answers: {
      numeracy_q1: 6600,
      numeracy_q2: 1120,
      financial_literacy_q1: 1,
      CRT_q1: 5,
      CRT_q2: 47,
      scenario_s1: "s1_a",
      scenario_s2: "s2_a",
      scenario_s3: "s3_a",
      scenario_s4: "s4_a",
      scenario_s5: "s5_a",
      scenario_s6: "s6_a",
      honesty_trap_q1: 5, 
      scenario_s8: "s8_b", // Inconsistent with S1
      open_response_text: "Everything was perfectly fine and we had no difficulties. I handled it instantly because my finances are perfect and I am the best loan candidate ever."
    },
    behavioral: {
      avg_response_time_ms: 1800.0,
      answer_change_rate: 0.0,
      session_duration_sec: 75.0,
      dropout_count: 0,
      scroll_hesitation_score: 0.0,
      risk_response_speed_ratio: 1.0,
      time_of_day: "night",
      device_type: "desktop",
      typing_speed_wpm: 92.0
    }
  },
  {
    id: "impulsive",
    name: "Impulsive Fast Responder",
    description: "Answering randomly in under a second. High math error rates, short text block.",
    answers: {
      numeracy_q1: 6000,
      numeracy_q2: 100,
      financial_literacy_q1: 0,
      CRT_q1: 100,
      CRT_q2: 10,
      scenario_s1: "s1_d",
      scenario_s2: "s2_d",
      scenario_s3: "s3_d",
      scenario_s4: "s4_d",
      scenario_s5: "s5_a",
      scenario_s6: "s6_d",
      honesty_trap_q1: 3,
      scenario_s8: "s8_d",
      open_response_text: "I had a crisis and solved it. Standard situation."
    },
    behavioral: {
      avg_response_time_ms: 550.0,
      answer_change_rate: 0.0,
      session_duration_sec: 22.0,
      dropout_count: 0,
      scroll_hesitation_score: 0.0,
      risk_response_speed_ratio: 1.0,
      time_of_day: "morning",
      device_type: "mobile",
      typing_speed_wpm: 15.0
    }
  },
  {
    id: "thoughtful",
    name: "Thoughtful Stable Applicant",
    description: "Highly deliberate responder. Very low error rates, steady timing, complete responses.",
    answers: {
      numeracy_q1: 6600,
      numeracy_q2: 1120,
      financial_literacy_q1: 1,
      CRT_q1: 5,
      CRT_q2: 47,
      scenario_s1: "s1_a",
      scenario_s2: "s2_b",
      scenario_s3: "s3_c",
      scenario_s4: "s4_a",
      scenario_s5: "s5_b",
      scenario_s6: "s6_a",
      honesty_trap_q1: 2,
      scenario_s8: "s8_a",
      open_response_text: "We faced a significant agricultural price decline during harvest season. I analyzed price variations, renegotiated store inventory terms with key suppliers, and held key grains for better trade prices. The strategy paid off within two months."
    },
    behavioral: {
      avg_response_time_ms: 5300.0,
      answer_change_rate: 0.018,
      session_duration_sec: 210.0,
      dropout_count: 0,
      scroll_hesitation_score: 0.037,
      risk_response_speed_ratio: 0.98,
      time_of_day: "morning",
      device_type: "desktop",
      typing_speed_wpm: 56.0
    }
  }
];
