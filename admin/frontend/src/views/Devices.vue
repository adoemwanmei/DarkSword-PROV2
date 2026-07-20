<template>
  <div class="devices">
    <el-card>
      <el-table :data="devices" border v-loading="loading">
        <el-table-column prop="device_uuid" label="设备UUID" width="300" />
        <el-table-column prop="ip" label="IP" width="150" />
        <el-table-column prop="first_seen" label="首次访问" width="180" />
        <el-table-column prop="last_seen" label="最后访问" width="180" />
        <el-table-column prop="user_agent" label="User Agent" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'">
              {{ scope.row.status === 'active' ? '活跃' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="viewDetail(scope.row.device_uuid)">详情</el-button>
            <el-button size="small" type="warning" @click="viewLogs(scope.row.device_uuid)">日志</el-button>
            <el-button size="small" type="danger" @click="deleteDevice(scope.row.device_uuid)">删除</el-button>
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
import { useRouter } from 'vue-router'
import axios from '../utils/axios'

const router = useRouter()
const devices = ref([])
const loading = ref(false)

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

async function loadDevices() {
  loading.value = true
  try {
    const response = await axios.get(`/api/devices?skip=${(pagination.page - 1) * pagination.size}&limit=${pagination.size}`)
    devices.value = response.data
  } catch (error) {
    console.error('加载设备失败:', error)
  } finally {
    loading.value = false
  }
}

function viewDetail(uuid) {
  router.push(`/devices/${uuid}`)
}

function viewLogs(uuid) {
  router.push(`/logs?device_uuid=${uuid}`)
}

async function deleteDevice(uuid) {
  if (!confirm('确定要删除这个设备吗？')) return
  try {
    await axios.delete(`/api/devices/${uuid}`)
    loadDevices()
  } catch (error) {
    console.error('删除设备失败:', error)
  }
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadDevices()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadDevices()
}

loadDevices()
</script>
