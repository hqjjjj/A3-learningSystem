import React, { useState } from 'react';

const ChatInput = ({ onSendMessage, isLoading, userId }) => {
  const [inputValue, setInputValue] = useState('');

  const handleSend = () => {
    if (!inputValue.trim() || isLoading) return;
    onSendMessage(inputValue.trim());
    setInputValue('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{
      padding: '16px',
      borderTop: '1px solid #e5e7eb',
      display: 'flex',
      gap: '12px',
      flexShrink: 0
    }}>
      <textarea
        style={{
          flex: 1,
          padding: '10px 14px',
          border: '1px solid #d1d5db',
          borderRadius: '8px',
          fontSize: '14px',
          fontFamily: 'inherit',
          resize: 'none',
          outline: 'none',
          minHeight: '40px'
        }}
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyPress}
        placeholder="输入消息... (Enter 发送，Shift+Enter 换行)"
        rows={2}
        disabled={isLoading}
      />
      <button
        style={{
          padding: '0 24px',
          background: (!inputValue.trim() || isLoading) ? '#9ca3af' : '#3b82f6',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          fontSize: '14px',
          fontWeight: 500,
          cursor: (!inputValue.trim() || isLoading) ? 'not-allowed' : 'pointer'
        }}
        onClick={handleSend}
        disabled={!inputValue.trim() || isLoading}
      >
        发送
      </button>
    </div>
  );
};

export default ChatInput;