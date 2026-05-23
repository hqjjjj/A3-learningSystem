
// PathPanel 接收：
//   - learningPath (object, 必填)
//     topic (string, 必填)

import React from 'react';

const PathPanel = ({ learningPath }) => {
  if (!learningPath || !learningPath.topic) {
    return <div>暂无路径数据</div>;
  }

  return (
    <div>
      <h3>学习路径</h3>
      <p>当前知识点：{learningPath.topic}</p>
    </div>
  );
};

export default PathPanel;