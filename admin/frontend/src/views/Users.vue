<template>
  <div class="users">
    <el-card>
      <el-button type="primary" @click="showAddDialog = true" style="margin-bottom: 20px;">
        添加用户
      </el-button>
      
      <el-table :data="users" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'info'">
              {{ scope.row.role === 'admin' ? '管理员' : '操作员' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="last_login" label="最后登录" width="180" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click="editUser(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteUser(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <el-dialog :title="editingUser ? '编辑用户' : '添加用户'" v-model="showAddDialog">
      <el-form :model="userForm" ref="userFormRef" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="userForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role">
            <el-option label="管理员" value="admin" />
            <el-option label="操作员" value="operator" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveUser">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from '../utils/axios'

const users = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const userFormRef = ref(null)
const editingUser = ref(null)

const userForm = reactive({
  username: '',
  password: '',
  role: 'operator'
})

async function loadUsers() {
  loading.value = true
  try {
    const response = await axios.get('/api/users')
    users.value = response.data
  } catch (error) {
    console.error('加载用户失败:', error)
  } finally {
    loading.value = false
  }
}

function editUser(user) {
  editingUser.value = user
  userForm.username = user.username
  userForm.password = ''
  userForm.role = user.role
  showAddDialog.value = true
}

async function saveUser() {
  try {
    if (editingUser.value) {
      await axios.put(`/api/users/${editingUser.value.id}`, userForm)
    } else {
      await axios.post('/api/users', userForm)
    }
    showAddDialog.value = false
    editingUser.value = null
    userForm.username = ''
    userForm.password = ''
    userForm.role = 'operator'
    loadUsers()
  } catch (error) {
    console.error('保存用户失败:', error)
    alert(error.response?.data?.detail || '保存失败')
  }
}

async function deleteUser(user) {
  if (user.role === 'admin') {
    alert('不能删除管理员')
    return
  }
  if (!confirm(`确定要删除用户 ${user.username} 吗？`)) return
  try {
    await axios.delete(`/api/users/${user.id}`)
    loadUsers()
  } catch (error) {
    console.error('删除用户失败:', error)
    alert(error.response?.data?.detail || '删除失败')
  }
}

loadUsers()
</script>
