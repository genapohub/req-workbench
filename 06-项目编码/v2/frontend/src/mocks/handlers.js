import { http, HttpResponse } from 'msw'

const PERMISSIONS = {
  admin: ['overview.view','projects.view','projects.manage','requirements.view','requirements.create','requirements.analyze','requirements.review','requirements.export','users.view','users.manage'],
  pm: ['overview.view','projects.view','projects.manage','requirements.view','requirements.create','requirements.analyze','requirements.review','requirements.export','users.view','users.manage'],
  staff: ['overview.view','projects.view','requirements.view','requirements.create'],
  tech: ['overview.view','projects.view','requirements.view','requirements.review'],
}
const MENUS = [
  { id: 'overview', label: '工作概览', permission: 'overview.view' },
  { id: 'requirements', label: '需求挖掘', permission: 'requirements.view' },
  { id: 'projects', label: '基座信息', permission: 'projects.view' },
  { id: 'users', label: '账号管理', permission: 'users.view' },
]
const STATUS_LABELS = { draft: '草稿', clarifying: '澄清中', review: '待评审', pooled: '已入池', deferred: '暂缓', rejected: '不采纳' }
let seq = 1
let activeSessionId = ''
const uid = (p) => `${p}-${(seq++).toString(36)}${Date.now().toString(36).slice(-4)}`
const now = () => Math.floor(Date.now() / 1000)

// 需求种子工厂：兜底字段齐全，调用处只传差异项，避免重复书写长字段
function mkReq(o = {}) {
  return {
    id: uid('req'),
    project_id: 'project-default',
    proposer_id: 'employee',
    title: '',
    original: '',
    scenario: '待补充场景。',
    problem: '待从用户原话中还原真实问题。',
    impact: '待补充影响范围、发生频率、时间损失或风险后果。',
    authenticity: 'pending',
    business_relevance: 'unknown',
    priority: 'unassessed',
    depth: 0,
    scope_score: 0, intensity_score: 0, value_score: 0, cost_score: 0,
    priority_reason: '证据不足，暂不生成综合优先级。',
    status: 'draft',
    clarifications: [], evidence: [],
    solutions: [
      { name: '维持现状', benefit: '无开发成本', cost: '问题继续存在', risk: '隐性人力损耗扩大' },
      { name: '流程调整', benefit: '低成本先验证', cost: '需要业务配合', risk: '无法解决系统性瓶颈' },
      { name: '产品改造', benefit: '沉淀为长期能力', cost: '需要技术投入', risk: '证据不足时容易做偏' },
    ],
    analysis_history: [], deep_dive_suggestions: [],
    source: 'seed', updated_by: 'seed',
    created_at: now(), updated_at: now(),
    ...o,
  }
}

