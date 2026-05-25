import React from 'react';
import MessageBubble from './MessageBubble';

const ChatMessageList = ({ chatHistory, isLoading, messagesEndRef }) => {
  if (chatHistory.length === 0) {
    return (
      <div style={{
        textAlign: 'center',
        padding: '60px 20px',
        color: '#9ca3af'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>🤖</div>
        <p style={{ margin: 0, fontSize: '16px' }}>您好！我是您的学习助手</p >
        <p style={{ margin: '8px 0 0 0', fontSize: '13px' }}>
          您可以问我关于操作系统内存管理的问题
        </p >
      </div>
    );
  }

  return (
    <>
      {chatHistory.map((msg, index) => (
        <MessageBubble 
          key={index}
          role={msg.role}
          content={msg.content}
        />
      ))}
      {isLoading && (
        <MessageBubble 
          role="assistant"
          content="正在思考..."
          isLoading={true}
        />
      )}
      <div ref={messagesEndRef} />
    </>
  );
};

export default ChatMessageList;