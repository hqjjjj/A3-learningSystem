import React, { useState, useEffect } from 'react';

const ResourceGenerationProgress = ({ 
  isVisible, 
  onComplete, 
  onCancel,
  resourceType 
}) => {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('准备生成...');

  const typeLabels = {
    explanation: '知识点讲解',
    exercise: '练习题',
    code: '代码示例',
    mindmap: '思维导图',
    materials: '扩展材料',
    animation: '动画演示'
  };

  const steps = [
    { progress: 10, status: '📝 正在分析知识点...' },
    { progress: 30, status: '🔍 正在检索知识库...' },
    { progress: 50, status: '📋 正在生成内容结构...' },
    { progress: 70, status: '✍️ 正在编写具体内容...' },
    { progress: 85, status: '🎨 正在优化格式...' },
    { progress: 95, status: '⏳ 即将完成...' },
    { progress: 100, status: '✅ 生成完成！' }
  ];

  useEffect(() => {
    if (!isVisible) {
      setProgress(0);
      setStatus('准备生成...');
      return;
    }

    let currentStep = 0;
    setProgress(0);
    setStatus('🚀 开始生成...');

    const interval = setInterval(() => {
      currentStep++;
      if (currentStep < steps.length) {
        setProgress(steps[currentStep].progress);
        setStatus(steps[currentStep].status);
      }
      if (currentStep >= steps.length - 1) {
        clearInterval(interval);
        setTimeout(() => {
          if (onComplete) onComplete();
        }, 500);
      }
    }, 600);

    return () => clearInterval(interval);
  }, [isVisible, onComplete]);

  if (!isVisible) return null;

  const label = typeLabels[resourceType] || '资源';

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        background: 'white',
        borderRadius: '16px',
        padding: '32px 40px',
        maxWidth: '420px',
        width: '90%',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
      }}>
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '12px',
          marginBottom: '20px'
        }}>
          <span style={{ fontSize: '28px' }}>🚀</span>
          <div>
            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>
              正在生成{label}
            </h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#6b7280' }}>
              AI 正在为您创作...
            </p >
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <div style={{
            width: '100%',
            height: '8px',
            background: '#e5e7eb',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${progress}%`,
              height: '100%',
              background: `linear-gradient(90deg, #10b981, #3b82f6)`,
              borderRadius: '4px',
              transition: 'width 0.5s ease'
            }} />
          </div>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '6px',
            fontSize: '12px',
            color: '#6b7280'
          }}>
            <span>{status}</span>
            <span>{Math.round(progress)}%</span>
          </div>
        </div>

        <div style={{
          padding: '12px',
          background: '#f3f4f6',
          borderRadius: '8px',
          marginBottom: '20px',
          fontSize: '13px',
          color: '#374151',
          textAlign: 'center'
        }}>
          {progress < 100 ? '⏳ 请稍候...' : '✅ 资源已生成！'}
        </div>

        {progress < 100 && (
          <button
            style={{
              width: '100%',
              padding: '10px',
              background: 'transparent',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '14px',
              color: '#6b7280',
              cursor: 'pointer'
            }}
            onClick={onCancel}
          >
            取消生成
          </button>
        )}
      </div>
    </div>
  );
};

export default ResourceGenerationProgress;