const store = {
  users: [
    { id: 'admin', username: 'admin', name: '管理员', role_ids: ['admin'], status: 'active', password: 'Workbench2026!', must_change_password: false },
    { id: 'product', username: 'product', name: '陈思 · 需求负责人', role_ids: ['pm'], status: 'active', password: 'Workbench2026!', must_change_password: false },
    { id: 'employee', username: 'employee', name: '林晓 · 提出人', role_ids: ['staff'], status: 'active', password: 'Workbench2026!', must_change_password: false },
    { id: 'engineer', username: 'engineer', name: '周远 · 技术评估', role_ids: ['tech'], status: 'active', password: 'Workbench2026!', must_change_password: false },
  ],
  roles: Object.entries(PERMISSIONS).map(([id, permissions]) => ({ id, permissions })),
  projects: [
    { id: 'project-default', name: '需求智能工作台试点',
      company_business: '公司为内部业务团队提供数字化提效工具，核心链路是员工提出问题、产品还原需求、技术评估方案、评审确认投入。',
      project_background: '当前处于 v2 MVP 收窄阶段，目标是让 PM 更快判断员工诉求是否为真实需求。',
      progress: 'MVP 收窄开发中', business_goals: '提高需求判断质量和可追溯性。',
      business_process: '员工提交诉求 -> PM 挖掘真实场景 -> 补证据 -> 辨伪判断 -> 人工评审。',
      target_users: '员工、PM、技术评估人。', constraints: '一期只做需求挖掘和辨伪。', created_at: now(), updated_at: now() },
    { id: 'project-cs', name: '客户成功中台',
      company_business: '面向客户成功团队，统一客户健康度、续费预警与主动服务动作。',
      project_background: 'v2 方案设计阶段，目标是把散落在 CRM 与工单里的客户信号汇聚成可行动的健康度。',
      progress: '方案设计评审中', business_goals: '提升续费率、降低客户流失。',
      business_process: '信号采集 -> 健康度评分 -> 预警 -> 主动服务。',
      target_users: '客户成功经理、客户成功负责人。', constraints: '一期只做健康度与预警。', created_at: now(), updated_at: now() },
    { id: 'project-data', name: '数据资产目录',
      company_business: '数据团队为业务方提供统一的数据资产检索与血缘查看。',
      project_background: 'MVP 探索阶段，先验证业务方找数、懂数、用数的核心卡点。',
      progress: '需求调研', business_goals: '缩短找数时间、提升数据可信度。',
      business_process: '业务方提需求 -> 数据盘点 -> 资产编目 -> 检索授权。',
      target_users: '数据分析师、业务方、数据工程师。', constraints: '一期不做权限审批流。', created_at: now(), updated_at: now() },
  ],
  requirements: [
    // —— 草稿：员工刚提交，尚未开始挖掘 ——
    mkReq({ title: '新人入职环境配置繁琐', original: '我每次带新人都要手动装十几个环境和账号，容易漏。',
      scenario: '新人入职第一天的上午。', problem: '环境清单散落各处，靠老人口口相传。',
      impact: '每带一个新人约半天的隐性成本，且容易遗漏权限。',
      authenticity: 'pending', business_relevance: 'indirect', depth: 1 }),
    mkReq({ title: '跨团队知识库检索困难', original: '想找个历史方案要在三个文档系统里翻，经常找不到。',
      scenario: '方案评审前需要参考历史同类需求时。', problem: '知识分散，无统一检索入口。',
      impact: '重复造轮子，评审效率受影响。',
      authenticity: 'pending', business_relevance: 'unknown', depth: 0 }),

    // —— 澄清中：PM 正在补场景与证据 ——
    mkReq({ title: '运营日报重复整理', original: '我每天要从三个系统手动拼运营日报，希望减少重复整理。',
      scenario: '每个工作日上午提交运营日报前。', problem: '跨系统汇总依赖人工复制、核对和拼表。',
      impact: '每天约 1 次，影响产出效率；耗时和人数待补证据。',
      authenticity: 'pending', business_relevance: 'direct', priority: 'medium', depth: 3,
      scope_score: 3, intensity_score: 3, value_score: 4, cost_score: 2,
      priority_reason: '落在内部提效主链路，但缺少耗时和人数证据。',
      status: 'clarifying', evidence: [
        { id: uid('ev'), title: '日报字段梳理表', content: '已整理出 12 个高频字段。', kind: '梳理', source: '内部', supports: 'support', created_at: now(), created_by: 'product' },
      ] }),
    mkReq({ title: '数据导出等待时间长', original: '导出一份大表要等好几分钟，期间不敢动页面。',
      scenario: '月底对账需要导出的时刻。', problem: '导出为同步阻塞，前端长时间无响应。',
      impact: '每次导出约 3-5 分钟，影响多人并行工作。',
      authenticity: 'pending', business_relevance: 'indirect', depth: 2, status: 'clarifying' }),
    mkReq({ title: '用户反馈散落在多群', original: '客服把用户反馈截图发在不同群里，汇总量很大。',
      scenario: '每周整理用户反馈周报时。', problem: '反馈无结构化沉淀，靠人工搬运。',
      impact: '每周约 2 小时整理，易遗漏高优反馈。',
      authenticity: 'pending', business_relevance: 'direct', depth: 1, status: 'clarifying', evidence: [
        { id: uid('ev'), title: '一周反馈截图 23 张', content: '分散在 4 个群。', kind: '截图', source: '企业微信', supports: 'support', created_at: now(), created_by: 'employee' },
      ] }),

    // —— 待评审：证据较充分，等 PM 拍板 ——
    mkReq({ title: '审批流超时提醒', original: '审批老卡在某个人那，没人知道卡了多久。',
      scenario: '合同/报销审批流转中。', problem: '无超时预警，流程黑洞。',
      impact: '平均审批周期比预期长 1.5 天。',
      authenticity: 'supported', business_relevance: 'direct', priority: 'medium', depth: 3,
      scope_score: 4, intensity_score: 3, value_score: 4, cost_score: 2,
      priority_reason: '净分 9，建议优先级为 medium。',
      status: 'review', evidence: [
        { id: uid('ev'), title: '近一月审批时长统计', content: '超 48 小时占比 32%。', kind: '数据', source: 'OA', supports: 'support', created_at: now(), created_by: 'product' },
      ] }),
    mkReq({ title: '需求评审日历化', original: '评审会总跟其他会撞车，临时改期很乱。',
      scenario: '每周需求评审排期时。', problem: '评审缺少统一日历视图。',
      impact: '每月约 2 次改期，浪费参会人时间。',
      authenticity: 'supported', business_relevance: 'indirect', priority: 'low', depth: 2,
      scope_score: 2, intensity_score: 2, value_score: 3, cost_score: 2,
      priority_reason: '净分 5，建议优先级为 low。',
      status: 'review', evidence: [
        { id: uid('ev'), title: '三个月改期记录', content: '共 6 次改期。', kind: '记录', source: '日历', supports: 'support', created_at: now(), created_by: 'product' },
      ] }),

    // —— 已入池：按优先级排序（高→中→低→待评估，同级按深度降序）——
    mkReq({ title: '客服工单自动归类', original: '客服每天手工给上百条工单打标签，太慢了。',
      scenario: '每班客服交接前。', problem: '工单分类依赖人工，标准不一。',
      impact: '每班约 1 小时分类，分类准确率低。',
      authenticity: 'supported', business_relevance: 'direct', priority: 'high', depth: 4,
      scope_score: 4, intensity_score: 4, value_score: 5, cost_score: 3,
      priority_reason: '净分 10，建议优先级为 high。',
      status: 'pooled', evidence: [
        { id: uid('ev'), title: '工单抽样 200 条', content: '可规则化分类约 70%。', kind: '数据', source: '工单系统', supports: 'support', created_at: now(), created_by: 'product' },
        { id: uid('ev'), title: '准确率基线', content: '人工分类准确率 82%。', kind: '数据', source: '质检', supports: 'support', created_at: now(), created_by: 'product' },
      ] }),
    mkReq({ title: '报销审批移动化', original: '出差在外没法报销，回来堆一堆单据。',
      scenario: '出差途中产生费用时。', problem: '报销只能在 PC 端提交。',
      impact: '每月约 40 人次受影响，回公司集中处理拥堵。',
      authenticity: 'supported', business_relevance: 'direct', priority: 'high', depth: 3,
      scope_score: 3, intensity_score: 4, value_score: 4, cost_score: 3,
      priority_reason: '净分 8，建议优先级为 high。',
      status: 'pooled', evidence: [
        { id: uid('ev'), title: '出差频次调研', content: '销售岗月均出差 2 次。', kind: '访谈', source: '访谈', supports: 'support', created_at: now(), created_by: 'product' },
      ] }),
    mkReq({ title: '周报模板一键生成', original: '每周写周报都要重新搭结构，很烦。',
      scenario: '每周五下午。', problem: '周报无模板沉淀，重复搭建。',
      impact: '每人每周约 20 分钟，全公司量级可观。',
      authenticity: 'supported', business_relevance: 'indirect', priority: 'medium', depth: 3,
      scope_score: 3, intensity_score: 2, value_score: 3, cost_score: 2,
      priority_reason: '净分 6，建议优先级为 medium。',
      status: 'pooled', evidence: [
        { id: uid('ev'), title: '周报结构草稿', content: '已梳理 6 个通用模块。', kind: '梳理', source: '内部', supports: 'support', created_at: now(), created_by: 'employee' },
      ] }),
    mkReq({ title: '会议室智能推荐', original: '订会议室经常订到不合适的，白跑一趟。',
      scenario: '临时发起会议时。', problem: '无基于人数的智能推荐。',
      impact: '每周约 5 次订错，浪费走动时间。',
      authenticity: 'pending', business_relevance: 'indirect', priority: 'medium', depth: 2,
      scope_score: 2, intensity_score: 3, value_score: 3, cost_score: 2,
      priority_reason: '场景与证据待补充，暂定 medium。',
      status: 'pooled' }),
    mkReq({ title: '生日关怀自动化', original: '想给同事生日自动发个祝福，现在靠人记。',
      scenario: '同事生日当天。', problem: '无自动化提醒与触达。',
      impact: '覆盖约 120 人，低频但影响氛围。',
      authenticity: 'pending', business_relevance: 'unknown', priority: 'low', depth: 2,
      scope_score: 1, intensity_score: 1, value_score: 2, cost_score: 2,
      priority_reason: '价值偏低且非主链路，建议 low。',
      status: 'pooled' }),
    mkReq({ title: '临时任务看板', original: '突发任务在群里喊一声就过了，没留痕。',
      scenario: '临时插入任务时。', problem: '临时任务无看板承载。',
      impact: '任务易遗漏，复盘无据。',
      authenticity: 'pending', business_relevance: 'unknown', priority: 'unassessed', depth: 1,
      status: 'pooled' }),

    // —— 暂缓：排期靠后 ——
    mkReq({ title: '内部 IM 表情包商城', original: '想有个内部表情包库，聊天更有趣。',
      scenario: '日常沟通时。', problem: '无统一表情包资源。',
      impact: '锦上添花，无硬性痛点。',
      authenticity: 'pending', business_relevance: 'unknown', priority: 'low', depth: 1,
      status: 'deferred' }),
    mkReq({ title: '员工证照到期提醒', original: '资质证照到期了才发现，影响投标。',
      scenario: '资质管理周期。', problem: '无到期预警。',
      impact: '偶发但代价高，发生频率低。',
      authenticity: 'pending', business_relevance: 'indirect', priority: 'low', depth: 1,
      status: 'deferred' }),

    // —— 不采纳：存在反证或偏离主链路 ——
    mkReq({ title: '下班打卡自动化', original: '能不能自动帮我打卡，省得忘。',
      scenario: '下班时。', problem: '诉求本质是规避考勤。',
      impact: '与考勤制度冲突，存在合规风险。',
      authenticity: 'contradicted', business_relevance: 'unknown', priority: 'low', depth: 1,
      scope_score: 1, intensity_score: 1, value_score: 0, cost_score: 1,
      priority_reason: '存在反证，当前不建议投入开发资源。',
      status: 'rejected', evidence: [
        { id: uid('ev'), title: 'HR 制度说明', content: '考勤需本人操作，禁止代打卡。', kind: '制度', source: 'HR', supports: 'contradict', created_at: now(), created_by: 'product' },
      ] }),
    mkReq({ title: '团建地点全员投票', original: '团建去哪大家一起投个票就行。',
      scenario: '季度团建筹备。', problem: '与需求挖掘主链路无关。',
      impact: '属行政事务，无需产品化。',
      authenticity: 'contradicted', business_relevance: 'unknown', priority: 'low', depth: 0,
      status: 'rejected' }),

    // —— 跨项目：客户成功中台（project-cs）——
    mkReq({ project_id: 'project-cs', title: '续费前健康度看板缺失', original: '每次续费前都要手动拉好几个表看客户状态，容易漏掉下滑客户。',
      scenario: '季度续费盘点时。', problem: '健康度数据分散，无统一看板。',
      impact: '续费准备依赖人工拼表，易遗漏风险客户。',
      authenticity: 'pending', business_relevance: 'indirect', depth: 0 }),
    mkReq({ project_id: 'project-cs', title: '客户流失预警滞后', original: '客户都停用一周了我们才知道，太晚了。',
      scenario: '客户健康度周巡检时。', problem: '预警依赖人工发现，无自动阈值。',
      impact: '流失发现平均滞后 5-7 天，错过挽回窗口。',
      authenticity: 'pending', business_relevance: 'direct', depth: 2,
      status: 'clarifying',
      evidence: [{ id: uid('ev'), title: '近三月流失复盘', content: '60% 流失客户续费前无预警。', kind: '复盘', source: '内部', supports: 'support', created_at: now(), created_by: 'product' }] }),
    mkReq({ project_id: 'project-cs', title: '续费风险自动分级', original: '想把客户按续费风险分成高/中/低，优先跟进高的。',
      scenario: '续费季开始前。', problem: '风险全靠 CSM 主观判断。',
      impact: '约 200 家客户，人工分级耗时且不一致。',
      authenticity: 'supported', business_relevance: 'direct', priority: 'medium', depth: 3,
      scope_score: 3, intensity_score: 3, value_score: 4, cost_score: 2,
      priority_reason: '净分 8，建议优先级为 medium。',
      status: 'review', evidence: [{ id: uid('ev'), title: '客户分级访谈', content: '5 位 CSM 均认同分级跟进。', kind: '访谈', source: '访谈', supports: 'support', created_at: now(), created_by: 'product' }] }),
    mkReq({ project_id: 'project-cs', title: '客户成功周报自动生成', original: '每周给老板发客户成功周报，要手动汇总。',
      scenario: '每周一上午。', problem: '周报无模板沉淀。',
      impact: '每位 CSM 每周约 1 小时。',
      authenticity: 'supported', business_relevance: 'indirect', priority: 'medium', depth: 3,
      scope_score: 3, intensity_score: 2, value_score: 3, cost_score: 2,
      priority_reason: '净分 6，建议优先级为 medium。',
      status: 'pooled', evidence: [{ id: uid('ev'), title: '周报字段梳理', content: '已梳理 8 个高频指标。', kind: '梳理', source: '内部', supports: 'support', created_at: now(), created_by: 'employee' }] }),

    // —— 跨项目：数据资产目录（project-data）——
    mkReq({ project_id: 'project-data', title: '找数平均耗时过长', original: '想找一个指标的定义，问了三个人才找到。',
      scenario: '临时取数需求提出时。', problem: '资产无统一检索入口。',
      impact: '平均找数 30+ 分钟，影响分析效率。',
      authenticity: 'pending', business_relevance: 'direct', depth: 2,
      status: 'clarifying',
      evidence: [{ id: uid('ev'), title: '找数耗时抽样', content: '10 次取数平均 32 分钟。', kind: '数据', source: '内部', supports: 'support', created_at: now(), created_by: 'product' }] }),
    mkReq({ project_id: 'project-data', title: '指标口径一键核对', original: '不同报表同一个指标数值还不一样，到底信哪个？',
      scenario: '月度经营分析会前核对口径时。', problem: '指标口径散落，无权威来源。',
      impact: '每次对账约半天，且易出错。',
      authenticity: 'supported', business_relevance: 'direct', priority: 'high', depth: 4,
      scope_score: 4, intensity_score: 4, value_score: 5, cost_score: 3,
      priority_reason: '净分 10，建议优先级为 high。',
      status: 'pooled', evidence: [
        { id: uid('ev'), title: '口径冲突案例', content: '同一 GMV 出现 3 个版本。', kind: '数据', source: '数仓', supports: 'support', created_at: now(), created_by: 'product' },
        { id: uid('ev'), title: '影响范围统计', content: '涉及 12 张核心报表。', kind: '数据', source: '数仓', supports: 'support', created_at: now(), created_by: 'product' },
      ] }),
    mkReq({ project_id: 'project-data', title: '数据血缘可视化', original: '想看一个字段是从哪来的，只能翻 SQL。',
      scenario: '排查数据异常时。', problem: '无血缘视图。',
      impact: '排查链路问题耗时长。',
      authenticity: 'pending', business_relevance: 'indirect', priority: 'low', depth: 1,
      status: 'deferred' }),
  ],
  sessions: [],
}

