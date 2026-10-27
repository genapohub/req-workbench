<template>
  <div>
    <PageHeader
      title="需求挖掘"
      description="把用户原话还原成真实场景，用证据判断是不是值得做的真需求。"
    >
      <template #actions>
        <el-radio-group v-model="view" size="small">
          <el-radio-button value="board">看板</el-radio-button>
          <el-radio-button value="pool">需求池</el-radio-button>
          <el-radio-button value="list">列表</el-radio-button>
        </el-radio-group>
        <el-button type="primary" :icon="Plus" :disabled="!canCreate" @click="openCreate">
          提交原话
        </el-button>
      </template>
    </PageHeader>

    <el-alert
      v-if="baseWarning"
      class="wb-page-alert"
      type="warning"
      :closable="false"
      show-icon
      :title="baseWarning"
    />

    <PanelCard flush>
      <!-- 表格工具条：搜索 + 筛选 + 密度 + 列设置（主流后台标配） -->
      <div class="wb-table-toolbar">
        <el-input
          v-model="keyword"
          clearable
          :prefix-icon="Search"
          placeholder="搜索标题 / 原话"
          style="width: 220px"
        />
        <el-select v-model="filterProject" clearable placeholder="全部项目" style="width: 150px">
          <el-option v-for="p in projects" :key="p.id" :value="p.id" :label="p.name" />
        </el-select>
        <el-select v-model="filterAuth" clearable placeholder="真实性" style="width: 118px">
          <el-option
            v-for="o in AUTHENTICITY_OPTIONS"
            :key="o.value"
            :value="o.value"
            :label="o.label"
          />
        </el-select>
        <el-select v-model="filterPrio" clearable placeholder="优先级" style="width: 110px">
          <el-option
            v-for="o in PRIORITY_OPTIONS"
            :key="o.value"
            :value="o.value"
            :label="o.label"
          />
        </el-select>
        <!-- 看板视图下状态由列承载，再给状态筛选会语义冲突 -->
        <el-select
          v-if="view !== 'board'"
          v-model="filterStatus"
          clearable
          placeholder="状态"
          style="width: 118px"
        >
          <el-option v-for="o in STATUS_OPTIONS" :key="o.value" :value="o.value" :label="o.label" />
        </el-select>
        <el-button v-if="activeFilterCount" text @click="resetFilters">
          重置（{{ activeFilterCount }}）
        </el-button>

        <span class="wb-table-toolbar__spacer" />
        <span class="wb-table-toolbar__count">共 {{ viewCount }} 条</span>

        <!-- 列设置：仅表格视图有意义 -->
        <el-popover v-if="view !== 'board'" placement="bottom-end" width="190" trigger="click">
          <template #reference>
            <el-button text :icon="Setting">列设置</el-button>
          </template>
          <el-checkbox-group v-model="visibleCols" @change="tableKey++">
            <div v-for="c in COLUMNS" :key="c.key" class="wb-col-item">
              <el-checkbox :value="c.key" :label="c.label" />
            </div>
          </el-checkbox-group>
        </el-popover>

        <!-- 密度 -->
        <el-dropdown v-if="view !== 'board'" trigger="click" @command="setDensity">
          <el-button text :icon="Operation">{{ DENSITY_TEXT[density] }}</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="large">宽松</el-dropdown-item>
              <el-dropdown-item command="default">标准</el-dropdown-item>
              <el-dropdown-item command="small">紧凑</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>

      <!-- 看板视图：按状态分列的卡片墙（对齐 Jira Board / 飞书看板视图） -->
      <div v-if="view === 'board'" class="wb-board">
        <section v-for="col in boardColumns" :key="col.key" class="wb-board__col">
          <header class="wb-board__col-head">
            <StatusTag :label="col.label" :tone="col.tone" dot size="md" />
            <span class="wb-board__count wb-num">{{ col.items.length }}</span>
          </header>

          <div class="wb-board__list">
            <article
              v-for="r in col.items"
              :key="r.id"
              class="wb-board-card"
              @click="openDetail(r)"
            >
              <h4 class="wb-board-card__title">{{ r.title }}</h4>
              <p class="wb-board-card__original">{{ r.original }}</p>

              <div class="wb-board-card__meta">
                <span class="wb-muted">{{ r.project?.name || '-' }}</span>
                <span class="wb-num">深度 {{ r.depth || 0 }}/5</span>
              </div>

              <div class="wb-board-card__tags">
                <StatusTag
                  :label="labelOf(AUTHENTICITY, r.authenticity)"
                  :tone="toneOf(AUTHENTICITY, r.authenticity)"
                />
                <StatusTag
                  :label="labelOf(PRIORITY, r.priority)"
                  :tone="toneOf(PRIORITY, r.priority)"
                />
              </div>
            </article>

            <p v-if="!col.items.length" class="wb-board__empty">暂无</p>
          </div>
        </section>
      </div>

      <DataTable
        v-else
        :key="tableKey"
        :data="tableRows"
        :loading="loading"
        :size="density"
        clickable
        empty-text="需求池还是空的——先提交一条真实原话"
        @row-click="openDetail"
      >
        <template #empty-action>
          <el-button type="primary" :disabled="!canCreate" @click="openCreate">提交原话</el-button>
        </template>

        <el-table-column v-if="visible('title')" label="需求原话" min-width="260">
          <template #default="{ row }">
            <b class="req-title">{{ row.title }}</b>
            <div class="wb-muted one-line">{{ row.original }}</div>
          </template>
        </el-table-column>

        <el-table-column v-if="visible('project')" label="项目" width="150">
          <template #default="{ row }">{{ row.project?.name || '-' }}</template>
        </el-table-column>

        <el-table-column v-if="visible('authenticity')" label="问题真实性" width="118">
          <template #default="{ row }">
            <StatusTag
              :label="labelOf(AUTHENTICITY, row.authenticity)"
              :tone="toneOf(AUTHENTICITY, row.authenticity)"
            />
          </template>
        </el-table-column>

        <el-table-column v-if="visible('relevance')" label="业务相关性" width="118">
          <template #default="{ row }">
            <StatusTag
              :label="labelOf(RELEVANCE, row.business_relevance)"
              :tone="toneOf(RELEVANCE, row.business_relevance)"
            />
          </template>
        </el-table-column>

        <el-table-column v-if="visible('depth')" label="挖掘深度" width="120">
          <template #default="{ row }">
            <div class="depth-cell">
              <el-progress
                :percentage="Math.min(100, (row.depth || 0) * 20)"
                :stroke-width="6"
                :show-text="false"
              />
              <span class="depth-num wb-num">{{ row.depth || 0 }}/5</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column v-if="visible('priority')" label="优先级" width="96">
          <template #default="{ row }">
            <StatusTag
              :label="labelOf(PRIORITY, row.priority)"
              :tone="toneOf(PRIORITY, row.priority)"
            />
          </template>
        </el-table-column>

        <el-table-column v-if="visible('status')" label="状态" width="104">
          <template #default="{ row }">
            <StatusTag :label="labelOf(STATUS, row.status)" :tone="toneOf(STATUS, row.status)" />
          </template>
        </el-table-column>
      </DataTable>
    </PanelCard>

    <!-- 需求详情抽屉 -->
    <el-drawer
      v-model="drawer"
      :title="detail?.title || '需求详情'"
      size="560px"
      @closed="detail = null"
    >
      <template v-if="detail">
        <el-alert
          v-if="!detail.base_complete"
          class="wb-drawer-alert"
          type="warning"
          :closable="false"
          :title="detail.base_message"
        />

        <!-- 0. 使用流程引导：挖掘 → 分析 → 辨伪（默认展开，可折叠） -->
        <el-collapse v-model="usagePanels" class="wb-usage">
          <el-collapse-item name="usage">
            <template #title>
              <span class="wb-usage__title">这条需求怎么用？挖掘 → 分析 → 辨伪</span>
            </template>
            <ol class="wb-usage__steps">
              <li v-for="(s, i) in FLOW_STEPS" :key="i">
                <b>{{ s.title }}</b>：{{ s.text }}
              </li>
            </ol>
            <p class="wb-usage__glossary">
              术语速查：<template v-for="(g, i) in FLOW_GLOSSARY" :key="g.term"><b>{{ g.term }}</b>＝{{ g.desc }}<template v-if="i < FLOW_GLOSSARY.length - 1">；</template></template>
            </p>
          </el-collapse-item>
        </el-collapse>

        <!-- 0.5 修改 / 补充入口：编辑需求正文、补证据、补追问（后端 PATCH / evidence / clarifications 已就绪，此前仅缺 UI 入口） -->
        <div class="action-row">
          <el-button :icon="Edit" @click="openEdit">编辑需求</el-button>
          <el-button :icon="Document" @click="openEvidence">补充证据</el-button>
          <el-button :icon="QuestionFilled" @click="openClarification">补充追问</el-button>
        </div>

        <!-- 1. 判断总览：先给结论，再给依据（设计方向 §3） -->
        <SectionTitle text="判断总览" />
        <div class="judge-grid">
          <div class="judge-cell">
            <span class="judge-cell__label">问题真实性</span>
            <StatusTag
              :label="labelOf(AUTHENTICITY, detail.authenticity)"
              :tone="toneOf(AUTHENTICITY, detail.authenticity)"
              size="md"
            />
          </div>
          <div class="judge-cell">
            <span class="judge-cell__label">业务相关性</span>
            <StatusTag
              :label="labelOf(RELEVANCE, detail.business_relevance)"
              :tone="toneOf(RELEVANCE, detail.business_relevance)"
              size="md"
            />
          </div>
          <div class="judge-cell">
            <span class="judge-cell__label">投入优先级</span>
            <StatusTag
              :label="labelOf(PRIORITY, detail.priority)"
              :tone="toneOf(PRIORITY, detail.priority)"
              size="md"
            />
          </div>
          <div class="judge-cell">
            <span class="judge-cell__label">挖掘深度</span>
            <span class="judge-cell__value wb-num">{{ detail.depth || 0 }}/5</span>
          </div>
        </div>

        <!-- 2. 基座引用：先给判断所依赖的事实基座 -->
        <SectionTitle text="基座引用" />
        <dl class="field-list">
          <div class="field-row"><dt>公司业务</dt><dd>{{ detail.project?.company_business || '待补充' }}</dd></div>
          <div class="field-row"><dt>项目背景</dt><dd>{{ detail.project?.project_background || '待补充' }}</dd></div>
          <div class="field-row"><dt>项目进度</dt><dd>{{ detail.project?.progress || '待补充' }}</dd></div>
        </dl>

        <!-- 2.5 基座背书：同项目已确认（已入池）的历史需求作为判断依据 -->
        <SectionTitle text="基座背书" />
        <div v-if="detail.endorsements?.length" class="endorse-list">
          <div v-for="e in detail.endorsements" :key="e.id" class="endorse">
            <div class="endorse__head">
              <b class="endorse__title">{{ e.title }}</b>
              <StatusTag :label="labelOf(STATUS, e.status)" :tone="toneOf(STATUS, e.status)" size="sm" />
              <StatusTag v-if="e.source === 'ai'" label="AI 建议" tone="info" size="sm" />
              <StatusTag v-else-if="e.overlap_level === 'high'" label="疑似同类" tone="warning" size="sm" />
            </div>
            <p class="endorse__problem">{{ e.problem }}</p>
            <p v-if="e.source === 'ai'" class="endorse__reason">
              AI 语义匹配（非词面重合）：{{ e.ai_reason || '语义上指向同类业务问题' }}——仅供 PM 参考，不构成判断结论。
            </p>
            <p v-else class="endorse__reason">
              本项目已确认投入，与本次需求重合 {{ e.overlap }} 个业务词：<span class="wb-num">{{ (e.shared_terms || []).join('、') }}</span>
            </p>
          </div>
        </div>
        <p v-else class="wb-drawer-empty">本项目暂无已入池需求可作为背书，先积累首批已确认需求。</p>

        <!-- 3. 真实场景还原 -->
        <SectionTitle text="真实场景还原" />
        <dl class="field-list">
          <div class="field-row"><dt>用户原话</dt><dd>{{ detail.original }}</dd></div>
          <div class="field-row"><dt>发生场景</dt><dd>{{ detail.scenario || '待补充' }}</dd></div>
          <div class="field-row"><dt>还原问题</dt><dd>{{ detail.problem || '待补充' }}</dd></div>
          <div class="field-row"><dt>影响说明</dt><dd>{{ detail.impact || '待补充' }}</dd></div>
        </dl>

        <!-- 4. 证据与疑点：先呈现事实（证据链），再给方法论判定 -->
        <SectionTitle text="证据与疑点" />
        <div v-if="detail.evidence?.length" class="evidence-list">
          <div v-for="e in detail.evidence" :key="e.id" class="evidence">
            <StatusTag
              :label="e.supports === 'contradict' ? '反证' : '支撑'"
              :tone="e.supports === 'contradict' ? 'danger' : 'success'"
            />
            <span class="evidence__text"><b>{{ e.title }}</b>：{{ e.content }}</span>
          </div>
        </div>
        <p v-else class="wb-drawer-empty">暂无证据，建议先补充工单、截图、数据或访谈摘录。</p>

        <!-- 5. 方法论检查（PRD 9.2）：基于上方事实给出完整性判定 -->
        <SectionTitle text="方法论检查">
          <template #extra>
            <el-button size="small" :icon="MagicStick" @click="analyze">运行方法论检查</el-button>
          </template>
        </SectionTitle>
        <div class="method-list">
          <MethodCheckCard
            v-for="m in detail.method_cards"
            :key="m.name"
            :name="m.name"
            :text="m.text"
            :status="m.status"
          />
        </div>

        <!-- 6. 深挖建议（PRD 4.3 独立区块）：下一步追问与验证动作 -->
        <SectionTitle text="深挖建议">
          <template #extra>
            <el-button size="small" :icon="Promotion" @click="deepDive">生成追问建议</el-button>
          </template>
        </SectionTitle>
        <div v-if="detail.deep_dive_suggestions?.length || detail.ai_suggestions?.length" class="suggestion-list">
          <div v-for="(s, i) in detail.deep_dive_suggestions || []" :key="'r' + i" class="suggestion">
            {{ s.text }}
          </div>
          <div v-for="(s, i) in detail.ai_suggestions || []" :key="'a' + i" class="suggestion suggestion--ai">
            <StatusTag label="AI 建议" tone="info" size="sm" /> {{ s.text }}
          </div>
        </div>
        <p v-else class="wb-drawer-empty">暂无建议，点击右上角「生成追问建议」。</p>

        <!-- 6. 评审判断：结论仍由人确认（PRD 9.2） -->
        <SectionTitle text="评审判断" />
        <el-form label-width="88px" class="review-form">
          <el-form-item label="状态">
            <el-select
              v-model="detail.status"
              size="small"
              @change="patch({ status: detail.status })"
            >
              <el-option v-for="o in STATUS_OPTIONS" :key="o.value" :value="o.value" :label="o.label" />
            </el-select>
          </el-form-item>
          <el-form-item label="真实性">
            <el-select
              v-model="detail.authenticity"
              size="small"
              @change="patch({ authenticity: detail.authenticity })"
            >
              <el-option
                v-for="o in AUTHENTICITY_OPTIONS"
                :key="o.value"
                :value="o.value"
                :label="o.label"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="优先级">
            <el-select
              v-model="detail.priority"
              size="small"
              @change="patch({ priority: detail.priority })"
            >
              <el-option v-for="o in PRIORITY_OPTIONS" :key="o.value" :value="o.value" :label="o.label" />
            </el-select>
          </el-form-item>
        </el-form>

        <el-alert
          v-if="detail.priority_reason"
          class="wb-drawer-alert"
          :title="detail.priority_reason"
          type="info"
          :closable="false"
        />

        <!-- 7. 时间线 -->
        <SectionTitle text="时间线" />
        <el-timeline>
          <el-timeline-item
            v-for="(t, i) in detail.timeline"
            :key="i"
            :timestamp="fmt(t.at)"
          >
            {{ t.type }}：{{ t.text }}
          </el-timeline-item>
        </el-timeline>

      </template>

      <!-- 抽屉底栏：主操作固定可见，不随正文滚动（主流后台惯例） -->
      <template #footer>
        <div class="wb-drawer-footer">
          <el-button @click="drawer = false">关闭</el-button>
          <el-button type="primary" :icon="Download" @click="exportMd">
            导出需求卡 Markdown
          </el-button>
        </div>
      </template>
    </el-drawer>

    <!-- 提交原话 -->
    <FormDialog
      v-model="createVisible"
      title="提交原话"
      width="600px"
      confirm-text="提交"
      :disabled="!selectedProject?.base_complete"
      @confirm="create"
    >
      <el-alert
        v-if="selectedProject && !selectedProject.base_complete"
        class="wb-dialog-alert"
        type="warning"
        :closable="false"
        :title="selectedProject.base_status_label + '，请先去基座信息页补齐。'"
      />
      <el-form label-width="88px">
        <el-form-item label="所属项目">
          <el-select v-model="form.project_id" style="width: 100%">
            <el-option
              v-for="p in projects"
              :key="p.id"
              :value="p.id"
              :label="p.name + (p.base_complete ? '' : '（基座不完整）')"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="标题">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="用户原话">
          <el-input v-model="form.original" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="场景">
          <el-input
            v-model="form.scenario"
            type="textarea"
            :rows="2"
            placeholder="上次真实发生在什么时候？谁在什么情况下要完成什么？"
          />
        </el-form-item>
        <el-form-item label="真实问题">
          <el-input
            v-model="form.problem"
            type="textarea"
            :rows="2"
            placeholder="当前怎么处理？卡在哪里？"
          />
        </el-form-item>
        <el-form-item label="影响">
          <el-input
            v-model="form.impact"
            type="textarea"
            :rows="2"
            placeholder="影响多少人、多久一次、损失多少时间或带来什么风险？"
          />
        </el-form-item>
      </el-form>
    </FormDialog>

    <!-- 编辑需求：修改标题 / 原话 / 场景 / 问题 / 影响（后端 PATCH 现已支持这些字段） -->
    <FormDialog
      v-model="editVisible"
      title="编辑需求"
      width="600px"
      confirm-text="保存"
      :loading="saving"
      :disabled="!editForm.title.trim() || !editForm.original.trim()"
      @confirm="saveEdit"
    >
      <el-form label-width="88px">
        <el-form-item label="标题">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="用户原话">
          <el-input v-model="editForm.original" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="场景">
          <el-input
            v-model="editForm.scenario"
            type="textarea"
            :rows="2"
            placeholder="上次真实发生在什么时候？谁在什么情况下要完成什么？"
          />
        </el-form-item>
        <el-form-item label="真实问题">
          <el-input
            v-model="editForm.problem"
            type="textarea"
            :rows="2"
            placeholder="当前怎么处理？卡在哪里？"
          />
        </el-form-item>
        <el-form-item label="影响">
          <el-input
            v-model="editForm.impact"
            type="textarea"
            :rows="2"
            placeholder="影响多少人、多久一次、损失多少时间或带来什么风险？"
          />
        </el-form-item>
      </el-form>
    </FormDialog>

    <!-- 补充证据：截图 / 数据 / 工单 / 访谈摘录，标注支撑或反证 -->
    <FormDialog
      v-model="evidenceVisible"
      title="补充证据"
      width="560px"
      confirm-text="提交证据"
      :loading="saving"
      :disabled="!evidenceForm.title.trim() || !evidenceForm.content.trim()"
      @confirm="addEvidence"
    >
      <el-form label-width="88px">
        <el-form-item label="证据名称">
          <el-input v-model="evidenceForm.title" placeholder="如：近一月审批时长统计" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="evidenceForm.content"
            type="textarea"
            :rows="3"
            placeholder="具体数据或事实描述"
          />
        </el-form-item>
        <el-form-item label="类型">
          <el-input v-model="evidenceForm.kind" placeholder="数据 / 截图 / 工单 / 访谈 / 制度（选填）" />
        </el-form-item>
        <el-form-item label="来源">
          <el-input v-model="evidenceForm.source" placeholder="如：OA / 企业微信 / 质检（选填）" />
        </el-form-item>
        <el-form-item label="立场">
          <el-radio-group v-model="evidenceForm.supports">
            <el-radio-button value="support">支撑需求</el-radio-button>
            <el-radio-button value="contradict">反证</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
    </FormDialog>

    <!-- 补充追问：记录 5 Whys 追问与初步回答 -->
    <FormDialog
      v-model="clarificationVisible"
      title="补充追问"
      width="560px"
      confirm-text="提交追问"
      :loading="saving"
      :disabled="!clarificationForm.question.trim()"
      @confirm="addClarification"
    >
      <el-form label-width="88px">
        <el-form-item label="追问问题">
          <el-input
            v-model="clarificationForm.question"
            type="textarea"
            :rows="2"
            placeholder="为什么需要这个功能？背后真正的任务是什么？"
          />
        </el-form-item>
        <el-form-item label="初步回答">
          <el-input
            v-model="clarificationForm.answer"
            type="textarea"
            :rows="2"
            placeholder="用户或 PM 的初步回答（选填，可后续补全）"
          />
        </el-form-item>
      </el-form>
    </FormDialog>
  </div>
