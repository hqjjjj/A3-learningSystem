// MainPage.jsx
import React, { useState } from 'react';
import ProfilePanel from './components/ProfilePanel';
import ChatPanel from './components/ChatPanel';
import PathPanel from './components/PathPanel';
import KnowledgeGraphPanel from './components/KnowledgeGraphPanel'; // 新组件，队友实现
import ResourcePanel from './components/ResourcePanel';
import './MainPage.css';
import chatIcon from '../img/1779594814480.png';
import profileIcon from '../img/1779594816401.png';
const MainPage = () => {
  // 左侧折叠状态
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // 右侧主 Tab：'path' 或 'resource'
  const [activeMainTab, setActiveMainTab] = useState('path');

  // 路径区子 Tab：'learningPath' 或 'knowledgeGraph'
  const [activePathTab, setActivePathTab] = useState('learningPath');

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
              <ProfilePanel />
            </div>
            <div className="chat-section">
              <ChatPanel />
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
                {activePathTab === 'learningPath' && <PathPanel />}
                {activePathTab === 'knowledgeGraph' && <KnowledgeGraphPanel />}
              </div>
            </div>
          )}
          {activeMainTab === 'resource' && (
            <div className="resource-container">
              <ResourcePanel />
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default MainPage;