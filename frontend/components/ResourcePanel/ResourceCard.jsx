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

  if (!resource) return null;

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

  const renderKnowledgeSource = () => {
    if (!resource.knowledge_base_quote || resource.knowledge_base_quote.length === 0) {
      return null;
    }
    return (
      <details style={{ 
        marginTop: '16px', 
        padding: '10px 14px',
        borderTop: '1px solid #e5e7eb',
        fontSize: '12px', 
        color: '#6b7280',
        cursor: 'pointer'
      }}>
        <summary style={{ fontWeight: 500, fontSize: '13px' }}>
          📚 知识来源（{resource.knowledge_base_quote.length}个引用）
        </summary>
        <ul style={{ margin: '8px 0 0 0', paddingLeft: '18px' }}>
          {resource.knowledge_base_quote.map((source, idx) => (
            <li key={idx} style={{ marginBottom: '6px', fontSize: '12px', lineHeight: 1.5 }}>
              {source}
            </li>
          ))}
        </ul>
      </details>
    );
  };

  // ========== 改动1：完善 renderContent 函数，识别全部六种资源类型 ==========
  // 目的：根据 type 和 subtype 组合判断资源类型，使用对应的渲染组件
  // =========================================================================
  const renderContent = () => {
    // 1️⃣ 动画演示 (type: html, subtype: animation)
    if (resource.type === 'html' && resource.subtype === 'animation') {
      return (
        <div>
          <div style={{
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            overflow: 'hidden',
            marginTop: '8px',
            background: '#fff'
          }}>
            <div style={{
              padding: '10px 16px',
              background: '#f8fafc',
              borderBottom: '1px solid #e5e7eb',
              fontSize: '13px',
              fontWeight: 500,
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span>🎬</span>
              <span>{resource.title || '动画演示'}</span>
              <span style={{ 
                fontSize: '11px', 
                color: '#6b7280', 
                background: '#e5e7eb', 
                padding: '2px 8px', 
                borderRadius: '10px',
                marginLeft: 'auto'
              }}>
                交互式动画
              </span>
            </div>
            <iframe
              srcDoc={resource.html_content}
              title={resource.title}
              style={{
                width: '100%',
                height: '520px',
                border: 'none',
                backgroundColor: '#fff'
              }}
              sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
            />
            {resource.description && (
              <div style={{
                padding: '10px 16px',
                fontSize: '13px',
                color: '#6b7280',
                background: '#f9fafb',
                borderTop: '1px solid #e5e7eb',
                lineHeight: 1.6
              }}>
                💡 {resource.description}
              </div>
            )}
          </div>
          {renderKnowledgeSource()}
        </div>
      );
    }

    // 2️⃣ 思维导图 (type: markdown, subtype: mindmap)
    if (resource.type === 'markdown') {
      return (
        <div>
          <MarkdownResource content={resource.content} title={resource.title} />
          {renderKnowledgeSource()}
        </div>
      );
    }

    // 3️⃣ 代码示例 (type: code, subtype: code_example)
    // 改动2：支持 code_lines 数组格式
    // 目的：后端可能返回 code_lines 数组或 content 字符串，需要兼容
    // =====================================================================
    if (resource.type === 'code') {
      const codeContent = resource.code_lines 
        ? resource.code_lines.join('\n') 
        : resource.content || '';
      return (
        <div>
          <CodeBlock code={codeContent} language={resource.language || 'python'} />
          {renderKnowledgeSource()}
        </div>
      );
    }

    // 4️⃣ 练习题 (type: choice, subtype: exercise)
    if (resource.type === 'choice') {
      return (
        <div>
          <ChoiceQuestion 
            question={{
              text: resource.question || resource.text,
              options: resource.options,
              answer: resource.answer,
              correctAnswer: resource.correctAnswer,
              analysis: resource.analysis
            }}
            onSubmit={handleSubmitAnswer}
            resetTrigger={resetTrigger}
          />
          {renderKnowledgeSource()}
        </div>
      );
    }

    // 5️⃣ 简答题 (type: short)
    if (resource.type === 'short') {
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
    }

    // 6️⃣ 知识点讲解 和 扩展材料 (type: text)
    // subtype: explanation 或 materials
    if (resource.type === 'text') {
      const content = resource.content || '';
      return (
        <div>
          <TextResource content={content} title={resource.title} />
          {renderKnowledgeSource()}
        </div>
      );
    }

    // 默认降级处理
    return (
      <div>
        <TextResource content={resource.content || JSON.stringify(resource)} title={resource.title} />
        {renderKnowledgeSource()}
      </div>
    );
  };

  // ========== 改动3：添加类型图标和标签函数 ==========
  // 目的：在标题栏显示资源类型标识，方便用户识别
  // ==================================================
  const getTypeIcon = () => {
    if (resource.type === 'html' && resource.subtype === 'animation') return '🎬';
    if (resource.type === 'markdown' && resource.subtype === 'mindmap') return '🧠';
    if (resource.type === 'code') return '💻';
    if (resource.type === 'choice') return '✏️';
    if (resource.type === 'short') return '📋';
    if (resource.type === 'text') {
      if (resource.subtype === 'explanation') return '📖';
      if (resource.subtype === 'materials') return '📚';
    }
    return '📄';
  };

  const getTypeLabel = () => {
    if (resource.type === 'html' && resource.subtype === 'animation') return '动画演示';
    if (resource.type === 'markdown' && resource.subtype === 'mindmap') return '思维导图';
    if (resource.type === 'code') return '代码示例';
    if (resource.type === 'choice') return '练习题';
    if (resource.type === 'short') return '简答题';
    if (resource.type === 'text') {
      if (resource.subtype === 'explanation') return '知识点讲解';
      if (resource.subtype === 'materials') return '扩展材料';
    }
    return resource.subtype || resource.type || '资源';
  };

  if (showResult && resultData) {
    return (
      <div style={{
        background: 'white',
        borderRadius: '12px',
        border: '1px solid #e5e7eb',
        marginBottom: '16px',
        overflow: 'hidden'
      }}>
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
          <span style={{ 
            fontSize: '11px', 
            color: '#6b7280', 
            background: '#e5e7eb', 
            padding: '2px 8px', 
            borderRadius: '10px' 
          }}>
            {getTypeLabel()}
          </span>
        </div>
        <div style={{ padding: '16px' }}>
          <ExerciseResult result={resultData} onRetry={handleRetry} />
        </div>
      </div>
    );
  }

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      border: '1px solid #e5e7eb',
      marginBottom: '16px',
      overflow: 'hidden'
    }}>
      {/* ========== 改动4：标题栏显示类型标签 ========== */}
      {/* 目的：用户一眼就能看出这是什么类型的资源 */}
      {/* ============================================== */}
      <div style={{
        padding: '12px 16px',
        background: '#f9fafb',
        borderBottom: '1px solid #e5e7eb',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        flexWrap: 'wrap'
      }}>
        <span style={{ fontSize: '18px' }}>{getTypeIcon()}</span>
        <span style={{ fontWeight: 600, fontSize: '14px' }}>{resource.title}</span>
        <span style={{ 
          fontSize: '11px', 
          color: '#6b7280', 
          background: '#e5e7eb', 
          padding: '2px 8px', 
          borderRadius: '10px',
          marginLeft: 'auto'
        }}>
          {getTypeLabel()}
        </span>
      </div>

      <div style={{ padding: '16px' }}>
        {renderContent()}
      </div>
    </div>
  );
};

export default ResourceCard;