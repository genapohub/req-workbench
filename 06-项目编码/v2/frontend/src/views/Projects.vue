<template>
  <div>
    <PageHeader
      title="基座信息"
      description="公司业务、项目背景、项目进度是需求判断的前置上下文；每个项目都有独立提需入口。"
    >
      <template #actions>
        <el-button type="primary" :icon="Plus" @click="openCreate">新建项目</el-button>
      </template>
    </PageHeader>

    <PanelCard flush>
      <div class="wb-table-toolbar">
        <el-input
          v-model="keyword"
          clearable
          :prefix-icon="Search"
          placeholder="搜索项目 / 业务 / 背景"
          style="width: 240px"
        />
        <span class="wb-table-toolbar__spacer" />
        <span class="wb-table-toolbar__count">共 {{ filtered.length }} 条</span>
      </div>

      <DataTable
        :data="filtered"
        :loading="loading"
        empty-text="还没有基座信息，先补公司业务、项目背景、项目进度，再提交需求"
      >
        <template #empty-action>
          <el-button type="primary" :icon="Plus" @click="openCreate">新建项目</el-button>
        </template>

        <el-table-column prop="name" label="项目" min-width="150" />

        <el-table-column label="基座完整度" width="140">
          <template #default="{ row }">
            <StatusTag
              :label="row.base_status_label"
              :tone="row.base_complete ? 'success' : 'warning'"
              dot
            />
          </template>
        </el-table-column>

        <el-table-column prop="company_business" label="公司业务" min-width="180" show-overflow-tooltip />
        <el-table-column prop="project_background" label="项目背景" min-width="180" show-overflow-tooltip />
        <el-table-column prop="progress" label="项目进度" width="130" show-overflow-tooltip />
        <el-table-column prop="requirement_count" label="需求数" width="88" />

        <!-- 公开提需入口（PRD 9.1） -->
        <el-table-column label="提需入口" width="190">
          <template #default="{ row }">
            <div class="wb-row-actions">
              <el-button size="small" text @click.stop="copyLink(row)">复制链接</el-button>
              <el-button size="small" text @click.stop="showQr(row)">二维码</el-button>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="88">
          <template #default="{ row }">
            <el-button size="small" text @click="edit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </DataTable>
    </PanelCard>

    <!-- 新建 / 编辑基座 -->
    <FormDialog
      v-model="visible"
      :title="form.id ? '编辑基座信息' : '新建基座信息'"
      width="680px"
      @confirm="save"
    >
      <el-alert
        class="wb-dialog-alert"
        type="info"
        :closable="false"
        title="缺项可以保存，但需求提交和方法论检查会要求先补齐公司业务、项目背景、项目进度。"
      />
      <el-form label-width="96px">
        <el-form-item label="项目名">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="公司业务">
          <el-input
            v-model="form.company_business"
            type="textarea"
            :rows="3"
            placeholder="公司怎么赚钱、核心业务链路是什么、当前重点指标是什么"
          />
        </el-form-item>
        <el-form-item label="项目背景">
          <el-input
            v-model="form.project_background"
            type="textarea"
            :rows="3"
            placeholder="项目为什么做、面向谁、当前边界和目标是什么"
          />
        </el-form-item>
        <el-form-item label="项目进度">
          <el-input v-model="form.progress" placeholder="例如：MVP 收窄开发中 / 试点中 / 已上线" />
        </el-form-item>
        <el-form-item label="业务目标">
          <el-input v-model="form.business_goals" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="关键流程">
          <el-input v-model="form.business_process" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="目标用户">
          <el-input v-model="form.target_users" />
        </el-form-item>
        <el-form-item label="限制条件">
          <el-input v-model="form.constraints" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
    </FormDialog>

    <!-- 项目提需二维码（PRD 9.1） -->
    <el-dialog v-model="qrVisible" title="项目提需二维码" width="420px">
      <div v-if="qrProject" class="qr-box">
        <h3 class="qr-box__name">{{ qrProject.name }}</h3>

        <div v-if="qrUrl" class="qr-box__img">
          <img :src="qrUrl" :alt="`${qrProject.name} 提需二维码`" />
        </div>
        <EmptyState v-else size="sm" description="二维码生成失败，请手动复制下方链接分享给员工" />

        <p class="wb-muted qr-box__tip">员工可用微信扫码，或在 PC 浏览器打开链接提交原话。</p>

        <div class="qr-box__link">
          <el-input :model-value="publicLink(qrProject)" readonly>
            <template #append>
              <el-button @click="copyLink(qrProject)">复制</el-button>
            </template>
          </el-input>
        </div>
      </div>

      <template #footer>
        <el-button @click="qrVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 基座信息：改造前 .toolbar / .page-title 为本页私有，弹窗手写 el-dialog。
