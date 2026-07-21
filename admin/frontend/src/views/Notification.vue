<template>
  <div class="notification">
    <el-card>
      <div class="toolbar">
        <el-button @click="markAllRead">全部标为已读</el-button>
        <el-button type="danger" @click="clearAll">清空通知</el-button>
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
            <div class="notification-time">{{ formatTime(notification.created_at) }}</div>
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
import { ref } from 'vue'
import axios from '../utils/axios'
import { Phone, FolderOpened, Monitor, Bell } from '@element-plus/icons-vue'

const notifications = ref([])

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

async function loadNotifications() {
  try {
    const response = await axios.get('/api/notifications')
    notifications.value = response.data
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
  }
}

async function markAllRead() {
  try {
    await axios.put('/api/notifications/read')
    loadNotifications()
  } catch (error) {
    console.error('标记失败:', error)
  }
}

async function clearAll() {
  if (!confirm('确定要清空所有通知吗？')) return
  try {
    await axios.delete('/api/notifications')
    loadNotifications()
  } catch (error) {
    console.error('清空失败:', error)
  }
}

loadNotifications()
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
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
