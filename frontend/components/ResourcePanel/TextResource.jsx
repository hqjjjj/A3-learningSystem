// TextResource.jsx
import React from 'react';

const TextResource = ({ content, title }) => {
  return (
    <div>
      <div style={{ fontSize: '14px', lineHeight: 1.6, color: '#374151' }}>
        {content}
      </div>
    </div>
  );
};

export default TextResource;