</template>

<script setup>
// 需求挖掘：改造前状态标签的 label/type 映射在本页与 Dashboard 各写一份，
// 抽屉内的 method-grid / judge-grid 为内联私有样式。现已全部组件化 + 枚举统一。
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Plus,
  MagicStick,
  Promotion,
  Search,
  Setting,
  Operation,
  Download,
  Edit,
  Document,
  QuestionFilled,
} from '@element-plus/icons-vue'
import PageHeader from '../components/PageHeader.vue'
import PanelCard from '../components/PanelCard.vue'
import DataTable from '../components/DataTable.vue'
import FormDialog from '../components/FormDialog.vue'
import StatusTag from '../components/StatusTag.vue'
import MethodCheckCard from '../components/MethodCheckCard.vue'
import SectionTitle from '../components/SectionTitle.vue'
import { FLOW_STEPS, FLOW_GLOSSARY } from '../constants/methodology'
import {
  AUTHENTICITY,
  RELEVANCE,
  PRIORITY,
  STATUS,
  STATUS_OPTIONS,
  AUTHENTICITY_OPTIONS,
  PRIORITY_OPTIONS,
  labelOf,
  toneOf,
} from '../constants/enums'
import client from '../api/client'

const view = ref('board')
const keyword = ref('')
const filterProject = ref('')
const filterAuth = ref('')
const filterPrio = ref('')
const filterStatus = ref('')
const density = ref('default')
const tableKey = ref(0)
const items = ref([])
const loading = ref(false)
const projects = ref([])
const drawer = ref(false)
const detail = ref(null)
const createVisible = ref(false)
/** 使用流程引导面板：默认展开，PM 熟悉后可手动折叠 */
const usagePanels = ref(['usage'])
const form = ref({ project_id: '', title: '', original: '', scenario: '', problem: '', impact: '' })
/** 修改 / 补充入口状态：编辑需求正文、补证据、补追问 */
const editVisible = ref(false)
const evidenceVisible = ref(false)
const clarificationVisible = ref(false)
const saving = ref(false)
const editForm = ref({ title: '', original: '', scenario: '', problem: '', impact: '' })
const evidenceForm = ref({ title: '', content: '', kind: '', source: '', supports: 'support' })
const clarificationForm = ref({ question: '', answer: '' })

