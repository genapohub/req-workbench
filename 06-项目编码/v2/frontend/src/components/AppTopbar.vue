<template>
  <header class="wb-topbar">
    <div class="wb-topbar__left">
      <slot name="left">
        <!-- 侧边栏开关：桌面折叠 / 移动端抽屉（主流后台标配） -->
        <button
          class="wb-topbar__trigger"
          type="button"
          :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
          :aria-expanded="!collapsed"
          @click="$emit('toggle-sidebar')"
        >
          <el-icon><component :is="triggerIcon" /></el-icon>
        </button>

        <!-- 面包屑：标示当前位置，替代原固定标语位 -->
        <nav v-if="crumbLabel" class="wb-crumb" aria-label="面包屑">
          <RouterLink class="wb-crumb__root" to="/overview">首页</RouterLink>
          <span class="wb-crumb__sep" aria-hidden="true">/</span>
          <span class="wb-crumb__current">{{ crumbLabel }}</span>
        </nav>
        <p v-else-if="hint" class="wb-topbar__hint">{{ hint }}</p>
      </slot>
    </div>

    <div class="wb-topbar__right">
      <slot name="actions" />

      <!-- 退出登录降为用户菜单中的二级操作（PRD 9.4） -->
      <el-dropdown trigger="click" placement="bottom-end" @command="onCommand">
        <button class="wb-user" type="button" aria-haspopup="menu" aria-label="用户菜单">
          <span class="wb-user__avatar" aria-hidden="true">{{ initial }}</span>
          <span class="wb-user__name">{{ displayName }}</span>
          <el-icon class="wb-user__caret"><ArrowDown /></el-icon>
        </button>

        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="logout" :icon="SwitchButton">
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup>
// 顶栏：改造前内联在 App.vue，高度 64px（与契约 §0 的 56px 不符），
// 且同样使用半透明 + 毛玻璃。此处统一为 56px 实色白底。
defineOptions({ name: 'AppTopbar' })

import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { SwitchButton, ArrowDown, Fold, Expand } from '@element-plus/icons-vue'

const props = defineProps({
  /** 当前用户对象，需含 name */
  user: { type: Object, default: null },
  /** 左侧说明文案（无面包屑时的兜底） */
  hint: { type: String, default: '' },
  /** 面包屑当前页名称（由 App.vue 根据菜单推导） */
  crumbLabel: { type: String, default: '' },
  /** 桌面折叠态（决定触发图标） */
  collapsed: { type: Boolean, default: false },
})

const emit = defineEmits(['logout', 'toggle-sidebar'])

const displayName = computed(() => props.user?.name || '未登录')
const initial = computed(() => displayName.value.charAt(0) || '?')

/** 折叠时显示「展开」图标，展开时显示「收起」图标 */
const triggerIcon = computed(() => (props.collapsed ? Expand : Fold))

function onCommand(cmd) {
  if (cmd === 'logout') emit('logout')
}
</script>

<style scoped>
.wb-topbar {
  height: var(--wb-topbar-h);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--wb-sp-4);
  padding: 0 var(--wb-sp-5);
  background: var(--wb-surface);
  border-bottom: 1px solid var(--wb-border);
}

.wb-topbar__left {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: var(--wb-sp-3);
}

/* ---------- 侧边栏开关 ---------- */
.wb-topbar__trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: var(--wb-radius-sm);
  color: var(--wb-text-muted);
  font-size: 16px;
  cursor: pointer;
  flex-shrink: 0;
  transition: background var(--wb-dur-fast) var(--wb-ease), color var(--wb-dur-fast) var(--wb-ease);
}

.wb-topbar__trigger:hover {
  background: var(--wb-surface-hover);
  color: var(--wb-text-strong);
}

.wb-topbar__trigger:focus-visible {
  outline: 2px solid var(--wb-green-600);
  outline-offset: 1px;
}

/* ---------- 面包屑 ---------- */
.wb-crumb {
  display: flex;
  align-items: center;
  gap: var(--wb-sp-2);
  font-size: var(--wb-fs-sm);
  line-height: var(--wb-lh-sm);
  min-width: 0;
}

.wb-crumb__root {
  color: var(--wb-text-muted);
  text-decoration: none;
  transition: color var(--wb-dur-fast) var(--wb-ease);
}

.wb-crumb__root:hover { color: var(--wb-green-700); }

.wb-crumb__sep {
  color: var(--wb-text-disabled);
  user-select: none;
}

.wb-crumb__current {
  color: var(--wb-text-strong);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wb-topbar__hint {
  margin: 0;
  font-size: var(--wb-fs-sm);
  line-height: var(--wb-lh-sm);
  color: var(--wb-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wb-topbar__right {
  display: flex;
  align-items: center;
  gap: var(--wb-sp-2);
  flex-shrink: 0;
}

/* ---------- 用户菜单触发按钮 ---------- */
.wb-user {
  display: inline-flex;
  align-items: center;
  gap: var(--wb-sp-2);
  height: 32px;
  padding: 0 var(--wb-sp-2) 0 3px;
  border: none;
  background: transparent;
  border-radius: var(--wb-radius-sm);
  color: var(--wb-text);
  font-family: inherit;
  font-size: var(--wb-fs-sm);
  cursor: pointer;
  transition: background var(--wb-dur-fast) var(--wb-ease);
}

.wb-user:hover { background: var(--wb-surface-hover); }

.wb-user:focus-visible {
  outline: 2px solid var(--wb-green-600);
  outline-offset: 1px;
}

.wb-user__avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--wb-green-600);
  color: var(--wb-on-accent);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: var(--wb-fs-xs);
  font-weight: 600;
  flex-shrink: 0;
}

.wb-user__name {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wb-user__caret { font-size: 12px; color: var(--wb-text-muted); }

/* 窄屏：隐藏说明文案与用户名，保留头像；面包屑只留当前页 */
@media (max-width: 720px) {
  .wb-topbar__hint { display: none; }
  .wb-user__name { display: none; }
  .wb-crumb__root, .wb-crumb__sep { display: none; }
}
</style>