const ok = (data) => HttpResponse.json({ code: 0, data, message: 'ok' })
const fail = (code, message, status = 400) => HttpResponse.json({ code, data: null, message }, { status })
const pubUser = (u) => { const { password, ...rest } = u; return rest }
const roleItems = () => Object.entries(PERMISSIONS).map(([id, permissions]) => ({ id, name: { admin: '系统管理员', pm: '需求负责人', staff: '普通员工', tech: '技术评估人' }[id] || id, permissions }))
function getCookie(req, key) { const raw = req.headers.get('Cookie') || ''; const m = raw.split(';').map((s) => s.trim()).find((s) => s.startsWith(key + '=')); return m ? m.slice(key.length + 1) : null }
function getBearer(req) { const raw = req.headers.get('Authorization') || ''; return raw.startsWith('Bearer ') ? raw.slice(7) : '' }
function currentUser(req) { const sid = getCookie(req, 'workbench_session') || getBearer(req) || activeSessionId; if (!sid) return null; if (sid.startsWith('mock-')) { const userId = sid.split('-')[1]; return store.users.find((u) => u.id === userId) || null } const s = store.sessions.find((x) => x.id === sid); return s ? store.users.find((u) => u.id === s.user_id) : null }
function rolePerms(user) { const set = new Set(); user.role_ids.forEach((rid) => (PERMISSIONS[rid] || []).forEach((p) => set.add(p))); return [...set] }
function menusOf(perms) { return MENUS.filter((m) => perms.includes(m.permission)) }
function baseMissing(project) { return ['company_business','project_background','progress'].filter((f) => !String(project?.[f] || '').trim()) }
function enrichProject(p) { const missing = baseMissing(p); return { ...p, base_complete: !missing.length, base_missing_fields: missing, base_status_label: missing.length ? '缺' + missing.map((f) => ({ company_business: '公司业务', project_background: '项目背景', progress: '项目进度' }[f])).join('、') : '完整' } }
function methodCards(req) { const ev = req.evidence || []; return [{ name: 'JTBD 场景', status: req.scenario && !req.scenario.includes('待补充') ? 'ok' : 'missing', text: req.scenario && !req.scenario.includes('待补充') ? '已描述真实场景' : '缺最近一次真实发生场景' }, { name: '5 Whys 追问', status: (req.clarifications || []).length ? 'ok' : 'missing', text: (req.clarifications || []).length ? '已有追问记录' : '至少补一轮为什么，避免停在用户给的方案' }, { name: '证据链', status: ev.length ? 'ok' : 'missing', text: ev.length ? `已有 ${ev.length} 条证据或反证` : '缺截图、数据、工单或访谈摘录' }, { name: 'RICE 四维', status: [req.scope_score, req.intensity_score, req.value_score, req.cost_score].some(Boolean) ? 'ok' : 'missing', text: [req.scope_score, req.intensity_score, req.value_score, req.cost_score].some(Boolean) ? '已填写部分评分' : '缺四维评分，暂不生成综合优先级' }] }
// 基座背书：与后端 analysis.py 口径一致——同项目「已入池」（= 已确认投入）的历史需求，
// 按业务词重合度取最相关若干条，仅作历史依据展示，不自动改写基座字段。
const ENDORSABLE_STATUSES = ['pooled']
function reqText(r) { return ['title', 'problem', 'scenario', 'impact'].map((k) => r[k] || '').join(' ') }
// 与后端 analysis.py _tokens 同口径：中文按字符 2-gram 切（中文无空格，按标点切会整句成一个 token），英文按词切
function tok(s) {
  const out = new Set()
  const text = String(s || '')
  ;(text.match(/[A-Za-z0-9]{2,}/g) || []).forEach((w) => out.add(w.toLowerCase()))
  ;(text.match(/[一-鿿]+/g) || []).forEach((seg) => {
    if (seg.length === 1) out.add(seg)
    for (let i = 0; i < seg.length - 1; i += 1) out.add(seg.slice(i, i + 2))
  })
  return out
}
function baseEndorsements(item, limit = 3) {
  const cur = tok(reqText(item))
  if (!cur.size) return []
  const out = []
  store.requirements.forEach((r) => {
    if (r.project_id !== item.project_id || r.id === item.id) return
    if (!ENDORSABLE_STATUSES.includes(r.status || 'draft')) return
    const hist = tok(reqText(r))
    const shared = [...cur].filter((w) => hist.has(w))
    if (!shared.length) return
    out.push({
      id: r.id,
      title: r.title || '',
      status: r.status || 'draft',
      status_label: STATUS_LABELS[r.status] || r.status || '',
      priority: r.priority || 'unassessed',
      problem: r.problem || r.original || '',
      shared_terms: shared.sort().slice(0, 6),
      overlap: shared.length,
      overlap_level: shared.length >= 3 ? 'high' : 'medium',
    })
  })
  out.sort((a, b) => b.overlap - a.overlap)
  return out.slice(0, limit)
}
function enrich(req) { const project = store.projects.find((p) => p.id === req.project_id); const proposer = store.users.find((u) => u.id === req.proposer_id); const ep = enrichProject(project); return { ...req, project: ep, base_complete: ep.base_complete, base_message: ep.base_complete ? '基座信息完整' : `请先补充${ep.base_status_label.slice(1)}，再使用需求挖掘与辨伪。`, proposer_name: proposer ? proposer.name : (req.proposer_name_text || req.proposer_id), method_cards: methodCards(req), endorsements: baseEndorsements(req) } }
function visibleReqs(user) { const perms = rolePerms(user); if (perms.includes('requirements.review') || perms.includes('requirements.analyze')) return store.requirements; return store.requirements.filter((r) => r.proposer_id === user.id) }
function checkLogin(request) { const u = currentUser(request); return u || fail(1001, '未登录或会话已过期', 401) }
function autoAnalyze(item) { const ev = item.evidence || []; const support = ev.filter((e) => e.supports === 'support').length; const contradict = ev.filter((e) => e.supports === 'contradict').length; let authenticity = 'pending'; if (contradict && !support) authenticity = 'contradicted'; else if (support && item.scenario && item.problem) authenticity = 'supported'; const scores = [item.scope_score || 0, item.intensity_score || 0, item.value_score || 0, item.cost_score || 0]; const has = scores.some(Boolean); let priority = 'unassessed'; let priority_reason = '证据或场景不足，先补材料，不自动判定优先级。'; if (authenticity === 'contradicted') { priority = 'low'; priority_reason = '存在反证，当前不建议投入开发资源。' } else if (authenticity === 'supported' && has) { const total = scores[0] + scores[1] + scores[2] - scores[3]; priority = total >= 9 ? 'high' : total >= 5 ? 'medium' : 'low'; priority_reason = `净分 ${total}，建议优先级为 ${priority}。` } return { authenticity, business_relevance: item.business_relevance || 'unknown', depth: Math.min(5, [item.scenario, item.problem, item.impact].filter(Boolean).length + (ev.length ? 1 : 0) + ((item.solutions || []).length >= 2 ? 1 : 0)), priority, priority_reason } }

