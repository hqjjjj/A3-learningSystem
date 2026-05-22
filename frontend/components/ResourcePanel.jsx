// 实现单资源生成和资源推送，具体见backend/api/aaapi使用文档.txt


// 刚刚访问完的资源，mindmap、materials、code_example、exercise、explanation之一
//  resource_type:"",要在退出资源的时候
// 作为调用URL：POST /api/resource/finish_view这个api的参数
// 即请求体的参数传入

// 传入参数
// ResourcePanel
// props:

// recommended_resources (array, 必填)

// 元素为资源对象（type, title, content, subtype 等）

// generated_resource (object, 可选)

// 单个资源对象，结构同上

// topic (string, 必填)

// 当前知识点名称