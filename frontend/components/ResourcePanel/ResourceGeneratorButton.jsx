import React, { useState } from 'react';

const ResourceGeneratorButton = ({ onGenerate, isLoading, userId }) => {
  const [showOptions, setShowOptions] = useState(false);
  const [selectedType, setSelectedType] = useState('exercise');

  const resourceTypes = [
    { value: 'exercise', label: '📝 生成习题' },
    { value: 'code', label: '💻 生成代码示例' },
    { value: 'explanation', label: '📖 生成讲解' }
  ];

  const handleGenerate = () => {
    onGenerate(selectedType);
    setShowOptions(false);
  };

  return (
    <div style={{ position: 'relative' }}>
      <button
        style={{
          width: '100%',
          padding: '12px 16px',
          background: '#10b981',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          fontSize: '14px',
          fontWeight: 500,
          cursor: isLoading ? 'not-allowed' : 'pointer'
        }}
        onClick={() => setShowOptions(!showOptions)}
        disabled={isLoading}
      >
        {isLoading ? '生成中...' : '✨ 生成更多资源'}
      </button>

      {showOptions && (
        <div style={{
          position: 'absolute',
          bottom: '100%',
          left: 0,
          right: 0,
          background: 'white',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          marginBottom: '8px',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
          zIndex: 10
        }}>
          {resourceTypes.map(type => (
            <button
              key={type.value}
              style={{
                display: 'block',
                width: '100%',
                padding: '10px 16px',
                background: 'none',
                border: 'none',
                textAlign: 'left',
                fontSize: '14px',
                cursor: 'pointer',
                borderBottom: '1px solid #f0f2f5'
              }}
              onClick={() => {
                setSelectedType(type.value);
                handleGenerate();
              }}
            >
              {type.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default ResourceGeneratorButton;