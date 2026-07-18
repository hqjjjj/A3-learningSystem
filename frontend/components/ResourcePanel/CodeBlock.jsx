import React, { useState } from 'react';

const CodeBlock = ({ code, language = 'javascript' }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // ========== 最简版本 - 只做转义 ==========
  const highlightCode = (code, lang) => {
    if (!code) return '';
    
    
    return code
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  };

  return (
    <div style={{
      background: '#f6f8fa',
      border: '1px solid #E2E8F0',
      borderRadius: '8px',
      overflow: 'hidden'
    }}>
      <div style={{
        padding: '8px 16px',
        background: '#f1f3f5',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid #E2E8F0'
      }}>
        <span style={{ 
          fontSize: '12px', 
          color: '#475569',
          fontWeight: 500
        }}>
          {language}
        </span>
        <button
          style={{
            padding: '4px 12px',
            background: copied ? '#10b981' : '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            fontSize: '12px',
            cursor: 'pointer',
            transition: 'background 0.2s'
          }}
          onClick={handleCopy}
        >
          {copied ? '已复制' : '复制'}
        </button>
      </div>
      <pre style={{
        padding: '16px',
        margin: 0,
        overflow: 'auto',
        fontSize: '13px',
        fontFamily: 'Consolas, Monaco, "Courier New", monospace',
        lineHeight: 1.6,
        color: '#1E293B',
        background: '#f6f8fa'
      }}>
        <code>{highlightCode(code, language)}</code>
      </pre>
    </div>
  );
};





export default CodeBlock;