
import React, { useState, useEffect } from 'react';

const ShortQuestion = ({ question, onSubmit, resetTrigger }) => {
  const [answer, setAnswer] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [startTime] = useState(Date.now());

  useEffect(() => {
    setAnswer('');
    setSubmitted(false);
  }, [resetTrigger]);

  const handleSubmit = () => {
    if (!answer.trim()) return;

    const duration = Math.floor((Date.now() - startTime) / 1000);
    
    setSubmitted(true);
    onSubmit(-1, duration);
  };

  return (
    <div style={{ border: '1px solid #E2E8F0', borderRadius: 10, padding: 20 }}>
      <h4 style={{ margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600, color: '#1E293B' }}>
        {question.text}
      </h4>
      <textarea
        style={{
          width: '100%',
          padding: '12px',
          border: '1px solid #d1d5db',
          borderRadius: '8px',
          fontSize: '14px',
          fontFamily: 'inherit',
          resize: 'vertical',
          marginBottom: '16px',
          boxSizing: 'border-box',
          background: '#fff'
        }}
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        placeholder="输入你的答案..."
        rows={4}
        disabled={submitted}
      />
      {!submitted && (
        <button
          style={{
            padding: '8px 16px',
            background: answer.trim() ? '#3b82f6' : '#9ca3af',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: answer.trim() ? 'pointer' : 'not-allowed'
          }}
          onClick={handleSubmit}
          disabled={!answer.trim()}
        >
          提交答案
        </button>
      )}
      {submitted && question.correctAnswer && (
        <div style={{
          marginTop: '16px',
          padding: '12px',
          background: '#f0fdf4',
          borderRadius: '8px',
          borderLeft: '4px solid #22c55e'
        }}>
          <strong style={{ fontSize: '13px', color: '#166534' }}> 参考答案：</strong>
          <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: '#374151', lineHeight: 1.5 }}>
            {question.correctAnswer}
          </p >
        </div>
      )}
    </div>
  );
};

export default ShortQuestion;