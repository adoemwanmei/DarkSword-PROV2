<template>
  <div class="command-scripts">
    <el-card>
      <div class="toolbar">
        <el-button type="primary" @click="showAddDialog">新建脚本</el-button>
      </div>
      
      <el-table :data="scriptsData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="脚本名称" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="command" label="命令" show-overflow-tooltip />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="runScript(scope.row)">运行</el-button>
            <el-button size="small" @click="editScript(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteScript(scope.row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog :title="editMode ? '编辑脚本' : '新建脚本'" v-model="dialogVisible" width="60%">
      <el-form :model="scriptForm" label-width="80px">
        <el-form-item label="脚本名称">
          <el-input v-model="scriptForm.name" placeholder="请输入脚本名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="scriptForm.description" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="命令内容">
          <el-input v-model="scriptForm.command" type="textarea" :rows="5" placeholder="请输入命令内容" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveScript">确定</el-button>
      </template>
    </el-dialog>
    
    <el-dialog title="选择设备运行" v-model="runDialogVisible" width="50%">
      <el-select v-model="selectedDevices" multiple placeholder="选择设备" style="width: 100%;">
        <el-option v-for="device in devices" :key="device.device_uuid" :label="device.device_uuid" :value="device.device_uuid" />
      </el-select>
      <template #footer>
        <el-button @click="runDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="executeScript">执行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from '../utils/axios'

const scriptsData = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const runDialogVisible = ref(false)
const editMode = ref(false)
const currentScript = ref(null)
const devices = ref([])
const selectedDevices = ref([])

const scriptForm = reactive({
  name: '',
  description: '',
  command: ''
})

async function loadScripts() {
  loading.value = true
  try {
    const response = await axios.get('/api/commands/scripts')
    scriptsData.value = response.data
  } catch (error) {
    console.error('加载脚本失败:', error)
  } finally {
    loading.value = false
  }
}

async function loadDevices() {
  try {
    const response = await axios.get('/api/devices?limit=100')
    devices.value = response.data
  } catch (error) {
    console.error('加载设备失败:', error)
  }
}

function showAddDialog() {
  editMode.value = false
  currentScript.value = null
  scriptForm.name = ''
  scriptForm.description = ''
  scriptForm.command = ''
  dialogVisible.value = true
}

function editScript(script) {
  editMode.value = true
  currentScript.value = script
  scriptForm.name = script.name
  scriptForm.description = script.description
  scriptForm.command = script.command
  dialogVisible.value = true
}

async function saveScript() {
  try {
    if (editMode.value) {
      await axios.put(`/api/commands/scripts/${currentScript.value.id}`, scriptForm)
    } else {
      await axios.post('/api/commands/scripts', scriptForm)
    }
    dialogVisible.value = false
    loadScripts()
  } catch (error) {
    console.error('保存失败:', error)
  }
}

async function deleteScript(id) {
  if (!confirm('确定要删除这个脚本吗？')) return
  try {
    await axios.delete(`/api/commands/scripts/${id}`)
    loadScripts()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

function runScript(script) {
  currentScript.value = script
  loadDevices()
  runDialogVisible.value = true
}

async function executeScript() {
  if (selectedDevices.value.length === 0) {
    alert('请选择设备')
    return
  }
  try {
    for (const device_uuid of selectedDevices.value) {
      await axios.post(`/api/commands?device_uuid=${device_uuid}`, { command: currentScript.value.command })
    }
    runDialogVisible.value = false
    alert('命令已发送')
  } catch (error) {
    console.error('执行失败:', error)
  }
}

loadScripts()
</script>

<style scoped>
.toolbar {
  margin-bottom: 20px;
}
</style>