export const handlers = [
  http.get('/api/healthz', () => ok({ service: '需求智能工作台 v2', status: 'ok' })),
  http.post('/api/auth/login', async ({ request }) => { const { username, password } = await request.json(); const u = store.users.find((x) => x.username === username); if (!u || u.password !== password) return fail(1002, '账号或密码错误', 401); if (u.status === 'disabled') return fail(1003, '账号已禁用', 403); const sid = `mock-${u.id}-${uid('sess')}`; activeSessionId = sid; store.sessions.push({ id: sid, user_id: u.id, expires: now() + 7 * 86400 }); return new HttpResponse(JSON.stringify({ code: 0, data: { token: sid, user: pubUser(u) }, message: 'ok' }), { status: 200, headers: { 'Content-Type': 'application/json', 'Set-Cookie': `workbench_session=${sid}; HttpOnly; Path=/; Max-Age=604800; SameSite=Lax` } }) }),
  http.post('/api/auth/logout', ({ request }) => { const sid = getCookie(request, 'workbench_session'); if (sid) store.sessions = store.sessions.filter((s) => s.id !== sid); activeSessionId = ''; return new HttpResponse(JSON.stringify({ code: 0, data: {}, message: 'ok' }), { status: 200, headers: { 'Content-Type': 'application/json', 'Set-Cookie': 'workbench_session=; HttpOnly; Path=/; Max-Age=0' } }) }),
  http.get('/api/auth/me', ({ request }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; const perms = rolePerms(u); return ok({ user: pubUser(u), permissions: perms, menus: menusOf(perms) }) }),
  http.post('/api/auth/change-password', async ({ request }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; const b = await request.json(); if (u.password !== b.old_password) return fail(1002, '原密码错误', 401); if (!b.new_password || b.new_password.length < 8 || !/[a-zA-Z]/.test(b.new_password) || !/\d/.test(b.new_password)) return fail(3001, '新密码至少 8 位且需包含字母和数字', 422); if (b.new_password === b.old_password) return fail(3001, '新密码不能与原密码相同', 422); u.password = b.new_password; u.must_change_password = false; return ok({ id: u.id }) }),

  http.get('/api/users', ({ request }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; if (!rolePerms(u).includes('users.view')) return fail(1003, '无权限', 403); return ok({ items: store.users.map(pubUser), roles: roleItems(), total: store.users.length }) }),
  http.post('/api/users', async ({ request }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; if (!rolePerms(u).includes('users.manage')) return fail(1003, '无权限', 403); const b = await request.json(); if (store.users.some((x) => x.username === b.username)) return fail(2002, '账号已存在', 409); const initialPassword = b.password || `Wb!${uid('pw')}`; const item = { id: uid('user'), username: b.username, name: b.name, department_id: b.department_id || '', role_ids: b.role_ids || ['pm'], status: b.status || 'active', password: initialPassword, must_change_password: true, created_at: now(), updated_at: now() }; store.users.push(item); const data = pubUser(item); if (!b.password) data.initial_password = initialPassword; return ok(data) }),
  http.put('/api/users/:id', async ({ request, params }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; if (!rolePerms(u).includes('users.manage')) return fail(1003, '无权限', 403); const item = store.users.find((x) => x.id === params.id); if (!item) return fail(2001, '账号不存在', 404); const b = await request.json(); if (b.username && store.users.some((x) => x.username === b.username && x.id !== params.id)) return fail(2002, '账号已存在', 409); Object.assign(item, b, { updated_at: now() }); if (!b.password) item.password = item.password || 'Workbench2026!'; return ok(pubUser(item)) }),
  http.delete('/api/users/:id', ({ request, params }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; if (!rolePerms(u).includes('users.manage')) return fail(1003, '无权限', 403); if (u.id === params.id) return fail(3001, '不能删除当前登录账号', 422); store.users = store.users.filter((x) => x.id !== params.id); return ok({ id: params.id }) }),
  http.get('/api/public/projects/:id/form', ({ params }) => { const project = store.projects.find((p) => p.id === params.id); if (!project) return fail(2001, '项目不存在', 404); const ep = enrichProject(project); return ok({ project: { id: ep.id, name: ep.name, base_complete: ep.base_complete, base_status_label: ep.base_status_label, base_message: ep.base_complete ? '基座信息完整' : `请先补充${ep.base_status_label.slice(1)}，再使用需求挖掘与辨伪。`, company_business: ep.company_business, project_background: ep.project_background, progress: ep.progress } }) }),
  http.post('/api/public/projects/:id/requirements', async ({ request, params }) => { const b = await request.json(); const project = store.projects.find((p) => p.id === params.id); if (!project) return fail(2001, '项目不存在', 404); if (baseMissing(project).length) return fail(3001, '请先补充公司业务、项目背景、项目进度，再使用需求挖掘与辨伪。', 422); const item = { id: uid('req'), project_id: params.id, proposer_id: 'public', proposer_name_text: b.submitter_name || '公开表单提交人', submitter_department: b.submitter_department || '', source: 'public_form', title: b.title, original: b.original, scenario: b.scenario || '待补充场景。', problem: b.problem || '待从用户原话中还原真实问题。', impact: b.impact || '待补充影响范围、发生频率、时间损失或风险后果。', authenticity: 'pending', business_relevance: 'unknown', priority: 'unassessed', depth: 0, scope_score: 0, intensity_score: 0, value_score: 0, cost_score: 0, priority_reason: '公开表单只记录原话，需 PM 补证据后再判断优先级。', status: 'draft', clarifications: [], evidence: [], solutions: [], analysis_history: [], deep_dive_suggestions: [], created_at: now(), updated_at: now(), updated_by: 'public_form' }; store.requirements.push(item); return ok({ id: item.id, status: item.status, message: '需求已提交，PM 会继续挖掘和评审。' }) }),
  http.get('/api/dashboard', ({ request }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; const reqs = visibleReqs(u); const byStatus = {}, byAuth = {}, byPri = {}; reqs.forEach((r) => { byStatus[STATUS_LABELS[r.status] || r.status] = (byStatus[STATUS_LABELS[r.status] || r.status] || 0) + 1; byAuth[r.authenticity] = (byAuth[r.authenticity] || 0) + 1; byPri[r.priority] = (byPri[r.priority] || 0) + 1 }); const complete = store.projects.filter((p) => !baseMissing(p).length).length; return ok({ total_requirements: reqs.length, by_status: byStatus, by_authenticity: byAuth, by_priority: byPri, total_projects: store.projects.length, base_complete_projects: complete, base_incomplete_projects: store.projects.length - complete }) }),
  http.get('/api/projects', ({ request }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; const counts = {}; store.requirements.forEach((r) => { counts[r.project_id] = (counts[r.project_id] || 0) + 1 }); const items = store.projects.map((p) => ({ ...enrichProject(p), requirement_count: counts[p.id] || 0 })); return ok({ items, total: items.length }) }),
  http.post('/api/projects', async ({ request }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; if (!rolePerms(u).includes('projects.manage')) return fail(1003, '无权限', 403); const b = await request.json(); if (!b.name?.trim()) return fail(3001, '项目名称不能为空', 422); const item = { id: uid('proj'), ...b, created_at: now(), updated_at: now(), updated_by: u.id }; store.projects.push(item); return ok(enrichProject(item)) }),
  http.put('/api/projects/:id', async ({ request, params }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; if (!rolePerms(u).includes('projects.manage')) return fail(1003, '无权限', 403); const item = store.projects.find((p) => p.id === params.id); if (!item) return fail(2001, '项目不存在', 404); Object.assign(item, await request.json(), { updated_at: now(), updated_by: u.id }); return ok(enrichProject(item)) }),
  http.get('/api/requirements', ({ request }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; const items = visibleReqs(u).map(enrich); return ok({ items, total: items.length }) }),
  http.post('/api/requirements', async ({ request }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; if (!rolePerms(u).includes('requirements.create')) return fail(1003, '无权限', 403); const b = await request.json(); const project = store.projects.find((p) => p.id === b.project_id); if (!project) return fail(2001, '项目不存在', 404); const missing = baseMissing(project); if (missing.length) return fail(3001, '请先补充公司业务、项目背景、项目进度，再使用需求挖掘与辨伪。', 422); const item = { id: uid('req'), project_id: b.project_id, proposer_id: u.id, title: b.title, original: b.original, scenario: b.scenario || '待补充场景。', problem: b.problem || '待从用户原话中还原真实问题。', impact: b.impact || '待补充影响范围、发生频率、时间损失或风险后果。', authenticity: 'pending', business_relevance: 'unknown', priority: 'unassessed', depth: 0, scope_score: 0, intensity_score: 0, value_score: 0, cost_score: 0, priority_reason: '证据不足，暂不生成综合优先级。', status: 'draft', clarifications: [], evidence: [], solutions: [{ name: '维持现状', benefit: '无开发成本', cost: '问题继续存在', risk: '隐性人力损耗扩大' }, { name: '流程调整', benefit: '低成本先验证', cost: '需要业务配合', risk: '无法解决系统性瓶颈' }, { name: '产品改造', benefit: '沉淀为长期能力', cost: '需要技术投入', risk: '证据不足时容易做偏' }], analysis_history: [], deep_dive_suggestions: [], created_at: now(), updated_at: now(), updated_by: u.id }; store.requirements.push(item); return ok(enrich(item)) }),
  http.get('/api/requirements/:id', ({ request, params }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; const item = store.requirements.find((r) => r.id === params.id); if (!item) return fail(2001, '需求不存在', 404); const perms = rolePerms(u); if (!(perms.includes('requirements.review') || perms.includes('requirements.analyze') || item.proposer_id === u.id)) return fail(1003, '无权限', 403); const e = enrich(item); e.timeline = [{ at: item.created_at, type: '提交', text: `${e.proposer_name} 提交了需求` }, ...(item.clarifications || []).map((c) => ({ at: c.created_at, type: '追问', text: c.question })), ...(item.evidence || []).map((c) => ({ at: c.created_at, type: '证据', text: c.title })), ...(item.analysis_history || []).map((h) => ({ at: h.at, type: '分析', text: h.summary })), { at: item.updated_at, type: '状态', text: `当前状态：${STATUS_LABELS[item.status] || item.status}` }]; return ok(e) }),
  http.patch('/api/requirements/:id', async ({ request, params }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; const perms = rolePerms(u); if (!(perms.includes('requirements.review') || perms.includes('requirements.analyze'))) return fail(1003, '无权限', 403); const item = store.requirements.find((r) => r.id === params.id); if (!item) return fail(2001, '需求不存在', 404); Object.assign(item, await request.json(), { updated_at: now(), updated_by: u.id }); return ok(enrich(item)) }),
  http.post('/api/requirements/:id/clarifications', async ({ request, params }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; const item = store.requirements.find((r) => r.id === params.id); if (!item) return fail(2001, '需求不存在', 404); const b = await request.json(); item.clarifications.push({ id: uid('cl'), question: b.question, answer: b.answer || '待补充', asked_by: u.id, answered_by: b.answer ? u.id : '', created_at: now() }); item.updated_at = now(); return ok(enrich(item)) }),
  http.post('/api/requirements/:id/evidence', async ({ request, params }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; const item = store.requirements.find((r) => r.id === params.id); if (!item) return fail(2001, '需求不存在', 404); const b = await request.json(); item.evidence.push({ id: uid('ev'), title: b.title, content: b.content, kind: b.kind || '未填', source: b.source || '未填', supports: b.supports || 'support', created_at: now(), created_by: u.id }); item.updated_at = now(); return ok(enrich(item)) }),
  http.post('/api/requirements/:id/analyze', ({ request, params }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; if (!rolePerms(u).includes('requirements.analyze')) return fail(1003, '无权限', 403); const item = store.requirements.find((r) => r.id === params.id); if (!item) return fail(2001, '需求不存在', 404); const project = store.projects.find((p) => p.id === item.project_id); if (baseMissing(project).length) return fail(3001, '请先补充公司业务、项目背景、项目进度，再使用需求挖掘与辨伪。', 422); const res = autoAnalyze(item); Object.assign(item, res); item.deep_dive_suggestions = [{ type: '验证', text: '继续补充工单、截图、数据或访谈摘录，避免把用户原话直接当事实。' }]; item.analysis_history.push({ at: now(), summary: `方法论检查：真实性=${res.authenticity}，业务相关性=${res.business_relevance}，挖掘深度=${res.depth}/5，优先级=${res.priority}。AI 仅作辅助建议。` }); item.updated_at = now(); const e = enrich(item); e.analysis = res; return ok(e) }),
  http.post('/api/requirements/:id/deep-dive', ({ request, params }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; const item = store.requirements.find((r) => r.id === params.id); if (!item) return fail(2001, '需求不存在', 404); item.deep_dive_suggestions = [{ type: '追问', text: '请补充最近一次真实发生场景：谁、何时、在哪个业务环节、要完成什么任务。' }, { type: '证据', text: '请补充发生频率、影响人数、单次耗时或错误率。' }]; item.updated_at = now(); return ok(enrich(item)) }),
  http.get('/api/requirements/:id/export.md', ({ request, params }) => { const u = checkLogin(request); if (u instanceof HttpResponse) return u; const item = store.requirements.find((r) => r.id === params.id); if (!item) return fail(2001, '需求不存在', 404); const project = store.projects.find((p) => p.id === item.project_id); return HttpResponse.text(`# ${item.title}_需求卡_PRD草案\n\n## 基座信息\n\n- 公司业务：${project?.company_business || '待补充'}\n- 项目背景：${project?.project_background || '待补充'}\n- 项目进度：${project?.progress || '待补充'}\n\n## 用户原话\n\n${item.original}\n\n## 真实问题\n\n${item.problem}\n`, { headers: { 'Content-Type': 'text/markdown; charset=utf-8' } }) }),
]
