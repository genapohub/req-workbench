<template>
  <div>
    <PageHeader
      title="审计日志"
      description="关键写操作全量留痕：登录、改密、账号增删改、基座编辑、需求创建/评审/导出、公开提需。"
    >
      <template #actions>
        <el-button :icon="Refresh" @click="load">刷新</el-button>
      </template>
    </PageHeader>

    <PanelCard flush>
      <div class="wb-table-toolbar">
        <el-input
          v-model="keyword"
          clearable
          :prefix-icon="Search"
          placeholder="搜索操作人 / 对象"
          style="width: 220px"
        />
        <el-select v-model="filterAction" clearable placeholder="全部动作" style="width: 140px">
          <el-option
            v-for="o in AUDIT_ACTION_OPTIONS"
            :key="o.value"
            :value="o.value"
            :label="o.label"
          />
        </el-select>
        <span class="wb-table-toolbar__spacer" />
        <span class="wb-table-toolbar__count">共 {{ filtered.length }} 条</span>
      </div>

      <DataTable :data="filtered" :loading="loading" empty-text="暂无审计记录">
        <el-table-column label="时间" width="170">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="username" label="操作人" width="140">
          <template #default="{ row }">
            <span v-if="row.username">{{ row.username }}</span>
            <span v-else class="wb-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="动作" width="120">
          <template #default="{ row }">
            <StatusTag
              :label="labelOf(AUDIT_ACTION, row.action)"
              :tone="toneOf(AUDIT_ACTION, row.action)"
              dot
            />
          </template>
        </el-table-column>
        <el-table-column label="对象" width="200">
          <template #default="{ row }">
            <span v-if="row.target_type">{{ targetText(row) }}</span>
            <span v-else class="wb-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="详情" min-width="280">
          <template #default="{ row }">
            <span v-if="detailText(row)" class="audit-detail">{{ detailText(row) }}</span>
            <span v-else class="wb-muted">-</span>
          </template>
        </el-table-column>
      </DataTable>
    </PanelCard>
  </div>
</template>

<script setup>
// 审计日志查看页（Phase 1 P1-1）：只读，admin 专属（audit.view）。
defineOptions({ name: 'AuditLogsView' })

import { computed, onMounted, ref } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'
import PageHeader from '../components/PageHeader.vue'
import PanelCard from '../components/PanelCard.vue'
import DataTable from '../components/DataTable.vue'
import StatusTag from '../components/StatusTag.vue'
import { AUDIT_ACTION, AUDIT_ACTION_OPTIONS, labelOf, toneOf } from '../constants/enums'
import client from '../api/client'

const items = ref([])
const loading = ref(false)
const keyword = ref('')
const filterAction = ref('')

const filtered = computed(() => {
  let list = items.value
  if (filterAction.value) list = list.filter((i) => i.action === filterAction.value)
  const kw = keyword.value.trim()
  if (kw) {
    list = list.filter((i) =>
      (i.username || '').includes(kw) ||
      (i.target_id || '').includes(kw) ||
      JSON.stringify(i.detail || {}).includes(kw),
    )
  }
  return list
})

function formatTime(ts) {
  if (!ts) return '-'
  const d = new Date(ts * 1000)
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

const TARGET_LABELS = { user: '账号', project: '项目', requirement: '需求' }
function targetText(row) {
  return `${TARGET_LABELS[row.target_type] || row.target_type} ${row.target_id?.slice(0, 8) || ''}`
}

/** 前后值 diff 展平为「字段: 旧 → 新」，其余 detail 取关键字段 */
function detailText(row) {
  const d = row.detail || {}
  const parts = []
  if (d.name) parts.push(String(d.name))
  if (d.title) parts.push(String(d.title))
  if (d.username && !d.name) parts.push(String(d.username))
  if (d.reason) parts.push(String(d.reason))
  if (d.changed) {
    for (const [k, [o, n]] of Object.entries(d.changed)) {
      parts.push(`${k}: ${o ?? '空'} → ${n ?? '空'}`)
    }
  }
  return parts.join('；')
}

async function load() {
  loading.value = true
  try {
    const data = await client.get('/api/audit-logs', { params: { limit: 500 } })
    items.value = data.items || []
  } catch (e) {
    /* 拦截器统一提示 */
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.audit-detail {
  color: var(--wb-text-muted);
  font-size: var(--wb-fs-xs);
  word-break: break-all;
}
</style>
