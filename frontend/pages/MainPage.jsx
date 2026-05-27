// MainPage.jsx
import React, { useState, useEffect } from 'react';
import ProfilePanel from './components/ProfilePanel';
import ChatPanel from './components/ChatPanel';
import PathPanel from './components/PathPanel';
import KnowledgeGraphPanel from './components/KnowledgeGraphPanel';
import ResourcePanel from './components/ResourcePanel';
import './MainPage.css';
import chatIcon from '../img/1779594814480.png';
import profileIcon from '../img/1779594816401.png';
import * as api from '../api/api';   // 导入真实 API

// 初始状态（根据子组件需求调整）
const initialAppState = {
  profile: {
    learning_style: 'visual',
    learning_pace: 'moderate',
    weak_points: ['页面置换', '段页式'],
    knowledge_level: {
      '内存管理': 0.6,
      '进程调度': 0.8,
      '文件系统': 0.4
    }
  },
  topic: '内存管理',
  recommended_resources: [],   // 从后端获取的推荐资源列表
  generated_resources: [],     // 用户主动生成的资源列表
  current_progress: 'learning',
  chat_history: [
    { role: 'assistant', content: '你好！我是你的学习助手，有什么可以帮你的？' }
  ],
  learning_path: []            // 学习路径数组，如 ['内存管理', '进程管理', ...]
};

