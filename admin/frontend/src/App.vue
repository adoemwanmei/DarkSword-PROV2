<template>
  <el-container class="app-container">
    <el-aside v-if="$route.meta.requiresAuth" width="200px" class="sidebar">
      <div class="logo">
        <h2>DarkSword</h2>
        <p>Admin Panel</p>
      </div>
      <el-menu :default-active="activeMenu" class="sidebar-menu" @select="handleMenuSelect">
        <el-menu-item index="/">
          <el-icon><Monitor /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/logs">
          <el-icon><Document /></el-icon>
          <span>访问日志</span>
        </el-menu-item>
        <el-menu-item index="/devices">
          <el-icon><Phone /></el-icon>
          <span>设备管理</span>
        </el-menu-item>
        <el-menu-item index="/exfil">
          <el-icon><FolderOpened /></el-icon>
          <span>数据管理</span>
        </el-menu-item>
        <el-menu-item v-if="user?.role === 'admin'" index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header v-if="$route.meta.requiresAuth" class="header">
        <div class="header-left">
          <el-button @click="toggleSidebar" class="toggle-btn">
            <el-icon><Menu /></el-icon>
          </el-button>
        </div>
        <div class="header-right">
          <el-dropdown trigger="click">
            <span class="user-info">
              <el-icon><User /></el-icon>
              <span>{{ user?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>角色: {{ user?.role === 'admin' ? '管理员' : '操作员' }}</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { 
  Monitor, Document, Phone, FolderOpened, User, 
  Menu, ArrowDown, SwitchButton 
} from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const user = computed(() => authStore.user)

const activeMenu = computed(() => {
  return router.currentRoute.value.path
})

function toggleSidebar() {
}

function handleMenuSelect(index) {
  router.push(index)
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.sidebar {
  background: #1a1a2e;
  color: #fff;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #333;
}

.logo h2 {
  margin: 0;
  font-size: 20px;
  font-weight: bold;
}

.logo p {
  margin: 5px 0 0;
  font-size: 12px;
  color: #888;
}

.sidebar-menu {
  border-right: none;
}

.header {
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.toggle-btn {
  background: transparent;
  border: none;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.main-content {
  padding: 20px;
  background: #f5f5f5;
}
</style>
