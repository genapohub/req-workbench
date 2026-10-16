<template>
  <div class="wb-data-table">
    <el-table
      v-bind="$attrs"
      :data="data"
      :size="size"
      v-loading="loading"
      :element-loading-text="loadingText"
      :row-class-name="clickable ? 'wb-row-clickable' : undefined"
    >
      <slot />

      <!-- 空状态统一：带引导动作，而非干巴巴一行「暂无数据」 -->
      <template #empty>
        <EmptyState size="sm" :description="emptyText">
          <template v-if="$slots['empty-action']" #action>
            <slot name="empty-action" />
          </template>
        </EmptyState>
      </template>
    </el-table>
  </div>
</template>

<script setup>
// 统一表格：通过覆写 Element Plus 的表格 CSS 变量（而非硬编码选择器）来统一
// 表头底色、行 hover、分割线与密度，避免 EP 版本升级时选择器失效。
defineOptions({ name: 'DataTable' })

import EmptyState from './EmptyState.vue'

defineProps({
  /** 行数据 */
  data: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  loadingText: { type: String, default: '加载中' },
  /** 行是否可点击（影响 hover 反馈与鼠标指针） */
  clickable: { type: Boolean, default: false },
  emptyText: { type: String, default: '暂无数据' },
  /** 密度：large 宽松 / default 标准 / small 紧凑（对应主流后台的密度切换） */
  size: {
    type: String,
    default: 'default',
    validator: (v) => ['large', 'default', 'small'].includes(v),
  },
})
</script>

<style scoped>
.wb-data-table {
  /* ------ 覆写 EP 表格变量，统一为飞书克制风格 ------ */
  --el-table-header-bg-color:      var(--wb-surface-sub);
  --el-table-header-text-color:    var(--wb-text-strong);
  --el-table-row-hover-bg-color:   var(--wb-surface-hover);
  --el-table-current-row-bg-color: var(--wb-green-50);
  --el-table-border-color:         var(--wb-border);
  --el-table-text-color:           var(--wb-text);
  --el-table-bg-color:             var(--wb-surface);
  --el-table-tr-bg-color:          var(--wb-surface);

  /* 单元格纵向留白：中等信息密度 */
  --el-table-row-height: 48px;

  width: 100%;
}

/* 表头：细分割线 + 不加粗过度 */
.wb-data-table :deep(.el-table__header th.el-table__cell) {
  font-weight: 600;
  font-size: var(--wb-fs-sm);
  color: var(--wb-text-strong);
  background: var(--wb-surface-sub);
  border-bottom: 1px solid var(--wb-border);
}

/* 单元格：统一垂直对齐与行高 */
.wb-data-table :deep(.el-table__body td.el-table__cell) {
  font-size: var(--wb-fs-sm);
  color: var(--wb-text);
  border-bottom: 1px solid var(--wb-border);
}

/* 可点击行：指针 + 轻微底色反馈 */
.wb-data-table :deep(.wb-row-clickable) { cursor: pointer; }

/* 去掉表格最外层多余圆角，交给 PanelCard 统一承载 */
.wb-data-table :deep(.el-table) {
  border-radius: 0;
  background: transparent;
}

/* 表格内滚动条与全局一致 */
.wb-data-table :deep(.el-table__body-wrapper::-webkit-scrollbar) { height: 8px; }
</style>
