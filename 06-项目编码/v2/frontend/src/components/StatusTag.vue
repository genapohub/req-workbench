<template>
  <span class="wb-tag" :class="[`wb-tag--${tone}`, `wb-tag--${size}`]">
    <i v-if="dot" class="wb-tag__dot" aria-hidden="true" />
    <slot>{{ label }}</slot>
  </span>
</template>

<script setup>
// 统一状态标签：自绘而非用 el-tag，因为契约要求「待验证/待明确用中性色」，
// 而 Element Plus 没有 neutral 态，只有 primary/success/info/warning/danger。
defineOptions({ name: 'StatusTag' })

defineProps({
  /** 显示文案 */
  label: { type: String, default: '' },
  /** 语义色调：success 绿 / warning 橙 / danger 红 / info 蓝 / neutral 灰 */
  tone: {
    type: String,
    default: 'neutral',
    validator: (v) => ['success', 'warning', 'danger', 'info', 'neutral'].includes(v),
  },
  /** 尺寸：sm 表格内 / md 抽屉与卡片内 */
  size: {
    type: String,
    default: 'sm',
    validator: (v) => ['sm', 'md'].includes(v),
  },
  /** 是否显示状态圆点 */
  dot: { type: Boolean, default: false },
})
</script>

<style scoped>
.wb-tag {
  display: inline-flex;
  align-items: center;
  gap: var(--wb-sp-1);
  padding: 1px 8px;
  border-radius: var(--wb-radius-xs);
  font-size: var(--wb-fs-xs);
  line-height: 18px;
  font-weight: 500;
  white-space: nowrap;
  border: 1px solid transparent;
  transition: background var(--wb-dur-fast) var(--wb-ease);
}

.wb-tag--md {
  padding: 3px 10px;
  font-size: var(--wb-fs-sm);
  line-height: 20px;
}

/* 状态圆点：与主文字同色 */
.wb-tag__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

/* ---------- 语义色调（低饱和，取自 token） ---------- */
.wb-tag--success {
  color: var(--wb-good);
  background: var(--wb-good-bg);
  border-color: var(--wb-good-border);
}
.wb-tag--warning {
  color: var(--wb-warn);
  background: var(--wb-warn-bg);
  border-color: var(--wb-warn-border);
}
.wb-tag--danger {
  color: var(--wb-bad);
  background: var(--wb-bad-bg);
  border-color: var(--wb-bad-border);
}
.wb-tag--info {
  color: var(--wb-info);
  background: var(--wb-info-bg);
  border-color: var(--wb-info-border);
}
/* 中性态：不制造「已确认」的错觉，用于待验证 / 待明确 / 待评估 */
.wb-tag--neutral {
  color: var(--wb-neutral);
  background: var(--wb-neutral-bg);
  border-color: var(--wb-neutral-border);
}
</style>
