// ============================================================
// 需求智能工作台 v2 · 统一枚举字典（唯一事实源）
// ------------------------------------------------------------
// 背景：改造前 authLabel / relLabel / prioLabel / statusLabel 及对应色调
//       映射在 Dashboard 与 Requirements 各写一份，改一个要改两处。
// 约定：tone 取值 success(绿) / warning(橙) / danger(红) / info(蓝) / neutral(灰)
//       红色只留给「存在反证 / 不采纳」，避免与「高优先级」混淆语义。
// ============================================================

/** 问题真实性（PRD 4.4） */
export const AUTHENTICITY = {
  pending:      { label: '待验证',   tone: 'neutral' },
  supported:    { label: '已佐证',   tone: 'success' },
  contradicted: { label: '存在反证', tone: 'danger'  },
}

/** 业务相关性（PRD 4.4） */
export const RELEVANCE = {
  unknown:  { label: '待明确',   tone: 'neutral' },
  direct:   { label: '直接相关', tone: 'success' },
  indirect: { label: '间接相关', tone: 'warning' },
}

/** 投入优先级（PRD 4.4） */
export const PRIORITY = {
  unassessed: { label: '待评估', tone: 'neutral' },
  high:       { label: '高',     tone: 'warning' },
  medium:     { label: '中',     tone: 'info'    },
  low:        { label: '低',     tone: 'neutral' },
}

/** 需求状态（主流程） */
export const STATUS = {
  draft:      { label: '草稿',   tone: 'neutral' },
  clarifying: { label: '澄清中', tone: 'warning' },
  review:     { label: '待评审', tone: 'info'    },
  pooled:     { label: '已入池', tone: 'success' },
  deferred:   { label: '暂缓',   tone: 'neutral' },
  rejected:   { label: '不采纳', tone: 'danger'  },
}

/** 账号状态 */
export const ACCOUNT_STATUS = {
  active:   { label: '启用', tone: 'success' },
  disabled: { label: '停用', tone: 'neutral' },
}

/** 基座完整度 */
export const BASE_STATUS = {
  complete:   { label: '已完整', tone: 'success' },
  incomplete: { label: '缺项',   tone: 'warning' },
}

/**
 * 方法论检查卡片状态（PRD 9.2）
 * ⚠️ 取值必须与后端 build_method_cards 保持一致：实际返回 ok / missing，
 *    不是 pass / fail。取错会导致卡片全部退化成中性灰。
 */
export const METHOD_STATUS = {
  ok:      { label: '已满足', tone: 'success' },
  missing: { label: '待补充', tone: 'warning' },
}

/** 审计日志动作 */
export const AUDIT_ACTION = {
  'auth.login':           { label: '登录成功',   tone: 'info'    },
  'auth.login_failed':    { label: '登录失败',   tone: 'danger'  },
  'auth.logout':          { label: '退出登录',   tone: 'neutral' },
  'auth.change_password': { label: '修改密码',   tone: 'warning' },
  'users.create':         { label: '新增账号',   tone: 'success' },
  'users.update':         { label: '编辑账号',   tone: 'warning' },
  'users.delete':         { label: '删除账号',   tone: 'danger'  },
  'projects.create':      { label: '新建项目',   tone: 'success' },
  'projects.update':      { label: '编辑基座',   tone: 'warning' },
  'requirements.create':  { label: '提交需求',   tone: 'success' },
  'requirements.review':  { label: '评审变更',   tone: 'warning' },
  'requirements.export':  { label: '导出需求卡', tone: 'info'    },
  'public.submit':        { label: '公开提需',   tone: 'success' },
}

// ---------- 取值辅助 ----------

/** 取显示文案；未登记时回退原始值，避免空白 */
export const labelOf = (map, key, fallback = '-') => map?.[key]?.label || key || fallback

/** 取语义色调；未登记时回退 neutral */
export const toneOf = (map, key) => map?.[key]?.tone || 'neutral'

/**
 * 按「显示文案」反查色调。
 * 背景：/api/dashboard 的 by_status 键是中文 label（如「澄清中」）而非英文 key
 *       （后端为 `{STATUS_LABELS.get(k, k): c}`），直接按 key 查会全部退化成灰色。
 */
export const toneByLabel = (map, label) => {
  const hit = Object.values(map || {}).find((v) => v.label === label)
  return hit?.tone || 'neutral'
}

/** 生成 <el-option> 用的选项数组，避免每个下拉各写一遍 */
export const optionsOf = (map) =>
  Object.entries(map).map(([value, v]) => ({ value, label: v.label }))

/** 状态列表（供下拉/筛选复用） */
export const STATUS_OPTIONS = optionsOf(STATUS)
export const AUTHENTICITY_OPTIONS = optionsOf(AUTHENTICITY)
export const PRIORITY_OPTIONS = optionsOf(PRIORITY)
export const RELEVANCE_OPTIONS = optionsOf(RELEVANCE)
export const ACCOUNT_STATUS_OPTIONS = optionsOf(ACCOUNT_STATUS)
export const AUDIT_ACTION_OPTIONS = optionsOf(AUDIT_ACTION)