const route = useRoute()
const router = useRouter()

const selectedProject = computed(() => projects.value.find((p) => p.id === form.value.project_id))
const canCreate = computed(() => projects.value.some((p) => p.base_complete))

const baseWarning = computed(() => {
  if (!projects.value.length) return '还没有基座信息，请先补充公司业务、项目背景和项目进度。'
  const bad = projects.value.filter((p) => !p.base_complete)
  return bad.length ? `有 ${bad.length} 个项目基座不完整，缺项项目不能提交和分析需求。` : ''
})

/** 可显隐列：与 COLUMNS 顺序保持一致 */
const COLUMNS = [
  { key: 'title', label: '需求原话' },
  { key: 'project', label: '项目' },
  { key: 'authenticity', label: '问题真实性' },
  { key: 'relevance', label: '业务相关性' },
  { key: 'depth', label: '挖掘深度' },
  { key: 'priority', label: '优先级' },
  { key: 'status', label: '状态' },
]
const visibleCols = ref(COLUMNS.map((c) => c.key))
const visible = (key) => visibleCols.value.includes(key)

const DENSITY_TEXT = { large: '宽松', default: '标准', small: '紧凑' }
const setDensity = (cmd) => {
  density.value = cmd
}

/** 生效中的筛选项数量：用于「重置」按钮的显示与计数 */
const activeFilterCount = computed(
  () =>
    [
      keyword.value,
      filterProject.value,
      filterAuth.value,
      filterPrio.value,
      view.value === 'board' ? '' : filterStatus.value, // 看板下状态由列承载，不计入
    ].filter(Boolean).length,
)

