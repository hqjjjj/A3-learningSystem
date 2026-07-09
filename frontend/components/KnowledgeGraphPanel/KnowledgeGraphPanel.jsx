// frontend/components/KnowledgeGraphPanel/KnowledgeGraphPanel.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';

// ========== 配置 ==========
const DATA_PATH = '../../../data/knowledge';
const INDEX_FILE = 'index.json';

// ========== 数据加载 ==========
async function loadIndex() {
    const response = await fetch(`${DATA_PATH}/${INDEX_FILE}`);
    if (!response.ok) throw new Error(`索引加载失败: ${response.status}`);
    const data = await response.json();
    return data.chapters || [];
}

async function loadChapter(chapterId, fileName, chapterCache) {
    if (chapterCache[chapterId]) return chapterCache[chapterId];
    const response = await fetch(`${DATA_PATH}/${fileName}`);
    if (!response.ok) throw new Error(`章节加载失败: ${fileName}`);
    const data = await response.json();
    chapterCache[chapterId] = data;
    return data;
}

// ========== 子组件 ==========

// 叶子节点
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

// 文本节点
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

// 答案容器
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
                        <strong>📖 答案：</strong> {question.answer}<br />
                        <strong>📝 解析：</strong> {question.analysis}
                    </div>
                </div>
            )}
        </div>
    );
};

// 题目节点
const QuestionNode = ({ question, index }) => {
    const [expanded, setExpanded] = useState(false);
    const displayName = `${index}. ${question.question.length > 55 ? question.question.substring(0, 55) + '...' : question.question}`;
    
    return (
        <li className="tree-node detail-node">
            <div className="node-content" onClick={() => setExpanded(!expanded)}>
                <span className="toggle-icon">{expanded ? '▼' : '▶'}</span>
                <span className="node-name">{displayName}</span>
            </div>
            {expanded && (
                <div className="children" style={{ marginLeft: '28px' }}>
                    {question.options && question.options.length > 0 && (
                        <LeafNode icon="📋" label={`选项：${question.options.join(' ｜ ')}`} />
                    )}
                    <AnswerContainer question={question} />
                </div>
            )}
        </li>
    );
};

// 懒加载内容节点
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
            {expanded && loaded && (
                <div className="children" style={{ marginLeft: '28px' }}>
                    {children}
                </div>
            )}
        </li>
    );
};

