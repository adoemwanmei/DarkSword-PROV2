<template>
  <div class="audit-log">
    <el-card>
      <div class="search-bar">
        <el-input v-model="filters.username" placeholder="用户名" style="width: 150px;" />
        <el-select v-model="filters.action" placeholder="操作类型">
          <el-option label="全部" value="" />
          <el-option label="登录" value="login" />
          <el-option label="登出" value="logout" />
          <el-option label="添加" value="create" />
          <el-option label="修改" value="update" />
          <el-option label="删除" value="delete" />
          <el-option label="命令执行" value="command" />
        </el-select>
        <el-date-picker v-model="filters.date" type="date" placeholder="选择日期" style="width: 180px;" />
        <el-button type="primary" @click="loadLogs">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
      
      <el-table :data="logsData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="action" label="操作" width="120">
          <template #default="scope">
            <el-tag :type="getActionType(scope.row.action)">{{ getActionName(scope.row.action) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resource" label="资源" />
        <el-table-column prop="details" label="详情" show-overflow-tooltip />
        <el-table-column prop="ip" label="IP" width="150" />
        <el-table-column prop="created_at" label="时间" width="180" />
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
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from '../utils/axios'

const logsData = ref([])
const loading = ref(false)

const filters = reactive({
  username: '',
  action: '',
  date: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

function getActionType(action) {
  const types = { 'login': 'success', 'logout': 'info', 'create': 'warning', 'update': 'info', 'delete': 'danger', 'command': 'warning' }
  return types[action] || 'info'
}

function getActionName(action) {
  const names = { 'login': '登录', 'logout': '登出', 'create': '添加', 'update': '修改', 'delete': '删除', 'command': '命令执行' }
  return names[action] || action
}

async function loadLogs() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.username) params.append('username', filters.username)
    if (filters.action) params.append('action', filters.action)
    if (filters.date) params.append('date', filters.date)
    
    const response = await axios.get(`/api/audit?${params}`)
    logsData.value = response.data
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.username = ''
  filters.action = ''
  filters.date = ''
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
</style>
