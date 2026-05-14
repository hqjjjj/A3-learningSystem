# models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime

class CognitiveStyle(BaseModel):
    """认知风格（量化分布，内部使用）"""
    visual: float = Field(0.33, ge=0, le=1, description="视觉偏好")
    textual: float = Field(0.33, ge=0, le=1, description="文字偏好")
    auditory: float = Field(0.34, ge=0, le=1, description="听觉偏好")

class Preference(BaseModel):
    """学习偏好"""
    resource_type: Optional[str] = Field(default="document", description="偏好的资源类型: video, document, exercise, diagram")
    difficulty: str = Field(default="medium", description="偏好的难度: easy, medium, hard")
    active_hours: Optional[str] = Field(default=None, description="活跃时段: morning, afternoon, night")

class Progress(BaseModel):
    """学习进度"""
    current_topic: Optional[str] = Field(default=None, description="当前学习主题")
    completed_topics: List[str] = Field(default_factory=list, description="已完成主题列表")

class StudentProfile(BaseModel):
    """【全系统共享】学生画像标准结构"""
    user_id: str
    
    # 基础信息
    major: Optional[str] = Field(default=None, description="专业")
    grade: Optional[str] = Field(default=None, description="年级")
    course: Optional[str] = Field(default=None, description="当前课程")
    
    # 核心动态维度 (共7个维度)
    knowledge_level: Dict[str, float] = Field(default_factory=dict, description="各知识点掌握度(0-1)")
    weak_points: List[str] = Field(default_factory=list, description="薄弱知识点列表")
    error_tags: List[str] = Field(default_factory=list, description="高频错误标签")
    
    # 【关键修改】learning_style 简化为 text 或 diagram
    learning_style: Optional[str] = Field(default=None, description="学习风格: text(文本型) 或 diagram(图解型)")
    
    # 内部量化分析 (保留但不作为主要输出维度)
    cognitive_style: CognitiveStyle = Field(default_factory=CognitiveStyle, description="认知风格内部量化数据")
    
    learning_pace: str = Field(default="normal", description="学习节奏: fast, normal, slow")
    resource_type: List[str] = Field(default_factory=lambda: ["explanation"], description="偏好的资源类型列表: explanation, mindmap, exercise, code_example")
    difficulty: Optional[str] = Field(default="medium", description="偏好的难度: easy, medium, hard")
    progress: Progress = Field(default_factory=Progress, description="学习进度追踪")
    learning_goal: Optional[str] = Field(default=None, description="学习目标")
    
    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class ProfileResponse(BaseModel):
    """Agent返回给外部的标准响应（对齐团队文档）"""
    profile: StudentProfile
    update_type: str = Field(description="init 或 update")
    confidence: float = Field(default=0.85, ge=0, le=1)