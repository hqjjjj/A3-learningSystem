// api基础封装
const BASE_URL = 'http://127.0.0.1:8080';

// 通用请求异步函数
// api.js
async function request(url, options) {
  try {
    const response = await fetch(`${BASE_URL}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || `HTTP ${response.status}`);
    }
    
    const json = await response.json();
    console.log(`API Response [${url}]:`, json); // 添加日志
    
    return json; // 直接返回响应数据
    
  } catch (error) {
    console.error(`API Error [${url}]:`, error);
    throw error;
  }
}




export const sendChat = async (user_id, message, topic) => {
    return request('/api/chat/', {
        method: 'POST',
        body: JSON.stringify({ user_id, message, topic }),
    });
};

export const generateResource = async (user_id,topic,resource_type) => {
    return request('/api/resource/generate',
        {method:'POST',
         body: JSON.stringify({ user_id,topic,resource_type }),  
        }
    )
}

export const fetchPath = async (user_id, topic) => {
  if (!topic) throw new Error('topic is required for fetchPath');
  return request('/api/path/', {
    method: 'POST',
    body: JSON.stringify({ user_id, topic })
  });
};

export const finishResource = async ( user_id, resource_type,topic,duration ) => {
  return request('/api/resource/finish_view', {
    method: 'POST',
    body: JSON.stringify({ user_id, resource_type,topic,duration }),
  });
};

export const submitAnswer = async (user_id, topic, correct_rate, duration) => {
  return request('/api/resource/submit_answer', {
    method: 'POST',
    body: JSON.stringify({ user_id, topic, correct_rate, duration }),
  });
};

export const loadUserState = async (user_id) => {
    return request('/api/user/load_state', {
        method: 'POST',
        body: JSON.stringify({ user_id }),
    });
};
