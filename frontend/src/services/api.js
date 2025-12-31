import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

const getCsrfToken = async () => {
  try {
    const response = await axios.get('/api/auth/current-user/', {
      withCredentials: true
    })
    return document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1]
  } catch (error) {
    return document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1] || null
  }
}

api.interceptors.request.use(async (config) => {
  const csrftoken = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1]
  
  if (csrftoken) {
    config.headers['X-CSRFToken'] = csrftoken
  }
  
  return config
})

export default api

