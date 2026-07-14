import React from 'react';
import WeakPointList from './WeakPointList';
import KnowledgeChart from './KnowledgeChart';

const ProfilePanel = ({ profile }) => {
  if (!profile || Object.keys(profile).length === 0) {
    return (
      <div style={{
        padding: '20px',
        border: '1px solid #E2E8F0',
        borderRadius: 10,
        color: '#64748b',
        fontSize: 14
      }}>
        暂无画像数据
      </div>
    );
  }

  return (
    <div style={{
      border: '1px solid #E2E8F0',
      borderRadius: 10,
      padding: '20px'
    }}>
      <h3 style={{
        fontSize: 18,
        fontWeight: 600,
        margin: '0 0 8px 0',
        color: '#1E293B'
      }}>用户画像</h3>

      <p style={{
        fontSize: 14,
        margin: '0 0 8px 0',
        color: '#334155'
      }}>学习风格：{profile.learning_style || '未知'}</p >
      <p style={{
        fontSize: 14,
        margin: '0 0 8px 0',
        color: '#334155'
      }}>学习节奏：{profile.learning_pace || '未知'}</p >

      <WeakPointList weakPoints={profile.weak_points} />

      <div style={{
        height: 1,
        background: '#E2E8F0',
        margin: '20px 0'
      }} />

      <KnowledgeChart knowledgeLevel={profile.knowledge_level} />
    </div>
  );
};

export default ProfilePanel;