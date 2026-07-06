// 前端状态结构
export const appState = {
    user_id:"",
    profile: {},
    topic: "",
    // 资源推送区的多个资源
    recommended_resources: [],
    // 用户选择生成单个资源
    generated_resource:{},
    // 当前学习状态：复习/学习
    current_progress:0,
    chat_history: [],
    learning_path:[]
}