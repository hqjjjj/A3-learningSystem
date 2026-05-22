// api基础封装
const BASE_URL = 'http://127.0.0.1:8080';

// 通用请求异步函数
async function request(url, options) {
  try {
    const response = await fetch(`${BASE_URL}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();//解析响应体为 JSON 对象
    return data;
  } catch (error) {
    console.error(`API Error [${url}]:`, error);
    throw error; // 让调用方自行处理
  }
}



export const sendChat = async (user_id,message) => {
    return request('/api/chat/',{
        method:'POST',
        body:JSON.stringify({ user_id, message }),}
    );
}; 

export const generateResource = async (user_id,topic,resource_type) => {
    return request('/api/resource/generate',
        {method:'POST',
         body: JSON.stringify({ user_id,topic,resource_type }),  
        }
    )
}

export const fetchPath = async (user_id) => {
  return request(`/api/path/${user_id}`, { method: 'GET' });
};

export const finishResource = async ( user_id, resource_type,topic,duration ) => {
  return request('/api/resource/finish_view', {
    method: 'POST',
    body: JSON.stringify({ user_id, resource_type,topic,duration }),
  });
};

export const submitAnswer = async (user_id, topic,correct_rate,duration) => {
  return request('/api/answer/submit_answer', {
    method: 'POST',
    body: JSON.stringify({  
         user_id, topic,correct_rate,duration}),
  });
  
};


