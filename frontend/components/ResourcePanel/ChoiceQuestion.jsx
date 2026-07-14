import React, { useState, useEffect } from 'react';

const ChoiceQuestion = ({ question, onSubmit, resetTrigger }) => {
  const [selectedOption, setSelectedOption] = useState(null);
  const [submitted, setSubmitted] = useState(false);
  const [startTime] = useState(Date.now());
  const [showAnswer, setShowAnswer] = useState(false);

  useEffect(() => {
    setSelectedOption(null);
    setSubmitted(false);
    setShowAnswer(false);
  }, [resetTrigger]);

  const handleSubmit = () => {
    if (selectedOption === null) return;
    const duration = Math.floor((Date.now() - startTime) / 1000);
    const isCorrect = (selectedOption === (question.answer || question.correctAnswer));
    const correctRate = isCorrect ? 1.0 : 0.0;
    setSubmitted(true);
    setShowAnswer(true);
    onSubmit(correctRate, duration);
  };

  return (
    <div style={{ border: '1px solid #E2E8F0', borderRadius: 10, padding: 20 }}>
      <h4 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600, color: '#1E293B' }}>
        {question.text || question.question}
      </h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '16px' }}>
        {question.options?.map((opt, idx) => {
          const correctAnswer = question.answer || question.correctAnswer;
          let optionStyle = {};
          let statusText = null;
          
          if (showAnswer) {
            if (opt === correctAnswer) {
              optionStyle = { background: '#d4edda', border: '2px solid #28a745' };
              statusText = <span style={{ marginLeft: '8px', color: '#28a745', fontWeight: 'bold' }}>✓ 正确答案</span>;
            } else if (opt === selectedOption && opt !== correctAnswer) {
              optionStyle = { background: '#f8d7da', border: '2px solid #dc3545' };
              statusText = <span style={{ marginLeft: '8px', color: '#dc3545' }}>✗</span>;
            }
          }
          
          return (
            <label key={idx} style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '8px', 
              cursor: submitted ? 'default' : 'pointer',
              padding: '8px 12px',
              borderRadius: '6px',
              border: '1px solid #E2E8F0',
              background: '#fff',
              ...optionStyle
            }}>
              <input
                type="radio"
                name="choice"
                value={opt}
                checked={selectedOption === opt}
                onChange={() => setSelectedOption(opt)}
                disabled={submitted}
              />
              <span style={{ fontSize: '14px' }}>{opt}</span>
              {statusText}
            </label>
          );
        })}
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
      {showAnswer && question.analysis && (
        <div style={{ 
          marginTop: '12px', 
          padding: '12px', 
          background: '#f8fafc', 
          borderRadius: '6px',
          border: '1px solid #E2E8F0',
          borderLeft: '4px solid #3b82f6'
        }}>
          <p style={{ margin: 0, fontSize: '14px', color: '#333' }}>
            <strong>解析：</strong> {question.analysis}
          </p >
        </div>
      )}
    </div>
  );
};

export default ChoiceQuestion;