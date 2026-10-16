<template>
  <div class="login-page">
    <!-- 品牌区：契约 §1 主文案 -->
    <div class="login-brand">
      <div class="brand-inner">
        <div class="brand-logo">需求智能工作台</div>
        <h1>先补齐业务基座，再判断需求真假</h1>
        <p>需求智能工作台只做两件事：挖真实场景，辨真实需求。</p>
        <ul class="brand-points">
          <li>真伪挖掘：证据固化，AI 推断不自动变事实</li>
          <li>基座信息：公司业务、项目背景、项目进度先补齐</li>
          <li>辨伪判断：证据不足保持待验证，不把推断当事实</li>
        </ul>
      </div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card-wrap">
      <el-card class="login-card" shadow="never">
        <h2 class="login-card__title">登录</h2>

        <!-- 错误提示留在卡片内，避免 toast 一闪而过 -->
        <el-alert
          v-if="errorMsg"
          class="login-card__alert"
          type="error"
          :closable="false"
          show-icon
          :title="errorMsg"
        />

        <el-form @submit.prevent="submit" label-position="top">
          <el-form-item label="账号">
            <el-input
              v-model="username"
              placeholder="请输入账号"
              :prefix-icon="User"
            />
          </el-form-item>
          <el-form-item label="密码">
            <el-input
              v-model="password"
              type="password"
              show-password
              placeholder="请输入密码"
              :prefix-icon="Lock"
              @keyup.enter="submit"
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-card__submit"
            :loading="loading"
            @click="submit"
          >
            登 录
          </el-button>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import client from '../api/client'
import { setSession } from '../store/session'

const route = useRoute()
const router = useRouter()

const username = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')

async function submit() {
  if (loading.value) return
  errorMsg.value = ''
  loading.value = true
  try {
    const login = await client.post('/api/auth/login', { username: username.value, password: password.value })
    const me = await client.get('/api/auth/me')
    setSession({ ...me, token: login.token })
    ElMessage.success('登录成功')
    router.replace(route.query.redirect || '/overview')
  } catch (e) {
    errorMsg.value = e?.message || '账号或密码不正确，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  height: 100%;
  display: flex;
}

/* ---------- 品牌区 ---------- */
.login-brand {
  flex: 1;
  /* Spotify 式：品牌区同样沉入近黑，只用一束绿色微光做品牌暗示
     （不是紫粉渐变，也不做发光描边） */
  background:
    radial-gradient(900px 520px at 16% 18%, rgba(30, 215, 96, .22), transparent 62%),
    var(--wb-bg);
  color: var(--wb-text);
  display: flex;
  align-items: center;
  padding: 0 6%;
}

.brand-logo {
  font-size: var(--wb-fs-xl);
  font-weight: 700;
  letter-spacing: .5px;
}

.brand-inner h1 {
  font-size: var(--wb-fs-3xl);
  line-height: var(--wb-lh-3xl);
  margin: var(--wb-sp-5) 0 var(--wb-sp-3);
  font-weight: 700;
}

.brand-inner p {
  font-size: var(--wb-fs-lg);
  opacity: .9;
  line-height: 1.7;
  max-width: 460px;
  margin: 0;
}

.brand-points {
  margin-top: var(--wb-sp-8);
  padding-left: 18px;
  line-height: 2.1;
  opacity: .92;
  font-size: var(--wb-fs-sm);
}

/* ---------- 登录卡片 ---------- */
.login-card-wrap {
  width: 460px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--wb-bg);
  padding: var(--wb-sp-6);
}

.login-card {
  width: 360px;
  border-radius: var(--wb-radius-lg);
  border: 1px solid var(--wb-border);
  box-shadow: var(--wb-shadow-md);
}

.login-card__title {
  margin: var(--wb-sp-1) 0 var(--wb-sp-5);
  font-size: var(--wb-fs-xl);
  font-weight: var(--wb-fw-xl);
  color: var(--wb-text-strong);
}

.login-card__alert { margin-bottom: var(--wb-sp-4); }

.login-card__submit { width: 100%; }

/* ---------- 响应式 ---------- */
@media (max-width: 860px) {
  .login-brand { display: none; }
  .login-card-wrap { width: 100%; }
}
</style>
