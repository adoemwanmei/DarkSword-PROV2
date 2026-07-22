<template>
  <div class="logs">
    <el-card>
      <div class="search-bar">
        <el-input v-model="filters.ip" placeholder="IP地址" style="width: 150px;" />
        <el-input v-model="filters.device_uuid" placeholder="设备UUID" style="width: 200px;" />
        <el-input v-model="filters.path" placeholder="路径" style="width: 200px;" />
        <el-select v-model="filters.log_type" placeholder="日志类型">
          <el-option label="全部" value="" />
          <el-option label="iOS设备" value="ios" />
          <el-option label="请求" value="request" />
          <el-option label="数据窃取" value="exfil" />
          <el-option label="前端" value="frontend" />
          <el-option label="API" value="api" />
        </el-select>
        <el-date-picker
          v-model="filters.start_time"
          type="datetime"
          placeholder="开始时间"
          style="width: 200px;"
        />
        <el-date-picker
          v-model="filters.end_time"
          type="datetime"
          placeholder="结束时间"
          style="width: 200px;"
        />
        <el-button type="primary" @click="loadLogs">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
      
      <div class="action-bar">
        <el-button type="danger" @click="batchDelete" :disabled="selectedIds.length === 0">批量删除</el-button>
        <el-button type="danger" @click="clearLogs">清空日志</el-button>
      </div>
      
      <el-table :data="logs" border v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="timestamp" label="时间" width="180" />
        <el-table-column prop="ip" label="IP" width="150" />
        <el-table-column prop="device_uuid" label="设备UUID" width="200">
          <template #default="scope">
            <span v-if="scope.row.device_uuid">{{ scope.row.device_uuid }}</span>
            <span v-else style="color:#999">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="method" label="方法" width="80" />
        <el-table-column prop="path" label="路径" />
        <el-table-column prop="status_code" label="状态码" width="100" />
        <el-table-column prop="content_length" label="大小" width="100" />
        <el-table-column prop="log_type" label="类型" width="100">
          <template #default="scope">
            <el-tag :type="getLogTypeTag(scope.row.log_type)">
              {{ getLogTypeText(scope.row.log_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="user_agent" label="User Agent" show-overflow-tooltip />
        <el-table-column label="操作" width="100">
          <template #default="scope">
            <el-button size="small" @click="deleteLog(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        :current-page="pagination.page"
        :page-sizes="[10, 20, 50, 100]"
        :page-size="pagination.size"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from '../utils/axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const logs = ref([])
const loading = ref(false)
const selectedIds = ref([])

const route = useRoute()

const filters = reactive({
  ip: '',
  device_uuid: '',
  path: '',
  log_type: '',
  start_time: null,
  end_time: null
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

onMounted(() => {
  if (route.query.device_uuid) {
    filters.device_uuid = route.query.device_uuid
  }
})

async function loadLogs() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.ip) params.append('ip', filters.ip)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.path) params.append('path', filters.path)
    if (filters.log_type) params.append('log_type', filters.log_type)
    if (filters.start_time) params.append('start_time', filters.start_time.toISOString())
    if (filters.end_time) params.append('end_time', filters.end_time.toISOString())
    
    const response = await axios.get(`/api/logs?${params}`)
    logs.value = response.data
    pagination.total = response.data.length + ((pagination.page - 1) * pagination.size) + 1
  } catch (error) {
    console.error('加载日志失败:', error)
  } finally {
    loading.value = false
  }
}

function getLogTypeTag(type) {
  const tags = {
    'ios': 'danger',
    'exfil': 'danger',
    'request': 'info',
    'frontend': 'warning',
    'api': 'success'
  }
  return tags[type] || 'info'
}

function getLogTypeText(type) {
  const texts = {
    'ios': 'iOS设备',
    'exfil': '数据窃取',
    'request': '请求',
    'frontend': '前端',
    'api': 'API'
  }
  return texts[type] || type
}

async function deleteLog(id) {
  await ElMessageBox.confirm('确定要删除这条日志吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
  try {
    await axios.delete(`/api/logs/${id}`)
    ElMessage.success('删除成功')
    loadLogs()
  } catch (error) {
    console.error('删除日志失败:', error)
    ElMessage.error('删除失败')
  }
}

async function batchDelete() {
  await ElMessageBox.confirm(`确定要删除选中的 ${selectedIds.value.length} 条日志吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
  try {
    await axios.delete('/api/logs/batch', { data: { ids: selectedIds.value } })
    ElMessage.success(`成功删除 ${selectedIds.value.length} 条日志`)
    loadLogs()
  } catch (error) {
    console.error('批量删除失败:', error)
    ElMessage.error('批量删除失败')
  }
}

async function clearLogs() {
  let msg = '确定要清空所有日志吗？'
  if (filters.device_uuid) msg = '确定要清空当前设备的所有日志吗？'
  await ElMessageBox.confirm(msg, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
  try {
    let url = '/api/logs/clear'
    if (filters.device_uuid) url += '?device_uuid=' + filters.device_uuid
    await axios.delete(url)
    ElMessage.success('日志清空成功')
    loadLogs()
  } catch (error) {
    console.error('清空日志失败:', error)
    ElMessage.error('清空日志失败')
  }
}

function handleSelectionChange(selections) {
  selectedIds.value = selections.map(item => item.id)
}

function resetFilters() {
  filters.ip = ''
  filters.device_uuid = ''
  filters.path = ''
  filters.log_type = ''
  filters.start_time = null
  filters.end_time = null
  loadLogs()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadLogs()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadLogs()
}

loadLogs()
</script>

<style scoped>
.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.action-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}
</style>
