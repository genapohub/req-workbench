<template>
  <FormDialog
    :model-value="modelValue"
    title="修改密码"
    width="420px"
    :loading="loading"
    :disabled="!canSubmit"
    :closable="!forced"
    confirm-text="确认修改"
    @update:model-value="onUpdate"
    @confirm="submit"
  >
    <p v-if="forced" class="wb-cp__tip">首次登录需修改初始密码后才能继续使用。</p>
    <el-form label-position="top" @submit.prevent>
      <el-form-item label="原密码">
        <el-input v-model="form.oldPassword" type="password" show-password placeholder="请输入原密码" />
      </el-form-item>
      <el-form-item label="新密码（至少 8 位，需含字母和数字）">
        <el-input v-model="form.newPassword" type="password" show-password placeholder="请输入新密码" />
      </el-form-item>
      <el-form-item label="确认新密码" :error="confirmError">
        <el-input v-model="form.confirmPassword" type="password" show-password placeholder="请再次输入新密码" />
      </el-form-item>
    </el-form>
  </FormDialog>
</template>

<script setup>
// 自助改密（P0-3）：所有登录用户可用；forced 模式（初始密码首登）不可关闭。
defineOptions({ name: 'ChangePasswordDialog' })

import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import FormDialog from './FormDialog.vue'
import client from '../api/client'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  /** 强制改密（must_change_password）：隐藏关闭入口，改完才能继续 */
  forced: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue', 'changed'])

const loading = ref(false)
const form = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })

const canSubmit = computed(
  () => form.oldPassword && form.newPassword.length >= 8 && form.confirmPassword,
)
const confirmError = computed(() =>
  form.confirmPassword && form.confirmPassword !== form.newPassword ? '两次输入的新密码不一致' : '',
)

watch(
  () => props.modelValue,
  (v) => {
    if (v) {
      form.oldPassword = ''
      form.newPassword = ''
      form.confirmPassword = ''
    }
  },
)

function onUpdate(v) {
  if (props.forced && !v) return
  emit('update:modelValue', v)
}

async function submit() {
  if (form.confirmPassword !== form.newPassword) return
  loading.value = true
  try {
    await client.post('/api/auth/change-password', {
      old_password: form.oldPassword,
      new_password: form.newPassword,
    })
    ElMessage.success('密码已修改')
    emit('changed')
    emit('update:modelValue', false)
  } catch (e) {
    /* 错误提示由 client 拦截器统一处理 */
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.wb-cp__tip {
  margin: 0 0 var(--wb-sp-3);
  padding: var(--wb-sp-2) var(--wb-sp-3);
  border-radius: var(--wb-radius-sm);
  background: var(--wb-warn-bg);
  color: var(--wb-warn);
  font-size: var(--wb-fs-sm);
  line-height: var(--wb-lh-sm);
}
</style>
