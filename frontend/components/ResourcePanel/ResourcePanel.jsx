import React, { useState, useEffect } from 'react';
import ResourceCard from './ResourceCard';
import ResourceGeneratorButton from './ResourceGeneratorButton';
import ResourceGenerationProgress from './ResourceGenerationProgress';

const ResourcePanel = ({
  recommendedResources = [],
  generatedResources = null,
  onGenerateResource,
  onSubmitAnswer,
  onFinishResource,
  isLoading = false,
  userId
}) => {
  const [activeTab, setActiveTab] = useState('recommended');
  const [showProgress, setShowProgress] = useState(false);
  const [generatingType, setGeneratingType] = useState('explanation');

  const getGeneratedList = () => {
    if (!generatedResources) return [];
    if (Array.isArray(generatedResources)) return generatedResources;
    if (typeof generatedResources === 'object' && generatedResources.type) {
      return [generatedResources];
    }
    return [];
  };

  const generatedList = getGeneratedList();

  const handleGenerate = async (resourceType) => {
    setGeneratingType(resourceType);
    setShowProgress(true);
    
    try {
      await onGenerateResource(resourceType); 
    } catch (error) {
      console.error('生成失败:', error);
      setShowProgress(false);
    }
  };

  const handleProgressComplete = () => {
    setShowProgress(false);
  };

  const handleProgressCancel = () => {
    setShowProgress(false);
  };

  const displayResources = Array.isArray(recommendedResources) ? recommendedResources : [];

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      width: '100%'
    }}>
      {/* 头部 */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid #e5e7eb',
        flexShrink: 0
      }}>
        <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>学习资源</h3>
        <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: '#6b7280' }}>
          根据您的学习情况推荐
        </p >
      </div>

      <div style={{
        display: 'flex',
        borderBottom: '1px solid #e5e7eb',
        padding: '0 20px',
        gap: '24px',
        flexShrink: 0
      }}>
        <button
          style={{
            flex: 1,
            padding: '12px 0',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'recommended' ? '2px solid #3b82f6' : '2px solid transparent',
            color: activeTab === 'recommended' ? '#3b82f6' : '#6b7280',
            fontSize: '14px',
            fontWeight: 500,
            cursor: 'pointer'
          }}
          onClick={() => setActiveTab('recommended')}
        >
          推荐资源 ({displayResources.length})
        </button>
        <button
          style={{
            flex: 1,
            padding: '12px 0',
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'generated' ? '2px solid #3b82f6' : '2px solid transparent',
            color: activeTab === 'generated' ? '#3b82f6' : '#6b7280',
            fontSize: '14px',
            fontWeight: 500,
            cursor: 'pointer'
          }}
          onClick={() => setActiveTab('generated')}
        >
          我的生成 ({generatedList.length})
        </button>
      </div>

      {/* 资源列表区域 */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px 20px'
      }}>
        {/* 推荐资源 Tab */}
        {activeTab === 'recommended' && (
          <>
            {isLoading ? (
              <div style={{
                textAlign: 'center',
                padding: '60px 20px',
                color: '#9ca3af'
              }}>
            
                <p style={{ margin: 0, fontSize: '14px' }}>加载推荐资源中...</p >
              </div>
            ) : displayResources.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '60px 20px',
                color: '#9ca3af'
              }}>
                
                <p style={{ margin: 0, fontSize: '14px' }}>暂无推荐资源</p >
                <p style={{ margin: '8px 0 0 0', fontSize: '12px' }}>
                  发送消息后，系统会为您推荐丰富的学习资源
                </p >
              </div>
            ) : (
              displayResources.map((resource, index) => (
                <ResourceCard
                  key={resource.id || index}
                  resource={resource}
                  onFinishResource={onFinishResource}
                  onSubmitAnswer={onSubmitAnswer}
                  userId={userId}
                />
              ))
            )}
          </>
        )}

        {/* 我的生成 Tab */}
        {activeTab === 'generated' && (
          <>
            <div style={{ marginBottom: '16px' }}>
              <ResourceGeneratorButton 
                onGenerate={handleGenerate}
                isLoading={isLoading}
                userId={userId}
              />
            </div>
            {generatedList.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '60px 20px',
                color: '#9ca3af'
              }}>
                <p style={{ margin: 0, fontSize: '14px' }}>暂无生成的资源</p >
                <p style={{ margin: '8px 0 0 0', fontSize: '12px' }}>
                  点击上方按钮生成定制资源
                </p >
              </div>
            ) : (
              generatedList.map((resource, index) => (
                <ResourceCard
                  key={resource.id || index}
                  resource={resource}
                  onFinishResource={onFinishResource}
                  onSubmitAnswer={onSubmitAnswer}
                  userId={userId}
                />
              ))
            )}
          </>
        )}
      </div>
      <ResourceGenerationProgress
        isVisible={showProgress}
        onComplete={handleProgressComplete}
        onCancel={handleProgressCancel}
        resourceType={generatingType}
      />
    </div>
  );
};

export default ResourcePanel;