<template>
  <div class="public-page">
    <el-card class="public-card" shadow="never">
      <div class="public-card__brand">需求智能工作台</div>

      <!-- loading：读取项目信息 -->
      <div v-if="loading" class="public-body">
        <p class="wb-muted">正在读取项目提需表单…</p>
      </div>

      <!-- success：提交成功（契约 §8 要求页面级成功态，原实现只有 toast） -->
      <div v-else-if="submitted" class="public-body success-box">
        <svg class="success-icon" width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
          <circle cx="24" cy="24" r="21" stroke="currentColor" stroke-width="2" opacity=".35" />
          <path d="M15 24.5l6 6 12-13" stroke="currentColor" stroke-width="2.4"
                stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <h1 class="success-title">已提交</h1>
        <p class="wb-muted">
          PM 会继续追问、补证据并做方法论检查。如果想起别的场景，可以再提交一条。
        </p>
        <el-button type="primary" size="large" @click="resetForm">再提交一条</el-button>
      </div>

      <!-- 表单 -->
      <template v-else-if="project">
        <h1 class="public-title">提交需求原话</h1>
        <p class="wb-muted">
          所属项目：<b class="project-name">{{ project.name }}</b>
        </p>

        <el-alert
          v-if="!project.base_complete"
          class="public-alert"
          type="warning"
          :closable="false"
          show-icon
          :title="project.base_message"
        />

        <el-alert
          v-if="errorMsg"
          class="public-alert"
          type="error"
          :closable="false"
          show-icon
          :title="errorMsg"
        />

        <el-form label-position="top" class="public-form">
          <el-form-item label="你的姓名">
            <el-input v-model="form.submitter_name" placeholder="可选，便于后续追问" />
          </el-form-item>
          <el-form-item label="所属部门">
            <el-input v-model="form.submitter_department" placeholder="可选，例如：运营部" />
          </el-form-item>
          <el-form-item label="标题">
            <el-input v-model="form.title" placeholder="一句话概括这条诉求" />
          </el-form-item>
          <el-form-item label="用户原话">
            <el-input
              v-model="form.original"
              type="textarea"
              :rows="3"
              placeholder="按你自己的话描述，不需要写 PRD"
            />
          </el-form-item>
          <el-form-item label="最近一次真实场景">
            <el-input
              v-model="form.scenario"
              type="textarea"
              :rows="2"
              placeholder="谁在什么时候，想完成什么任务？"
            />
          </el-form-item>
          <el-form-item label="当前卡点">
            <el-input
              v-model="form.problem"
              type="textarea"
              :rows="2"
              placeholder="现在怎么处理，最麻烦的是哪一步？"
            />
          </el-form-item>
          <el-form-item label="影响说明">
            <el-input
              v-model="form.impact"
              type="textarea"
              :rows="2"
              placeholder="多久一次、影响多少人、耗时多久或有什么后果？"
            />
          </el-form-item>
        </el-form>

        <el-button
          type="primary"
          size="large"
          class="public-submit"
          :disabled="!project.base_complete || submitting"
          :loading="submitting"
          @click="submit"
        >
          提交
        </el-button>

        <p v-if="!project.base_complete" class="wb-muted public-foot">
          该项目基座尚不完整，暂时无法提交，请联系项目负责人补齐后再来。
        </p>
      </template>

      <!-- error：项目不存在或读取失败 -->
      <div v-else class="public-body">
        <EmptyState :description="errorMsg || '找不到该项目的提需表单，请检查链接是否正确'" />
      </div>
    </el-card>
  </div>
</template>

<script setup>
// 公开提需表单（PRD 9.1）：员工无需登录，扫码或打开链接即可提交原话。
// 状态覆盖：loading / 缺基座禁用 / 提交成功 / 提交失败（契约 §8）
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import EmptyState from '../components/EmptyState.vue'
import client from '../api/client'

const route = useRoute()
const project = ref(null)
const loading = ref(true)
const submitting = ref(false)
const submitted = ref(false)
const errorMsg = ref('')

const emptyForm = () => ({
  submitter_name: '',
  submitter_department: '',
  title: '',
  original: '',
  scenario: '',
  problem: '',
  impact: '',
})
const form = ref(emptyForm())

onMounted(async () => {
  loading.value = true
  try {
    const r = await client.get(`/api/public/projects/${route.params.projectId}/form`)
    project.value = r.project
  } catch (e) {
    errorMsg.value = '项目信息读取失败，请检查链接或联系项目负责人'
  } finally {
    loading.value = false
  }
})

async function submit() {
  errorMsg.value = ''
  submitting.value = true
  try {
    await client.post(`/api/public/projects/${route.params.projectId}/requirements`, form.value)
    submitted.value = true
    ElMessage.success('已提交，PM 会继续挖掘和评审')
  } catch (e) {
    // 提交失败：页面内显式呈现，而非只弹一个 toast 就消失
    errorMsg.value = e?.message || '提交失败，请稍后重试'
  } finally {
    submitting.value = false
  }
}

function resetForm() {
  form.value = emptyForm()
  submitted.value = false
  errorMsg.value = ''
}
</script>

<style scoped>
.public-page {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--wb-sp-8) var(--wb-sp-4);
  background: var(--wb-bg-gradient);
}

.public-card {
  width: min(720px, 100%);
  border-radius: var(--wb-radius-lg);
  border: 1px solid var(--wb-border);
  box-shadow: var(--wb-shadow-md);
}

.public-card__brand {
  color: var(--wb-green-600);
  font-weight: 700;
  font-size: var(--wb-fs-lg);
  margin-bottom: var(--wb-sp-3);
}

.public-title {
  margin: 0 0 var(--wb-sp-1);
  font-size: var(--wb-fs-2xl);
  line-height: var(--wb-lh-2xl);
  font-weight: var(--wb-fw-2xl);
  color: var(--wb-text-strong);
}

.project-name { color: var(--wb-text-strong); }

.public-alert { margin: var(--wb-sp-4) 0; }

.public-form { margin-top: var(--wb-sp-5); }

.public-submit { width: 100%; margin-top: var(--wb-sp-2); }

.public-foot {
  margin-top: var(--wb-sp-3);
  font-size: var(--wb-fs-xs);
  text-align: center;
}

/* ---------- 成功态 ---------- */
.public-body { padding: var(--wb-sp-4) 0; }

.success-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--wb-sp-3);
  padding: var(--wb-sp-6) 0;
}

.success-icon { color: var(--wb-good); }

.success-title {
  margin: 0;
  font-size: var(--wb-fs-2xl);
  font-weight: var(--wb-fw-2xl);
  color: var(--wb-text-strong);
}
</style>
