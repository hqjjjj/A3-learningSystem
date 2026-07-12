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

  // 时长上报
  useEffect(() => {
    return () => {
      const duration = Math.floor((Date.now() - startTime) / 1000);
      if (onFinishResource && resource) {
        onFinishResource(resource.subtype, duration);
      }

    };
  }, []);

  const handleSubmitAnswer = async (correct_rate, duration) => {
    const result = await onSubmitAnswer(correct_rate, duration);
    setResultData(result);
    setShowResult(true);
  };

  const handleRetry = () => {
    setShowResult(false);
    setResultData(null);
    setResetTrigger(prev => prev + 1);
  };

  // ✅ 渲染知识来源
  const renderKnowledgeSource = () => {
    if (!resource.knowledge_base_quote || resource.knowledge_base_quote.length === 0) {
      return null;
    }
    return (
      <details style={{ 
        marginTop: '12px', 
        padding: '8px 12px',
        borderTop: '1px solid #e5e7eb',
        fontSize: '12px', 
        color: '#6b7280',
        cursor: 'pointer'
      }}>
        <summary style={{ fontWeight: 500 }}>
          📚 来源（{resource.knowledge_base_quote.length}个）
        </summary>
        <ul style={{ margin: '8px 0 0 0', paddingLeft: '16px' }}>
          {resource.knowledge_base_quote.map((source, idx) => (
            <li key={idx} style={{ marginBottom: '4px', fontSize: '12px', lineHeight: 1.4 }}>
              {source}
            </li>
          ))}
        </ul>
      </details>
    );
  };

  const renderContent = () => {
    // 动画类型
    if (resource.type === 'html' && resource.subtype === 'animation') {
      return (
        <div>
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
          {renderKnowledgeSource()}
        </div>
      );
    }

    switch (resource.type) {
      case 'text':
        return (
          <div>
            <TextResource content={resource.content} title={resource.title} />
            {renderKnowledgeSource()}
          </div>
        );
      case 'markdown':
        return (
          <div>
            <MarkdownResource content={resource.content} title={resource.title} />
            {renderKnowledgeSource()}
          </div>
        );
      case 'code':
        return (
          <div>
            <CodeBlock code={resource.content} language={resource.language} />
            {renderKnowledgeSource()}
          </div>
        );
      case 'choice':
        return (
          <div>
            <ChoiceQuestion 
              question={{
                text: resource.question || resource.text,     // 兼容新旧格式
                options: resource.options,
                answer: resource.answer || resource.correctAnswer,  // 新格式用 answer
                correctAnswer: resource.correctAnswer,        // 兼容旧格式
                analysis: resource.analysis
              }}
              onSubmit={handleSubmitAnswer}
              resetTrigger={resetTrigger}
            />
            {renderKnowledgeSource()}
          </div>
        );
      case 'short':
        return (
          <div>
            <ShortQuestion 
              question={{
                text: resource.question || resource.text,
                answer: resource.answer,
                analysis: resource.analysis,
                correctAnswer: resource.correctAnswer
              }}
              onSubmit={handleSubmitAnswer}
              resetTrigger={resetTrigger}
            />
            {renderKnowledgeSource()}
          </div>
        );
      default:
        return (
          <div>
            <TextResource content={resource.content} title={resource.title} />
            {renderKnowledgeSource()}
          </div>
        );
    }
  };

  const getTypeIcon = () => {
    if (resource.type === 'html' && resource.subtype === 'animation') return '🎬';
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