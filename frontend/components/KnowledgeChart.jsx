import React from 'react';

const RadarChart = ({ knowledgeLevel }) => {
  if (!knowledgeLevel || Object.keys(knowledgeLevel).length === 0) {
    return <p>暂无知识掌握数据</p >;
  }

  const topics = Object.keys(knowledgeLevel);
  const maxScore = 1;

  return (
    <div>
      <h4>知识点掌握度</h4>
      {topics.map((topic) => (
        <div 
          key={topic} 
          style={{ 
            marginBottom: 2, 
            border: '1px solid #E2E8F0',
            borderRadius: 8,
            padding: '10px 12px'
          }}
        >
          {/* 文字和百分比同一行左右分布 */}
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
            <span style={{ fontSize:14,fontWeight: 450 }}>{topic}</span>
            <span style={{ fontSize: 12 }}>{(knowledgeLevel[topic] * 100).toFixed(0)}%</span>
          </div>
          {/* 进度条保持单独一行在下方 */}
          <div style={{ width: '100%', background: '#eee', height: 8, borderRadius: 8, marginTop: 4 }}>
            <div
              style={{
                width: `${(knowledgeLevel[topic] / maxScore) * 100}%`,
                height: '100%',
                background: knowledgeLevel[topic] >= 0.7 ? '#3b82f6' : knowledgeLevel[topic] >= 0.4 ? '#f39c12' : '#e74c3c',
                borderRadius: 8
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

export default RadarChart;