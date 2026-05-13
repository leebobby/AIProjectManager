import axios from 'axios'
import { auth } from '../store/auth'

const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

http.interceptors.request.use((config) => {
  if (auth.state.token) {
    config.headers.Authorization = `Bearer ${auth.state.token}`
  }
  return config
})

http.interceptors.response.use(
  (resp) => resp,
  (error) => {
    if (error.response?.status === 401) {
      auth.clear()
      if (location.pathname !== '/login') {
        location.replace('/login')
      }
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: (data) => http.post('/auth/login', data),
  register: (data) => http.post('/auth/register', data),
  me: () => http.get('/auth/me'),
}

export const userApi = {
  list: () => http.get('/users'),
  create: (data) => http.post('/users', data),
  update: (id, data) => http.put(`/users/${id}`, data),
  remove: (id) => http.delete(`/users/${id}`),
}

export const configApi = {
  get: () => http.get('/config'),
}

export const customerStatusApi = {
  list: () => http.get('/customer-status'),
  create: (data) => http.post('/customer-status', data),
  update: (id, data) => http.put(`/customer-status/${id}`, data),
  remove: (id) => http.delete(`/customer-status/${id}`),
}

export const versionApi = {
  list: () => http.get('/versions'),
  create: (data) => http.post('/versions', data),
  update: (id, data) => http.put(`/versions/${id}`, data),
  remove: (id) => http.delete(`/versions/${id}`),
}

export const iterationApi = {
  list: () => http.get('/iterations'),
  create: (data) => http.post('/iterations', data),
  update: (id, data) => http.put(`/iterations/${id}`, data),
  remove: (id) => http.delete(`/iterations/${id}`),
}

export default http
