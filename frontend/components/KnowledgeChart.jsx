import React from 'react';

const RadarChart = ({ knowledgeLevel }) => {
  if (!knowledgeLevel || Object.keys(knowledgeLevel).length === 0) {
    return <p>暂无知识掌握数据</p>;
  }

  const topics = Object.keys(knowledgeLevel);
  const maxScore = 1;

  return (
    <div>
      <h4>知识点掌握度</h4>
      {topics.map((topic) => (
        <div key={topic} style={{ marginBottom: 8 }}>
          <span>{topic}</span>
          <div style={{ background: '#eee', height: 16, borderRadius: 8, marginTop: 4 }}>
            <div
              style={{
                width: `${(knowledgeLevel[topic] / maxScore) * 100}%`,
                height: '100%',
                background: knowledgeLevel[topic] >= 0.7 ? '#2ecc71' : knowledgeLevel[topic] >= 0.4 ? '#f39c12' : '#e74c3c',
                borderRadius: 8
              }}
            />
          </div>
          <span style={{ fontSize: 12 }}>{(knowledgeLevel[topic] * 100).toFixed(0)}%</span>
        </div>
      ))}
    </div>
  );
};

export default RadarChart;