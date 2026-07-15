
// MainPage.jsx
import React, { useState, useEffect } from 'react';   
import ProfilePanel from '../components/ProfilePanel';
import ChatPanel from "../components/ChatPanel/ChatPanel";
import KnowledgeGraphPanel from "../components/KnowledgeGraphPanel/KnowledgeGraphPanel";
import ResourcePanel from "../components/ResourcePanel/ResourcePanel";
import PathPanel from '../components/PathPanel';
import './MainPage.css';
import chatIcon from '../imgs/1779594814480.png';
import profileIcon from '../imgs/1779594816401.png';
import * as api from '../api/api';
import { useCallback } from 'react';


const MainPage = ({appState, setAppState, userId}) => {
  // 左侧折叠状态
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  
  
  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };


  // 右侧主 Tab：'path' 或 'resource'
  const [activeMainTab, setActiveMainTab] = useState('path');

  // 路径区子 Tab：'learningPath' 或 'knowledgeGraph'
  const [activePathTab, setActivePathTab] = useState('learningPath');


  const [isLoading, setIsLoading] = useState(false);

  // 辅助函数：用于合并后端返回更新
const mergeAppState =useCallback((updates) => {
  setAppState(prev => {
    const processedUpdates = typeof updates === 'function' ? updates(prev) : updates;
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


  // 聊天模块回调函数
  const handleSendMessage=useCallback(async(message)=>{
    // 乐观更新：立即显示用户消息
    const userMsg={role :'user',content:message};
    setAppState(prev => ({
      ...prev,
      chat_history: [...prev.chat_history, userMsg]
    }));
    setIsLoading(true);

    try{
      const data=await api.sendChat(userId,message);

      const assistantMsg = { role: 'assistant', content: data.reply };
      
      mergeAppState((prev) => ({
        chat_history: [...prev.chat_history, assistantMsg],
        profile: data.profile,
        recommended_resources: data.recommended_resources,
        learning_path: data.learning_path,   // 后端可能返回更新的学习路径
        topic: data.topic,
        current_progress: data.current_progress
      }));
    }catch(error){
      console.error('发送消息失败', error);
      const errorMsg={ role: 'assistant', content: '抱歉，服务出错了，请稍后再试。' };
      setAppState(prev => ({
        ...prev,
        chat_history: [...prev.chat_history, errorMsg]
      }));
    }finally{
      setIsLoading(false);
    }
  }, [userId, setAppState, mergeAppState]
)
//资源生成回调函数
const handleGenerateResource= useCallback(async(resourceType)=>{
  setIsLoading(true);
  try{
        const data = await api.generateResource(userId, appState.topic, resourceType);
      const newResource=data.generated_resource;
      mergeAppState({
      generated_resource: data.generated_resource,   // 单个资源对象
      topic: data.topic,
      current_progress: data.current_progress
      });
      }catch(error){
        console.error('生成资源失败', error);
      }finally{
        setIsLoading(false);
      }

}, [userId, appState.topic, mergeAppState]);

//提交答案回调函数
const handleSubmitAnswer =useCallback(async(correct_rate,duration)=>{
  setIsLoading(true);
  try{
    const data=await api.submitAnswer(userId,appState.topic,correct_rate,duration);
    mergeAppState({
      profile: data.profile,
      learning_path: data.learning_path,
      recommended_resources: data.recommended_resources,
      topic: data.topic,
      current_progress: data.current_progress
    });
  }catch(error)
  {
    console.error('提交答案失败', error);
    return { correct: false, message: '提交失败，请重试' };
  }finally{
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
        {/* 顶部主 TabBar */}
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

        {/* 主 Tab 内容 */}
        <div className="main-tab-content">
          {activeMainTab === 'path' && (
            <div className="path-container">
              {/* 路径区子 TabBar */}
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
              {/* 子 Tab 内容 */}
              <div className="sub-tab-content">
                {activePathTab === 'learningPath' 
                && <PathPanel
                     learningPath={appState.learning_path}
                     topic={appState.topic}
                     onTopicChange={handlePathNodeClick}
                    />}
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