function resetFilters() {
  keyword.value = ''
  filterProject.value = ''
  filterAuth.value = ''
  filterPrio.value = ''
  filterStatus.value = ''
}

/** 关键词 + 项目 / 真实性 / 优先级筛选（不含状态，不含视图过滤） */
const baseFiltered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  const status = view.value === 'board' ? '' : filterStatus.value
  return items.value.filter((r) => {
    if (filterProject.value && (r.project_id || r.project?.id) !== filterProject.value) return false
    if (filterAuth.value && r.authenticity !== filterAuth.value) return false
    if (filterPrio.value && r.priority !== filterPrio.value) return false
    if (status && r.status !== status) return false
    if (kw) {
      const hay = `${r.title || ''} ${r.original || ''} ${r.project?.name || ''}`.toLowerCase()
      if (!hay.includes(kw)) return false
    }
    return true
  })
})

/** backlog 语义：需求池按优先级排序（高 → 中 → 低 → 待评估），对齐 Jira backlog */
const PRIORITY_RANK = { high: 0, medium: 1, low: 2, unassessed: 3 }
const poolRows = computed(() =>
  [...baseFiltered.value]
    .filter((r) => r.status === 'pooled')
    .sort(
      (a, b) =>
        (PRIORITY_RANK[a.priority] ?? 9) - (PRIORITY_RANK[b.priority] ?? 9) ||
        (b.depth || 0) - (a.depth || 0), // 同优先级按挖掘深度降序：挖得深的排前面
    ),
)

