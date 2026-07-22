<template>
  <div class="notification">
    <el-card>
      <div class="toolbar toolbar--with-switch">
        <div class="toolbar-left">
          <el-button @click="markAllRead">全部标为已读</el-button>
          <el-button type="danger" @click="clearAll">清空通知</el-button>
        </div>
        <div class="toolbar-right">
          <div class="notify-switch-row">
            <el-switch
              v-model="notifyEnabled"
              @change="handleNotifySwitchChange"
              @click.capture="onSwitchCaptureClick"
              :loading="permissionRequesting"
            />
            <span class="notify-switch-label">浏览器主动通知</span>
            <el-tag size="small" :type="permissionTagType" effect="plain">
              {{ permissionText }}
            </el-tag>
            <el-button
              v-if="permission === 'default'"
              type="primary"
              size="small"
              plain
              @click="requestNotifyPermission"
              :loading="permissionRequesting"
            >立即授权</el-button>
            <el-button
              v-else-if="permission === 'denied'"
              type="warning"
              size="small"
              plain
              @click="openSiteSettingsHelp"
            >如何开启</el-button>
          </div>
          <div class="notify-switch-row">
            <el-switch
              v-model="pageToastEnabled"
              @change="handlePageToastSwitchChange"
            />
            <span class="notify-switch-label">页面悬浮通知</span>
            <el-tag size="small" type="success" effect="plain" v-if="pageToastEnabled">已启用</el-tag>
            <el-tag size="small" type="info" effect="plain" v-else>已关闭</el-tag>
          </div>
          <div class="notify-hint" v-if="notifyEnabled && permission === 'default'">
            点击右侧「立即授权」按钮，在浏览器弹窗中点击 <b>允许</b>，之后新设备上线等事件会弹出桌面提醒
          </div>
          <div class="notify-hint notify-hint--warn" v-else-if="notifyEnabled && permission === 'denied'">
            权限被浏览器拒绝，请点击「如何开启」，或在地址栏左侧的「站点设置」里把通知权限设为「允许」后刷新页面
          </div>
          <div class="notify-hint" v-if="!pageToastEnabled && notifyEnabled">
            已关闭页面内悬浮通知，仅浏览器系统通知会弹出
          </div>
        </div>
      </div>

      <div v-if="totalCount !== null" class="list-summary">
        共 {{ totalCount }} 条通知 · 未读 {{ unreadCount }} 条
      </div>
      
      <div class="notification-list">
        <div 
          v-for="notification in notifications" 
          :key="notification.id" 
          class="notification-item"
          :class="{ 'read': notification.read }"
          @click="markRead(notification.id)"
        >
          <div class="notification-icon">
            <el-icon v-if="notification.type === 'device'"><Phone /></el-icon>
            <el-icon v-else-if="notification.type === 'exfil'"><FolderOpened /></el-icon>
            <el-icon v-else-if="notification.type === 'command'"><Monitor /></el-icon>
            <el-icon v-else><Bell /></el-icon>
          </div>
          <div class="notification-content">
            <div class="notification-title">{{ notification.title }}</div>
            <div class="notification-desc">{{ notification.description }}</div>
            <div class="notification-meta">
              <span class="notification-time">{{ formatTime(notification.created_at) }}</span>
              <el-tag
                v-if="notification.related_device_uuid"
                size="small"
                effect="plain"
                type="info"
              >
                设备: {{ truncateUuid(notification.related_device_uuid) }}
              </el-tag>
            </div>
          </div>
          <div class="notification-status">
            <el-tag v-if="!notification.read" type="danger">未读</el-tag>
          </div>
        </div>
        
        <div v-if="notifications.length === 0" class="empty-state">
          <el-icon size="48" style="color: #ccc;"><Bell /></el-icon>
          <p>暂无通知</p>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import axios from '../utils/axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Phone, FolderOpened, Monitor, Bell } from '@element-plus/icons-vue'

const LS_KEY = 'notify_enabled'
const LS_PAGE_TOAST_KEY = 'page_toast_enabled'

const notifications = ref([])
const totalCount = ref(null)
const unreadCount = ref(null)
const notifyEnabled = ref(localStorage.getItem(LS_KEY) === 'true')
const pageToastEnabled = ref(localStorage.getItem(LS_PAGE_TOAST_KEY) !== 'false')
const permissionRequesting = ref(false)

