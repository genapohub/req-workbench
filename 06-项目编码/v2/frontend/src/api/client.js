import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'
import { clearSession, session } from '../store/session'
import { getApiGate } from './gate'

const client = axios.create({ baseURL: '', withCredentials: true })

// 请求网关：Mock 模式下等 MSW worker 就绪再发请求（main.js 已设 10s 超时兜底，不会永久挂起）
client.interceptors.request.use(async (config) => {
  await getApiGate()
  if (session.token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${session.token}`
  }
  return config
})

client.interceptors.response.use(
  (resp) => {
    const body = resp.data
    // 统一响应包裹 { code, data, message }
    if (body && typeof body.code === 'number') {
      if (body.code !== 0) {
        if (body.code === 1001) {
          clearSession()
          router.replace('/login')
        } else {
          // AC-17 错误态：统一错误提示（"请求失败：{message}"）
          ElMessage.error(body.message || '请求失败')
        }
        return Promise.reject(new Error(body.message || '请求失败'))
      }
      return body.data
    }
    return body
  },
  (err) => {
    const body = err.response && err.response.data
    if (body && body.code === 1001) {
      clearSession()
      router.replace('/login')
    } else if (body && typeof body.code === 'number') {
      ElMessage.error(body.message || '请求失败')
    } else {
      ElMessage.error('网络请求失败，请稍后重试')
    }
    return Promise.reject(err)
  }
)

export default client
