// 实现单资源生成和资源推送，具体见backend/api/aaapi使用文档.txt


// 刚刚访问完的资源，mindmap、materials、code_example、exercise、explanation之一
//  resource_type:"",要在退出资源的时候
// 作为调用URL：POST /api/resource/finish_view这个api的参数
// 即请求体的参数传入

<ResourcePanel
    recommended_resources={}
    generated_resource={}
    topic=""
/>