// 补充：契约 §8 要求「二维码生成失败时提示手动复制链接」，原实现无 try/catch。
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import QRCode from 'qrcode'
import PageHeader from '../components/PageHeader.vue'
import PanelCard from '../components/PanelCard.vue'
import DataTable from '../components/DataTable.vue'
import FormDialog from '../components/FormDialog.vue'
import StatusTag from '../components/StatusTag.vue'
import EmptyState from '../components/EmptyState.vue'
import client from '../api/client'

const emptyForm = () => ({
  name: '',
  company_business: '',
  project_background: '',
  progress: '',
  business_goals: '',
  business_process: '',
  target_users: '',
  constraints: '',
})

const items = ref([])
const keyword = ref('')
const loading = ref(false)
const visible = ref(false)
const qrVisible = ref(false)
const qrProject = ref(null)
const qrUrl = ref('')
const form = ref(emptyForm())

async function load() {
  loading.value = true
  try {
    items.value = (await client.get('/api/projects')).items
  } finally {
    loading.value = false
  }
}
onMounted(load)

/** 列表内轻量搜索：项目名 / 公司业务 / 项目背景 / 进度 */
const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return items.value
  return items.value.filter((r) =>
    `${r.name || ''} ${r.company_business || ''} ${r.project_background || ''} ${r.progress || ''}`
      .toLowerCase()
      .includes(kw),
  )
})

function publicLink(row) {
  return `${window.location.origin}/submit/${row.id}`
}

async function copyLink(row) {
  try {
    await navigator.clipboard.writeText(publicLink(row))
    ElMessage.success('提需链接已复制')
  } catch (e) {
    ElMessage.warning('复制失败，请在二维码弹窗中手动复制')
  }
}

async function showQr(row) {
  qrProject.value = row
  qrVisible.value = true
  qrUrl.value = ''
  try {
    qrUrl.value = await QRCode.toDataURL(publicLink(row), { width: 220, margin: 1 })
  } catch (e) {
    // 契约 §8：生成失败时提示手动复制链接，而不是留一个坏图
    ElMessage.warning('二维码生成失败，请手动复制链接分享')
  }
}

function openCreate() {
  form.value = emptyForm()
  visible.value = true
}

function edit(row) {
  form.value = { ...row }
  visible.value = true
}

async function save() {
  try {
    if (form.value.id) await client.put(`/api/projects/${form.value.id}`, form.value)
    else await client.post('/api/projects', form.value)
    visible.value = false
    ElMessage.success('基座信息已保存')
    await load()
  } catch (e) {
    /* 拦截器统一提示 */
  }
}
</script>

<style scoped>
.wb-row-actions {
  display: flex;
  align-items: center;
  gap: var(--wb-sp-1);
}

.wb-dialog-alert { margin-bottom: var(--wb-sp-4); }

.qr-box { text-align: center; }

.qr-box__name {
  margin: 0 0 var(--wb-sp-3);
  font-size: var(--wb-fs-lg);
  color: var(--wb-text-strong);
}

.qr-box__img img {
  width: 220px;
  height: 220px;
  border: 1px solid var(--wb-border);
  border-radius: var(--wb-radius-md);
  padding: var(--wb-sp-2);
  background: var(--wb-surface);
}

.qr-box__tip {
  font-size: var(--wb-fs-xs);
  margin: var(--wb-sp-3) 0;
}

.qr-box__link { text-align: left; }
</style>
