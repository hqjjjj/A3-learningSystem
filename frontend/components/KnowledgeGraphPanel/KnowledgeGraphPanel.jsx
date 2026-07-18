import React, { useState, useEffect, useRef, useCallback } from 'react';
// ========== 仅新增静态导入，其余头部不动 ==========
import indexData from './knowledge/index.json';
const allChapterFiles = import.meta.glob('./knowledge/*.json', { eager: true });

// 【下方所有子组件、样式、渲染逻辑完全保留你原来代码，只改两处数据读取】
// ========== 子组件部分原样不动（你原本的LeafNode、TextNode、AnswerContainer、QuestionNode、LazyContentNode、TopicNode全部保留） ==========
const LeafNode = ({ icon, label, onClick, customStyle }) => {
  return (
    <li className="tree-node leaf-node" style={{ paddingLeft: '28px' }}>
      <div
        className="node-content"
        style={{ cursor: onClick ? 'pointer' : 'default', ...customStyle }}
        onClick={onClick}
      >
        <span className="toggle-icon" style={{ opacity: 0.4 }}>•</span>
        <span className="node-name">{icon} {label}</span>
      </div>
    </li>
  );
};

const TextNode = ({ content }) => {
  return (
    <li className="tree-node leaf-node" style={{ paddingLeft: '28px' }}>
      <div className="node-content" style={{ cursor: 'default', background: '#faf9f5' }}>
        <span className="toggle-icon" style={{ opacity: 0.4 }}>•</span>
        <span className="node-name" style={{ whiteSpace: 'normal', maxWidth: '600px' }}>
          {content}
        </span>
      </div>
    </li>
  );
};

const AnswerContainer = ({ question }) => {
  const [showAnswer, setShowAnswer] = useState(false);
  return (
    <div style={{ marginLeft: '28px', marginTop: '6px' }}>
      <LeafNode
        icon={showAnswer ? '🔓' : '🔒'}
        label={showAnswer ? '答案与解析' : '查看答案与解析'}
        onClick={() => setShowAnswer(!showAnswer)}
        customStyle={{ background: '#e0f2fe' }}
      />
      {showAnswer && (
        <div className="answer-container show">
          <div className="answer-card">
            <strong>答案：</strong> {question?.answer || '暂无'}<br />
            <strong>解析：</strong> {question?.analysis || '暂无'}
          </div>
        </div>
      )}
    </div>
  );
};

const QuestionNode = ({ question, index }) => {
  const [expanded, setExpanded] = useState(false);
  const displayName = question?.question
    ? (question.question.length > 55 ? question.question.substring(0, 55) + '...' : question.question)
    : `题目${index}`;

  return (
    <li className="tree-node detail-node">
      <div className="node-content" onClick={() => setExpanded(!expanded)}>
        <span className="toggle-icon">{expanded ? '▼' : '▶'}</span>
        <span className="node-name">{displayName}</span>
      </div>
      {expanded && (
        <div className="children" style={{ marginLeft: '28px' }}>
          {question?.options?.length > 0 && (
            <LeafNode  label={`选项：${question.options.join(' ｜ ')}`} />
          )}
          <AnswerContainer question={question} />
        </div>
      )}
    </li>
  );
};

const LazyContentNode = ({ label, icon, loadChildren }) => {
  const [expanded, setExpanded] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [children, setChildren] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    if (expanded) {
      setExpanded(false);
      return;
    }
    if (!loaded && !loading) {
      setLoading(true);
      try {
        const result = await loadChildren();
        setChildren(result);
        setLoaded(true);
      } catch (err) {
        console.error('加载失败:', err);
        setChildren(<div style={{ color: 'red', padding: '8px' }}>加载失败</div>);
      }
      setLoading(false);
    }
    setExpanded(true);
  };

  return (
    <li className="tree-node detail-node">
      <div className="node-content" onClick={handleClick}>
        <span className="toggle-icon">{loading ? '⏳' : (expanded ? '▼' : '▶')}</span>
        <span className="node-name">{icon} {label}</span>
      </div>
      {expanded && loaded && <div className="children" style={{ marginLeft: '28px' }}>{children}</div>}
    </li>
  );
};

