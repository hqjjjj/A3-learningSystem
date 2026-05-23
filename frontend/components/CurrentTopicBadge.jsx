import React from 'react';

const CurrentTopicBadge = ({ topic }) => {
  if (!topic) {
    return null;
  }

  return (
    <div
      style={{
        display: 'inline-block',
        padding: '6px 16px',
        borderRadius: 16,
        background: '#3498db',
        color: '#fff',
        fontWeight: 'bold',
        fontSize: 14
      }}
    >
      正在学习：{topic}
    </div>
  );
};

export default CurrentTopicBadge;