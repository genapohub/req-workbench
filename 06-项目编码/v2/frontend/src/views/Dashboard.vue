<template>
  <div>
    <PageHeader
      title="工作概览"
      description="看基座是否完整、需求是否有证据、是否已经挖到真实场景。"
    >
      <template #actions>
        <!-- PRD 9.4：首页「提交原话」直接打开提交流程，不再只跳转列表 -->
        <el-button type="primary" :icon="Plus" @click="goCreate">提交原话</el-button>
      </template>
    </PageHeader>

    <!-- 基座缺失醒目提示（设计方向 §3） -->
    <el-alert
      v-if="d.base_incomplete_projects"
      class="wb-page-alert"
      type="warning"
      :closable="false"
      show-icon
      title="还有项目缺少公司业务、项目背景或项目进度，需求挖掘与辨伪会被限制。"
    />

    <div class="stat-grid">
      <StatCard label="项目数" :value="d.total_projects || 0" :loading="loading">
        <template #icon><el-icon :size="18"><Files /></el-icon></template>
      </StatCard>
      <StatCard label="基座完整项目" :value="d.base_complete_projects || 0" :loading="loading">
        <template #icon><el-icon :size="18"><CircleCheck /></el-icon></template>
      </StatCard>
      <StatCard
        label="待验证需求"
        :value="pendingCount"
        :loading="loading"
        tone="neutral"
        hint="证据不足，尚未判定"
      >
        <template #icon><el-icon :size="18"><Clock /></el-icon></template>
      </StatCard>
      <StatCard
        label="已佐证需求"
        :value="supportedCount"
        :loading="loading"
        tone="success"
        hint="已有支持证据"
      >
        <template #icon><el-icon :size="18"><CircleCheckFilled /></el-icon></template>
      </StatCard>
    </div>

    <div class="dist-grid">
      <PanelCard title="评审状态">
        <div v-if="statusList.length" class="dist-list">
          <div v-for="s in statusList" :key="s.key" class="dist-item">
            <StatusTag :label="s.label" :tone="s.tone" dot size="md" />
            <div class="dist-bar">
              <span
                class="dist-bar__fill"
                :class="`dist-bar__fill--${s.tone}`"
                :style="{ width: pctOf(s.value, statusList) + '%' }"
              />
            </div>
            <span class="dist-num wb-num">{{ s.value }}</span>
          </div>
        </div>
        <EmptyState v-else size="sm" description="暂无需求" />
      </PanelCard>

      <PanelCard title="问题真实性">
        <div v-if="authList.length" class="dist-list">
          <div v-for="s in authList" :key="s.key" class="dist-item">
            <StatusTag :label="s.label" :tone="s.tone" dot size="md" />
            <div class="dist-bar">
              <span
                class="dist-bar__fill"
                :class="`dist-bar__fill--${s.tone}`"
                :style="{ width: pctOf(s.value, authList) + '%' }"
              />
            </div>
            <span class="dist-num wb-num">{{ s.value }}</span>
          </div>
        </div>
        <EmptyState v-else size="sm" description="暂无需求" />
      </PanelCard>

      <PanelCard title="投入优先级">
        <div v-if="prioList.length" class="dist-list">
          <div v-for="s in prioList" :key="s.key" class="dist-item">
            <StatusTag :label="s.label" :tone="s.tone" dot size="md" />
            <div class="dist-bar">
              <span
                class="dist-bar__fill"
                :class="`dist-bar__fill--${s.tone}`"
                :style="{ width: pctOf(s.value, prioList) + '%' }"
              />
            </div>
            <span class="dist-num wb-num">{{ s.value }}</span>
          </div>
        </div>
        <EmptyState v-else size="sm" description="暂无需求" />
      </PanelCard>
    </div>
  </div>
</template>

