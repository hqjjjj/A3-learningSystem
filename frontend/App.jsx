
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
    setIsLoading(true); // 显示加载弹窗
    
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
        chat_history: [],
        generated_resource:{},
      }));
      
      // 3. 标记为已登录，跳转到 MainPage
      // 同时关闭弹窗（因为 LoginPage 会被卸载）
      setIsLoggedIn(true);
      setIsLoading(false); // 立即关闭弹窗
      
    } catch (error) {
      console.error('加载用户状态失败:', error);
      // 登录失败，关闭弹窗并显示错误
      setIsLoading(false);
      alert('登录失败，请重试');
    }
  };

  // 未登录显示登录页
  if (!isLoggedIn) {
    return <LoginPage onLogin={handleLoginSuccess} isLoading={isLoading} />;
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