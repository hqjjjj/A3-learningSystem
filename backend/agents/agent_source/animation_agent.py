# backend/agents/agent_source/animation_agent.py
from backend.agents.agent_source.animation_prompt import system_prompt_animation
from backend.agents.agent_source.user_prompt import user_prompt_animation_build
from data.knowledge.KnowledgeBaseManager import KnowledgeBaseManager
from backend.agents.agent_source.lmm import SparkLLM
import json
import os
from json_repair import repair_json
import time
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent.parent.parent / "data" / "cache"
CACHE_FILE = CACHE_DIR / "animation_cache.json"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
kb = KnowledgeBaseManager(os.path.join(BASE_DIR, "data/knowledge"))
llm = SparkLLM()

def parse_output(result):
    fixed = repair_json(result)
    try:
        return json.loads(fixed)
    except Exception as e:
        return {"error": str(e), "raw": result}

class agentanimation:
    def run(self, input_data, topic):
        topic_id = input_data["topic_id"]
        if topic is None:
            return {"error": f"知识点不存在: {topic_id}"}
        
        system = system_prompt_animation
        user = user_prompt_animation_build(input_data, topic, kb)
        
        
        max_attempts = 3
        for attempt in range(max_attempts):
            t0 = time.time()
            result = llm.generate(system, user)
            print(f"LLM 调用耗时（第{attempt+1}次）: {time.time()-t0:.2f}秒")
            
            # 打印结果摘要 
            print(f" 返回结果长度: {len(result)} 字符")
            print(f" 预览 (前200字符): {result[:200]}...")
            
            parsed = parse_output(result)
            if not isinstance(parsed, dict):
                if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
                    parsed = parsed[0]
                else:
                    parsed = {"error": "返回结果不是JSON对象", "raw": result}
            
            # 检测 JSON 修复过程中产生的异常字段（表明原始 JSON 不完整）
            if any(k in parsed for k in ("fixed", "dynamic", "已分配")):
                print(f" 检测到修复残留字段: {[k for k in parsed if k in ('fixed', 'dynamic', '已分配')]}")
                user += "\n 你输出的 JSON 不完整，包含修复残留字段。请确保 JSON 完全正确，且 HTML 代码以 </html> 结尾。"
                continue
            
            if "error" not in parsed and "animation" in parsed:
                anim_data = parsed["animation"]
                anim = {}
                if isinstance(anim_data, dict):
                    anim = anim_data
                elif isinstance(anim_data, list):
                    for item in anim_data:
                        if isinstance(item, dict):
                            anim = item
                            break
                if not isinstance(anim, dict):
                    anim = {}
                
                anim.setdefault("type", "html")
                anim.setdefault("title", f"{input_data.get('module', '动画')}演示")
                anim.setdefault("html_content", "")
                anim.setdefault("description", "")
                
                if not anim["html_content"].strip():
                    anim["html_content"] = "<div style='padding:20px;text-align:center;color:red;'>动画生成失败，请重试</div>"
                
                html = anim.get("html_content", "")
                # 检查 HTML 完整性
                if (not html.strip().startswith("<!DOCTYPE html>") or 
                    not html.strip().endswith("</html>") or
                    len(html) < 200):
                    print(f" HTML 校验失败: 长度={len(html)}, 开头={html[:50]}, 结尾={html[-50:]}")
                    #  追加更明确的压缩指令 
                    user += "\n 生成的 HTML 不完整，必须包含完整的 <!DOCTYPE html> 和 </html>，且长度应大于 200 字符。请生成更紧凑的 HTML 代码，尽量精简 CSS 和 JS，总字符数控制在 3000 以内。"
                    continue
                
                # 添加引用
                module = input_data.get("module", "未知章节")
                topic_name = topic.get("name", "未知知识点")
                base_citation = f"源于教材知识库：《{module}》{topic_name}"
                if "knowledge_base_quote" not in anim:
                    anim["knowledge_base_quote"] = [base_citation]
                else:
                    new_list = [base_citation]
                    for item in anim["knowledge_base_quote"][1:]:
                        if len(new_list) < 3:
                            new_list.append(item)
                    anim["knowledge_base_quote"] = new_list
                
                print(" 动画生成成功并校验通过！")
                return {"animation": anim}
            else:
                error_msg = parsed.get('error', '未知错误')
                print(f" JSON 解析错误: {error_msg}")
                user += f"\n你上次输出的JSON不合法，错误：{error_msg}，请重新输出合法JSON。"
        
        # 全部重试失败，返回默认静态提示页面
        print(" 所有重试均失败，返回默认提示页面")
        module = input_data.get("module", "未知章节")
        topic_name = topic.get("name", "未知知识点")
        base_citation = f"源于教材知识库：《{module}》{topic_name}"
        
        default_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>动画生成提示</title>
    <style>
        body {{
            font-family: "Microsoft YaHei", sans-serif;
            background: #f0f2f5;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }}
        .card {{
            background: white;
            padding: 40px 60px;
            border-radius: 16px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
            text-align: center;
            max-width: 500px;
        }}
        .icon {{
            font-size: 48px;
            margin-bottom: 16px;
        }}
        h2 {{
            color: #2c3e50;
            margin: 0 0 12px 0;
        }}
        p {{
            color: #7f8c8d;
            line-height: 1.6;
            margin: 8px 0;
        }}
        .footnote {{
            margin-top: 20px;
            font-size: 13px;
            color: #95a5a6;
            border-top: 1px solid #ecf0f1;
            padding-top: 16px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">🔄</div>
        <h2>动画生成暂时不可用</h2>
        <p>很抱歉，当前无法生成该知识点的交互式动画。</p>
        <p>可能原因：生成内容过长或网络波动，请稍后重试。</p>
        <div class="footnote">
            📚 知识点：《{module}》- {topic_name}
        </div>
    </div>
</body>
</html>"""
        
        default_anim = {
            "type": "html",
            "title": f"{module} - 动画生成提示",
            "html_content": default_html,
            "description": "动画生成失败，请重试。",
            "knowledge_base_quote": [base_citation]
        }
        
        return {"animation": default_anim}