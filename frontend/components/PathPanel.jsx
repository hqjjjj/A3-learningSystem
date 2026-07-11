import React from 'react';
import PathStep from './PathStep';

const PathPanel = ({ learningPath, topic, onTopicChange }) => {
  // 如果 learningPath 是空数组或不存在，显示暂无路径数据
  if (!learningPath || learningPath.length === 0) {
    return <div>暂无路径数据</div>;
  }

  // 找到当前主题在 learningPath 中的索引
  const currentIndex = learningPath.findIndex(item => item.name === topic);

  // 处理点击事件
  const handleClick = (name) => {
    if (window.confirm(`是否学习"${name}"？`)) {
      onTopicChange(name);
    }
  };

  return (
    <div>
      <h3>学习路径</h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', marginTop: 16 }}>
        {learningPath.map((item, index) => (
          <PathStep
            key={item.id || index}  // 使用 item.id 作为 key，如果没有则用 index
            name={item.name}  // 使用 item.name
            status={index === currentIndex ? 'current' : 'pending'}
            isCurrent={index === currentIndex}
            onClick={() => handleClick(item.name)}  // 传递 item.name
          />
        ))}
      </div>
    </div>
  );
};

export default PathPanel;
