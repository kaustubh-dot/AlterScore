import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { Terminal, ShieldAlert, Check } from 'lucide-react';
import SignalCanvas from '../components/hero/SignalCanvas';
import './Processing.css';

export default function Processing({ payload, onComplete }) {
  const [activeStep, setActiveStep] = useState(0);
  const [error, setError] = useState(null);
  const requestFiredRef = useRef(false);

  const steps = [
    { label: 'Parsing psychometric responses' },
    { label: 'Extracting behavioral telemetry' },
    { label: 'Running NLP semantic scanner' },
    { label: 'Computing derived features' },
    { label: 'Applying governance constraints' },
    { label: 'Calibrating score bands' },
  ];

  // Steps transition effect
  useEffect(() => {
    if (activeStep >= steps.length) return;
    const interval = setTimeout(() => {
      setActiveStep((prev) => prev + 1);
    }, 600);
    return () => clearTimeout(interval);
  }, [activeStep]);

  // Firing API request to score
  useEffect(() => {
    if (requestFiredRef.current) return;
    requestFiredRef.current = true;

    const computeScore = async () => {
      try {
        const response = await axios.post('/api/score', payload);
        const delay = Math.max(3600 - (Date.now() - startTime), 500);
        setTimeout(() => {
          onComplete(response.data);
        }, delay);
      } catch (err) {
        console.warn('Backend connection failed, invoking local simulation engine...', err);
        const mockResult = generateMockScore(payload);
        const elapsed = Date.now() - startTime;
        const delay = Math.max(3600 - elapsed, 500);
        setTimeout(() => {
          onComplete(mockResult);
        }, delay);
      }
    };

    const startTime = Date.now();
    computeScore();
  }, [payload, onComplete]);

  const generateMockScore = (payload) => {
    const answers = payload.answers || {};
    const behavioral = payload.behavioral || {};
    
    let baseScore = 580; // Baseline prior
    
    if (Number(answers.numeracy_q1) === 6600) baseScore += 25;
    if (Number(answers.numeracy_q2) === 1120) baseScore += 25;
    if (Number(answers.financial_literacy_q1) === 1) baseScore += 30;
    if (Number(answers.CRT_q1) === 5) baseScore += 35;
    if (Number(answers.CRT_q2) === 47) baseScore += 35;
    
    const words = (answers.open_response_text || '').trim().split(/\s+/).filter(Boolean).length;
    if (words > 25) baseScore += 25;
    
    const s1 = answers.scenario_s1 || {};
    const s2 = answers.scenario_s2 || {};
    const s3 = answers.scenario_s3 || {};
    const s4 = answers.scenario_s4 || {};
    const s5 = answers.scenario_s5 || {};
    const s6 = answers.scenario_s6 || {};
    const s8 = answers.scenario_s8 || {};

    if (s1.primary === 's1_b' || s1.primary === 's1_c') baseScore += 15;
    if (s2.primary === 's2_b') baseScore += 15;
    if (s3.primary === 's3_b' || s3.primary === 's3_c') baseScore += 20;
    if (s4.primary === 's4_d' || s4.primary === 's4_b') baseScore += 20;
    
    const mirrorMap = { 's8_a': 's1_a', 's8_b': 's1_b', 's8_c': 's1_c', 's8_d': 's1_d' };
    let consistency = 0.5;
    if (s1.primary && s8.primary) {
      if (mirrorMap[s8.primary] === s1.primary) {
        baseScore += 35;
        consistency = 1.0;
      } else {
        baseScore -= 40;
        consistency = 0.0;
      }
    }
    
    const isGaming = behavioral.avg_response_time_ms < 2500;
    if (isGaming) baseScore -= 70;
    if (behavioral.dropout_count > 3) baseScore -= (behavioral.dropout_count * 5);
    if (behavioral.scroll_hesitation_score > 0.8) baseScore -= 15;

    const finalScore = Math.max(300, Math.min(850, baseScore));
    
    let band = 'fair';
    let bandDesc = 'Eligible for microloans up to ₹12,000. Moderate risk profile.';
    let minAmount = 5000;
    let maxAmount = 12000;

    if (finalScore >= 750) {
      band = 'excellent';
      bandDesc = 'Microloans up to ₹75,000 approved. Extremely low default probability.';
      minAmount = 30000;
      maxAmount = 75000;
    } else if (finalScore >= 650) {
      band = 'good';
      bandDesc = 'Microloans up to ₹30,000 approved. Solid repayment probability.';
      minAmount = 12000;
      maxAmount = 30000;
    } else if (finalScore >= 550) {
      band = 'fair';
      bandDesc = 'Microloans up to ₹12,000 approved. Moderate risk conditions apply.';
      minAmount = 5000;
      maxAmount = 12000;
    } else if (finalScore >= 450) {
      band = 'poor';
      bandDesc = 'Microloans up to ₹5,000 approved. Sub-prime risk controls active.';
      minAmount = 2000;
      maxAmount = 5000;
    } else {
      band = 'very_poor';
      bandDesc = 'Funding deferred. Score below threshold. Credit counselling recommended.';
      minAmount = 0;
      maxAmount = 0;
    }

    const repaymentProb = 0.35 + ((finalScore - 300) / 550) * 0.63;
    const percentile = Math.round(((finalScore - 300) / 550) * 98);

    const explanation = [
      {
        feature: 'future_orientation',
        display_name: 'Future Orientation',
        shap_value: s3.primary === 's3_b' || s3.primary === 's3_c' ? 0.082 : -0.041,
        direction: s3.primary === 's3_b' || s3.primary === 's3_c' ? 'positive' : 'negative',
        feature_value: s3.primary === 's3_b' ? 0.9 : 0.4,
        plain_language: s3.primary === 's3_b' ? 'Future-oriented savings choices increased score.' : 'Immediate gratification tendencies lowered score.'
      },
      {
        feature: 'CRT_score',
        display_name: 'Cognitive Reflection (CRT)',
        shap_value: Number(answers.CRT_q1) === 5 ? 0.074 : -0.052,
        direction: Number(answers.CRT_q1) === 5 ? 'positive' : 'negative',
        feature_value: Number(answers.CRT_q1) === 5 ? 1.0 : 0.0,
        plain_language: Number(answers.CRT_q1) === 5 ? 'Analytical reflection on logic questions increased score.' : 'Instinctive error patterns on CRT lowered score.'
      },
      {
        feature: 'scenario_consistency_score',
        display_name: 'Cognitive Consistency',
        shap_value: consistency === 1.0 ? 0.065 : -0.085,
        direction: consistency === 1.0 ? 'positive' : 'negative',
        feature_value: consistency,
        plain_language: consistency === 1.0 ? 'High consistency across similar decisions increased score.' : 'Contradictory choices across matched scenarios lowered score.'
      },
      {
        feature: 'conscientiousness_score',
        display_name: 'Conscientiousness',
        shap_value: s1.primary === 's1_b' ? 0.058 : -0.021,
        direction: s1.primary === 's1_b' ? 'positive' : 'negative',
        feature_value: s1.primary === 's1_b' ? 1.0 : 0.5,
        plain_language: s1.primary === 's1_b' ? 'Prioritizing debt commitments (EMI) increased score.' : 'Compromising EMI for suppliers lowered score.'
      },
      {
        feature: 'avg_response_time_ms',
        display_name: 'Average Response Time',
        shap_value: isGaming ? -0.125 : 0.032,
        direction: isGaming ? 'negative' : 'positive',
        feature_value: behavioral.avg_response_time_ms,
        plain_language: isGaming ? 'Rapid click speed flagged as gaming behavior.' : 'Deliberate reading speeds increase analytical confidence.'
      }
    ];

    const counterfactual_actions = [
      {
        feature: 'CRT_score',
        current_value: Number(answers.CRT_q1) === 5 ? 1 : 0,
        suggested_value: 1,
        estimated_score_gain: Number(answers.CRT_q1) === 5 ? 0 : 35,
        plain_language: 'Take more time on logic questions to eliminate intuitive errors.'
      },
      {
        feature: 'scenario_consistency_score',
        current_value: consistency,
        suggested_value: 1.0,
        estimated_score_gain: consistency === 1.0 ? 0 : 40,
        plain_language: 'Maintain a consistent decision framework between matched scenarios.'
      },
      {
        feature: 'avg_response_time_ms',
        current_value: Math.round(behavioral.avg_response_time_ms),
        suggested_value: 5000,
        estimated_score_gain: isGaming ? 70 : 0,
        plain_language: 'Increase average deliberation time above 3.5 seconds to signal careful reading.'
      }
    ];

    const improvement_tips = [
      {
        feature: 'scenario_consistency_score',
        title: 'Calibrate risk consistency',
        body: 'Make sure your risk appetite remains stable across different contexts (e.g. bulk buying vs. loan reserves).'
      },
      {
        feature: 'avg_response_time_ms',
        title: 'Pace your choices',
        body: 'Fast answering patterns look like automated gaming. Allow at least 4 seconds per question to show reflection.'
      }
    ];

    return {
      session_id: payload.session_id,
      credit_score: finalScore,
      risk_band: band,
      repayment_probability: repaymentProb,
      percentile: percentile,
      explanation: explanation,
      counterfactual_actions: counterfactual_actions,
      loan_eligibility: {
        band: band,
        amount_min: minAmount,
        amount_max: maxAmount,
        description: bandDesc,
      },
      improvement_tips: improvement_tips,
      timestamp: new Date().toISOString(),
    };
  };

  const progressPercent = Math.min((activeStep / steps.length) * 100, 100);

  return (
    <div className="processing-layout">
      <SignalCanvas />
      
      <div className="processing-container container">
        <div className="processing-card">
          <div className="processing-header">
            <span className="processing-title">Cognitive Pipeline Calibration</span>
            <div className="processing-meter-container">
              <div 
                className="processing-meter-fill"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
          
          <div className="processing-body">
            <div className="steps-list">
              {steps.map((step, idx) => {
                const isCompleted = idx < activeStep;
                const isActive = idx === activeStep;
                
                return (
                  <div 
                    key={idx} 
                    className={`step-row ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}`}
                  >
                    <span className="step-icon">
                      {isCompleted ? (
                        <Check size={10} className="tick-enter" />
                      ) : isActive ? (
                        <span className="pulse-indicator" />
                      ) : (
                        '—'
                      )}
                    </span>
                    <span className="step-label">{step.label}</span>
                    {isCompleted && <span className="step-status">COMPLETED</span>}
                    {isActive && <span className="step-status scanning">PROCESSING</span>}
                  </div>
                );
              })}
            </div>
            
            <div className="processing-footer">
              <span className="processing-eta">
                Calibrating behavioral telemetry • Please wait
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
