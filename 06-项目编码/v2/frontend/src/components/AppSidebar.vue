<template>
  <aside
    class="wb-sidebar"
    :class="{ 'is-collapsed': collapsed, 'is-mobile-open': mobileOpen }"
  >
    <!-- 品牌区 -->
    <div class="wb-sidebar__brand">
      <div class="wb-sidebar__logo" aria-hidden="true">需</div>
      <div class="wb-sidebar__brand-text">
        <strong>{{ title }}</strong>
        <span>{{ subtitle }}</span>
      </div>
    </div>

    <!-- 导航 -->
    <nav class="wb-sidebar__nav">
      <RouterLink
        v-for="m in menus"
        :key="m.id"
        :to="'/' + m.id"
        class="wb-sidebar__item"
        :class="{ 'is-active': isActive(m.id) }"
        :title="m.label"
      >
        <el-icon v-if="iconOf(m.id)" class="wb-sidebar__icon">
          <component :is="iconOf(m.id)" />
        </el-icon>
        <span class="wb-sidebar__label">{{ m.label }}</span>
      </RouterLink>
    </nav>

    <div class="wb-sidebar__foot">
      <slot name="footer" />
    </div>
  </aside>
</template>

<script setup>
// 侧边栏：改造前内联在 App.vue，且使用 rgba 半透明 + backdrop-filter 毛玻璃
// （设计红线禁「渐变+发光+毛玻璃」三件套，且滚动时有性能开销）。
// 改为自绘而非 el-menu：飞书风格导航用 el-menu 需大量 :deep 覆盖，自绘更可控。
// v2.1 UI 迭代：新增桌面折叠态（64px 图标导航）与移动端抽屉态，
// 对齐 Ant Design Pro / TDesign Admin 的导航惯例（展开 224–232px / 收起 64px）。
defineOptions({ name: 'AppSidebar' })

import { RouterLink } from 'vue-router'
import { Odometer, Files, List, User } from '@element-plus/icons-vue'

const props = defineProps({
  /** 菜单项：{ id, label }，id 同时作为路由路径 */
  menus: { type: Array, default: () => [] },
  /** 当前激活路径 */
  activePath: { type: String, default: '' },
  /** 桌面折叠态：只留图标，悬停由 RouterLink 原生 title 提示 */
  collapsed: { type: Boolean, default: false },
  /** 移动端抽屉展开态（<768px） */
  mobileOpen: { type: Boolean, default: false },
  title: { type: String, default: '需求智能工作台' },
  subtitle: { type: String, default: '问题 · 证据 · 取舍' },
})

const ICONS = { overview: Odometer, projects: Files, requirements: List, users: User }
const iconOf = (id) => ICONS[id] || null

/** 支持 /requirements?req=1 这类子路径仍高亮父菜单 */
const isActive = (id) => {
  const base = '/' + id
  return props.activePath === base || props.activePath.startsWith(base + '/') || props.activePath.startsWith(base + '?')
}
</script>

<style scoped>
.wb-sidebar {
  width: var(--wb-sidebar-w);
  flex-shrink: 0;
  background: var(--wb-surface);
  border-right: 1px solid var(--wb-border);
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* ---------- 品牌区 ---------- */
.wb-sidebar__brand {
  height: var(--wb-topbar-h);
  display: flex;
  align-items: center;
  gap: var(--wb-sp-2);
  padding: 0 var(--wb-sp-4);
  border-bottom: 1px solid var(--wb-border);
  flex-shrink: 0;
}

.wb-sidebar__logo {
  width: 30px;
  height: 30px;
  border-radius: 50%; /* Spotify 式圆形品牌标 */
  background: var(--wb-green-600);
  color: var(--wb-on-accent); /* 绿底上用黑字 */
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: var(--wb-fs-base);
  flex-shrink: 0;
}

.wb-sidebar__brand-text { min-width: 0; }
.wb-sidebar__brand-text strong {
  display: block;
  font-size: var(--wb-fs-sm);
  font-weight: 600;
  color: var(--wb-text-strong);
  white-space: nowrap;
}
.wb-sidebar__brand-text span {
  display: block;
  font-size: var(--wb-fs-xs);
  color: var(--wb-text-muted);
  margin-top: 1px;
  white-space: nowrap;
}

/* ---------- 导航 ---------- */
.wb-sidebar__nav {
  flex: 1;
  padding: var(--wb-sp-2) var(--wb-sp-2);
  overflow-y: auto;
}

.wb-sidebar__item {
  display: flex;
  align-items: center;
  gap: var(--wb-sp-2);
  height: 36px;
  padding: 0 var(--wb-sp-3);
  margin-bottom: 2px;
  border-radius: var(--wb-radius-sm);
  color: var(--wb-text);
  font-size: var(--wb-fs-base);
  text-decoration: none;
  transition:
    background var(--wb-dur-fast) var(--wb-ease),
    color var(--wb-dur-fast) var(--wb-ease);
}

.wb-sidebar__item:hover {
  background: var(--wb-surface-hover);
  color: var(--wb-text-strong);
}

.wb-sidebar__item.is-active {
  background: var(--wb-green-100);
  color: var(--wb-green-700);
  font-weight: 600;
}

.wb-sidebar__icon { font-size: 16px; flex-shrink: 0; }
.wb-sidebar__label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.wb-sidebar__foot {
  padding: var(--wb-sp-2) var(--wb-sp-3);
  border-top: 1px solid var(--wb-border);
}

/* ---------- 桌面折叠态：64px 图标导航（对齐主流后台惯例） ---------- */
.wb-sidebar.is-collapsed {
  width: var(--wb-sidebar-w-collapsed);
}

.wb-sidebar.is-collapsed .wb-sidebar__brand {
  justify-content: center;
  padding: 0;
}

.wb-sidebar.is-collapsed .wb-sidebar__brand-text { display: none; }

.wb-sidebar.is-collapsed .wb-sidebar__item {
  justify-content: center;
  padding: 0;
}

.wb-sidebar.is-collapsed .wb-sidebar__label { display: none; }

.wb-sidebar.is-collapsed .wb-sidebar__foot { padding: var(--wb-sp-2) var(--wb-sp-2); }

/* ---------- 移动端抽屉态：固定定位 + 滑入滑出 ---------- */
@media (max-width: 768px) {
  .wb-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: var(--wb-z-drawer);
    transform: translateX(-100%);
    transition: transform var(--wb-dur-base) var(--wb-ease);
  }

  .wb-sidebar.is-mobile-open {
    transform: translateX(0);
    box-shadow: var(--wb-shadow-lg);
  }
}
</style>
