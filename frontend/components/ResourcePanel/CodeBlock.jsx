import React, { useState } from 'react';



const CodeBlock = ({ code, language = 'javascript' }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // 添加语法高亮功能 
  
  const highlightCode = (code, lang) => {
    let highlighted = code;
    
    // JavaScript/Python 关键词
    const keywords = {
      javascript: ['const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while', 'class', 'import', 'export', 'from', 'new', 'this', 'async', 'await', 'try', 'catch', 'throw', 'switch', 'case', 'break', 'continue'],
      python: ['def', 'class', 'import', 'from', 'return', 'if', 'elif', 'else', 'for', 'while', 'True', 'False', 'None', 'with', 'as', 'try', 'except', 'finally', 'raise', 'break', 'continue', 'pass', 'lambda', 'yield']
    };
    
    const langKeywords = keywords[lang] || keywords.javascript;
    
    // 关键词高亮（蓝色）
    langKeywords.forEach(keyword => {
      const regex = new RegExp(`\\b${keyword}\\b`, 'g');
      highlighted = highlighted.replace(regex, `<span style="color:#d73a49;font-weight:600;">${keyword}</span>`);
    });
    
    // 字符串高亮（绿色）
    highlighted = highlighted.replace(/(['"])(.*?)\1/g, '<span style="color:#032f62;">$1$2$1</span>');
    
    // 注释高亮（灰色）
    highlighted = highlighted.replace(/\/\/.*/g, '<span style="color:#6a737d;">$&</span>');
    highlighted = highlighted.replace(/#.*/g, '<span style="color:#6a737d;">$&</span>');
    
    // 数字高亮（红色）
    highlighted = highlighted.replace(/\b(\d+)\b/g, '<span style="color:#005cc5;">$1</span>');
    
    return highlighted;
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
          {copied ? ' 已复制' : ' 复制'}
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
        <code 
          dangerouslySetInnerHTML={{ 
            __html: highlightCode(code, language) 
          }} 
        />
      </pre>
    </div>
  );
};

export default CodeBlock;