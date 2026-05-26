import React from 'react';
import ReactMarkdown from 'react-markdown';  // ← 新增导入

const MessageBubble = ({ role, content, isLoading = false }) => {
  const isUser = role === 'user';

  return (
    <div style={{
      display: 'flex',
      gap: '12px',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: '16px'
    }}>
      {!isUser && (
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          background: '#e5e7eb',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '18px',
          flexShrink: 0
        }}>
          🤖
        </div>
      )}
      
      <div style={{
        maxWidth: '70%',
        padding: '10px 14px',
        borderRadius: '12px',
        background: isUser ? '#3b82f6' : '#f3f4f6',
        color: isUser ? 'white' : '#1f2937',
        fontSize: '14px',
        lineHeight: 1.5,
        wordBreak: 'break-word'
      }}>
        {isLoading ? (
          <span style={{ display: 'flex', gap: '4px' }}>
            <span style={{ animation: 'pulse 1.4s infinite 0s' }}>.</span>
            <span style={{ animation: 'pulse 1.4s infinite 0.2s' }}>.</span>
            <span style={{ animation: 'pulse 1.4s infinite 0.4s' }}>.</span>
          </span>
        ) : isUser ? (
          content
        ) : (
        <ReactMarkdown>{content}</ReactMarkdown>  // ← 助手消息支持 Markdown
        )}
      </div>

      {isUser && (
        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          background: '#3b82f6',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '18px',
          flexShrink: 0,
          color: 'white'
        }}>
          👤
        </div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 60%, 100% { opacity: 0; }
          30% { opacity: 1; }
        }
      `}</style>
    </div>
  );
};

export default MessageBubble;