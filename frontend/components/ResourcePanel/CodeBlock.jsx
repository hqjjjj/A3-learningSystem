// CodeBlock.jsx
import React, { useState } from 'react';

const CodeBlock = ({ code, language = 'javascript' }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{
      background: '#ffffff',
      border: '1px solid #E2E8F0',
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      <div style={{
        padding: '8px 12px',
        background: '#f8fafc',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span style={{ fontSize: '12px', color: '#475569' }}>{language}</span>
        <button
          style={{
            padding: '4px 8px',
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '11px',
            cursor: 'pointer'
          }}
          onClick={handleCopy}
        >
          {copied ? '已复制' : '复制'}
        </button>
      </div>
      <pre style={{
        padding: '12px',
        margin: 0,
        overflow: 'auto',
        fontSize: '12px',
        color: '#1E293B'
      }}>
        <code>{code}</code>
      </pre>
    </div>
  );
};

export default CodeBlock;