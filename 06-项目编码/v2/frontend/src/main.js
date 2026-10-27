import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import './styles/tokens.css'
// 必须在 element-plus 之后、组件之前加载：统一 EP 组件外观（弹窗/抽屉/表单等）
import './styles/overrides.css'
import App from './App.vue'
import router from './router'
import { setApiGate } from './api/gate'

// Mock 仅限开发环境：生产构建（DEV=false）时该分支为死代码，
// Rollup 会连同动态导入一起剔除，产物中不含 MSW 与任何演示数据。
const USE_MOCK = import.meta.env.DEV && import.meta.env.VITE_USE_MOCK !== 'false'

function escapeHtml(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

/**
 * 兜底错误卡片。
 * 始终展示错误堆栈（截断 + 滚动）：DOM 改写类崩溃只有堆栈能定位到具体组件/时机，
 * 用户直接截图此卡片即可回传完整诊断信息。
 */
function showFatal(msg, err) {
  const el = document.getElementById('app')
  if (!el) return
  const stackHtml =
    err && err.stack
      ? '<pre style="margin:12px 0 0;padding:10px 12px;border:1px solid var(--wb-border);' +
        'border-radius:var(--wb-radius-sm);background:var(--wb-surface-sub);color:var(--wb-text-muted);' +
        'font:12px/18px ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap;' +
        'word-break:break-all;max-height:220px;overflow:auto">' +
        escapeHtml(err.stack).slice(0, 1500) +
        '</pre>'
      : ''
  el.innerHTML =
    '<div style="max-width:640px;margin:10vh auto;padding:24px 28px;border:1px solid var(--wb-border);' +
    'border-radius:var(--wb-radius-lg);background:var(--wb-surface);color:var(--wb-text);' +
    'font:14px/22px var(--wb-font);box-shadow:var(--wb-shadow-md)">' +
    '<div style="font-size:16px;font-weight:600;color:var(--wb-green-600);margin-bottom:10px">需求智能工作台 v2</div>' +
    '<div style="white-space:pre-line">' + msg + '</div>' +
    stackHtml +
    '<button onclick="location.reload()" style="margin-top:16px;padding:8px 18px;border:1px solid var(--wb-green-600);' +
    'border-radius:var(--wb-radius-sm);background:var(--wb-green-600);color:#fff;font:14px/1 var(--wb-font);cursor:pointer">重新加载</button>' +
    '</div>'
}

/**
 * 识别「DOM 被外部改写」类错误，仅用于给出更准确的排障指引。
 * 典型来源：翻译/深色/划词类浏览器扩展在页面渲染期间搬走或清理节点，
 * 导致 Vue 插入时锚点失效（堆栈：insert ← mountElement ← patch ← mountChildren）。
 * 说明：此类问题属于浏览器环境侧，代码层不做 DOM 语义改写（那是技术债），
 *       只保留「重试 + 单次自动重载」这类不侵入的兜底。
 */
function isDomMutatedError(err) {
  const m = (err?.message || String(err)) + ''
  return /insertBefore|appendChild|removeChild|not a child/i.test(m)
}

const DOM_RECOVER_KEY = 'wb_dom_recover'
let domRecoverTried = false

/**
 * DOM 改写类错误的轻量兜底：单会话内最多自动重载一次（竞态型崩溃常可恢复），
 * 不做任何 DOM 原型改写；仍失败则落错误卡片并给出排障路径。
 */
function tryDomRecover(err) {
  if (domRecoverTried || !isDomMutatedError(err)) return false
  try {
    if (sessionStorage.getItem(DOM_RECOVER_KEY)) return false
    sessionStorage.setItem(DOM_RECOVER_KEY, '1')
  } catch (e) {
    return false
  }
  domRecoverTried = true
  location.reload()
  return true
}

/** 统一兜底文案：DOM 改写类错误直接指认扩展并给排障路径，其余维持通用提示 */
function fatalText(prefix, err) {
  const detail = (err?.message || err) + ''
  if (isDomMutatedError(err)) {
    return (
      prefix + detail +
      '\n\n该错误几乎都由浏览器扩展在页面渲染期间改写 DOM 引起（翻译/深色/划词类最典型，' +
      '如沉浸式翻译、Google 翻译、Dark Reader）：它们会搬走或清理 Vue 依赖的锚点节点。' +
      '\n请先点下方「重新加载」重试；若反复出现，把 127.0.0.1:5173 加入该扩展的「永不翻译/禁用」名单，' +
      '或改用无痕窗口（默认不带扩展）打开本页。'
    )
  }
  return prefix + detail + '\n\n请刷新重试；若持续出现请按 F12 查看控制台报错。'
}

/** 每次调用都产出全新 app 实例：挂载崩溃后重试必须换新实例，同实例二次 mount 会被 Vue 拒绝 */
function buildApp() {
  const app = createApp(App)
  for (const [key, comp] of Object.entries(ElementPlusIconsVue)) {
    if (comp) app.component(key, comp)
  }
  app.use(router)
  app.use(ElementPlus)

  app.config.errorHandler = (err, _inst, info) => {
    console.error('[App] 渲染错误：', err, info)
    if (tryDomRecover(err)) return
    showFatal(fatalText('页面渲染出现问题：', err), err)
  }
  return app
}

/** 全新实例重挂：清空容器换新实例重试（不改任何 DOM 语义，正常环境不会触发） */
function mountApp(retries) {
  const app = buildApp()
  try {
    app.mount('#app')
    return true
  } catch (err) {
    console.error('[Bootstrap] 挂载失败（剩余重试 ' + retries + '）：', err)
    if (retries > 0 && isDomMutatedError(err)) {
      document.getElementById('app')?.replaceChildren()
      return mountApp(retries - 1)
    }
    showFatal(fatalText('页面启动失败：', err), err)
    return false
  }
}

async function bootstrap() {
  if (USE_MOCK) {
    const { startMock } = await import('./mocks/browser')
    const timeout = new Promise((resolve) => setTimeout(() => resolve('timeout'), 10000))
    const gate = Promise.race([
      startMock()
        .then(() => 'ready')
        .catch((e) => {
          console.error('[MSW] mock 启动失败（页面仍可用，仅接口不可用）：', e)
          return 'failed'
        }),
      timeout,
    ])
    setApiGate(gate)
  } else {
    setApiGate(Promise.resolve('ready'))
  }

  router.onError((err) => {
    console.error('[Router] 路由错误：', err)
    if (tryDomRecover(err)) return
    showFatal(fatalText('页面加载出现问题：', err), err)
  })

  // ⚠️ 顺序敏感：Vue Router 4 的首次导航由 app.use(router)（install）触发，
  // 必须先构建并安装实例，await isReady() 才能完成；否则页面静默空白。
  const app = buildApp()
  await router.isReady()
  try {
    app.mount('#app')
  } catch (err) {
    console.error('[Bootstrap] 首次挂载失败：', err)
    if (isDomMutatedError(err)) {
      document.getElementById('app')?.replaceChildren()
      mountApp(2)
    } else {
      showFatal(fatalText('页面启动失败：', err), err)
    }
  }
}

bootstrap().catch((err) => {
  console.error('[Bootstrap] 启动失败：', err)
  if (tryDomRecover(err)) return
  showFatal(fatalText('页面启动失败：', err), err)
})
