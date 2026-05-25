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
import React, { useState, useEffect } from 'react';
import ResourceCard from './ResourceCard';
import ResourceGeneratorButton from './ResourceGeneratorButton';

/**
 * ResourcePanel - 资源面板
 * 
 * 角色: 核心业务容器
 * 任务:
 * 1. 展示推荐资源列表（recommended_resources）和用户主动生成的资源（generated_resource）
 * 2. 根据资源类型调用不同的渲染子组件
 * 3. 提供"生成更多资源"按钮（调用 generateResource API）
 * 4. 退出资源时负责上报资源浏览时长（调用 finishResource API）
 * 5. 用户提交习题答案时调用 submitAnswer API
 * 
 * Props:
 * - recommendedResources: 推荐资源列表
 * - generatedResources: 用户生成的资源列表
 * - onGenerateResource: 生成资源回调
 * - onSubmitAnswer: 提交答案回调
 * - onFinishResource: 资源浏览完成回调
 * - isLoading: 是否正在加载
 * - userId: 用户ID
 */
const ResourcePanel = ({
  recommendedResources = [],
  generatedResources = [],
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
            {generatedResources.length === 0 ? (
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
              generatedResources.map((resource, index) => (
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
      </div>
    </div>
  );
};

export default ResourcePanel;