const TopicNode = ({ topic }) => {
  const [expanded, setExpanded] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [contentChildren, setContentChildren] = useState(null);
  const [loading, setLoading] = useState(false);

  const difficultyBadge = topic?.difficulty ? (
    <span className={`difficulty-badge difficulty-${topic.difficulty}`}>
      {topic.difficulty === 'easy' ? '简单' : topic.difficulty === 'medium' ? '中等' : '困难'}
    </span>
  ) : null;

  const loadContent = useCallback(async () => {
    const content = topic?.content || {};
    const children = [];
    const contentMap = {
      '核心解释': content.explanation,
      '示例': content.example,
      '小结': content.summary
    };

    Object.entries(contentMap).forEach(([label, value]) => {
      if (value) {
        children.push(
          <LazyContentNode
            key={label}
            label={label}
            icon=""
            loadChildren={() => Promise.resolve(<TextNode content={value} />)}
          />
        );
      }
    });

    if (topic?.common_mistakes?.length > 0) {
      children.push(
        <LazyContentNode
          key="mistakes"
          label={`⚠️ 常见误区 (${topic.common_mistakes.length})`}
          icon=""
          loadChildren={() => Promise.resolve(
            topic.common_mistakes.map((mistake, idx) => (
              <LeafNode key={idx} icon="⚠️" label={`误区 ${idx + 1}: ${mistake}`} />
            ))
          )}
        />
      );
    }

    if (topic?.questions?.length > 0) {
      children.push(
        <LazyContentNode
          key="questions"
          label={` 练习题 (${topic.questions.length})`}
          icon=""
          loadChildren={() => Promise.resolve(
            topic.questions.map((q, idx) => <QuestionNode key={idx} question={q} index={idx + 1} />)
          )}
        />
      );
    }
    return children;
  }, [topic]);

  const handleClick = async () => {
    if (expanded) {
      setExpanded(false);
      return;
    }
    if (!loaded && !loading) {
      setLoading(true);
      try {
        const result = await loadContent();
        setContentChildren(result);
        setLoaded(true);
      } catch (err) {
        console.error('加载失败:', err);
        setContentChildren(<div style={{ color: 'red', padding: '8px' }}>加载失败</div>);
      }
      setLoading(false);
    }
    setExpanded(true);
  };

  return (
    <li className="tree-node topic-node">
      <div className="node-content" onClick={handleClick}>
        <span className="toggle-icon">{loading ? '⏳' : (expanded ? '▼' : '▶')}</span>
        <span className="node-name">{topic?.name || '未知知识点'} {difficultyBadge}</span>
      </div>
      {expanded && loaded && <div className="children" style={{ marginLeft: '28px' }}>{contentChildren}</div>}
    </li>
  );
};

// ========== 仅修改章节文件读取逻辑，其余交互样式不动 ==========
const ChapterNode = ({ chapter, chapterCache }) => {
  const [expanded, setExpanded] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleClick = async () => {
    if (expanded) {
      setExpanded(false);
      return;
    }
    if (!loaded && !loading) {
      setLoading(true);
      try {
        let data = chapterCache.current[chapter.id];
        if (!data) {
          const fileName = chapter.file;
          const matchKey = Object.keys(allChapterFiles).find(k => k.endsWith(fileName));
          data = matchKey ? allChapterFiles[matchKey].default : {};
          chapterCache.current[chapter.id] = data;
        }
        setTopics(data.topics || []);
        setLoaded(true);
      } catch (err) {
        console.error('章节加载失败:', err);
        setTopics([]);
        setLoaded(true);
      }
      setLoading(false);
    }
    setExpanded(true);
  };

  return (
    <li className="tree-node chapter-node">
      <div className="node-content" onClick={handleClick}>
        <span className="toggle-icon">{loading ? '⏳' : (expanded ? '▼' : '▶')}</span>
        <span className="node-name">{chapter?.name || '未知章节'}</span>
      </div>
      {expanded && loaded && (
        <div className="children" style={{ marginLeft: '28px' }}>
          {topics.length === 0 ? (
            <LeafNode label="暂无知识点" />
          ) : (
            topics.map((topic, idx) => <TopicNode key={idx} topic={topic} />)
          )}
        </div>
      )}
    </li>
  );
};

