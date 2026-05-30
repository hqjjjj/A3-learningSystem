
import React, { useState, useRef, useEffect } from 'react';
import ChatMessageList from './ChatMessageList';
import ChatInput from './ChatInput';

/**
 * ChatPanel - 聊天面板
 * 
 * 角色: 交互型 + 展示型容器
 * 任务:
 * 1. 提供文本输入框，允许用户自由提问或发送指令
 * 2. 展示与用户的对话历史（chat_history）
 * 3. 调用 sendChat API，将用户消息发送给后端，并将返回的 reply 追加到对话历史中
 * 
 * 子组件:
 * - ChatMessageList: 遍历 chat_history
 * - ChatInput: 输入框 + 发送按钮
 * 
 * Props:
 * - chatHistory: 对话历史数组 [{role: 'user'|'assistant', content: string}]
 * - onSendMessage: 发送消息的回调函数（调用 API）
 * - isLoading: 是否正在加载
 * - userId: 用户ID
 */
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