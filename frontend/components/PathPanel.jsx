// PathPanel.jsx
import React from 'react';
import PathStep from './PathStep';

// PathPanel.jsx
const PathPanel = ({ learningPath, topic, onTopicChange }) => {
  if (!learningPath) {
    return <div>加载中...</div>;
  }
  
  //  兼容两种字段名
  const pathList = learningPath.path_list || learningPath.learning_path || [];
  
  if (!pathList || pathList.length === 0) {
    return <div>暂无路径数据</div>;
  }

  const currentIndex = pathList.findIndex(item => item.name === topic);

  const handleClick = (name) => {
    if (window.confirm(`是否学习"${name}"？`)) {
      onTopicChange(name);
    }
  };

  return (
    <div>
      <h3>当前主题: {learningPath.current || '无'}</h3>
      <h3>下一个主题: {learningPath.next || '无'}</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', marginTop: 16 }}>
        {pathList.map((item, index) => (
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
