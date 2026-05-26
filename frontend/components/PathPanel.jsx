import React from 'react';
import PathStep from './PathStep';

const PathPanel = ({ learningPath, topic, onTopicChange }) => {
  if (!learningPath || learningPath.length === 0) {
    return <div>暂无路径数据</div>;
  }

  const currentIndex = learningPath.indexOf(topic);

  const handleClick = (name) => {
    if (window.confirm(`是否学习“${name}”？`)) {
      onTopicChange(name);
    }
  };

  return (
    <div>
      <h3>学习路径</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', marginTop: 16 }}>
        {learningPath.map((name, index) => (
          <PathStep
            key={index}
            name={name}
            status={index === currentIndex ? 'current' : 'pending'}
            isCurrent={index === currentIndex}
            onClick={() => handleClick(name)}
          />
        ))}
      </div>
    </div>
  );
};

export default PathPanel;