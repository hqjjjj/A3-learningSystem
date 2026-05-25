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

  useEffect(() => {
    return () => {
      // 组件卸载时上报时长
      const duration = Math.floor((Date.now() - startTime) / 1000);
      if (onFinishResource && resource.id) {
        onFinishResource(resource.id, duration);
      }
    };
  }, [startTime, onFinishResource, resource.id]);

  const handleSubmitAnswer = async (answer) => {
    const result = await onSubmitAnswer(resource.id, answer);
    setResultData(result);
    setShowResult(true);
  };

  const renderContent = () => {
    switch (resource.type) {
      case 'text':
        return <TextResource content={resource.content} title={resource.title} />;
      case 'markdown':
        return <MarkdownResource content={resource.content} title={resource.title} />;
      case 'code':
        return <CodeBlock code={resource.content} language={resource.language} />;
      case 'choice':
        return <ChoiceQuestion question={resource} onSubmit={handleSubmitAnswer} />;
      case 'short':
        return <ShortQuestion question={resource} onSubmit={handleSubmitAnswer} />;
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
          <ExerciseResult result={resultData} onRetry={() => setShowResult(false)} />
        ) : (
          renderContent()
        )}
      </div>
    </div>
  );
};

export default ResourceCard;