const permission = ref(
  (typeof window !== 'undefined' && 'Notification' in window) ? Notification.permission : 'unsupported'
)

let permissionInterval = null

function handlePushNotification(event) {
  const item = event && event.detail
  if (!item) return
  const existingId = typeof item.id === 'number' ? item.id : null
  if (existingId && notifications.value.some(n => n.id === existingId)) return
  notifications.value.unshift({
    id: item.id ?? Date.now(),
    title: item.title || '',
    description: item.description || '',
    type: item.type || item.category || 'info',
    read: false,
    created_at: item.created_at || new Date().toISOString(),
    related_device_uuid: item.related_device_uuid || null,
  })
  totalCount.value = (totalCount.value ?? notifications.value.length - 1) + 1
  unreadCount.value = (unreadCount.value ?? 0) + 1
}

onMounted(() => {
  loadNotifications()
  if ('Notification' in window) {
    permissionInterval = setInterval(() => {
      permission.value = Notification.permission
    }, 2000)
  }
  window.addEventListener('darksword:notification', handlePushNotification)
})

onBeforeUnmount(() => {
  if (permissionInterval) clearInterval(permissionInterval)
  window.removeEventListener('darksword:notification', handlePushNotification)
})

const permissionText = computed(() => {
  if (permission.value === 'granted') return '权限已允许'
  if (permission.value === 'denied') return '权限被拒绝'
  if (permission.value === 'default') return '尚未授权'
  return '浏览器不支持'
})

const permissionTagType = computed(() => {
  if (permission.value === 'granted') return 'success'
  if (permission.value === 'denied') return 'danger'
  if (permission.value === 'default') return 'warning'
  return 'info'
})

function truncateUuid(uuid) {
  if (!uuid) return ''
  if (uuid.length <= 8) return uuid
  return uuid.slice(0, 8) + '...'
}

function fireTestNotification() {
  try {
    const n = new Notification('DarkSword 通知已开启 ✅', {
      body: '当有新设备上线、访问或重要事件时，您会收到浏览器桌面通知（点击此通知跳转到通知中心）',
      tag: 'darksword-notify-test-' + Date.now(),
      icon: '/favicon.ico'
    })
    if (n && typeof n.addEventListener === 'function') {
      n.addEventListener('click', () => {
        window.focus()
        n.close()
      })
    }
    setTimeout(() => n && n.close && n.close(), 7000)
  } catch (_) {}
}

function refreshPermission() {
  if ('Notification' in window) {
    permission.value = Notification.permission
  }
}

async function requestNotifyPermission(thenEnableSwitch = true) {
  if (!('Notification' in window)) {
    ElMessage.warning('当前浏览器不支持桌面通知')
    return false
  }
  refreshPermission()
  if (permission.value === 'granted') {
    if (thenEnableSwitch) {
      notifyEnabled.value = true
      localStorage.setItem(LS_KEY, 'true')
    }
    fireTestNotification()
    ElMessage.success('通知权限已就绪')
    return true
  }
  if (permission.value === 'denied') {
    ElMessage.warning('通知权限已被浏览器拒绝，请在地址栏左侧站点设置中手动开启后刷新')
    return false
  }
  if (permissionRequesting.value) return false
  permissionRequesting.value = true
  try {
    const result = await Notification.requestPermission()
    permission.value = result
    if (result === 'granted') {
      if (thenEnableSwitch) {
        notifyEnabled.value = true
        localStorage.setItem(LS_KEY, 'true')
      }
      ElMessage.success('通知权限已授权，新设备上线等事件会主动提醒')
      fireTestNotification()
      return true
    } else if (result === 'denied') {
      ElMessage.warning('您点击了「拒绝」，浏览器不会主动弹出通知')
      return false
    } else {
      ElMessage.info('未授权通知权限，仅在页面通知列表中可见')
      return false
    }
  } catch (err) {
    console.error('申请通知权限失败:', err)
    ElMessage.error('申请通知权限失败')
    return false
  } finally {
    permissionRequesting.value = false
  }
}

