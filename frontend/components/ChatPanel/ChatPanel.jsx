import React, { useState, useRef, useEffect } from 'react';
import ChatMessageList from './ChatMessageList';
import ChatInput from './ChatInput';


const ChatPanel = ({ 
  chatHistory = [], 
  onSendMessage, 
  isLoading = false,
  userId 
}) => {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      width: '100%'
    }}>
      {/* 聊天记录区域 */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px'
      }}>
        <ChatMessageList 
          chatHistory={chatHistory} 
          isLoading={isLoading}
          messagesEndRef={messagesEndRef}
        />
      </div>

      {/* 输入框区域 */}
      <ChatInput 
        onSendMessage={onSendMessage}
        isLoading={isLoading}
        userId={userId}
      />
    </div>
  );
};

export default ChatPanel;