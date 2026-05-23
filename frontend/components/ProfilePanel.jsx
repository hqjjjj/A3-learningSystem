// ProfilePanel
// props:

// profile (object, 必填)

// 字段参考 appState.profile

import React from 'react';

const ProfilePanel = ({ profile }) => {
  return (
    <div>
      <h3>用户画像</h3>
      
      {profile && Object.keys(profile).length > 0 ? (
        <>
          <p>学习风格：{profile.learning_style || '未知'}</p>
          <p>学习节奏：{profile.learning_pace || '未知'}</p>
          
          <h4>薄弱知识点</h4>
          {profile.weak_points && profile.weak_points.length > 0 ? (
            <ul>
              {profile.weak_points.map((point, index) => (
                <li key={index}>{point}</li>
              ))}
            </ul>
          ) : (
            <p>暂无薄弱点</p>
          )}
        </>
      ) : (
        <p>暂无画像数据</p>
      )}
    </div>
  );
};

export default ProfilePanel;