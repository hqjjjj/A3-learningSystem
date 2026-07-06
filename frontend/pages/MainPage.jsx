
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

//isloding??zuoyong ??


const MainPage = ({appState, setAppState, userId}) => {
  // 左侧折叠状态
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // 右侧主 Tab：'path' 或 'resource'
  const [activeMainTab, setActiveMainTab] = useState('path');

  // 路径区子 Tab：'learningPath' 或 'knowledgeGraph'
  const [activePathTab, setActivePathTab] = useState('learningPath');


  const [isLoading, setIsLoading] = useState(false);

  // 辅助函数：用于合并后端返回更新
   const mergeAppState = (updates) => {
    setAppState(prev => ({
      ...prev,
      ...updates,
       profile: updates.profile ?? prev.profile,
      // 推荐资源如果是数组则直接替换
      recommended_resources: updates.recommended_resources ?? prev.recommended_resources,
      generated_resource: updates.generated_resource ?? prev.generated_resource,
      chat_history: updates.chat_history ?? prev.chat_history,
      learning_path: updates.learning_path ?? prev.learning_path,
      topic: updates.topic ?? prev.topic,
      current_progress:updates.current_progress ?? prev.current_progress
    }));
  };


  // 聊天模块回调函数
  const handleSendMessage=async(message)=>{
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
      
      mergeAppState({
        chat_history: [...appState.chat_history, assistantMsg],
        profile: data.profile,
        recommended_resources: data.recommended_resources,
        learning_path: data.learning_path,   // 后端可能返回更新的学习路径
        topic: data.topic,
        current_progress: data.current_progress
      })
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
  }
   
//资源生成回调函数
const handleGenerateResource= async(resourceType)=>{
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

};

//提交答案回调函数
const handleSubmitAnswer =async(correct_rate,duration)=>{
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
};

// 完成浏览回调函数
const handleFinishResource=async(resourceType,duration)=>{
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
}

//切换主题回调函数
const handleTopicChange=async(newTopic)=>{
  setIsLoading(true);
  try{
    // 先更新主题，让用户立即看到反馈
    mergeAppState({ topic: newTopic });
    
    // 然后获取新的学习路径数据
    const pathData=await api.fetchPath(userId,newTopic);
    
    // 更新学习路径、推荐资源和学习进度
    // 如果新主题是路径中的下一个节点，进度应该增加
    const currentIndex = appState.learning_path ? appState.learning_path.indexOf(appState.topic) : -1;
    const newIndex = pathData.learning_path ? pathData.learning_path.indexOf(newTopic) : -1;
    const progressIncrement = newIndex > currentIndex ? 1 : 0;
    
    mergeAppState({
        learning_path: pathData.learning_path,
        recommended_resources: pathData.recommended_resources || [],
        current_progress: (appState.current_progress || 0) + progressIncrement
    });
  }catch (error) {
      console.error('切换知识点失败', error);
      // 如果获取新路径失败，尝试获取当前主题的路径
      try {
        const pathData=await api.fetchPath(userId,newTopic);
        
        // 更新学习路径、推荐资源和学习进度
        const currentIndex = appState.learning_path ? appState.learning_path.indexOf(appState.topic) : -1;
        const newIndex = pathData.learning_path ? pathData.learning_path.indexOf(newTopic) : -1;
        const progressIncrement = newIndex > currentIndex ? 1 : 0;
        
        mergeAppState({
            learning_path: pathData.learning_path,
            recommended_resources: pathData.recommended_resources || [],
            current_progress: (appState.current_progress || 0) + progressIncrement
        });
      } catch (retryError) {
        console.error('重试获取路径失败', retryError);
        // 至少更新主题和进度
        mergeAppState({
          topic: newTopic,
          current_progress: (appState.current_progress || 0) + 1
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

    // 初始化加载学习路径
  useEffect(() => {
    
    const loadInitial = async () => {
      try {
        const pathData = await api.fetchPath(userId,appState.topic);
        mergeAppState({
          learning_path: pathData.learning_path,
          recommended_resources: pathData.recommended_resources || []
        });
      } catch (error) {
        console.error(error);
      }
    };
    if (userId) loadInitial();
    
  }, [userId]);

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

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
              <ProfilePanel 
              profile={appState.profile}/>
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
        {/* 折叠时只显示一个窄条（可选：显示图标） */}
        {isSidebarCollapsed && (
            <div className="collapsed-icons">
            <img src={profileIcon} alt="用户画像" className="icon-img" title="用户画像" />
            <img src={chatIcon} alt="聊天" className="icon-img" title="聊天" />
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
                     onTopicChange={handleTopicChange}
                    />}
                {activePathTab ==='knowledgeGraph' && (
                         <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
                    知识图谱功能开发中，敬请期待...
                      </div>
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