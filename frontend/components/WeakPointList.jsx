import React from 'react';

const WeakPointList = ({ weakPoints }) => {
  if (!weakPoints || weakPoints.length === 0) {
    return <p style={{ color: '#64748b', fontSize: 14 }}>暂无薄弱知识点</p >;
  }

  return (
    <div style={{ marginTop: 8 }}>
      <h4 style={{ fontSize: 16, fontWeight: 600, margin: '0 0 8px 0', color: '#1e293b' }}>薄弱知识点</h4>
      <ul style={{ paddingLeft: 0, margin: 0, listStyle: 'none' }}>
        {weakPoints.map((point, index) => (
          <li 
            key={index} 
            style={{ 
              color: '#e74c3c',
              fontSize: 14,
              fontWeight: 400,
              marginBottom: 4,
              padding: '4px 12px',
              border: '1px solid #fecdd3',
              borderRadius: 8,
              background: '#fef2f2'
            }}
          >
            {point}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default WeakPointList;