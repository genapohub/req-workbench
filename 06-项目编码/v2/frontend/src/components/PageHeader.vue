<template>
  <header class="wb-page-header">
    <div class="wb-page-header__text">
      <h2 class="wb-page-header__title">
        <slot name="title">{{ title }}</slot>
      </h2>
      <p v-if="description || $slots.description" class="wb-page-header__desc">
        <slot name="description">{{ description }}</slot>
      </p>
    </div>

    <div v-if="$slots.actions" class="wb-page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup>
// 页头：改造前 .toolbar / .page-head / .page-title 在 Dashboard、Projects、
// Requirements、Users 四个视图各写一遍（含重复 CSS），此处统一。
defineOptions({ name: 'PageHeader' })

defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
})
</script>

<style scoped>
.wb-page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--wb-sp-4);
  margin-bottom: var(--wb-sp-5);
}

.wb-page-header__text { min-width: 0; }

.wb-page-header__title {
  margin: 0;
  font-size: var(--wb-fs-2xl);
  line-height: var(--wb-lh-2xl);
  font-weight: var(--wb-fw-2xl);
  color: var(--wb-text-strong);
  letter-spacing: -0.01em;
}

.wb-page-header__desc {
  margin: var(--wb-sp-1) 0 0;
  font-size: var(--wb-fs-sm);
  line-height: var(--wb-lh-sm);
  color: var(--wb-text-muted);
  max-width: 720px;
}

.wb-page-header__actions {
  display: flex;
  align-items: center;
  gap: var(--wb-sp-2);
  flex-shrink: 0;
}

/* 窄屏：动作区换行到下一行，避免挤压标题 */
@media (max-width: 720px) {
  .wb-page-header {
    flex-direction: column;
    align-items: stretch;
  }
  .wb-page-header__actions {
    flex-wrap: wrap;
  }
}
</style>
