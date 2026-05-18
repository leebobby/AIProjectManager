import axios from 'axios'
import { ElMessage } from 'element-plus'
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
    } else if (error.response?.status === 409) {
      ElMessage.warning(error.response.data?.detail || '数据已被他人修改，请刷新后重试')
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: (data) => http.post('/auth/login', data),
  register: (data) => http.post('/auth/register', data),
  me: () => http.get('/auth/me'),
  changePassword: (data) => http.post('/auth/change-password', data),
}

export const userApi = {
  list: () => http.get('/users'),
  create: (data) => http.post('/users', data),
  update: (id, data) => http.put(`/users/${id}`, data),
  remove: (id) => http.delete(`/users/${id}`),
}

export const configApi = {
  get: () => http.get('/config'),
  save: (data) => http.put('/config', data),
}

export const issueApi = {
  listDates:    ()     => http.get('/issues/dates'),
  getData:      (date) => http.get('/issues/data', date ? { params: { date } } : {}),
  getTrend:     ()     => http.get('/issues/trend'),
  scriptStatus: ()     => http.get('/issues/run-script/status'),
  runScript:    ()     => http.post('/issues/run-script'),
  exportPptx:   (date) => http.get('/issues/export.pptx', { responseType: 'blob', ...(date ? { params: { date } } : {}) }),
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

export const majorVersionApi = {
  list: (project_id) => http.get('/major-versions', { params: project_id != null ? { project_id } : {} }),
  create: (data) => http.post('/major-versions', data),
  update: (id, data) => http.put(`/major-versions/${id}`, data),
  remove: (id) => http.delete(`/major-versions/${id}`),
  allIterationVersions: () => http.get('/iteration-versions/all'),
  createIterVersion: (data) => http.post('/iteration-versions', data),
  updateIterVersion: (id, data) => http.put(`/iteration-versions/${id}`, data),
  removeIterVersion: (id) => http.delete(`/iteration-versions/${id}`),
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
  importTemplate: () => http.get('/iteration-requirements/import-template.xlsx', { responseType: 'blob' }),
  importExcel: (iteration_id, file) => {
    const fd = new FormData()
    fd.append('file', file)
    return http.post('/iteration-requirements/import', fd, {
      params: { iteration_id },
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export const stakeholderApi = {
  listProjectContacts: () => http.get('/stakeholders/project-contacts'),
  createProjectContact: (data) => http.post('/stakeholders/project-contacts', data),
  updateProjectContact: (id, data) => http.put(`/stakeholders/project-contacts/${id}`, data),
  removeProjectContact: (id) => http.delete(`/stakeholders/project-contacts/${id}`),

  listBattlefields: () => http.get('/stakeholders/battlefields'),
  createBattlefield: (data) => http.post('/stakeholders/battlefields', data),
  updateBattlefield: (id, data) => http.put(`/stakeholders/battlefields/${id}`, data),
  removeBattlefield: (id) => http.delete(`/stakeholders/battlefields/${id}`),
}

export const roadmapApi = {
  listProjects: (include_inactive = false) =>
    http.get('/roadmap/projects', { params: { include_inactive } }),
  getProject: (id) => http.get(`/roadmap/projects/${id}`),
  createProject: (data) => http.post('/roadmap/projects', data),
  updateProject: (id, data) => http.put(`/roadmap/projects/${id}`, data),
  removeProject: (id) => http.delete(`/roadmap/projects/${id}`),

  createPhase: (data) => http.post('/roadmap/phases', data),
  updatePhase: (id, data) => http.put(`/roadmap/phases/${id}`, data),
  removePhase: (id) => http.delete(`/roadmap/phases/${id}`),

  createMilestone: (data) => http.post('/roadmap/milestones', data),
  updateMilestone: (id, data) => http.put(`/roadmap/milestones/${id}`, data),
  removeMilestone: (id) => http.delete(`/roadmap/milestones/${id}`),
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