<script setup>
// 工作概览：改造前 .page-head / .stat / el-card 样式均为本页私有，
// 且「真实性与优先级」挤在一个卡片里，与契约 §2 的三块分布不符。
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Files, CircleCheck, CircleCheckFilled, Clock } from '@element-plus/icons-vue'
import PageHeader from '../components/PageHeader.vue'
import PanelCard from '../components/PanelCard.vue'
import StatCard from '../components/StatCard.vue'
import StatusTag from '../components/StatusTag.vue'
import EmptyState from '../components/EmptyState.vue'
import { STATUS, AUTHENTICITY, PRIORITY, labelOf, toneByLabel } from '../constants/enums'
import client from '../api/client'

const router = useRouter()
const d = ref({ by_status: {}, by_authenticity: {}, by_priority: {} })
const loading = ref(false)

const pendingCount = computed(() => d.value.by_authenticity?.pending || 0)
const supportedCount = computed(() => d.value.by_authenticity?.supported || 0)

/**
 * 把后端 { key: count } 映射为「标签 + 色调 + 数值」。
 * 兼容两种键形态：
 *  - 英文 key（by_authenticity / by_priority）：直接查枚举
 *  - 中文 label（by_status，后端用 STATUS_LABELS 转过）：按文案反查色调
 */
const toDistList = (map, enumMap) =>
  Object.entries(map || {}).map(([key, value]) => {
    const known = enumMap[key]
    return {
      key,
      value,
      label: known?.label || labelOf(enumMap, key),
      tone: known?.tone || toneByLabel(enumMap, key),
    }
  })

const statusList = computed(() => toDistList(d.value.by_status, STATUS))
const authList = computed(() => toDistList(d.value.by_authenticity, AUTHENTICITY))
const prioList = computed(() => toDistList(d.value.by_priority, PRIORITY))

/** 占比条长度：同组内按最大值归一，避免小样本时条都看不见 */
const pctOf = (value, list) => {
  const total = (list || []).reduce((sum, i) => sum + (Number(i.value) || 0), 0)
  if (!total) return 0
  return Math.round(((Number(value) || 0) / total) * 100)
}

function goCreate() {
  router.push({ path: '/requirements', query: { create: '1' } })
}

onMounted(async () => {
  loading.value = true
  try {
    d.value = await client.get('/api/dashboard')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.wb-page-alert { margin-bottom: var(--wb-sp-5); }

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--wb-sp-4);
  margin-bottom: var(--wb-sp-5);
}

.dist-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--wb-sp-4);
}

.dist-list {
  display: flex;
  flex-direction: column;
  gap: var(--wb-sp-1);
}

.dist-item {
  display: grid;
  grid-template-columns: minmax(72px, auto) 1fr 36px;
  align-items: center;
  gap: var(--wb-sp-3);
  padding: var(--wb-sp-1) 0;
}

/* 占比条：把「多少」变成一眼可读的长度，而不是靠读数字 */
.dist-bar {
  height: 6px;
  background: var(--wb-border);
  border-radius: var(--wb-radius-pill);
  overflow: hidden;
}

.dist-bar__fill {
  display: block;
  height: 100%;
  border-radius: var(--wb-radius-pill);
  background: var(--wb-neutral);
  transition: width var(--wb-dur-slow) var(--wb-ease);
}

.dist-bar__fill--success { background: var(--wb-good); }
.dist-bar__fill--warning { background: var(--wb-warn); }
.dist-bar__fill--danger  { background: var(--wb-bad); }
.dist-bar__fill--info    { background: var(--wb-info); }
.dist-bar__fill--neutral { background: var(--wb-neutral); }

.dist-num {
  font-size: var(--wb-fs-lg);
  font-weight: 600;
  color: var(--wb-text-strong);
  text-align: right;
}

/* ---------- 响应式 ---------- */
@media (max-width: 1100px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .dist-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
  .stat-grid { grid-template-columns: 1fr; }
  .dist-grid { grid-template-columns: 1fr; }
}
</style>
