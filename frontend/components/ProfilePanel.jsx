// ProfilePanel
// props:

// profile (object, 必填)

// 字段参考 appState.profile

import React from 'react';
import WeakPointList from './WeakPointList';
import RadarChart from './RadarChart';

const ProfilePanel = ({ profile }) => {
  if (!profile || Object.keys(profile).length === 0) {
    return <div>暂无画像数据</div>;
  }

  return (
    <div>
      <h3>用户画像</h3>
      <p>学习风格：{profile.learning_style || '未知'}</p>
      <p>学习节奏：{profile.learning_pace || '未知'}</p>
      <WeakPointList weakPoints={profile.weak_points} />
      <RadarChart knowledgeLevel={profile.knowledge_level} />
    </div>
  );
};

export default ProfilePanel;