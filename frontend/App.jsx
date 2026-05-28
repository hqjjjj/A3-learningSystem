// src/App.jsx
import React, { useState } from 'react';
import LoginPage from './pages/LoginPage';
import MainPage from './MainPage';
import { initialAppState } from './appState';

const App = () => {
  const [appState, setAppState] = useState(initialAppState);
  const [isLoggedIn, setIsLoggedIn] = useState(false); 

  // 登录/注册成功回调
  const handleLoginSuccess = (userId, profile) => {
    setAppState(prev => ({
      ...prev,
      user_id: userId,
      profile: { ...prev.profile, ...profile }  // 合并后端返回的用户画像
    }));
    setIsLoggedIn(true);
  };

  // 如果未登录，显示登录界面；已登录显示主界面，并传入 appState 和 setAppState
  if (!isLoggedIn && !appState.user_id) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  // 已登录，渲染主界面，将 appState 和 setAppState 以及 user_id 传给 MainPage
  return (
    <MainPage
      appState={appState}
      setAppState={setAppState}
      userId={appState.user_id}
    />
  );
};

export default App;