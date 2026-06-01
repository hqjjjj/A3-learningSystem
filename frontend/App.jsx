import React, { useState } from 'react';
import LoginPage from './pages/LoginPage';  
import MainPage from './pages/MainPage';    
import { appState as initialAppState } from './state/appState';

const App = () => {
  const [appState, setAppState] = useState(initialAppState);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // 登录/注册成功回调
  const handleLoginSuccess = (userId, profile = {}) => {
    setAppState(prev => ({
      ...prev,
      user_id: userId,
      profile: { ...prev.profile, ...profile }
    }));
    setIsLoggedIn(true);   //标记已登录
  };

  // 未登录:显示登录页
  if (!isLoggedIn && !appState.user_id) {
    return <LoginPage onLogin={handleLoginSuccess} />;
  }

  // 已登录:显示主页
  return (
    <MainPage
      appState={appState}
      setAppState={setAppState}
      userId={appState.user_id}   
    />
  );
};

export default App;