// 知识点节点
const TopicNode = ({ topic }) => {
    const [expanded, setExpanded] = useState(false);
    const [loaded, setLoaded] = useState(false);
    const [contentChildren, setContentChildren] = useState(null);
    const [loading, setLoading] = useState(false);
    
    const difficultyBadge = topic.difficulty ? (
        <span className={`difficulty-badge difficulty-${topic.difficulty}`}>
            {topic.difficulty === 'easy' ? '简单' : (topic.difficulty === 'medium' ? '中等' : '困难')}
        </span>
    ) : null;
    
    const loadContent = useCallback(async () => {
        const content = topic.content || {};
        const children = [];
        const contentMap = {
            '📖 核心解释': content.explanation,
            '💡 示例': content.example,
            '📌 小结': content.summary
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
        
        if (topic.common_mistakes && topic.common_mistakes.length > 0) {
            children.push(
                <LazyContentNode 
                    key="mistakes"
                    label={`⚠️ 常见误区 (${topic.common_mistakes.length})`}
                    icon=""
                    loadChildren={() => Promise.resolve(
                        topic.common_mistakes.map((mistake, idx) => (
                            <LeafNode key={idx} icon="⚠️" label={`误区 ${idx+1}: ${mistake}`} />
                        ))
                    )}
                />
            );
        }
        
        if (topic.questions && topic.questions.length > 0) {
            children.push(
                <LazyContentNode 
                    key="questions"
                    label={`📝 练习题 (${topic.questions.length})`}
                    icon=""
                    loadChildren={() => Promise.resolve(
                        topic.questions.map((q, idx) => (
                            <QuestionNode key={idx} question={q} index={idx + 1} />
                        ))
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
                <span className="node-name">{topic.name} {difficultyBadge}</span>
            </div>
            {expanded && loaded && (
                <div className="children" style={{ marginLeft: '28px' }}>
                    {contentChildren}
                </div>
            )}
        </li>
    );
};

// 章节节点
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
                const data = await loadChapter(chapter.id, chapter.file, chapterCache);
                setTopics(data.topics || []);
                setLoaded(true);
            } catch (err) {
                console.error('加载失败:', err);
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
                <span className="node-name">{chapter.name}</span>
            </div>
            {expanded && loaded && (
                <div className="children" style={{ marginLeft: '28px' }}>
                    {topics.length === 0 ? (
                        <LeafNode icon="📭" label="暂无知识点" />
                    ) : (
                        topics.map((topic, idx) => (
                            <TopicNode key={idx} topic={topic} />
                        ))
                    )}
                </div>
            )}
        </li>
    );
};

// ========== 主组件 ==========
const KnowledgeGraphPanel = () => {
    const [chapters, setChapters] = useState([]);
    const [loaded, setLoaded] = useState(false);
    const [rootExpanded, setRootExpanded] = useState(false);
    const chapterCache = useRef({});
    
    useEffect(() => {
        const loadData = async () => {
            try {
                const result = await loadIndex();
                setChapters(result);
                setLoaded(true);
            } catch (err) {
                console.error('加载索引失败:', err);
                setLoaded(true);
            }
        };
        loadData();
    }, []);
    
    const handleRootClick = () => {
        setRootExpanded(!rootExpanded);
    };
    
    if (!loaded) {
        return (
            <div style={{ padding: '60px', textAlign: 'center', color: '#94a3b8' }}>
                🌳 加载操作系统知识库...
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
            <div style={{ 
                marginBottom: '16px',
                fontSize: '18px',
                fontWeight: '600',
                color: '#1e293b'
            }}>
                📚 知识图谱
                <span style={{ fontSize: '12px', color: '#94a3b8', marginLeft: '12px' }}>
                    {chapters.length} 章
                </span>
            </div>
            
            <div className="tree-container" style={{ 
                background: 'white',
                borderRadius: '16px',
                padding: '20px'
            }}>
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
                                background: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
                                borderRadius: '16px',
                                cursor: 'pointer',
                                width: 'fit-content',
                                minWidth: '180px',
                                boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                            }}
                        >
                            <span className="toggle-icon" style={{ color: 'white', fontSize: '14px' }}>
                                {rootExpanded ? '▼' : '▶'}
                            </span>
                            <span className="node-name" style={{ color: 'white', fontSize: '18px', fontWeight: 'bold' }}>
                                📘 操作系统
                            </span>
                        </div>
                        {rootExpanded && (
                            <div className="children" style={{ marginLeft: '28px', paddingLeft: 0 }}>
                                {chapters.map((chapter, idx) => (
                                    <ChapterNode 
                                        key={idx} 
                                        chapter={chapter} 
                                        chapterCache={chapterCache.current}
                                    />
                                ))}
                            </div>
                        )}
                    </li>
                </ul>
            </div>
            
            {/* 内联样式 */}
            <style>{`
                .tree-node {
                    list-style: none;
                    position: relative;
                    padding-left: 28px;
                    margin: 6px 0;
                }
                .tree-node::before {
                    content: '';
                    position: absolute;
                    left: 8px;
                    top: 20px;
                    width: 16px;
                    height: 1px;
                    background: #cbd5e1;
                }
                .tree-node::after {
                    content: '';
                    position: absolute;
                    left: 8px;
                    top: 0;
                    width: 1px;
                    height: 100%;
                    background: #cbd5e1;
                }
                .tree-node:last-child::after {
                    height: 20px;
                }
                .tree-node:first-child::after {
                    top: 20px;
                }
                .tree-root {
                    list-style: none;
                    position: relative;
                }
                .node-content {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 8px 16px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
                    cursor: pointer;
                    transition: all 0.2s;
                    border: 1px solid #e2e8f0;
                    margin: 4px 0;
                    width: fit-content;
                    min-width: 180px;
                }
                .node-content:hover {
                    transform: translateX(4px);
                    background: #fef9e3;
                }
                .toggle-icon {
                    font-size: 12px;
                    color: #64748b;
                    width: 20px;
                    text-align: center;
                }
                .node-name {
                    font-size: 14px;
                    font-weight: 500;
                    color: #1f2937;
                    flex: 1;
                }
                .root-node .node-content {
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    border: none;
                }
                .root-node .node-name { color: white; }
                .root-node .toggle-icon { color: white; }
                .chapter-node .node-content {
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    border: none;
                }
                .chapter-node .node-name { color: white; }
                .chapter-node .toggle-icon { color: white; }
                .topic-node .node-content {
                    background: #e0f2fe;
                    border: 1px solid #7dd3fc;
                }
                .topic-node .node-name { color: #1f2937; }
                .detail-node .node-content {
                    background: #fef9c3;
                    border: 1px solid #facc15;
                }
                .leaf-node .node-content {
                    background: #f8fafc;
                    border: 1px solid #cbd5e1;
                }
                .answer-container {
                    margin-top: 6px;
                    margin-left: 28px;
                }
                .answer-card {
                    background: #dcfce7;
                    padding: 10px 14px;
                    border-radius: 10px;
                    font-size: 12px;
                    line-height: 1.5;
                    color: #166534;
                    border-left: 3px solid #22c55e;
                }
                .difficulty-badge {
                    display: inline-block;
                    font-size: 10px;
                    padding: 2px 8px;
                    border-radius: 20px;
                    margin-left: 8px;
                }
                .difficulty-easy { background: #bbf7d0; color: #166534; }
                .difficulty-medium { background: #fed7aa; color: #9a3412; }
                .difficulty-hard { background: #fecaca; color: #991b1b; }
                .children {
                    margin-left: 28px;
                    padding-left: 0;
                }
            `}</style>
        </div>
    );
};

export default KnowledgeGraphPanel;