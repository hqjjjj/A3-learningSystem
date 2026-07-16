// MainPage.jsx
import React, { useState, useEffect, useCallback } from 'react';   
import ProfilePanel from '../components/ProfilePanel';
import ChatPanel from "../components/ChatPanel/ChatPanel";
import KnowledgeGraphPanel from "../components/KnowledgeGraphPanel/KnowledgeGraphPanel";
import ResourcePanel from "../components/ResourcePanel/ResourcePanel";
import PathPanel from '../components/PathPanel';
import './MainPage.css';
import chatIcon from '../imgs/1779594814480.png';
import profileIcon from '../imgs/1779594816401.png';
import * as api from '../api/api';

const MainPage = ({ appState, setAppState, userId }) => {
  // ===== 左侧折叠状态 =====
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  
  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  // ===== 右侧主 Tab =====
  const [activeMainTab, setActiveMainTab] = useState('path');

  // ===== 路径区子 Tab =====
  const [activePathTab, setActivePathTab] = useState('learningPath');

  // ===== 加载状态 =====
  const [isLoading, setIsLoading] = useState(false);

  // ===== 辅助函数：合并后端返回更新 =====
  const mergeAppState = useCallback((updates) => {
    setAppState(prev => {
      const processedUpdates = typeof updates === 'function' ? updates(prev) : updates;
      console.log('Processed updates:', processedUpdates);
      
      return {
        ...prev,
        ...processedUpdates,
        profile: processedUpdates.profile ?? prev.profile,
        recommended_resources: processedUpdates.recommended_resources ?? prev.recommended_resources,
        generated_resource: processedUpdates.generated_resource ?? prev.generated_resource,
        chat_history: processedUpdates.chat_history !== undefined ? processedUpdates.chat_history : prev.chat_history,
        learning_path: processedUpdates.learning_path ?? prev.learning_path,
        topic: processedUpdates.topic ?? prev.topic,
        current_progress: processedUpdates.current_progress ?? prev.current_progress
      };
    });
  }, [setAppState]);

  // ===== 初始数据加载 =====
  // MainPage.jsx - useEffect
  useEffect(() => {
    // ✅ 如果已有数据且用户ID匹配，跳过加载
    if (appState.profile && appState.profile.user_id === userId) {
      console.log('数据已加载，跳过重复请求');
      return;
    }
  
    const loadInitialData = async () => {
      try {
        setIsLoading(true);
        const data = await api.loadUserState(userId);
        console.log('Initial data loaded:', data);
        mergeAppState(data);
      } catch (error) {
        console.error('加载初始数据失败:', error);
      } finally {
        setIsLoading(false);
      }
    };
  
    loadInitialData();
  }, [userId, mergeAppState, appState.profile]);

  // ===== 聊天模块回调函数 =====
  const handleSendMessage = useCallback(async (message) => {
    const userMsg = { role: 'user', content: message };
    setAppState(prev => ({
      ...prev,
      chat_history: [...prev.chat_history, userMsg]
    }));
    setIsLoading(true);

    try {
      const data = await api.sendChat(userId, message);
      const assistantMsg = { role: 'assistant', content: data.reply };
      
      mergeAppState((prev) => ({
        chat_history: [...prev.chat_history, assistantMsg],
        profile: data.profile,
        recommended_resources: data.recommended_resources,
        learning_path: data.learning_path,
        topic: data.topic,
        current_progress: data.current_progress
      }));
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
  }, [userId, setAppState, mergeAppState]);

const handleGenerateResource = useCallback(async (resourceTypes) => {
  setIsLoading(true);
  try {
    // 现在 api.generateResource 返回的是业务数据，直接解构
    const { generated_resource, topic, current_progress } = await api.generateResource(userId, appState.topic, resourceTypes);
    mergeAppState({ generated_resource, topic, current_progress });
  } catch (error) {
    console.error('生成资源失败', error);
  } finally {
    setIsLoading(false);
  }
}, [userId, appState.topic, mergeAppState]);
  
  // ===== 提交答案回调函数 =====
  const handleSubmitAnswer = useCallback(async (correct_rate, duration) => {
    setIsLoading(true);
    try {
      const data = await api.submitAnswer(userId, appState.topic, correct_rate, duration);
      mergeAppState({
        profile: data.profile,
        learning_path: data.learning_path,
        recommended_resources: data.recommended_resources,
        topic: data.topic,
        current_progress: data.current_progress
      });
    } catch (error) {
      console.error('提交答案失败', error);
      return { correct: false, message: '提交失败，请重试' };
    } finally {
      setIsLoading(false);
    }
  }, [userId, appState.topic, mergeAppState]);


// 完成浏览回调函数
const handleFinishResource=useCallback(async(resourceType,duration)=>{
  try{
    const data=await api.finishResource(userId,resourceType,appState.topic,duration);
    mergeAppState({
      profile: data.profile,
      learning_path: data.learning_path,
      recommended_resources: data.recommended_resources,
      topic: data.topic,
      current_progress: data.current_progress
    })
  }catch (error) {
    console.error('上报资源浏览失败', error);
  }
}, [userId, appState.topic, mergeAppState])

//切换主题回调函数
const handlePathNodeClick = useCallback(async (newTopic) => {
  // 1. 先乐观更新 topic（让界面立刻响应）
  setAppState(prev => ({ ...prev, topic: newTopic }));

  // 2. 拉取该主题下的路径和资源
  setIsLoading(true);
  try {
    const pathData = await api.fetchPath(userId, newTopic);
    mergeAppState({
      profile: pathData.profile,
      learning_path: pathData.learning_path,
      recommended_resources: pathData.recommended_resources || [],
      current_progress: pathData.current_progress,
      topic: pathData.topic, 
    });
  } catch (error) {
    console.error('加载新主题路径失败', error);
  } finally {
    setIsLoading(false);
  }
}, [userId, mergeAppState, setAppState, setIsLoading]);


 

  return (
    <div className="main-page">
      {/* 左侧栏：可折叠 */}
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
                    learningPath={{
                      current: appState.learning_path?.current,
                      next: appState.learning_path?.next,
                      path_list: appState.learning_path?.path_list || []
                    }}
                    topic={appState.topic}
                    onTopicChange={handlePathNodeClick}
                  />
                )}
                {activePathTab === 'knowledgeGraph' && (
                  <KnowledgeGraphPanel 
                    knowledgeGraph={appState.knowledge_graph}
                    userId={userId}
                  />
                )}
              </div>
            </div>
          )}
          {activeMainTab === 'resource' && (
            <div className="resource-container">
              <ResourcePanel 
                recommendedResources={appState.recommended_resources}
                generatedResources={appState.generated_resource}
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