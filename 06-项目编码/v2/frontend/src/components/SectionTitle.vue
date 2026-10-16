<template>
  <div class="wb-section-title">
    <span class="wb-section-title__text">
      <slot>{{ text }}</slot>
    </span>
    <div v-if="$slots.extra" class="wb-section-title__extra">
      <slot name="extra" />
    </div>
  </div>
</template>

<script setup>
// 分区标题：改造前需求详情抽屉内用 el-divider 分隔，视觉重量与层级不统一。
defineOptions({ name: 'SectionTitle' })

defineProps({
  text: { type: String, default: '' },
})
</script>

<style scoped>
.wb-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--wb-sp-3);
  margin: var(--wb-sp-6) 0 var(--wb-sp-3);
}

.wb-section-title:first-child { margin-top: 0; }

.wb-section-title__text {
  font-size: var(--wb-fs-sm);
  line-height: var(--wb-lh-sm);
  font-weight: 600;
  color: var(--wb-text-strong);
  display: inline-flex;
  align-items: center;
  gap: var(--wb-sp-2);
}

/* 左侧短竖条：轻量标识分区起点，不用整条分割线（降低视觉噪音） */
.wb-section-title__text::before {
  content: '';
  width: 3px;
  height: 12px;
  border-radius: 2px;
  background: var(--wb-green-600);
  flex-shrink: 0;
}

.wb-section-title__extra {
  display: flex;
  align-items: center;
  gap: var(--wb-sp-2);
}
</style>
