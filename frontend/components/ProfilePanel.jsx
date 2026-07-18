import React from 'react';
import WeakPointList from './WeakPointList';
import KnowledgeChart from './KnowledgeChart';

// 认知风格标签映射
const COGNITIVE_LABELS = {
  visual: '视觉型',
  textual: '文字型',
  auditory: '听觉型'
};

// 资源类型映射
const RESOURCE_TYPE_LABELS = {
  explanation: ' 讲解文档',
  mindmap: ' 思维导图',
  exercise: ' 练习题',
  code_example: ' 代码案例',
  animation: ' 教学动画'
};

const ProfilePanel = ({ profile }) => {
  if (!profile || Object.keys(profile).length === 0) {
    return (
      <div style={{
        padding: '20px',
        border: '1px solid #E2E8F0',
        borderRadius: 10,
        color: '#64748b',
        fontSize: 14,
        textAlign: 'center'
      }}>
         暂无画像数据
      </div>
    );
  }

  const cognitiveStyle = profile.cognitive_style || { visual: 0.33, textual: 0.34, auditory: 0.33 };
  const dominantStyle = Object.keys(cognitiveStyle).reduce((a, b) => 
    cognitiveStyle[a] > cognitiveStyle[b] ? a : b
  );

  const resourceTypes = (profile.resource_type || []).map(
    r => RESOURCE_TYPE_LABELS[r] || r
  );

  return (
    <div style={{
      border: '1px solid #E2E8F0',
      borderRadius: 10,
      padding: '16px 18px',
      maxHeight: '100%',
      overflowY: 'auto',
      background: '#ffffff'
    }}>
      
      {/* ===== 标题 ===== */}
      <h3 style={{
        fontSize: 17,
        fontWeight: 600,
        margin: '0 0 14px 0',
        color: '#1E293B',
        textAlign: 'center',
        borderBottom: '2px solid #3b82f6',
        paddingBottom: 8
      }}>
         用户画像
      </h3>

      {/* ===== 第一行：基础信息（4列网格） ===== */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr', 
        gap: '2px 12px',
        marginBottom: 14,
        fontSize: 13,
        color: '#334155',
        background: '#f8fafc',
        padding: '8px 12px',
        borderRadius: 8
      }}>
        <span><strong>专业：</strong>{profile.major || '未知'}</span>
        <span><strong>年级：</strong>{profile.grade || '未知'}</span>
        <span><strong>课程：</strong>{profile.course || '操作系统'}</span>
        <span><strong>目标难度：</strong>
          <span style={{
            color: profile.difficulty === 'easy' ? '#16a34a' : 
                   profile.difficulty === 'hard' ? '#dc2626' : '#f59e0b'
          }}>
            {profile.difficulty === 'easy' ? ' 简单' : 
             profile.difficulty === 'hard' ? ' 困难' : ' 中等'}
          </span>
        </span>
      </div>

      {/* ===== 第二行：学习风格 + 节奏（并排两个卡片） ===== */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr', 
        gap: 10,
        marginBottom: 14
      }}>
        {/* 学习风格 */}
        <div style={{
          background: '#eff6ff',
          borderRadius: 8,
          padding: '8px 12px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 11, color: '#6b7280', fontWeight: 500 }}>📚 学习风格</div>
          <div style={{
            fontSize: 15,
            fontWeight: 600,
            color: '#2563eb'
          }}>
            {profile.learning_style === 'diagram' ? '📐 图解型' : 
             profile.learning_style === 'text' ? '📄 文字型' : 
             profile.learning_style || '未知'}
          </div>
        </div>
        {/* 学习节奏 */}
        <div style={{
          background: profile.learning_pace === 'fast' ? '#f0fdf4' : 
                     profile.learning_pace === 'slow' ? '#fef2f2' : '#f8fafc',
          borderRadius: 8,
          padding: '8px 12px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 11, color: '#6b7280', fontWeight: 500 }}>⏱️ 学习节奏</div>
          <div style={{
            fontSize: 15,
            fontWeight: 600,
            color: profile.learning_pace === 'fast' ? '#16a34a' : 
                   profile.learning_pace === 'slow' ? '#dc2626' : '#6b7280'
          }}>
            {profile.learning_pace === 'fast' ? ' 快速' : 
             profile.learning_pace === 'slow' ? ' 缓慢' : '正常'}
          </div>
        </div>
      </div>

      {/* ===== 第三行：认知风格 ===== */}
      <div style={{ 
        marginBottom: 14,
        background: '#fafafa',
        borderRadius: 8,
        padding: '10px 12px'
      }}>
        <div style={{ 
          fontSize: 12, 
          fontWeight: 600, 
          color: '#1E293B', 
          marginBottom: 6,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span> 认知风格</span>
          <span style={{ 
            fontSize: 11, 
            fontWeight: 400, 
            color: '#3b82f6',
            background: '#eff6ff',
            padding: '0 10px',
            borderRadius: 10
          }}>
            主导：{COGNITIVE_LABELS[dominantStyle] || dominantStyle}
          </span>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {Object.entries(cognitiveStyle).map(([key, value]) => (
            <div key={key} style={{ flex: 1 }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                fontSize: 11,
                color: '#64748b'
              }}>
                <span>{COGNITIVE_LABELS[key] || key}</span>
                <span>{(value * 100).toFixed(0)}%</span>
              </div>
              <div style={{
                width: '100%',
                height: 6,
                background: '#e2e8f0',
                borderRadius: 3,
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${(value || 0) * 100}%`,
                  height: '100%',
                  background: key === dominantStyle ? '#3b82f6' : '#94a3b8',
                  borderRadius: 3
                }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ===== 第四行：资源偏好 ===== */}
      <div style={{ 
        marginBottom: 14,
        background: '#fafafa',
        borderRadius: 8,
        padding: '8px 12px'
      }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: '#1E293B', marginBottom: 4 }}>
           资源偏好
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {resourceTypes.length > 0 ? (
            resourceTypes.map((rt, i) => (
              <span key={i} style={{
                padding: '2px 10px',
                borderRadius: 12,
                background: '#dbeafe',
                color: '#2563eb',
                fontSize: 12
              }}>
                {rt}
              </span>
            ))
          ) : (
            <span style={{ color: '#94a3b8', fontSize: 12 }}>未识别偏好</span>
          )}
        </div>
      </div>

      {/* ===== 第五行：学习进度 ===== */}
      <div style={{ 
        marginBottom: 14,
        background: '#fafafa',
        borderRadius: 8,
        padding: '8px 12px'
      }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: '#1E293B', marginBottom: 2 }}>
           学习进度
        </div>
        <div style={{ fontSize: 13 }}>
          <strong>当前主题：</strong>
          <span style={{
            display: 'inline-block',
            padding: '0 10px',
            borderRadius: 10,
            background: '#dbeafe',
            color: '#2563eb',
            fontSize: 12
          }}>
            {profile.progress?.current_topic || '未开始'}
          </span>
        </div>
        <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
          <strong>已完成：</strong>
          {(profile.progress?.completed_topics || []).length > 0 ? 
            (profile.progress?.completed_topics || []).join(' → ') : 
            '暂无'
          }
        </div>
      </div>

      {/* ===== 第六行：薄弱点 ===== */}
      <WeakPointList weakPoints={profile.weak_points} />

      {/* ===== 第七行：知识掌握度 ===== */}
      <KnowledgeChart knowledgeLevel={profile.knowledge_level} />

      {/* ===== 底部更新时间 ===== */}
      <div style={{
        fontSize: 10,
        color: '#94a3b8',
        textAlign: 'right',
        marginTop: 10,
        borderTop: '1px solid #f1f5f9',
        paddingTop: 6
      }}>
        更新于：{profile.updated_at ? new Date(profile.updated_at).toLocaleString() : '未知'}
      </div>
    </div>
  );
};

export default ProfilePanel;