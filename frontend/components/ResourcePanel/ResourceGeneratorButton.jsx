import React, { useState } from 'react';

const ResourceGeneratorButton = ({ onGenerate, isLoading, userId }) => {
  const [showOptions, setShowOptions] = useState(false);
  const [selectedType, setSelectedType] = useState('exercise');

  const resourceTypes = [
    { value: 'explanation', label: '📖 知识点讲解' },
    { value: 'exercise', label: '✏️ 练习题' },
    { value: 'code', label: '💻 代码示例' },
    { value: 'mindmap', label: '🧠 思维导图' },
    { value: 'materials', label: '📚 扩展材料' },
    { value: 'animation', label: '🎬 动画演示' }
  ];

  // ========== 改动11：传入数组格式 ==========
  // 目的：与后端 API 保持一致，统一使用数组
  // ==========================================
  const handleGenerate = () => {
    onGenerate([selectedType]);  // 传入数组
    setShowOptions(false);
  };

  return (
    <div style={{ position: 'relative' }}>
      <button
        style={{
          width: '100%',
          padding: '12px 16px',
          background: '#82aaf3',
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
          top: '100%',
          left: 0,
          right: 0,
          background: 'white',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          marginTop: '4px',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
          zIndex: 10,
          maxHeight: '300px',
          overflowY: 'auto'
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
                borderBottom: '1px solid #f0f2f5',
                transition: 'background 0.2s'
              }}
              onMouseEnter={(e) => e.target.style.background = '#f3f4f6'}
              onMouseLeave={(e) => e.target.style.background = 'none'}
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