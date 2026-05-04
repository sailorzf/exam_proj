<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <h3>管理</h3>
      <nav>
        <router-link to="/teacher/admin/users">用户管理</router-link>
        <router-link to="/teacher/admin/settings">系统设置</router-link>
      </nav>
    </aside>
    <div class="admin-content">
      <router-view />
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.admin-layout { display: flex; gap: 1.5rem; }
.sidebar {
  width: 200px;
  flex-shrink: 0;
  background: #fff;
  border: 1px solid #e4e1ee;
  border-radius: 0.75rem;
  padding: 1rem 0;
  height: fit-content;
}
.sidebar h3 {
  font-size: 14px;
  font-weight: 600;
  color: #777587;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0 1rem;
  margin-bottom: 0.5rem;
}
.sidebar nav { display: flex; flex-direction: column; }
.sidebar nav a {
  padding: 0.625rem 1rem;
  color: #464555;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.15s;
  border-left: 3px solid transparent;
}
.sidebar nav a:hover {
  background: #f5f2ff;
  color: #3525cd;
}
.sidebar nav a.router-link-active {
  background: #f0ecf9;
  color: #3525cd;
  border-left-color: #3525cd;
  font-weight: 600;
}
.admin-content { flex: 1; min-width: 0; }
</style>
