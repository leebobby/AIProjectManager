<template>
  <div class="stakeholder-page">
    <!-- 项目组沟通地图 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><UserFilled /></el-icon> 项目组沟通地图
          </span>
          <el-button v-if="isAdmin" type="primary" size="small" :icon="Plus" @click="openProjectDialog()">
            新增
          </el-button>
        </div>
      </template>

      <el-table :data="projectContacts" v-loading="loadingProject" border stripe class="contact-table">
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="col1" label="角色" min-width="160" />
        <el-table-column prop="col2" label="姓名 / 工号" min-width="200" />
        <el-table-column v-if="isAdmin" label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" text :icon="EditIcon" @click="openProjectDialog(row)">编辑</el-button>
            <el-popconfirm title="确认删除该条目？" @confirm="deleteProjectContact(row.id)">
              <template #reference>
                <el-button size="small" type="danger" text :icon="Delete">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loadingProject && projectContacts.length === 0" class="empty-hint">
        暂无数据{{ isAdmin ? '，点击右上角「新增」添加条目' : '' }}
      </div>
    </el-card>

    <!-- 战场沟通矩阵 -->
    <el-card shadow="never" class="section-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Grid /></el-icon> 战场沟通矩阵
          </span>
          <el-button v-if="isAdmin" type="primary" size="small" :icon="Plus" @click="openBattlefieldDialog()">
            新增
          </el-button>
        </div>
      </template>

      <el-table :data="battlefields" v-loading="loadingBattlefield" border stripe class="battlefield-table">
        <el-table-column type="index" label="#" width="50" align="center" />
        <el-table-column prop="battlefield" label="战场" min-width="100" />
        <el-table-column prop="region" label="地域" min-width="80" />
        <el-table-column prop="service" label="服务" min-width="120" />
        <el-table-column label="联系方式" min-width="180">
          <template #default="{ row }">
            <span class="pre-text">{{ row.contact1 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="apps" label="APPS" min-width="120" />
        <el-table-column label="联系方式" min-width="180">
          <template #default="{ row }">
            <span class="pre-text">{{ row.contact2 }}</span>
          </template>
        </el-table-column>
        <el-table-column v-if="isAdmin" label="操作" width="140" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" text :icon="EditIcon" @click="openBattlefieldDialog(row)">编辑</el-button>
            <el-popconfirm title="确认删除该条目？" @confirm="deleteBattlefield(row.id)">
              <template #reference>
                <el-button size="small" type="danger" text :icon="Delete">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loadingBattlefield && battlefields.length === 0" class="empty-hint">
        暂无数据{{ isAdmin ? '，点击右上角「新增」添加条目' : '' }}
      </div>
    </el-card>

    <!-- 项目组联系人 Dialog -->
    <el-dialog
      v-model="projectDialogVisible"
      :title="projectForm.id ? '编辑联系人' : '新增联系人'"
      width="480px"
      @close="resetProjectForm"
    >
      <el-form :model="projectForm" label-width="90px">
        <el-form-item label="角色">
          <el-input v-model="projectForm.col1" placeholder="请输入角色名称" />
        </el-form-item>
        <el-form-item label="姓名/工号">
          <el-input v-model="projectForm.col2" placeholder="请输入姓名或工号" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="projectDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="projectSaving" @click="saveProjectContact">保存</el-button>
      </template>
    </el-dialog>

    <!-- 战场沟通矩阵 Dialog -->
    <el-dialog
      v-model="battlefieldDialogVisible"
      :title="battlefieldForm.id ? '编辑战场条目' : '新增战场条目'"
      width="560px"
      @close="resetBattlefieldForm"
    >
      <el-form :model="battlefieldForm" label-width="90px">
        <el-form-item label="战场">
          <el-input v-model="battlefieldForm.battlefield" placeholder="战场名称" />
        </el-form-item>
        <el-form-item label="地域">
          <el-input v-model="battlefieldForm.region" placeholder="地域" />
        </el-form-item>
        <el-form-item label="服务">
          <el-input v-model="battlefieldForm.service" placeholder="服务名称" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input
            v-model="battlefieldForm.contact1"
            type="textarea"
            :rows="3"
            placeholder="服务联系方式（支持多行）"
          />
        </el-form-item>
        <el-form-item label="APPS">
          <el-input v-model="battlefieldForm.apps" placeholder="APPS 名称" />
        </el-form-item>
        <el-form-item label="联系方式">
          <el-input
            v-model="battlefieldForm.contact2"
            type="textarea"
            :rows="3"
            placeholder="APPS 联系方式（支持多行）"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="battlefieldDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="battlefieldSaving" @click="saveBattlefield">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete, Edit as EditIcon, Grid, Plus, UserFilled } from '@element-plus/icons-vue'
import { auth } from '../store/auth'
import { stakeholderApi } from '../api'

const isAdmin = auth.isAdmin

// ── 项目组沟通地图 ─────────────────────────────────────────
const projectContacts     = ref([])
const loadingProject      = ref(false)
const projectDialogVisible = ref(false)
const projectSaving       = ref(false)
const projectForm         = reactive({ id: null, col1: '', col2: '' })

async function loadProjectContacts() {
  loadingProject.value = true
  try {
    const { data } = await stakeholderApi.listProjectContacts()
    projectContacts.value = data
  } catch {
    ElMessage.error('加载项目组沟通地图失败')
  } finally {
    loadingProject.value = false
  }
}

function openProjectDialog(row = null) {
  if (row) {
    Object.assign(projectForm, { id: row.id, col1: row.col1, col2: row.col2 })
  }
  projectDialogVisible.value = true
}

function resetProjectForm() {
  Object.assign(projectForm, { id: null, col1: '', col2: '' })
}

async function saveProjectContact() {
  projectSaving.value = true
  try {
    const payload = { col1: projectForm.col1, col2: projectForm.col2 }
    if (projectForm.id) {
      await stakeholderApi.updateProjectContact(projectForm.id, payload)
    } else {
      await stakeholderApi.createProjectContact(payload)
    }
    ElMessage.success('已保存')
    projectDialogVisible.value = false
    await loadProjectContacts()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    projectSaving.value = false
  }
}

async function deleteProjectContact(id) {
  try {
    await stakeholderApi.removeProjectContact(id)
    ElMessage.success('已删除')
    await loadProjectContacts()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

// ── 战场沟通矩阵 ──────────────────────────────────────────
const battlefields          = ref([])
const loadingBattlefield    = ref(false)
const battlefieldDialogVisible = ref(false)
const battlefieldSaving     = ref(false)
const battlefieldForm       = reactive({
  id: null, battlefield: '', region: '', service: '', contact1: '', apps: '', contact2: '',
})

async function loadBattlefields() {
  loadingBattlefield.value = true
  try {
    const { data } = await stakeholderApi.listBattlefields()
    battlefields.value = data
  } catch {
    ElMessage.error('加载战场沟通矩阵失败')
  } finally {
    loadingBattlefield.value = false
  }
}

function openBattlefieldDialog(row = null) {
  if (row) {
    Object.assign(battlefieldForm, {
      id: row.id,
      battlefield: row.battlefield,
      region: row.region,
      service: row.service,
      contact1: row.contact1,
      apps: row.apps,
      contact2: row.contact2,
    })
  }
  battlefieldDialogVisible.value = true
}

function resetBattlefieldForm() {
  Object.assign(battlefieldForm, {
    id: null, battlefield: '', region: '', service: '', contact1: '', apps: '', contact2: '',
  })
}

async function saveBattlefield() {
  battlefieldSaving.value = true
  try {
    const payload = {
      battlefield: battlefieldForm.battlefield,
      region:      battlefieldForm.region,
      service:     battlefieldForm.service,
      contact1:    battlefieldForm.contact1,
      apps:        battlefieldForm.apps,
      contact2:    battlefieldForm.contact2,
    }
    if (battlefieldForm.id) {
      await stakeholderApi.updateBattlefield(battlefieldForm.id, payload)
    } else {
      await stakeholderApi.createBattlefield(payload)
    }
    ElMessage.success('已保存')
    battlefieldDialogVisible.value = false
    await loadBattlefields()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    battlefieldSaving.value = false
  }
}

async function deleteBattlefield(id) {
  try {
    await stakeholderApi.removeBattlefield(id)
    ElMessage.success('已删除')
    await loadBattlefields()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

onMounted(() => {
  loadProjectContacts()
  loadBattlefields()
})
</script>

<style scoped>
.stakeholder-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.section-card :deep(.el-card__header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.pre-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.empty-hint {
  text-align: center;
  color: #909399;
  padding: 32px 0;
  font-size: 13px;
}

.contact-table :deep(.el-table__cell),
.battlefield-table :deep(.el-table__cell) {
  vertical-align: top;
  padding: 10px 12px;
}
</style>