/** 表格视图数据源：列表 = 全量；需求池 = 已入池且按优先级排序 */
const tableRows = computed(() => (view.value === 'pool' ? poolRows.value : baseFiltered.value))

/** 看板：按状态分列（列即工作流状态，对齐 Jira Board / 飞书看板视图） */
const boardColumns = computed(() =>
  Object.entries(STATUS).map(([key, meta]) => ({
    key,
    label: meta.label,
    tone: meta.tone,
    items: baseFiltered.value.filter((r) => r.status === key),
  })),
)

/** 当前视图下的条数（看板统计全部列） */
const viewCount = computed(() =>
  view.value === 'board' ? baseFiltered.value.length : tableRows.value.length,
)

const fmt = (ts) => (ts ? new Date(ts * 1000).toLocaleString('zh-CN') : '-')

async function load() {
  loading.value = true
  try {
    items.value = (await client.get('/api/requirements')).items
  } finally {
    loading.value = false
  }
}

async function loadProjects() {
  projects.value = (await client.get('/api/projects')).items
  const firstComplete = projects.value.find((p) => p.base_complete) || projects.value[0]
  if (firstComplete) form.value.project_id = firstComplete.id
}

onMounted(async () => {
  await loadProjects()
  await load()
  if (route.query.req) {
    try {
      detail.value = await client.get(`/api/requirements/${route.query.req}`)
      drawer.value = true
    } catch (e) {
      /* 忽略：需求可能已删除 */
    }
  }
  if (route.query.create === '1') openCreate()
})

