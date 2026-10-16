<template>
  <div class="wb-stat">
    <div class="wb-stat__top">
      <span class="wb-stat__label">{{ label }}</span>
      <span v-if="$slots.icon" class="wb-stat__icon"><slot name="icon" /></span>
    </div>

    <!-- loading：骨架屏而非空白，避免数字跳动 -->
    <div v-if="loading" class="wb-stat__value">
      <span class="wb-skeleton" />
    </div>
    <div v-else class="wb-stat__value wb-num" :class="`wb-stat__value--${tone}`">
      {{ value }}
    </div>

    <div v-if="hint" class="wb-stat__hint">{{ hint }}</div>
  </div>
</template>

<script setup>
// 指标卡：改造前 Dashboard 的 .stat 是纯文字居中，缺少层级与加载态。
defineOptions({ name: 'StatCard' })

defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: 0 },
  hint: { type: String, default: '' },
  /** 数字色调：brand 品牌绿（默认）/ success / warning / danger / neutral */
  tone: {
    type: String,
    default: 'brand',
    validator: (v) => ['brand', 'success', 'warning', 'danger', 'neutral'].includes(v),
  },
  loading: { type: Boolean, default: false },
})
</script>

<style scoped>
.wb-stat {
  background: var(--wb-surface);
  border: 1px solid var(--wb-border);
  border-radius: var(--wb-radius-md);
  box-shadow: var(--wb-shadow-xs);
  padding: var(--wb-sp-4) var(--wb-sp-5);
  display: flex;
  flex-direction: column;
  gap: var(--wb-sp-2);
  min-width: 0;
}

.wb-stat__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--wb-sp-2);
}

.wb-stat__label {
  font-size: var(--wb-fs-xs);
  line-height: var(--wb-lh-xs);
  color: var(--wb-text-muted);
  font-weight: 500;
}

.wb-stat__icon {
  color: var(--wb-green-600);
  display: inline-flex;
  opacity: .85;
}

.wb-stat__value {
  font-size: var(--wb-fs-metric);
  line-height: var(--wb-lh-metric);
  font-weight: var(--wb-fw-metric);
  letter-spacing: -0.02em;
}

.wb-stat__value--brand   { color: var(--wb-green-600); }
.wb-stat__value--success { color: var(--wb-good); }
.wb-stat__value--warning { color: var(--wb-warn); }
.wb-stat__value--danger  { color: var(--wb-bad); }
.wb-stat__value--neutral { color: var(--wb-text); }

.wb-stat__hint {
  font-size: var(--wb-fs-xs);
  line-height: var(--wb-lh-xs);
  color: var(--wb-text-muted);
}

/* 骨架屏 */
.wb-skeleton {
  display: block;
  width: 64%;
  height: 28px;
  border-radius: var(--wb-radius-xs);
  /* 深色上用白色微光做骨架，surface-hover 与 border 在近黑里区分度不够 */
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, .06) 25%,
    rgba(255, 255, 255, .16) 37%,
    rgba(255, 255, 255, .06) 63%
  );
  background-size: 400% 100%;
  animation: wb-shimmer 1.4s ease infinite;
}

@keyframes wb-shimmer {
  0%   { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}

@media (prefers-reduced-motion: reduce) {
  .wb-skeleton { animation: none; }
}
</style>
