// src/pages/LoginPage.jsx
import React, { useState } from 'react';

/**
 * 功能：
 * - 登录：输入 user_id，跳转 MainPage
 * - 注册：输入新的 user_id，跳转 MainPage
 * - 加载弹窗：纯文字跳动动画（由父组件控制）
 */

const LoginPage = ({ onLogin, isLoading }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [userId, setUserId] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!userId.trim()) {
      setError('请输入用户ID');
      return;
    }
    
    setError('');
    // 直接调用父组件的登录方法，由父组件控制加载状态
    onLogin(userId.trim());
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError('');
    setUserId('');
  };

  // 跳动文字组件
  const BouncingText = ({ text }) => {
    return (
      <div style={{
        display: 'flex',
        gap: '2px',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        {text.split('').map((char, index) => (
          <span
            key={index}
            style={{
              display: 'inline-block',
              fontSize: '36px',
              fontWeight: 600,
              color: '#ffffff',
              textShadow: '0 4px 20px rgba(0,0,0,0.3)',
              animation: 'bounceText 0.6s ease-in-out infinite',
              animationDelay: `${index * 0.08}s`
            }}
          >
            {char === ' ' ? '\u00A0' : char}
          </span>
        ))}
      </div>
    );
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      width: '100%',
      background: '#f5f7fa',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '16px',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        width: '100%',
        maxWidth: '400px',
        padding: '32px'
      }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '24px'
        }}>
          <h1 style={{
            margin: 0,
            fontSize: '28px',
            fontWeight: 600,
            color: '#1a1a2e'
          }}>
            学习助手
          </h1>
          <p style={{
            margin: '8px 0 0 0',
            fontSize: '14px',
            color: '#6b7280'
          }}>
            {isLogin ? '登录继续学习' : '创建新账号'}
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="请输入用户ID(例：u001)"
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '10px 14px',
                fontSize: '14px',
                border: error ? '1px solid #ef4444' : '1px solid #d1d5db',
                borderRadius: '8px',
                outline: 'none',
                boxSizing: 'border-box',
                transition: 'border-color 0.2s',
                background: isLoading ? '#f3f4f6' : 'white',
                cursor: isLoading ? 'not-allowed' : 'text'
              }}
              onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
              onBlur={(e) => {
                if (!error) e.target.style.borderColor = '#d1d5db';
              }}
            />
            {error && (
              <p style={{
                margin: '8px 0 0 0',
                fontSize: '12px',
                color: '#ef4444'
              }}>
                {error}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '12px',
              background: isLoading ? '#93c5fd' : '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 500,
              cursor: isLoading ? 'not-allowed' : 'pointer',
              transition: 'background 0.2s'
            }}
            onMouseEnter={(e) => {
              if (!isLoading) e.target.style.background = '#2563eb';
            }}
            onMouseLeave={(e) => {
              if (!isLoading) e.target.style.background = '#3b82f6';
            }}
          >
            {isLoading ? '处理中...' : (isLogin ? '登录' : '注册')}
          </button>
        </form>

        <div style={{
          textAlign: 'center',
          marginTop: '20px',
          fontSize: '14px',
          color: '#6b7280'
        }}>
          {isLogin ? '还没有账号？' : '已有账号？'}
          <button
            onClick={toggleMode}
            disabled={isLoading}
            style={{
              background: 'none',
              border: 'none',
              color: isLoading ? '#9ca3af' : '#3b82f6',
              cursor: isLoading ? 'not-allowed' : 'pointer',
              fontSize: '14px',
              fontWeight: 500,
              marginLeft: '4px'
            }}
          >
            {isLogin ? '立即注册' : '去登录'}
          </button>
        </div>
      </div>

      {/* 加载弹窗  */}
      {isLoading && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 9999,
          backdropFilter: 'blur(6px)'
        }}>
          <BouncingText text={isLogin ? '登录中...' : '注册中...'} />
        </div>
      )}

      {/* 全局动画样式 */}
      <style>{`
        @keyframes bounceText {
          0%, 100% {
            transform: translateY(0);
            opacity: 0.5;
          }
          50% {
            transform: translateY(-20px);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
};



export default LoginPage;