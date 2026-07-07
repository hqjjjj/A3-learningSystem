// src/App.jsx
import React, { useState } from 'react';
import LoginPage from './pages/LoginPage';
import MainPage from './pages/MainPage';
import { appState as initialAppState } from './state/appState';
import * as api from './api/api';

const App = () => {
  const [appState, setAppState] = useState(initialAppState);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // 登录时获取用户数据
  const handleLoginSuccess = async (userId) => {
    setIsLoading(true);
    try {
      // 1. 从后端加载用户状态
      const data = await api.loadUserState(userId);
      // 2. 合并到 appState
      setAppState(prev => ({
        ...prev,
        user_id: userId,
        profile: data.profile || {},
        learning_path: data.learning_path || [],
        recommended_resources: data.recommended_resources || [],
        topic: data.topic || '',
        current_progress: data.current_progress || 0,
        // chat_history 根据需要保留，后端不持久化则置空
        chat_history: [],
        generated_resource:{},
      }));
      setIsLoggedIn(true);
    } catch (error) {
      console.error('加载用户状态失败:', error);
      // 即使加载失败，也允许登录（显示空白状态）
      setAppState(prev => ({ ...prev, user_id: userId }));
      setIsLoggedIn(true);
    } finally {
      setIsLoading(false);
    }
  };

  // 未登录显示登录页
  if (!isLoggedIn && !appState.user_id) {
    return <LoginPage onLogin={handleLoginSuccess} loading={isLoading} />;
  }

  // 已登录显示主页
  return (
    <MainPage
      appState={appState}
      setAppState={setAppState}
      userId={appState.user_id}
    />
  );
};

export default App;