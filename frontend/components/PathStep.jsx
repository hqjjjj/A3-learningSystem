import React from 'react';

const PathStep = ({ name, status, isCurrent, onClick }) => {
  const statusColor = {
    completed: '#2ecc71',
    current: '#3498db',
    pending: '#bdc3c7'
  };

  return (
    <div
      onClick={onClick}
      style={{
        padding: '8px 16px',
        borderRadius: 20,
        background: isCurrent ? '#3498db' : statusColor[status] || '#bdc3c7',
        color: isCurrent || status === 'completed' ? '#fff' : '#333',
        cursor: 'pointer',
        display: 'inline-block',
        margin: 4
      }}
    >
      {name}
      {isCurrent && <span style={{ marginLeft: 8, fontSize: 12 }}>● 当前</span>}
    </div>
  );
};

export default PathStep;