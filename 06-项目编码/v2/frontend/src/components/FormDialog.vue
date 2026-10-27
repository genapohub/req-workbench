<template>
  <el-dialog
    :model-value="modelValue"
    :title="title"
    :width="width"
    :close-on-click-modal="false"
    :close-on-press-escape="!loading && closable"
    :show-close="closable"
    class="wb-form-dialog"
    @update:model-value="onUpdateModelValue"
  >
    <!-- 长表单（如基座信息 8 个字段）内部滚动，避免弹窗超出视口 -->
    <div class="wb-form-dialog__body">
      <slot />
    </div>

    <template #footer>
      <slot name="footer">
        <el-button v-if="closable" :disabled="loading" @click="close">{{ cancelText }}</el-button>
        <el-button
          type="primary"
          :loading="loading"
          :disabled="disabled"
          @click="emit('confirm')"
        >
          {{ confirmText }}
        </el-button>
      </slot>
    </template>
  </el-dialog>
</template>

<script setup>
// 统一表单弹窗：改造前 Projects / Users / Requirements 各自手写 el-dialog，
// footer 的「取消 + 保存」按钮与宽度、关闭行为各不相同。
defineOptions({ name: 'FormDialog' })

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  width: { type: String, default: '600px' },
  /** 提交中：锁定按钮并禁止 ESC 关闭，防误触丢数据 */
  loading: { type: Boolean, default: false },
  /** 提交按钮禁用（如基座不完整时不允许提交需求） */
  disabled: { type: Boolean, default: false },
  /** 是否允许关闭（强制改密场景传 false：隐藏 X 与取消、禁 ESC） */
  closable: { type: Boolean, default: true },
  confirmText: { type: String, default: '保存' },
  cancelText: { type: String, default: '取消' },
})

const emit = defineEmits(['update:modelValue', 'confirm', 'close'])

function onUpdateModelValue(v) {
  emit('update:modelValue', v)
}

function close() {
  emit('update:modelValue', false)
  emit('close')
}
</script>

<style scoped>
.wb-form-dialog__body {
  max-height: 60vh;
  overflow-y: auto;
  padding-right: var(--wb-sp-1);
}
</style>
