// PathPanel.jsx
import React from 'react';
import PathStep from './PathStep';

const PathPanel = ({ learningPath, topic, onTopicChange }) => {
  if (!learningPath) {
    return <div>加载中...</div>;
  }
  
  if (!learningPath.path_list || learningPath.path_list.length === 0) {
    return <div>暂无路径数据</div>;
  }

  // 找到当前主题在 path_list 中的索引
  const currentIndex = learningPath.path_list.findIndex(item => item.name === topic);

  // 处理点击事件
  const handleClick = (name) => {
    if (window.confirm(`是否学习"${name}"？`)) {
      onTopicChange(name);
    }
  };

  return (
    <div>
      <h3>当前主题: {learningPath.current}</h3>
      <h3>下一个主题: {learningPath.next}</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', marginTop: 16 }}>
        {learningPath.path_list.map((item, index) => (
          <PathStep
            key={item.id || index}
            name={item.name}
            status={index === currentIndex ? 'current' : 'pending'}
            isCurrent={index === currentIndex}
            onClick={() => handleClick(item.name)}
          />
        ))}
      </div>
    </div>
  );
};

export default PathPanel;
