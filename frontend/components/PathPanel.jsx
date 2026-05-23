
// PathPanel 接收：
//   - learningPath (object, 必填)
//     topic (string, 必填)

import React from 'react';
import CurrentTopicBadge from './CurrentTopicBadge';
import PathStep from './PathStep';

const PathPanel = ({ learningPath }) => {
  if (!learningPath || !learningPath.topic) {
    return <div>暂无路径数据</div>;
  }

  return (
    <div>
      <h3>学习路径</h3>
      <CurrentTopicBadge topic={learningPath.topic} />
      <div style={{ marginTop: 16 }}>
        <PathStep name={learningPath.current || learningPath.topic} status="current" isCurrent />
        {learningPath.next && (
          <PathStep name={learningPath.next} status="pending" />
        )}
      </div>
    </div>
  );
};

export default PathPanel;