const MainPage = () => {
  // UI 状态
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [activeMainTab, setActiveMainTab] = useState('path');
  const [activePathTab, setActivePathTab] = useState('learningPath');

  // 业务状态
  const [appState, setAppState] = useState(initialAppState);
  const [isLoading, setIsLoading] = useState(false);
  const userId = 'user123';   // 实际应从登录状态获取

  // ========== 辅助函数：合并后端返回的更新 ==========
  const mergeAppState = (updates) => {
    setAppState(prev => ({
      ...prev,
      ...updates,
      // 特殊处理：profile_update 需要合并到 profile 对象
      profile: updates.profile_update
        ? { ...prev.profile, ...updates.profile_update }
        : prev.profile,
      // 推荐资源如果是数组则直接替换
      recommended_resources: updates.recommended_resources ?? prev.recommended_resources,
      generated_resource: updates.generated_resource ?? prev.generated_resource,
      chat_history: updates.chat_history ?? prev.chat_history,
      learning_path: updates.learning_path ?? prev.learning_path,
      topic: updates.topic ?? prev.topic
    }));
  };

  // ========== 1. 聊天发送回调 ==========
  const handleSendMessage = async (message) => {
    // 乐观更新：立即显示用户消息
    const userMsg = { role: 'user', content: message };
    setAppState(prev => ({
      ...prev,
      chat_history: [...prev.chat_history, userMsg]
    }));
    setIsLoading(true);

    try {
      // 调用真实 API：POST /api/chat/
      const data = await api.sendChat(userId, message);
      // 期望后端返回格式：
      // {
      //   reply: "助手回复内容",
      //   profile_update: { weak_points?: [...], knowledge_level?: {...} },
      //   recommended_resources: [...],
      //   learning_path: [...]
      // }
      const assistantMsg = { role: 'assistant', content: data.reply };
      mergeAppState({
        chat_history: [...appState.chat_history, userMsg, assistantMsg],
        profile_update: data.profile_update,
        recommended_resources: data.recommended_resources,
        learning_path: data.learning_path    // 后端可能返回更新的学习路径
      });
    } catch (error) {
      console.error('发送消息失败', error);
      const errorMsg = { role: 'assistant', content: '抱歉，服务出错了，请稍后再试。' };
      setAppState(prev => ({
        ...prev,
        chat_history: [...prev.chat_history, errorMsg]
      }));
    } finally {
      setIsLoading(false);
    }
  };

  // ========== 2. 生成资源回调 ==========
  const handleGenerateResource = async (resourceType) => {
    setIsLoading(true);
    try {
      // 调用 API：POST /api/resource/generate
      const data = await api.generateResource(userId, appState.topic, resourceType);
      // 期望后端返回：{ generated_resource: {...} }
      const newResource = data.generated_resource;
      mergeAppState({
        generated_resources: [...appState.generated_resources, newResource]
      });
    } catch (error) {
      console.error('生成资源失败', error);
    } finally {
      setIsLoading(false);
    }
  };

  // ========== 3. 提交习题答案回调 ==========
  const handleSubmitAnswer = async (resourceId, answer) => {
    setIsLoading(true);
    try {
      // 第一步：根据 resourceId 找到对应的资源（可能在推荐资源或生成资源中）
      const allResources = [...appState.recommended_resources, ...appState.generated_resources];
      const resource = allResources.find(r => r.id === resourceId);
      if (!resource) throw new Error('资源不存在');

      // 第二步：计算正确率（仅支持选择题，简答题暂按 0 处理）
      let correctRate = 0;
      if (resource.type === 'choice') {
        // 假设资源对象中有 correctOption 字段
        correctRate = (answer === resource.correctOption) ? 1 : 0;
      } else {
        // 简答题或其它类型：这里简单处理为 0，实际需后端评判
        correctRate = 0;
      }

      // 第三步：调用提交答案 API（POST /api/answer/submit_answer）
      // 注意：duration 参数这里暂时传 0，实际应由 ResourceCard 计时传入
      const duration = 0;  // 理想情况下应该从 ResourceCard 的计时获得
      const data = await api.submitAnswer(userId, appState.topic, correctRate, duration);
      // 期望后端返回：{ result: { correct, message, explanation }, profile_update: {...} }

      // 第四步：更新用户画像（如果后端返回了 profile_update）
      if (data.profile_update) {
        mergeAppState({ profile_update: data.profile_update });
      }

      // 第五步：返回结果给 ResourceCard，用于显示正确/错误界面
      return data.result;   // { correct, message, explanation }
    } catch (error) {
      console.error('提交答案失败', error);
      return { correct: false, message: '提交失败，请重试' };
    } finally {
      setIsLoading(false);
    }
  };

  // ========== 4. 资源浏览结束回调（上报时长） ==========
  const handleFinishResource = async (resourceId, duration) => {
    try {
      // 需要知道资源的类型和对应的 topic，这里简化：从资源列表中查找
      const allResources = [...appState.recommended_resources, ...appState.generated_resources];
      const resource = allResources.find(r => r.id === resourceId);
      if (!resource) return;
      // 调用 API：POST /api/resource/finish_view
      await api.finishResource(userId, resource.type, appState.topic, duration);
    } catch (error) {
      console.error('上报资源时长失败', error);
    }
  };

  // ========== 5. 切换知识点回调（点击路径节点） ==========
  const handleTopicChange = async (newTopic) => {
    setIsLoading(true);
    try {
      // 调用 API：获取新主题的学习路径和推荐资源（如果有专门接口）
      // 注意：api.js 中有 fetchPath，可以获取学习路径
      const pathData = await api.fetchPath(userId);
      // 假设 pathData 返回格式：{ learning_path: [...], recommended_resources: [...] }
      mergeAppState({
        topic: newTopic,
        learning_path: pathData.learning_path,
        recommended_resources: pathData.recommended_resources || []
      });
    } catch (error) {
      console.error('切换知识点失败', error);
      // 降级：只更新本地 topic
      mergeAppState({ topic: newTopic });
    } finally {
      setIsLoading(false);
    }
  };

  // ========== 初始化：加载学习路径 ==========
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const pathData = await api.fetchPath(userId);
        mergeAppState({
          learning_path: pathData.learning_path,
          recommended_resources: pathData.recommended_resources || []
        });
      } catch (error) {
        console.error('加载初始数据失败', error);
      }
    };
    loadInitialData();
  }, []);   // 只在组件挂载时执行一次

  // ========== UI 渲染 ==========
  const toggleSidebar = () => setIsSidebarCollapsed(!isSidebarCollapsed);

  return (
    <div className="main-page">
      {/* 左侧栏：折叠/展开 */}
      <aside className={`sidebar ${isSidebarCollapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-toggle" onClick={toggleSidebar}>
          {isSidebarCollapsed ? '▶' : '◀'}
        </div>
        {!isSidebarCollapsed && (
          <div className="sidebar-content">
            <div className="profile-section">
              <ProfilePanel profile={appState.profile} />
            </div>
            <div className="chat-section">
              <ChatPanel
                chatHistory={appState.chat_history}
                onSendMessage={handleSendMessage}
                isLoading={isLoading}
                userId={userId}
              />
            </div>
          </div>
        )}
        {isSidebarCollapsed && (
          <div className="collapsed-icons">
            <img src={profileIcon} alt="用户画像" className="icon-img" />
            <img src={chatIcon} alt="聊天" className="icon-img" />
          </div>
        )}
      </aside>

      {/* 右侧主内容 */}
      <main className="main-content">
        <div className="main-tab-bar">
          <button
            className={activeMainTab === 'path' ? 'active' : ''}
            onClick={() => setActiveMainTab('path')}
          >
            学习路径
          </button>
          <button
            className={activeMainTab === 'resource' ? 'active' : ''}
            onClick={() => setActiveMainTab('resource')}
          >
            学习资源
          </button>
        </div>

        <div className="main-tab-content">
          {activeMainTab === 'path' && (
            <div className="path-container">
              <div className="sub-tab-bar">
                <button
                  className={activePathTab === 'learningPath' ? 'active' : ''}
                  onClick={() => setActivePathTab('learningPath')}
                >
                  学习路径
                </button>
                <button
                  className={activePathTab === 'knowledgeGraph' ? 'active' : ''}
                  onClick={() => setActivePathTab('knowledgeGraph')}
                >
                  知识图谱
                </button>
              </div>
              <div className="sub-tab-content">
                {activePathTab === 'learningPath' && (
                  <PathPanel
                    learningPath={appState.learning_path}
                    topic={appState.topic}
                    onTopicChange={handleTopicChange}
                  />
                )}
                {activePathTab === 'knowledgeGraph' && <KnowledgeGraphPanel />}
              </div>
            </div>
          )}
          {activeMainTab === 'resource' && (
            <div className="resource-container">
              <ResourcePanel
                recommendedResources={appState.recommended_resources}
                generatedResources={appState.generated_resources}
                onGenerateResource={handleGenerateResource}
                onSubmitAnswer={handleSubmitAnswer}
                onFinishResource={handleFinishResource}
                isLoading={isLoading}
                userId={userId}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default MainPage;