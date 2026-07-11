import React, { useState, useEffect } from 'react';
import ResourceCard from './ResourceCard';
import ResourceGeneratorButton from './ResourceGeneratorButton';

// ==================== 测试用假数据 ====================
// 当 recommendedResources 为空时，使用这些假数据测试
const MOCK_RESOURCES = [
  {
    id: "mock_001",
    type: "text",
    title: "📖 地址空间基本概念（测试数据）",
    topic: "地址空间基本概念",
    content: "地址空间是程序可访问的内存范围，分为逻辑地址空间和物理地址空间。逻辑地址需要转换为物理地址才能访问内存。",
    description: "这是测试数据，用于验证组件显示"
  },
  {
    id: "mock_002",
    type: "choice",
    title: "✏️ 分页概念小测（测试数据）",
    topic: "分页基本概念",
    text: "分页存储管理中，逻辑地址被分为哪两部分？",
    options: ["页号和页内偏移", "段号和段内偏移", "块号和块内偏移", "区号和区内偏移"],
    correctAnswer: "页号和页内偏移"
  },
  {
    id: "mock_003",
    type: "short",
    title: "📝 缺页中断简答（测试数据）",
    topic: "缺页中断",
    text: "请简述什么是缺页中断？它发生在什么情况下？",
    correctAnswer: "缺页中断是当程序访问的页面不在物理内存中时触发的异常。操作系统会将缺失的页面从磁盘换入内存，然后继续执行程序。"
  },
  {
    id: "mock_004",
    type: "html",
    title: "🎬 页面置换算法动画（测试数据）",
    topic: "页面置换算法",
    subtype: "animation",
    html_content: "<div style='padding:20px;font-family:Arial'><h3>FIFO 页面置换算法</h3><p>当内存满时，淘汰最先进入的页面。</p ><div style='background:#e5e7eb;padding:10px;border-radius:8px'>📊 动画演示区域</div></div>",
    description: "FIFO 页面置换算法动画演示（测试数据）"
  },
  {
    id: "mock_005",
    type: "code",
    title: "💻 分页代码示例（测试数据）",
    topic: "分页基本概念",
    language: "c",
    content: `// 分页地址转换示例
#include <stdio.h>
int main() {
    int logical_addr = 0x1234;
    int page_size = 4096;
    int page_num = logical_addr / page_size;
    int offset = logical_addr % page_size;
    printf("页号: %d, 偏移: %d\\n", page_num, offset);
    return 0;
}`,
    description: "C语言分页地址转换代码示例"
  }
];

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

 // 判断生成资源是否为空（处理 null、undefined、空对象、无 type 字段）
  const isEmptyGenerated = !generatedResources || 
                          (typeof generatedResources === 'object' && 
                           Object.keys(generatedResources).length === 0) ||
                          !generatedResources.type;

  // 显示的资源：如果传入的为空，用假数据测试；否则用真实数据
  const displayResources = recommendedResources.length === 0 ? MOCK_RESOURCES : recommendedResources;

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
        {/* 测试提示（上线后可删除） */}
        {recommendedResources.length === 0 && (
          <p style={{ margin: '8px 0 0 0', fontSize: '12px', color: '#f59e0b' }}>
            ⚠️ 测试模式：使用假数据（真实数据为空）
        </p >
        )}
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
        {/* 推荐资源 Tab */}        
        {activeTab === 'recommended' && (
          <>
            {displayResources.length === 0 ? (
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
              displayResources.map((resource, index) => (
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
            {isEmptyGenerated ? (
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
                resource={generatedResources}
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