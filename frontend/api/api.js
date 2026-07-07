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
    const json = await response.json();

    // 统一处理后端返回格式：{ status: "success", data: ... }
    if (json.status === 'success') {
      return json.data;   // 直接返回业务数据
    }
    // 如果后端返回其他状态，抛出错误
    throw new Error(json.message || '请求失败');
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
