import React from 'react';

const MarkdownResource = ({ content, title }) => {
  // ========== 改动5：添加 Markdown 转 HTML 渲染 ==========
  // 目的：思维导图内容以结构化格式显示（标题层级、列表等）
 
  const renderMarkdown = (text) => {
    if (!text) return '';
    
    let html = text;
    
    // 三级标题
    html = html.replace(/^### (.*$)/gim, '<h3 style="font-size:16px;margin:12px 0 8px;color:#1E293B;font-weight:600;">$1</h3>');
    
    // 二级标题
    html = html.replace(/^## (.*$)/gim, '<h2 style="font-size:18px;margin:16px 0 10px;color:#1E293B;border-bottom:2px solid #e5e7eb;padding-bottom:6px;">$1</h2>');
    
    // 一级标题
    html = html.replace(/^# (.*$)/gim, '<h1 style="font-size:20px;margin:20px 0 12px;color:#1E293B;border-bottom:2px solid #3b82f6;padding-bottom:8px;">$1</h1>');
    
    // 列表项（-, +, *）
    html = html.replace(/^- (.*$)/gim, '<li style="margin:4px 0;padding-left:4px;">$1</li>');
    html = html.replace(/^\+ (.*$)/gim, '<li style="margin:4px 0;padding-left:4px;">$1</li>');
    html = html.replace(/^\* (.*$)/gim, '<li style="margin:4px 0;padding-left:4px;">$1</li>');
    
    // 粗体
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#1E293B;">$1</strong>');
    
    // 换行转<br/>
    html = html.replace(/\n/g, '<br/>');
    
    // 将连续的列表项包裹在 ul 中
    html = html.replace(/((?:<li.*<\/li>\s*)+)/g, '<ul style="margin:8px 0;padding-left:20px;list-style-type:disc;">$1</ul>');
    
    return html;
  };

  return (
    <div style={{ 
      fontSize: '14px', 
      lineHeight: 1.8, 
      color: '#374151',
      padding: '4px 0'
    }}>
      <div dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }} />
    </div>
  );
};

export default MarkdownResource;