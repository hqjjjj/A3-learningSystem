import React, { useState } from 'react';

const ShortQuestion = ({ question, onSubmit }) => {
  const [answer, setAnswer] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = () => {
    if (!answer.trim()) return;
    setSubmitted(true);
    onSubmit(answer);
  };

  return (
    <div>
      <h4 style={{ margin: '0 0 12px 0', fontSize: '16px' }}>{question.text}</h4>
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
          boxSizing: 'border-box'
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
    </div>
  );
};

export default ShortQuestion;