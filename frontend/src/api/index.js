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
  exportPptx: () => http.get('/customer-status/export.pptx', { responseType: 'blob' }),
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

export const annualIterationApi = {
  years: () => http.get('/annual-iterations/years'),
  list: (year) => http.get('/annual-iterations', { params: { year } }),
  get: (id) => http.get(`/annual-iterations/${id}`),
  update: (id, data) => http.put(`/annual-iterations/${id}`, data),
  exportPptx: (id) => http.get(`/annual-iterations/${id}/export.pptx`, { responseType: 'blob' }),
}

export const iterationRequirementApi = {
  list: (iteration_id) => http.get('/iteration-requirements', { params: { iteration_id } }),
  create: (data) => http.post('/iteration-requirements', data),
  update: (id, data) => http.put(`/iteration-requirements/${id}`, data),
  remove: (id) => http.delete(`/iteration-requirements/${id}`),
}

export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

export default http
