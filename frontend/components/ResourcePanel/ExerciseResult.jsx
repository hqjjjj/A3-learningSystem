import React from 'react';

const ExerciseResult = ({ result, onRetry }) => {
  const isCorrect = result.correct;

  return (
    <div style={{
      textAlign: 'center',
      padding: '20px',
      border: '1px solid #E2E8F0',
      borderRadius: 10
    }}>
      <h4 style={{ margin: '0 0 8px 0', fontSize: '16px', fontWeight: 600, color: '#1E293B' }}>
        {isCorrect ? '回答正确！' : '回答错误'}
      </h4>
      <p style={{ margin: '0 0 16px 0', fontSize: '14px', color: '#6b7280' }}>
        {result.message || (isCorrect ? '恭喜你！' : '再试试看？')}
      </p >
      {result.explanation && (
        <div style={{
          textAlign: 'left',
          background: '#f8fafc',
          padding: '12px',
          borderRadius: '8px',
          marginBottom: '16px',
          fontSize: '13px',
          border: '1px solid #E2E8F0'
        }}>
          <strong>解析：</strong> {result.explanation}
        </div>
      )}
      <button
        style={{
          padding: '8px 16px',
          background: '#3b82f6',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer'
        }}
        onClick={onRetry}
      >
        重新答题
      </button>
    </div>
  );
};

export default ExerciseResult;