// MarkdownResource.jsx
import React from 'react';

const MarkdownResource = ({ content, title }) => {
  return (
    <div style={{ fontSize: '14px', lineHeight: 1.6 }}>
      {content}
    </div>
  );
};

export default MarkdownResource;