<<<<<<< HEAD

// 实现单资源生成和资源推送，具体见backend/api/aaapi使用文档.txt


// 刚刚访问完的资源，mindmap、materials、code_example、exercise、explanation之一
//  resource_type:"",要在退出资源的时候
// 作为调用URL：POST /api/resource/finish_view这个api的参数
// 即请求体的参数传入

// 传入参数
// ResourcePanel
// props:

// recommended_resources (array, 必填)

// 元素为资源对象（type, title, content, subtype 等）

// generated_resource (object, 可选)

// 单个资源对象，结构同上

// topic (string, 必填)

// 当前知识点名称

=======

>>>>>>> e25ecba6e7a658a2f0aa6abea1506f5c2b4d27e8
import React, { useState, useEffect } from 'react';
import ResourceCard from './ResourceCard';
import ResourceGeneratorButton from './ResourceGeneratorButton';


const ResourcePanel = ({
  recommendedResources = [],
  generatedResources = null,
  onGenerateResource,
  onSubmitAnswer,
  onFinishResource,
  isLoading = false,
  userId
}) => {
  const [activeTab, setActiveTab] = useState('recommended'); // 'recommended' | 'generated'

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
        <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>📚 学习资源</h3>
        <p style={{ margin: '8px 0 0 0', fontSize: '13px', color: '#6b7280' }}>
          根据您的学习情况推荐
        </p >
      </div>

      {/* Tab 切换器 */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #e5e7eb',
        padding: '0 20px',
        gap: '24px',
        flexShrink: 0
      }}>
        <button
          style={{
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
          推荐资源
        </button>
        <button
          style={{
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
          我的生成
        </button>
      </div>

      {/* 资源列表区域 */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px 20px'
      }}>
        {activeTab === 'recommended' && (
          <>
            {recommendedResources.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '60px 20px',
                color: '#9ca3af'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '12px' }}>✨</div>
                <p style={{ margin: 0, fontSize: '14px' }}>暂无推荐资源</p >
                <p style={{ margin: '8px 0 0 0', fontSize: '12px' }}>
                  发送消息后，系统会为您推荐资源
                </p >
              </div>
            ) : (
              recommendedResources.map((resource, index) => (
                <ResourceCard
                  key={index}
                  resource={resource}
                  onFinishResource={onFinishResource}
                  onSubmitAnswer={onSubmitAnswer}
                  userId={userId}
                />
              ))
            )}
          </>
        )}

        {activeTab === 'generated' && (
          <>
            <div style={{ marginBottom: '16px' }}>
              <ResourceGeneratorButton 
                onGenerate={onGenerateResource}
                isLoading={isLoading}
                userId={userId}
              />
            </div>
            {!generatedResources ? (
              <div style={{
                textAlign: 'center',
                padding: '60px 20px',
                color: '#9ca3af'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '12px' }}>🔧</div>
                <p style={{ margin: 0, fontSize: '14px' }}>暂无生成的资源</p >
                <p style={{ margin: '8px 0 0 0', fontSize: '12px' }}>
                  点击上方按钮生成定制资源
                </p >
              </div>
            ) : (
              
              <ResourceCard
                key={index}
                resource={resource}
                onFinishResource={onFinishResource}
                onSubmitAnswer={onSubmitAnswer}
                userId={userId}
              />
              
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ResourcePanel;