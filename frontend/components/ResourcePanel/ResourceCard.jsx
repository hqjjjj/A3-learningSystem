import React, { useState, useEffect } from 'react';
import TextResource from './TextResource';
import MarkdownResource from './MarkdownResource';
import CodeBlock from './CodeBlock';
import ChoiceQuestion from './ChoiceQuestion';
import ShortQuestion from './ShortQuestion';
import ExerciseResult from './ExerciseResult';

const ResourceCard = ({ resource, onFinishResource, onSubmitAnswer, userId }) => {
  const [startTime] = useState(Date.now());
  const [showResult, setShowResult] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [resetTrigger, setResetTrigger] = useState(0);

  useEffect(() => {
    return () => {
      // 组件卸载时上报时长
      const duration = Math.floor((Date.now() - startTime) / 1000);
      if (onFinishResource && resource.id) {
        onFinishResource(resource.type, resource.topic, duration);
      }
    };
  }, [startTime, onFinishResource, resource.id]);

  const handleSubmitAnswer = async (answer) => {
    const result = await onSubmitAnswer({
      resource_id: resource.id,
      resource_type: resource.type,
      topic: resource.topic,
      ...answerData
    });
    setResultData(result);
    setShowResult(true);
  };

  // ← 新增：重试处理函数
  const handleRetry = () => {
    setShowResult(false);
    setResultData(null);
    setResetTrigger(prev => prev + 1);  // 递增触发器
  };
  
  const renderContent = () => {
        // ✅ 新增：动画类型
    if (resource.type === 'html' && resource.subtype === 'animation') {
      return (
        <div style={{
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          overflow: 'hidden',
          marginTop: '8px'
        }}>
          <div style={{
            padding: '8px 12px',
            background: '#f3f4f6',
            borderBottom: '1px solid #e5e7eb',
            fontSize: '13px',
            fontWeight: 500
          }}>
            🎬 {resource.title}
          </div>
          <iframe
            srcDoc={resource.html_content}
            title={resource.title}
            style={{
              width: '100%',
              height: '500px',
              border: 'none',
              backgroundColor: '#fff'
            }}
            sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
          />
          {resource.description && (
            <div style={{
              padding: '8px 12px',
              fontSize: '12px',
              color: '#6b7280',
              background: '#f9fafb',
              borderTop: '1px solid #e5e7eb'
            }}>
              {resource.description}
            </div>
          )}
        </div>
      );
    }
    switch (resource.type) {
      case 'text':
        return <TextResource content={resource.content} title={resource.title} />;
      case 'markdown':
        return <MarkdownResource content={resource.content} title={resource.title} />;
      case 'code':
        return <CodeBlock code={resource.content} language={resource.language} />;
      case 'choice':
        return <ChoiceQuestion question={resource} onSubmit={handleSubmitAnswer} resetTrigger={resetTrigger} />;  // ← 传递 resetTrigger
      case 'short':
        return <ShortQuestion question={resource} onSubmit={handleSubmitAnswer} resetTrigger={resetTrigger} />;  // ← 传递 resetTrigger
      // ... 其他类型不变
      default:
        return <TextResource content={resource.content} title={resource.title} />;
    }
  };

  const getTypeIcon = () => {
    const icons = {
      text: '📖',
      markdown: '📝',
      code: '💻',
      choice: '✏️',
      short: '📋'
    };
    return icons[resource.type] || '📄';
  };

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      border: '1px solid #e5e7eb',
      marginBottom: '16px',
      overflow: 'hidden'
    }}>
      {/* 标题栏 */}
      <div style={{
        padding: '12px 16px',
        background: '#f9fafb',
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        <span style={{ fontSize: '18px' }}>{getTypeIcon()}</span>
        <span style={{ fontWeight: 600, fontSize: '14px' }}>{resource.title}</span>
      </div>

      {/* 内容区域 */}
      <div style={{ padding: '16px' }}>
        {showResult && resultData ? (
          <ExerciseResult result={resultData} onRetry={handleRetry} />
        ) : (
          renderContent()
        )}
      </div>
    </div>
  );
};

export default ResourceCard;