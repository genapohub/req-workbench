<template>
  <div class="wb-method" :class="`wb-method--${tone}`">
    <div class="wb-method__head">
      <strong class="wb-method__name">{{ name }}</strong>
      <StatusTag :label="statusText" :tone="tone" size="sm" />
    </div>
    <p v-if="desc" class="wb-method__desc">{{ desc }}</p>
    <p v-if="text" class="wb-method__text">{{ text }}</p>
    <slot />
  </div>
</template>

<script setup>
// 方法论检查卡片（PRD 9.2：JTBD 场景 / 5 Whys / 证据链 / RICE 四维）
// 改造前在 Requirements 抽屉里用 method-grid + 内联 class 实现，样式未组件化。
// 重要原则：这里只呈现「检查是否通过」，绝不把 AI 结果渲染成事实结论。
defineOptions({ name: 'MethodCheckCard' })

import { computed } from 'vue'
import StatusTag from './StatusTag.vue'
import { METHOD_STATUS, labelOf, toneOf } from '../constants/enums'
import { METHOD_DESC } from '../constants/methodology'

const props = defineProps({
  /** 方法论名称，如「JTBD 场景」 */
  name: { type: String, required: true },
  /** 检查说明文本 */
  text: { type: String, default: '' },
  /** 检查结果：pass 已满足 / warn 待补充 / fail 未满足 */
  status: { type: String, default: '' },
})

const statusText = computed(() => labelOf(METHOD_STATUS, props.status, '待检查'))
const tone = computed(() => toneOf(METHOD_STATUS, props.status))
/** 卡名白话注释（constants/methodology.js 按 name 对齐；未命中则静默不显示） */
const desc = computed(() => METHOD_DESC[props.name] || '')
</script>

<style scoped>
.wb-method {
  border: 1px solid var(--wb-border);
  border-left: 3px solid var(--wb-border-strong);
  border-radius: var(--wb-radius-sm);
  padding: var(--wb-sp-3);
  background: var(--wb-surface);
  transition: background var(--wb-dur-fast) var(--wb-ease);
}

.wb-method__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--wb-sp-2);
  margin-bottom: var(--wb-sp-1);
}

.wb-method__name {
  font-size: var(--wb-fs-sm);
  font-weight: 600;
  color: var(--wb-text-strong);
}

/* 白话注释：解释这张卡是什么，弱化但可读，与下方的「检查结果文本」区分开 */
.wb-method__desc {
  margin: 0 0 var(--wb-sp-2);
  font-size: var(--wb-fs-xs);
  line-height: var(--wb-lh-xs);
  color: var(--wb-text-disabled);
}

.wb-method__text {
  margin: 0;
  font-size: var(--wb-fs-xs);
  line-height: var(--wb-lh-xs);
  color: var(--wb-text-muted);
}

/* ---------- 状态变体 ---------- */
.wb-method--success {
  border-color: var(--wb-good-border);
  border-left-color: var(--wb-good);
  background: var(--wb-good-bg);
}
.wb-method--warning {
  border-color: var(--wb-warn-border);
  border-left-color: var(--wb-warn);
  background: var(--wb-warn-bg);
}
.wb-method--danger {
  border-color: var(--wb-bad-border);
  border-left-color: var(--wb-bad);
  background: var(--wb-bad-bg);
}
/* 未检查 / 未知状态保持中性，不制造已判断的错觉 */
.wb-method--neutral {
  border-color: var(--wb-neutral-border);
  border-left-color: var(--wb-neutral);
  background: var(--wb-neutral-bg);
}
</style>
