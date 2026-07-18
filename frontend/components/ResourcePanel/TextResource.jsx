import React from 'react';

const TextResource = ({ content, title }) => {
  // 添加文本格式化功能
  // 目的：知识点讲解和扩展材料显示更清晰（标题、加粗、段落）
 
  const formatText = (text) => {
    if (!text) return '';
    
    let formatted = text;
    
    // 二级标题
    formatted = formatted.replace(/^## (.*$)/gim, '<h3 style="font-size:16px;margin:12px 0 8px;color:#1E293B;font-weight:600;">$1</h3>');
    
    // 三级标题
    formatted = formatted.replace(/^### (.*$)/gim, '<h4 style="font-size:14px;margin:10px 0 6px;color:#1E293B;font-weight:600;">$1</h4>');
    
    // 加粗
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong style="color:#1E293B;">$1</strong>');
    
    // 换行转段落
    formatted = formatted.split('\n\n').map(p => 
      p.trim() ? `<p style="margin:8px 0;line-height:1.8;">${p.replace(/\n/g, '<br/>')}</p >` : ''
    ).join('');
    
    return formatted;
  };

  // 检测是否包含 HTML 标签
  const isHtml = /<[a-z][\s\S]*>/i.test(content);

  return (
    <div style={{ 
      fontSize: '14px', 
      lineHeight: 1.8, 
      color: '#374151',
      padding: '4px 0'
    }}>
      {isHtml ? (
        <div dangerouslySetInnerHTML={{ __html: content }} />
      ) : (
        <div dangerouslySetInnerHTML={{ __html: formatText(content) }} />
      )}
    </div>
  );
};

export default TextResource;