<template>
  <div>
    <PageHeader
      title="账号管理"
      description="一期支持账号增删改查、部门字段、状态启停；角色和菜单权限沿用预留模型。"
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="openCreate">新增账号</el-button>
      </template>
    </PageHeader>

    <PanelCard flush>
      <div class="wb-table-toolbar">
        <el-input
          v-model="keyword"
          clearable
          :prefix-icon="Search"
          placeholder="搜索账号 / 姓名 / 部门"
          style="width: 240px"
        />
        <el-select v-model="filterStatus" clearable placeholder="全部状态" style="width: 118px">
          <el-option
            v-for="o in ACCOUNT_STATUS_OPTIONS"
            :key="o.value"
            :value="o.value"
            :label="o.label"
          />
        </el-select>
        <span class="wb-table-toolbar__spacer" />
        <span class="wb-table-toolbar__count">共 {{ filtered.length }} 条</span>
      </div>

      <DataTable :data="filtered" :loading="loading" empty-text="还没有账号，先新增一个">
        <template #empty-action>
          <el-button type="primary" :icon="Plus" @click="openCreate">新增账号</el-button>
        </template>

        <el-table-column prop="username" label="登录账号" width="130" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="department_id" label="部门" width="140">
          <template #default="{ row }">
            <span v-if="row.department_id">{{ row.department_id }}</span>
            <span v-else class="wb-muted">未填写</span>
          </template>
        </el-table-column>

        <el-table-column label="角色" min-width="160">
          <template #default="{ row }">
            <div v-if="row.role_ids?.length" class="role-list">
              <StatusTag v-for="r in row.role_ids" :key="r" :label="roleName(r)" />
            </div>
            <span v-else class="wb-muted">未分配</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="96">
          <template #default="{ row }">
            <StatusTag
              :label="labelOf(ACCOUNT_STATUS, row.status)"
              :tone="toneOf(ACCOUNT_STATUS, row.status)"
              dot
            />
          </template>
        </el-table-column>

        <el-table-column label="操作" width="180">
          <template #default="{ row }">
            <div class="wb-row-actions">
              <el-button size="small" text @click="edit(row)">编辑</el-button>
              <!-- 契约 §8：列表需支持启停，原先只能在编辑弹窗内修改 -->
              <el-button size="small" text @click="toggleStatus(row)">
                {{ row.status === 'active' ? '停用' : '启用' }}
              </el-button>
              <el-button size="small" text type="danger" @click="remove(row)">删除</el-button>
            </div>
          </template>
        </el-table-column>
      </DataTable>
    </PanelCard>

    <FormDialog
      v-model="visible"
      :title="form.id ? '编辑账号' : '新增账号'"
      width="560px"
      @confirm="save"
    >
      <el-form label-width="86px">
        <el-form-item label="登录账号">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="form.department_id" placeholder="例如：产品部 / 技术部 / 运营部" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_ids" multiple style="width: 100%">
            <el-option v-for="r in roles" :key="r.id" :value="r.id" :label="r.name || r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio-button value="active">启用</el-radio-button>
            <el-radio-button value="disabled">停用</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="form.id ? '不填则不修改' : '默认 Workbench2026!'"
          />
        </el-form-item>
      </el-form>
    </FormDialog>
  </div>
</template>

<script setup>
// 账号管理（PRD 9.3）：改造前 .toolbar / .page-title 私有，弹窗手写。
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import PageHeader from '../components/PageHeader.vue'
import PanelCard from '../components/PanelCard.vue'
import DataTable from '../components/DataTable.vue'
import FormDialog from '../components/FormDialog.vue'
import StatusTag from '../components/StatusTag.vue'
import { ACCOUNT_STATUS, ACCOUNT_STATUS_OPTIONS, labelOf, toneOf } from '../constants/enums'
import client from '../api/client'

const items = ref([])
const keyword = ref('')
const filterStatus = ref('')
const roles = ref([])
const loading = ref(false)
const visible = ref(false)
const form = ref({})

const roleName = (id) => roles.value.find((r) => r.id === id)?.name || id
const emptyForm = () => ({
  username: '',
  name: '',
  department_id: '',
  role_ids: ['pm'],
  status: 'active',
  password: '',
})

async function load() {
  loading.value = true
  try {
    const r = await client.get('/api/users')
    items.value = r.items
    roles.value = r.roles
  } finally {
    loading.value = false
  }
}
onMounted(load)

/** 列表内轻量筛选：账号 / 姓名 / 部门 + 状态 */
const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return items.value.filter((r) => {
    if (filterStatus.value && r.status !== filterStatus.value) return false
    if (kw) {
      const hay = `${r.username || ''} ${r.name || ''} ${r.department_id || ''}`.toLowerCase()
      if (!hay.includes(kw)) return false
    }
    return true
  })
})

function openCreate() {
  form.value = emptyForm()
  visible.value = true
}

function edit(row) {
  form.value = { ...row, role_ids: [...(row.role_ids || [])], password: '' }
  visible.value = true
}

async function save() {
  try {
    const payload = { ...form.value }
    if (!payload.password) delete payload.password
    if (payload.id) await client.put(`/api/users/${payload.id}`, payload)
    else await client.post('/api/users', payload)
    visible.value = false
    ElMessage.success('账号已保存')
    await load()
  } catch (e) {
    /* 拦截器统一提示 */
  }
}

/** 列表快捷启停：传完整对象以兼容后端 PUT 的字段校验 */
async function toggleStatus(row) {
  const next = row.status === 'active' ? 'disabled' : 'active'
  try {
    await client.put(`/api/users/${row.id}`, { ...row, status: next })
    ElMessage.success(next === 'active' ? '账号已启用' : '账号已停用')
    await load()
  } catch (e) {
    /* 拦截器统一提示 */
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`确认删除账号「${row.username}」？`, '删除账号', { type: 'warning' })
    await client.delete(`/api/users/${row.id}`)
    ElMessage.success('账号已删除')
    await load()
  } catch (e) {
    /* 用户取消或拦截器提示 */
  }
}
</script>

<style scoped>
.wb-row-actions {
  display: flex;
  align-items: center;
  gap: var(--wb-sp-1);
}

.role-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--wb-sp-1);
}
</style>