watch(drawer, (open) => {
  if (!open) {
    const q = { ...route.query }
    delete q.req
    router.replace({ query: q })
  }
})

watch(createVisible, (open) => {
  if (!open && route.query.create === '1') {
    const q = { ...route.query }
    delete q.create
    router.replace({ query: q })
  }
})

async function openDetail(row) {
  detail.value = await client.get(`/api/requirements/${row.id}`)
  drawer.value = true
  router.replace({ query: { ...route.query, req: row.id } })
}

async function patch(payload) {
  try {
    detail.value = await client.patch(`/api/requirements/${detail.value.id}`, payload)
    await load()
    ElMessage.success('已更新')
  } catch (e) {
    /* 拦截器统一提示 */
  }
}

async function analyze() {
  try {
    const r = await client.post(`/api/requirements/${detail.value.id}/analyze`)
    detail.value = r
    await load()
    ElMessage.success('方法论检查完成')
  } catch (e) {
    /* 拦截器统一提示 */
  }
}

async function deepDive() {
  try {
    detail.value = await client.post(`/api/requirements/${detail.value.id}/deep-dive`)
    ElMessage.success('已生成追问建议')
  } catch (e) {
    /* 拦截器统一提示 */
  }
}

function exportMd() {
  window.open(`/api/requirements/${detail.value.id}/export.md`, '_blank')
}

function openCreate() {
  createVisible.value = true
  if (route.query.create !== '1') router.replace({ query: { ...route.query, create: '1' } })
}

async function create() {
  try {
    await client.post('/api/requirements', form.value)
    createVisible.value = false
    const q = { ...route.query }
    delete q.create
    router.replace({ query: q })
    ElMessage.success('需求已提交')
    await load()
  } catch (e) {
    /* 拦截器统一提示 */
  }
}

