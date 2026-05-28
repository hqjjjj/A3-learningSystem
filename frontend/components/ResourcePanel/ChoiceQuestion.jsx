
import React, { useState, useEffect } from 'react';  // ← 新增 useEffect

const ChoiceQuestion = ({ question, onSubmit, resetTrigger }) => {  // ← 新增 resetTrigger 参数
  const [selectedOption, setSelectedOption] = useState(null);
  const [submitted, setSubmitted] = useState(false);
  const [startTime] = useState(Date.now());

  // ← 新增：监听重置触发器
  useEffect(() => {
    setSelectedOption(null);
    setSubmitted(false);
  }, [resetTrigger]);

  const handleSubmit = () => {
    if (selectedOption === null) return;
    
    const duration = Math.floor((Date.now() - startTime) / 1000);
    const isCorrect = (selectedOption === question.correctAnswer);
    const correctRate = isCorrect ? 1.0 : 0.0;
    
    setSubmitted(true);
    onSubmit({
      user_answer: selectedOption,
      correct_rate: correctRate,
      duration: duration,
      resource_type: question.type || 'choice'
    });
  };

  return (
    <div>
      <h4 style={{ margin: '0 0 12px 0', fontSize: '16px' }}>{question.text}</h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
        {question.options?.map((opt, idx) => (
          <label key={idx} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="radio"
              name="choice"
              value={opt}
              checked={selectedOption === opt}
              onChange={() => setSelectedOption(opt)}
              disabled={submitted}
            />
            <span style={{ fontSize: '14px' }}>{opt}</span>
          </label>
        ))}
      </div>
      {!submitted && (
        <button
          style={{
            padding: '8px 16px',
            background: selectedOption ? '#3b82f6' : '#9ca3af',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: selectedOption ? 'pointer' : 'not-allowed'
          }}
          onClick={handleSubmit}
          disabled={!selectedOption}
        >
          提交答案
        </button>
      )}
    </div>
  );
};

export default ChoiceQuestion;