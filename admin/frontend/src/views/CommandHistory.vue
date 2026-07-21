<template>
  <div class="command-history">
    <el-card>
      <div class="search-bar">
        <el-input v-model="filters.device_uuid" placeholder="设备UUID" style="width: 250px;" />
        <el-input v-model="filters.command" placeholder="命令关键字" style="width: 200px;" />
        <el-select v-model="filters.status" placeholder="状态">
          <el-option label="全部" value="" />
          <el-option label="等待执行" value="pending" />
          <el-option label="执行中" value="executing" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>
        <el-button type="primary" @click="loadCommands">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
      
      <el-table :data="commandsData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_uuid" label="设备UUID" width="250" />
        <el-table-column prop="command" label="命令" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ getStatusName(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="output" label="输出" show-overflow-tooltip width="300">
          <template #default="scope">
            <el-button size="small" @click="showOutput(scope.row)">查看</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="executed_at" label="执行时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="retryCommand(scope.row.id)" v-if="scope.row.status !== 'pending'">重试</el-button>
            <el-button size="small" type="danger" @click="deleteCommand(scope.row.id)">删除</el-button>
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
    
    <el-dialog title="命令输出" v-model="outputDialogVisible" width="60%">
      <pre style="white-space: pre-wrap; max-height: 400px; overflow-y: auto;">{{ currentOutput }}</pre>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from '../utils/axios'

const commandsData = ref([])
const loading = ref(false)
const outputDialogVisible = ref(false)
const currentOutput = ref('')

const filters = reactive({
  device_uuid: '',
  command: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

function getStatusType(status) {
  const types = { 'pending': 'warning', 'executing': 'info', 'completed': 'success', 'failed': 'danger' }
  return types[status] || 'info'
}

function getStatusName(status) {
  const names = { 'pending': '等待执行', 'executing': '执行中', 'completed': '已完成', 'failed': '失败' }
  return names[status] || status
}

function showOutput(row) {
  currentOutput.value = row.output || '无输出'
  outputDialogVisible.value = true
}

async function loadCommands() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.command) params.append('command', filters.command)
    if (filters.status) params.append('status', filters.status)
    
    const response = await axios.get(`/api/commands?${params}`)
    commandsData.value = response.data
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

async function retryCommand(id) {
  try {
    await axios.post(`/api/commands/${id}/retry`)
    loadCommands()
  } catch (error) {
    console.error('重试失败:', error)
  }
}

async function deleteCommand(id) {
  if (!confirm('确定要删除这条命令吗？')) return
  try {
    await axios.delete(`/api/commands/${id}`)
    loadCommands()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

function resetFilters() {
  filters.device_uuid = ''
  filters.command = ''
  filters.status = ''
  loadCommands()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadCommands()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadCommands()
}

loadCommands()
</script>

<style scoped>
.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
</style>