/** 修改 / 补充入口：编辑需求正文（PATCH title/original/scenario/problem/impact） */
function openEdit() {
  editForm.value = {
    title: detail.value.title || '',
    original: detail.value.original || '',
    scenario: detail.value.scenario || '',
    problem: detail.value.problem || '',
    impact: detail.value.impact || '',
  }
  editVisible.value = true
}

async function saveEdit() {
  try {
    saving.value = true
    detail.value = await client.patch(`/api/requirements/${detail.value.id}`, { ...editForm.value })
    await load()
    ElMessage.success('需求已更新')
    editVisible.value = false
  } catch (e) {
    /* 拦截器统一提示 */
  } finally {
    saving.value = false
  }
}

/** 补充证据（POST /{rid}/evidence） */
function openEvidence() {
  evidenceForm.value = { title: '', content: '', kind: '', source: '', supports: 'support' }
  evidenceVisible.value = true
}

async function addEvidence() {
  try {
    saving.value = true
    detail.value = await client.post(`/api/requirements/${detail.value.id}/evidence`, { ...evidenceForm.value })
    await load()
    ElMessage.success('已补充证据')
    evidenceVisible.value = false
  } catch (e) {
    /* 拦截器统一提示 */
  } finally {
    saving.value = false
  }
}

/** 补充追问（POST /{rid}/clarifications） */
function openClarification() {
  clarificationForm.value = { question: '', answer: '' }
  clarificationVisible.value = true
}

async function addClarification() {
  try {
    saving.value = true
    detail.value = await client.post(`/api/requirements/${detail.value.id}/clarifications`, { ...clarificationForm.value })
    await load()
    ElMessage.success('已补充追问')
    clarificationVisible.value = false
  } catch (e) {
    /* 拦截器统一提示 */
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.wb-page-alert { margin-bottom: var(--wb-sp-5); }
.wb-drawer-alert { margin: var(--wb-sp-3) 0; }
.wb-dialog-alert { margin-bottom: var(--wb-sp-4); }

/* ---------- 基座背书 ---------- */
.endorse-list {
  display: flex;
  flex-direction: column;
  gap: var(--wb-sp-2);
}

.endorse {
  background: var(--wb-surface-sub);
  border: 1px solid var(--wb-border);
  border-left: 3px solid var(--wb-green-600);
  border-radius: var(--wb-radius-sm);
  padding: var(--wb-sp-3);
}

.endorse__head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--wb-sp-2);
  margin-bottom: var(--wb-sp-1);
}

.endorse__title {
  font-size: var(--wb-fs-sm);
  font-weight: 600;
  color: var(--wb-text-strong);
}

.endorse__problem {
  margin: 0;
  font-size: var(--wb-fs-xs);
  line-height: var(--wb-lh-xs);
  color: var(--wb-text);
}

.endorse__reason {
  margin: var(--wb-sp-2) 0 0;
  font-size: var(--wb-fs-xs);
  line-height: var(--wb-lh-xs);
  color: var(--wb-text-muted);
}

/* ---------- 使用流程引导 ---------- */
.wb-usage {
  margin-bottom: var(--wb-sp-4);
  --el-collapse-header-height: 40px;
}
.wb-usage :deep(.el-collapse-item__header) {
  font-size: var(--wb-fs-sm);
}
.wb-usage__title {
  font-weight: 600;
  color: var(--wb-text-strong);
}
.wb-usage__steps {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: var(--wb-sp-2);
  font-size: var(--wb-fs-xs);
  line-height: var(--wb-lh-sm);
  color: var(--wb-text);
}
.wb-usage__steps b { color: var(--wb-text-strong); }
.wb-usage__glossary {
  margin: var(--wb-sp-2) 0 0;
  font-size: var(--wb-fs-xs);
  line-height: var(--wb-lh-xs);
  color: var(--wb-text-muted);
}

/* 抽屉内区块空态：弱化但仍可见，避免「标题下一片空白像坏了」 */
.wb-drawer-empty {
  margin: 0;
  padding: var(--wb-sp-3) 0;
  font-size: var(--wb-fs-xs);
  line-height: var(--wb-lh-xs);
  color: var(--wb-text-disabled);
}

.req-title {
  display: block;
  font-size: var(--wb-fs-sm);
  color: var(--wb-text-strong);
  margin-bottom: 2px;
}

.one-line {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 420px;
}

.depth-cell {
  display: flex;
  align-items: center;
  gap: var(--wb-sp-2);
}
.depth-cell :deep(.el-progress) { flex: 1; }
.depth-num {
  font-size: var(--wb-fs-xs);
  color: var(--wb-text-muted);
  flex-shrink: 0;
}

/* ---------- 判断总览 ---------- */
.judge-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--wb-sp-2);
}

.judge-cell {
  background: var(--wb-surface-sub);
  border: 1px solid var(--wb-border);
  border-radius: var(--wb-radius-sm);
  padding: var(--wb-sp-3);
  display: flex;
  flex-direction: column;
  gap: var(--wb-sp-2);
  align-items: flex-start;
}

