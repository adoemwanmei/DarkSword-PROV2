<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>DarkSword</h1>
        <p>Admin Panel</p>
      </div>
      <el-form :model="loginForm" ref="loginFormRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="loginForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleLogin" :loading="loading" style="width: 100%">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <p>默认用户名: admin</p>
        <p>默认密码: admin123</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const loginFormRef = ref(null)

const loginForm = reactive({
  username: '',
  password: ''
})

async function handleLogin() {
  loading.value = true
  const success = await authStore.login(loginForm.username, loginForm.password)
  loading.value = false
  
  if (success) {
    router.push('/')
  } else {
    alert('用户名或密码错误')
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.login-box {
  background: #fff;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  width: 350px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.login-header h1 {
  margin: 0;
  font-size: 32px;
  color: #1a1a2e;
}

.login-header p {
  margin: 5px 0 0;
  color: #888;
}

.login-footer {
  margin-top: 20px;
  text-align: center;
  color: #888;
  font-size: 12px;
}

.login-footer p {
  margin: 5px 0;
}
</style>
