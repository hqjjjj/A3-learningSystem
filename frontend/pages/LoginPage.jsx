import React, { useState } from 'react';

/**

 * 功能：
 * - 登录：输入 user_id，跳转 MainPage
 * - 注册：输入新的 user_id，跳转 MainPage

 */

const LoginPage = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);  // true: 登录, false: 注册
  const [userId, setUserId] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!userId.trim()) {
      setError('请输入用户ID');
      return;
    }
    
    // 清除错误，调用父组件回调
    setError('');
    onLogin(userId.trim());
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError('');
    setUserId('');
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
        {/* 头部图标 */}
        <div style={{
          textAlign: 'center',
          marginBottom: '24px'
        }}>
          <div style={{
            fontSize: '48px',
            marginBottom: '12px'
          }}>
            📚
          </div>
          <h1 style={{
            margin: 0,
            fontSize: '24px',
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
          </p >
        </div>

        {/* 表单 */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '14px',
              fontWeight: 500,
              color: '#374151'
            }}>
              用户ID
            </label>
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="例如: u001"
              style={{
                width: '100%',
                padding: '10px 14px',
                fontSize: '14px',
                border: error ? '1px solid #ef4444' : '1px solid #d1d5db',
                borderRadius: '8px',
                outline: 'none',
                boxSizing: 'border-box',
                transition: 'border-color 0.2s'
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
              </p >
            )}
          </div>

          <button
            type="submit"
            style={{
              width: '100%',
              padding: '12px',
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'background 0.2s'
            }}
            onMouseEnter={(e) => e.target.style.background = '#2563eb'}
            onMouseLeave={(e) => e.target.style.background = '#3b82f6'}
          >
            {isLogin ? '登录' : '注册'}
          </button>
        </form>

        {/* 切换模式 */}
        <div style={{
          textAlign: 'center',
          marginTop: '20px',
          fontSize: '14px',
          color: '#6b7280'
        }}>
          {isLogin ? '还没有账号？' : '已有账号？'}
          <button
            onClick={toggleMode}
            style={{
              background: 'none',
              border: 'none',
              color: '#3b82f6',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 500,
              marginLeft: '4px'
            }}
          >
            {isLogin ? '立即注册' : '去登录'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;