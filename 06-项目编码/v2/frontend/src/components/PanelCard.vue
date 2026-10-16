<template>
  <section class="wb-panel-card">
    <header v-if="hasHead" class="wb-panel-card__head">
      <div class="wb-panel-card__titles">
        <slot name="title">
          <h3 v-if="title" class="wb-panel-card__title">{{ title }}</h3>
        </slot>
        <p v-if="description" class="wb-panel-card__desc">{{ description }}</p>
      </div>
      <div v-if="$slots.actions" class="wb-panel-card__actions">
        <slot name="actions" />
      </div>
    </header>

    <div class="wb-panel-card__body" :class="{ 'wb-panel-card__body--flush': flush }">
      <slot />
    </div>

    <footer v-if="$slots.footer" class="wb-panel-card__foot">
      <slot name="footer" />
    </footer>
  </section>
</template>

<script setup>
// 统一卡片容器：改造前 `el-card class="wb-panel" shadow="never"` 在多个视图重复，
// 且各视图卡片内边距、标题层级不一致。
// 注意：办公后台的表格容器不做 hover 位移（会干扰数据阅读），
// 可点击卡片由调用方通过 interactive 场景自行处理。
defineOptions({ name: 'PanelCard' })

import { computed, useSlots } from 'vue'

const props = defineProps({
  title: { type: String, default: '' },
  description: { type: String, default: '' },
  /** 去掉内容区内边距，用于容纳表格这类自带边界的组件 */
  flush: { type: Boolean, default: false },
})

const slots = useSlots()
const hasHead = computed(() => Boolean(props.title || props.description || slots.title || slots.actions))
</script>

<style scoped>
.wb-panel-card {
  background: var(--wb-surface);
  border: 1px solid var(--wb-border);
  border-radius: var(--wb-radius-md);
  box-shadow: var(--wb-shadow-xs);
  overflow: hidden;
}

.wb-panel-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--wb-sp-4);
  padding: var(--wb-sp-4) var(--wb-sp-5);
  border-bottom: 1px solid var(--wb-border);
  background: var(--wb-surface);
}

.wb-panel-card__titles { min-width: 0; }

.wb-panel-card__title {
  margin: 0;
  font-size: var(--wb-fs-lg);
  line-height: var(--wb-lh-lg);
  font-weight: var(--wb-fw-lg);
  color: var(--wb-text-strong);
}

.wb-panel-card__desc {
  margin: 2px 0 0;
  font-size: var(--wb-fs-xs);
  line-height: var(--wb-lh-xs);
  color: var(--wb-text-muted);
}

.wb-panel-card__actions {
  display: flex;
  align-items: center;
  gap: var(--wb-sp-2);
  flex-shrink: 0;
}

.wb-panel-card__body { padding: var(--wb-sp-5); }
.wb-panel-card__body--flush { padding: 0; }

.wb-panel-card__foot {
  padding: var(--wb-sp-3) var(--wb-sp-5);
  border-top: 1px solid var(--wb-border);
  background: var(--wb-surface-sub);
}
</style>