// ========== 主组件：仅修改useEffect数据读取，其余布局样式完全不变 ==========
const KnowledgeGraphPanel = () => {
  const [chapters, setChapters] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [rootExpanded, setRootExpanded] = useState(false);
  const chapterCache = useRef({});

  useEffect(() => {
    setChapters(indexData?.chapters || []);
    setLoaded(true);
  }, []);

  const handleRootClick = () => setRootExpanded(!rootExpanded);

  if (!loaded) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: '#94a3b8' }}>
        加载操作系统知识库...
      </div>
    );
  }

  return (
    <div style={{
      width: '100%',
      padding: '20px',
      background: '#f8fafc',
      borderRadius: '16px',
      minHeight: '500px',
      maxHeight: '700px',
      overflowY: 'auto'
    }}>
      <div style={{ marginBottom: '16px', fontSize: '18px', fontWeight: '600', color: '#1e293b' }}>
         知识图谱
        <span style={{ fontSize: '12px', color: '#94a3b8', marginLeft: '12px' }}>
          {chapters.length} 章
        </span>
      </div>

      <div className="tree-container" style={{ background: 'white', borderRadius: '16px', padding: '20px' }}>
        <ul className="tree-root" style={{ listStyle: 'none', paddingLeft: 0 }}>
          <li className="tree-node root-node" style={{ listStyle: 'none' }}>
            <div
              className="node-content"
              onClick={handleRootClick}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '12px 24px',
                background: 'linear-gradient(135deg, #6b9cf7 0%, #b3cdf9 100%)',
                borderRadius: '16px',
                cursor: 'pointer',
                width: 'fit-content',
                minWidth: '180px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
              }}
            >
              <span className="toggle-icon" style={{ color: '#133565', fontSize: '14px' }}>
                {rootExpanded ? '▼' : '▶'}
              </span>
              <span className="node-name" style={{ color: '#1f2937', fontSize: '18px', fontWeight: 'bold' }}>
                操作系统
              </span>
            </div>
            {rootExpanded && (
              <div className="children" style={{ marginLeft: '28px', paddingLeft: 0 }}>
                {chapters.map((chapter, idx) => (
                  <ChapterNode key={idx} chapter={chapter} chapterCache={chapterCache} />
                ))}
              </div>
            )}
          </li>
        </ul>
      </div>

      <style>{`
        .tree-node { list-style: none; position: relative; padding-left: 28px; margin: 6px 0; }
        .tree-node::before { content: ''; position: absolute; left: 8px; top: 20px; width: 16px; height: 1px; background: #cbd5e1; }
        .tree-node::after { content: ''; position: absolute; left: 8px; top: 0; width: 1px; height: 100%; background: #cbd5e1; }
        .tree-node:last-child::after { height: 20px; }
        .tree-root { list-style: none; position: relative; }
        .node-content { display: flex; align-items: center; gap: 10px; padding: 8px 16px; background: white; border-radius: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); cursor: pointer; transition: all 0.2s; border: 1px solid #15181b; margin: 4px 0; width: fit-content; min-width: 180px; }
        .node-content:hover { transform: translateX(4px); background: #fef9e3; }
        .toggle-icon { font-size: 12px; color: #64748b; width: 20px; text-align: center; }
        .node-name { font-size: 14px; font-weight: 500; color: #1f2937; flex: 1; }
        .root-node .node-content { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); border: none; }
        .root-node .node-name, .root-node .toggle-icon { color: white; }
        .chapter-node .node-content { background: linear-gradient(135deg, #f4a3d6 0%, #f7dbea 100%); border: none; }
        .chapter-node .node-name, .chapter-node .toggle-icon { color: #050f40; }
        .topic-node .node-content { background: #e0f2fe; border: 1px solid #7dd3fc; }
        .detail-node .node-content { background: #fef9c3; border: 1px solid #facc15; }
        .leaf-node .node-content { background: #f8fafc; border: 1px solid #cbd5e1; }
        .answer-card { background: #dcfce7; padding: 10px 14px; border-radius: 10px; font-size: 12px; line-height: 1.5; color: #166534; border-left: 3px solid #22c55e; }
        .difficulty-badge { display: inline-block; font-size: 10px; padding: 2px 8px; border-radius: 20px; margin-left: 8px; }
        .difficulty-easy { background: #bbf7d0; color: #166534; }
        .difficulty-medium { background: #fed7aa; color: #9a3412; }
        .difficulty-hard { background: #fecaca; color: #991b1b; }
        .children { margin-left: 28px; padding-left: 0; }
      `}</style>
    </div>
  );
};

export default KnowledgeGraphPanel;