.judge-cell__label {
  font-size: var(--wb-fs-xs);
  color: var(--wb-text-muted);
}

.judge-cell__value {
  font-size: var(--wb-fs-lg);
  font-weight: 600;
  color: var(--wb-text-strong);
}

/* ---------- 方法论检查 / 字段列表 ---------- */
.method-list {
  display: flex;
  flex-direction: column;
  gap: var(--wb-sp-2);
}

.field-list { margin: 0; }

.field-row {
  display: flex;
  gap: var(--wb-sp-2);
  padding: var(--wb-sp-1) 0;
  font-size: var(--wb-fs-sm);
}

.field-row dt {
  color: var(--wb-text-muted);
  flex-shrink: 0;
  width: 76px;
  margin: 0;
}

.field-row dd {
  margin: 0;
  color: var(--wb-text);
  word-break: break-word;
}

/* ---------- 证据与疑点 ---------- */
.action-row {
  display: flex;
  gap: var(--wb-sp-2);
  margin-bottom: var(--wb-sp-3);
}

.suggestion-list {
  display: flex;
  flex-direction: column;
  gap: var(--wb-sp-2);
  margin-bottom: var(--wb-sp-3);
}

.suggestion {
  background: var(--wb-green-50);
  border-left: 3px solid var(--wb-green-600);
  border-radius: var(--wb-radius-xs);
  padding: var(--wb-sp-2) var(--wb-sp-3);
  font-size: var(--wb-fs-xs);
  line-height: var(--wb-lh-sm);
  color: var(--wb-text);
}

/* AI 建议（LLM 增强层）：与规则建议视觉区分，只作参考 */
.suggestion--ai {
  background: var(--wb-info-bg, rgba(83, 157, 245, .14));
  border-left-color: var(--wb-info, #539df5);
  display: flex;
  align-items: baseline;
  gap: var(--wb-sp-2);
}

.evidence-list {
  display: flex;
  flex-direction: column;
  gap: var(--wb-sp-2);
}

.evidence {
  display: flex;
  align-items: flex-start;
  gap: var(--wb-sp-2);
  font-size: var(--wb-fs-xs);
  line-height: var(--wb-lh-sm);
}

.evidence__text { color: var(--wb-text); word-break: break-word; }

.review-form :deep(.el-select) { width: 160px; }

/* ---------- 看板视图：按状态分列的卡片墙 ---------- */
.wb-board {
  display: flex;
  align-items: flex-start;
  gap: var(--wb-sp-3);
  padding: var(--wb-sp-4) var(--wb-sp-5);
  overflow-x: auto;
}

.wb-board__col {
  flex: 0 0 264px;
  background: var(--wb-surface-sub);
  border: 1px solid var(--wb-border);
  border-radius: var(--wb-radius-md);
  padding: var(--wb-sp-3);
}

.wb-board__col-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--wb-sp-2);
  margin-bottom: var(--wb-sp-3);
}

.wb-board__count {
  font-size: var(--wb-fs-xs);
  color: var(--wb-text-muted);
}

.wb-board__list {
  display: flex;
  flex-direction: column;
  gap: var(--wb-sp-2);
  max-height: calc(100vh - 260px);
  overflow-y: auto;
}

.wb-board__empty {
  margin: 0;
  padding: var(--wb-sp-4) 0;
  text-align: center;
  font-size: var(--wb-fs-xs);
  color: var(--wb-text-disabled);
}

/* 卡片：hover 提亮 + 轻阴影，指针提示可点进详情 */
.wb-board-card {
  background: var(--wb-surface);
  border: 1px solid var(--wb-border);
  border-radius: var(--wb-radius-sm);
  padding: var(--wb-sp-3);
  cursor: pointer;
  transition:
    background var(--wb-dur-fast) var(--wb-ease),
    box-shadow var(--wb-dur-fast) var(--wb-ease);
}

.wb-board-card:hover {
  background: var(--wb-surface-hover);
  box-shadow: var(--wb-shadow-sm);
}

.wb-board-card:focus-visible {
  outline: 2px solid var(--wb-green-600);
  outline-offset: 1px;
}

.wb-board-card__title {
  margin: 0 0 2px;
  font-size: var(--wb-fs-sm);
  font-weight: 600;
  color: var(--wb-text-strong);
  line-height: var(--wb-lh-sm);
}

/* 原话最多两行，超出省略，避免卡片高度失控 */
.wb-board-card__original {
  margin: 0;
  font-size: var(--wb-fs-xs);
  line-height: var(--wb-lh-xs);
  color: var(--wb-text-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.wb-board-card__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--wb-sp-2);
  margin-top: var(--wb-sp-2);
  font-size: var(--wb-fs-xs);
  color: var(--wb-text-muted);
}

.wb-board-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--wb-sp-1);
  margin-top: var(--wb-sp-2);
}

/* 窄屏：判断总览改为单列 */
@media (max-width: 640px) {
  .judge-grid { grid-template-columns: 1fr; }
}
</style>
