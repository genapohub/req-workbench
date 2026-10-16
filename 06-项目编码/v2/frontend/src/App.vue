<template>
  <router-view v-slot="{ Component }">
    <!-- 公开提需页 / 登录页：不套后台外壳 -->
    <component :is="Component" v-if="isPublicPage" />

    <div v-else class="wb-layout">
      <AppSidebar
        :menus="session.menus"
        :active-path="activePath"
        :collapsed="collapsed"
        :mobile-open="mobileOpen"
      />
      <!-- 移动端抽屉遮罩 -->
      <div v-if="mobileOpen" class="wb-mask" @click="mobileOpen = false" />

      <div class="wb-main">
        <AppTopbar
          :user="session.user"
          :crumb-label="crumbLabel"
          :collapsed="collapsed"
          @toggle-sidebar="toggleSidebar"
          @logout="logout"
        />
        <main class="wb-content">
          <!-- 轻量页面切换过渡：克制动效，不做位移回弹 -->
          <transition name="wb-fade" mode="out-in">
            <component :is="Component" :key="route.path" />
          </transition>
        </main>
      </div>
    </div>
  </router-view>
</template>

<script setup>
// 后台外壳：改造前侧边栏与顶栏内联在此且使用半透明 + backdrop-filter 毛玻璃
// （设计红线禁「渐变+发光+毛玻璃」三件套）。现已抽出为组件，此处只负责布局与会话。
// v2.1 UI 迭代：新增侧边栏折叠（桌面，记忆到 localStorage）、移动端抽屉、
// 面包屑与页面切换过渡，对齐主流后台（Ant Design Pro / TDesign Admin）的壳层惯例。
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppSidebar from './components/AppSidebar.vue'
import AppTopbar from './components/AppTopbar.vue'
import { session, clearSession } from './store/session'
import client from './api/client'

const route = useRoute()
const router = useRouter()

const COLLAPSE_KEY = 'wb_sidebar_collapsed'

const collapsed = ref(localStorage.getItem(COLLAPSE_KEY) === '1')
const mobileOpen = ref(false)

/** 与侧边栏抽屉断点保持一致（768px） */
const mql = window.matchMedia('(max-width: 768px)')
const isMobile = ref(mql.matches)
const onMqlChange = (e) => {
  isMobile.value = e.matches
  if (!e.matches) mobileOpen.value = false
}
mql.addEventListener('change', onMqlChange)
onBeforeUnmount(() => mql.removeEventListener('change', onMqlChange))

/** 顶栏开关：桌面切换折叠并记忆；移动端切换抽屉 */
function toggleSidebar() {
  if (isMobile.value) {
    mobileOpen.value = !mobileOpen.value
    return
  }
  collapsed.value = !collapsed.value
  localStorage.setItem(COLLAPSE_KEY, collapsed.value ? '1' : '0')
}

/** 路由变化时收起移动端抽屉，避免遮罩挡内容 */
watch(
  () => route.path,
  () => {
    mobileOpen.value = false
  },
)

/** 面包屑当前页名称：按激活路径匹配菜单 */
const crumbLabel = computed(() => {
  const menu = session.menus.find((m) => '/' + m.id === activePath.value)
  return menu?.label || ''
})

const isPublicPage = computed(() => Boolean(route.meta.public))

/** /dashboard 与 / 都归到 /overview 高亮 */
const activePath = computed(() =>
  route.path === '/' || route.path === '/dashboard' ? '/overview' : route.path,
)

async function logout() {
  try {
    await client.post('/api/auth/logout')
  } catch (e) {
    /* 退出以本地清会话为准，接口失败不阻塞 */
  }
  clearSession()
  ElMessage.success('已退出登录')
  router.replace('/login')
}
</script>

<style scoped>
.wb-layout {
  display: flex;
  height: 100%;
  /* 契约 §8：浅绿色渐变背景 + 白色卡片，贴近办公后台产品 */
  background: var(--wb-bg-gradient);
}

.wb-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.wb-content {
  flex: 1;
  overflow: auto;
  padding: var(--wb-content-pad);
}

/* 内容区最大宽度约束，超宽屏不至于把表格拉得过长 */
.wb-content > :deep(*) { max-width: var(--wb-content-max); }

/* ---------- 移动端抽屉遮罩 ---------- */
.wb-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, .65);
  z-index: calc(var(--wb-z-drawer) - 1);
}

/* ---------- 页面切换过渡：克制淡入，无回弹 ---------- */
.wb-fade-enter-active,
.wb-fade-leave-active {
  transition: opacity var(--wb-dur-fast) var(--wb-ease);
}

.wb-fade-enter-from { opacity: 0; }
.wb-fade-leave-to { opacity: 0; }
</style>
