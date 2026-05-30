<<<<<<< HEAD
import React, { useState, useEffect } from "react";
const ShortQuestion = ({ question, onSubmit, resetTrigger }) => {  // ← 新增 resetTrigger 参数
  const [answer, setAnswer] = useState('');
  const [submitted, setSubmitted] = useState(false);

    // ← 新增：监听重置触发器
  useEffect(() => {
    setAnswer('');
    setSubmitted(false);
  }, [resetTrigger]);

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

=======

import React, { useState, useEffect } from 'react';  // ← 新增 useEffect

const ShortQuestion = ({ question, onSubmit, resetTrigger }) => {  // ← 新增 resetTrigger 参数
  const [answer, setAnswer] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [startTime] = useState(Date.now());

    // ← 新增：监听重置触发器
  useEffect(() => {
    setAnswer('');
    setSubmitted(false);
  }, [resetTrigger]);

  const handleSubmit = () => {
    if (!answer.trim()) return;
    
    const duration = Math.floor((Date.now() - startTime) / 1000);
    
    setSubmitted(true);
    onSubmit({
      user_answer: answer,
      correct_rate: -1,  // 简答题不自动评分
      duration: duration,
      resource_type: question.type || 'short',
      standard_answer: question.correctAnswer
    });
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
   
      {/* 提交后显示参考答案 */}
      {submitted && question.correctAnswer && (
        <div style={{
          marginTop: '16px',
          padding: '12px',
          background: '#f0fdf4',
          borderRadius: '8px',
          borderLeft: '4px solid #22c55e'
        }}>
          <strong style={{ fontSize: '13px', color: '#166534' }}>📖 参考答案：</strong>
          <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: '#374151', lineHeight: 1.5 }}>
            {question.correctAnswer}
          </p >
        </div>
      )}
    </div>
  );
};

>>>>>>> e25ecba6e7a658a2f0aa6abea1506f5c2b4d27e8
export default ShortQuestion;