import React from 'react';

const WeakPointList = ({ weakPoints }) => {
  if (!weakPoints || weakPoints.length === 0) {
    return <p>暂无薄弱知识点</p>;
  }

  return (
    <div>
      <h4>薄弱知识点</h4>
      <ul>
        {weakPoints.map((point, index) => (
          <li key={index} style={{ color: '#e74c3c' }}>{point}</li>
        ))}
      </ul>
    </div>
  );
};

export default WeakPointList;