function onSwitchCaptureClick() {
  if (!('Notification' in window)) return
  if (notifyEnabled.value === false) return
  if (permission.value === 'default') {
    requestNotifyPermission(false)
  }
}

function openSiteSettingsHelp() {
  const msg = '请在地址栏左侧「站点设置」(🔒 / ⚠️ 图标) 中，将「通知」改为「允许」，然后刷新页面即可'
  ElMessageBox && typeof ElMessageBox.alert === 'function'
    ? ElMessageBox.alert(msg, '如何开启浏览器通知权限', { confirmButtonText: '知道了' }).catch(() => {})
    : ElMessage.info(msg)
}

function handlePageToastSwitchChange(on) {
  localStorage.setItem(LS_PAGE_TOAST_KEY, on ? 'true' : 'false')
  if (on) {
    ElMessage.success('已开启页面悬浮通知，新事件会在右下角弹出卡片')
  } else {
    ElMessage.info('已关闭页面悬浮通知')
  }
}

async function handleNotifySwitchChange(on) {
  localStorage.setItem(LS_KEY, on ? 'true' : 'false')
  if (!on) {
    ElMessage.info('已关闭浏览器主动通知')
    return
  }
  await requestNotifyPermission(true)
}

function mapNotification(item) {
  if (!item) return item
  return {
    id: item.id,
    title: item.title || '',
    description: item.description || item.message || '',
    type: item.type || item.category || 'info',
    read: item.read === true || item.is_read === 1 || item.is_read === true,
    created_at: item.created_at || item.timestamp || new Date().toISOString(),
    related_device_uuid: item.related_device_uuid || null,
    related_resource_type: item.related_resource_type || null,
    related_resource_id: item.related_resource_id || null
  }
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

async function loadNotifications() {
  try {
    const response = await axios.get('/api/notifications')
    const data = response.data
    const items = Array.isArray(data) ? data : (data?.items || [])
    notifications.value = items.map(mapNotification)
    if (!Array.isArray(data)) {
      totalCount.value = typeof data.total === 'number' ? data.total : items.length
      unreadCount.value = typeof data.unread_count === 'number' ? data.unread_count
        : items.filter(n => !n.read).length
    } else {
      totalCount.value = items.length
      unreadCount.value = items.filter(n => !n.read).length
    }
  } catch (error) {
    console.error('加载通知失败:', error)
  }
}

async function markRead(id) {
  try {
    await axios.put(`/api/notifications/${id}/read`)
    loadNotifications()
  } catch (error) {
    console.error('标记失败:', error)
    ElMessage.error('标记失败')
  }
}

async function markAllRead() {
  try {
    await axios.put('/api/notifications/read')
    ElMessage.success('已全部标记为已读')
    loadNotifications()
  } catch (error) {
    console.error('标记失败:', error)
    ElMessage.error('标记失败')
  }
}

async function clearAll() {
  if (!confirm('确定要清空所有通知吗？')) return
  try {
    await axios.delete('/api/notifications')
    ElMessage.success('已清空通知')
    loadNotifications()
  } catch (error) {
    console.error('清空失败:', error)
    ElMessage.error('清空失败')
  }
}
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  align-items: flex-start;
  justify-content: space-between;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.toolbar-right {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-end;
}

.notify-switch-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.notify-switch-label {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.notify-hint {
  font-size: 12px;
  color: #606266;
  max-width: 360px;
  line-height: 1.5;
  padding: 6px 10px;
  background: #ecf5ff;
  border-radius: 4px;
  color: #409eff;
}

.notify-hint--warn {
  background: #fdf6ec;
  color: #e6a23c;
}

.list-summary {
  margin-bottom: 14px;
  color: #606266;
  font-size: 13px;
  padding-left: 4px;
}

.notification-list {
  max-height: 600px;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 15px;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: all 0.2s;
}

.notification-item:hover {
  background: #f5f7fa;
}

.notification-item.read {
  opacity: 0.6;
}

.notification-icon {
  font-size: 24px;
  color: #409eff;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-weight: bold;
  margin-bottom: 5px;
}

.notification-desc {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
  white-space: pre-line;
}

.notification-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.notification-time {
  font-size: 12px;
  color: #999;
}

.notification-status {
  flex-shrink: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #999;
}
</style>
