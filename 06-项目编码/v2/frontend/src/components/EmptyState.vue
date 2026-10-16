<template>
  <div class="wb-empty" :class="`wb-empty--${size}`">
    <div class="wb-empty__icon">
      <slot name="icon">
        <!-- 线性图标，非 emoji（设计红线） -->
        <svg width="52" height="52" viewBox="0 0 52 52" fill="none" aria-hidden="true">
          <rect x="10" y="8" width="32" height="38" rx="4"
                stroke="currentColor" stroke-width="1.6" opacity=".32" />
          <path d="M17 19h18M17 26h18M17 33h11"
                stroke="currentColor" stroke-width="1.6" stroke-linecap="round" opacity=".26" />
        </svg>
      </slot>
    </div>

    <p class="wb-empty__desc">
      <slot>{{ description }}</slot>
    </p>

    <!-- 空状态应「有教育意义」：告诉用户下一步能做什么 -->
    <div v-if="$slots.action" class="wb-empty__action">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup>
// 统一空状态：改造前各视图 el-empty 的描述与按钮各写各的，
// 且缺少「下一步该做什么」的引导。
defineOptions({ name: 'EmptyState' })

defineProps({
  description: { type: String, default: '暂无数据' },
  /** sm 用于表格内 / md 用于页面级 */
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md'].includes(v),
  },
})
</script>

<style scoped>
.wb-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--wb-text-muted);
}

.wb-empty--md { padding: var(--wb-sp-10) var(--wb-sp-5); }
.wb-empty--sm { padding: var(--wb-sp-6) var(--wb-sp-4); }

.wb-empty__icon { color: var(--wb-green-600); margin-bottom: var(--wb-sp-3); }
.wb-empty--sm .wb-empty__icon { margin-bottom: var(--wb-sp-2); }
.wb-empty--sm .wb-empty__icon :deep(svg) { width: 40px; height: 40px; }

.wb-empty__desc {
  margin: 0;
  font-size: var(--wb-fs-sm);
  line-height: var(--wb-lh-sm);
  color: var(--wb-text-muted);
  max-width: 380px;
}

.wb-empty__action { margin-top: var(--wb-sp-4); }
</style>
