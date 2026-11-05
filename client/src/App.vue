<template>
  <div class="app" :class="{ collapsed }">
    <aside id="sidebar" class="sidebar" :class="{ open: mobileOpen }" :inert="isMobile && !mobileOpen">
      <div class="sidebar-logo">
        <span class="logo-mark" aria-hidden="true">{{ t('nav.companyName').charAt(0) }}</span>
        <div class="logo-text">
          <h1>{{ t('nav.companyName') }}</h1>
          <span class="subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :title="collapsed ? t(item.labelKey) : null"
        >
          <svg class="nav-icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path v-for="d in item.icon" :key="d" :d="d" />
          </svg>
          <span class="nav-label">{{ t(item.labelKey) }}</span>
        </router-link>
      </nav>
      <button
        type="button"
        class="collapse-toggle"
        :aria-label="collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
        :title="collapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
        :aria-expanded="!collapsed"
        @click="toggleCollapsed"
      >
        <svg class="nav-icon chevron" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M15 18l-6-6 6-6" />
        </svg>
        <span class="nav-label">{{ t('nav.collapseSidebar') }}</span>
      </button>
    </aside>
    <div v-if="isMobile && mobileOpen" class="backdrop" aria-hidden="true" @click="mobileOpen = false"></div>

    <div class="content">
      <header class="topbar">
        <button
          type="button"
          class="hamburger"
          :aria-label="t('nav.openMenu')"
          :aria-expanded="mobileOpen"
          aria-controls="sidebar"
          @click="mobileOpen = !mobileOpen"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <div class="topbar-actions">
          <button
            type="button"
            class="theme-toggle"
            :aria-label="dark ? t('nav.lightMode') : t('nav.darkMode')"
            :title="dark ? t('nav.lightMode') : t('nav.darkMode')"
            :aria-pressed="dark"
            @click="toggleTheme"
          >
            <svg v-if="dark" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="4" />
              <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
            </svg>
            <svg v-else viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z" />
            </svg>
          </button>
          <LanguageSwitcher />
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </div>
      </header>
      <FilterBar />
      <main class="main-content">
        <router-view />
      </main>
    </div>

    <ProfileDetailsModal
      :is-open="showProfileDetails"
      @close="showProfileDetails = false"
    />

    <TasksModal
      :is-open="showTasks"
      :tasks="tasks"
      @close="showTasks = false"
      @add-task="addTask"
      @delete-task="deleteTask"
      @toggle-task="toggleTask"
    />
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'

const navItems = [
  { to: '/', labelKey: 'nav.overview', icon: ['M4 4h6v6H4z', 'M14 4h6v6h-6z', 'M4 14h6v6H4z', 'M14 14h6v6h-6z'] },
  { to: '/inventory', labelKey: 'nav.inventory', icon: ['M21 8l-9-5-9 5 9 5 9-5z', 'M3 8v8l9 5 9-5V8', 'M12 13v8'] },
  { to: '/orders', labelKey: 'nav.orders', icon: ['M9 4h6v3H9z', 'M15 5h2a2 2 0 012 2v12a2 2 0 01-2 2H7a2 2 0 01-2-2V7a2 2 0 012-2h2', 'M9 12h6M9 16h6'] },
  { to: '/spending', labelKey: 'nav.finance', icon: ['M12 3v18', 'M16 7.5c0-1.4-1.8-2.5-4-2.5s-4 1.1-4 2.5S9.8 10 12 10s4 1.1 4 2.5-1.8 2.5-4 2.5-4-1.1-4-2.5'] },
  { to: '/demand', labelKey: 'nav.demandForecast', icon: ['M3 17l6-6 4 4 8-8', 'M15 7h6v6'] },
  { to: '/reports', labelKey: 'nav.reports', icon: ['M5 20V10', 'M12 20V4', 'M19 20v-7'] },
  { to: '/backlog', labelKey: 'nav.backlog', icon: ['M9 6h11M9 12h11M9 18h11', 'M4 6h.01M4 12h.01M4 18h.01'] }
]

const STORAGE_KEY = 'sidebarCollapsed'
const THEME_KEY = 'app-theme'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    const route = useRoute()
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    // Sidebar state
    const readCollapsed = () => {
      try {
        const stored = localStorage.getItem(STORAGE_KEY)
        if (stored !== null) return stored === 'true'
      } catch (e) { /* storage unavailable */ }
      return window.matchMedia('(min-width: 768px) and (max-width: 1024px)').matches
    }

    const collapsed = ref(readCollapsed())
    const mobileOpen = ref(false)
    const mobileQuery = window.matchMedia('(max-width: 767px)')
    const isMobile = ref(mobileQuery.matches)

    const toggleCollapsed = () => {
      collapsed.value = !collapsed.value
      try {
        localStorage.setItem(STORAGE_KEY, String(collapsed.value))
      } catch (e) { /* storage unavailable */ }
    }

    // Theme state
    const readDark = () => {
      try {
        const stored = localStorage.getItem(THEME_KEY)
        if (stored) return stored === 'dark'
      } catch (e) { /* storage unavailable */ }
      return window.matchMedia('(prefers-color-scheme: dark)').matches
    }

    const dark = ref(readDark())
    watch(dark, (v) => {
      document.documentElement.dataset.theme = v ? 'dark' : 'light'
    }, { immediate: true })

    const toggleTheme = () => {
      dark.value = !dark.value
      try {
        localStorage.setItem(THEME_KEY, dark.value ? 'dark' : 'light')
      } catch (e) { /* storage unavailable */ }
    }

    const onMobileChange = (e) => {
      isMobile.value = e.matches
      if (!e.matches) mobileOpen.value = false
    }

    const onKeydown = (e) => {
      if (e.key === 'Escape') mobileOpen.value = false
    }

    watch(() => route.path, () => {
      mobileOpen.value = false
    })

    onMounted(() => {
      loadTasks()
      isMobile.value = mobileQuery.matches
      mobileQuery.addEventListener('change', onMobileChange)
      document.addEventListener('keydown', onKeydown)
    })

    onUnmounted(() => {
      mobileQuery.removeEventListener('change', onMobileChange)
      document.removeEventListener('keydown', onKeydown)
    })

    return {
      t,
      navItems,
      collapsed,
      mobileOpen,
      isMobile,
      toggleCollapsed,
      dark,
      toggleTheme,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style>
:root {
  --bg: #f8fafc;
  --surface: #ffffff;
  --border: #e2e8f0;
  --text: #0f172a;
  --text-muted: #64748b;
  --accent: #2563eb;
  --accent-soft: #eff6ff;
  --success: #059669;
  --warning: #ea580c;
  --danger: #dc2626;
  --info: #2563eb;
  --surface-2: #f1f5f9;
  --border-soft: #f1f5f9;
  --border-strong: #cbd5e1;
  --text-2: #334155;
  --text-3: #475569;
  --text-faint: #94a3b8;
  --c-green-bg: #d1fae5;
  --c-green-fg: #065f46;
  --c-green-tint: #f0fdf4;
  --c-orange-bg: #fed7aa;
  --c-orange-fg: #92400e;
  --c-amber-tint: #fffbeb;
  --c-red-bg: #fecaca;
  --c-red-bg-2: #fee2e2;
  --c-red-fg: #991b1b;
  --c-red-tint: #fef2f2;
  --c-blue-bg: #dbeafe;
  --c-blue-fg: #1e40af;
  --c-indigo-bg: #e0e7ff;
  --c-indigo-fg: #3730a3;
  --c-violet-tint: #f5f3ff;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;
  --radius-sm: 6px;
  --radius: 10px;
  --radius-lg: 14px;
  --shadow-sm: 0 1px 2px rgb(15 23 42 / 0.05);
  --shadow: 0 1px 3px rgb(15 23 42 / 0.08), 0 1px 2px rgb(15 23 42 / 0.04);
  --sidebar-w: 240px;
  --sidebar-w-collapsed: 68px;
  --topbar-h: 60px;
  --content-max: 1440px;
}

:root[data-theme='dark'] {
  color-scheme: dark;
  --bg: #0b1220;
  --surface: #111827;
  --border: #334155;
  --text: #e2e8f0;
  --text-muted: #94a3b8;
  --accent: #60a5fa;
  --accent-soft: rgb(59 130 246 / 0.18);
  --success: #34d399;
  --warning: #fb923c;
  --danger: #f87171;
  --info: #60a5fa;
  --surface-2: #1e293b;
  --border-soft: #1e293b;
  --border-strong: #475569;
  --text-2: #cbd5e1;
  --text-3: #94a3b8;
  --text-faint: #64748b;
  --c-green-bg: rgb(16 185 129 / 0.2);
  --c-green-fg: #6ee7b7;
  --c-green-tint: rgb(16 185 129 / 0.1);
  --c-orange-bg: rgb(249 115 22 / 0.2);
  --c-orange-fg: #fdba74;
  --c-amber-tint: rgb(245 158 11 / 0.1);
  --c-red-bg: rgb(239 68 68 / 0.2);
  --c-red-bg-2: rgb(239 68 68 / 0.2);
  --c-red-fg: #fca5a5;
  --c-red-tint: rgb(239 68 68 / 0.1);
  --c-blue-bg: rgb(59 130 246 / 0.2);
  --c-blue-fg: #93c5fd;
  --c-indigo-bg: rgb(99 102 241 / 0.2);
  --c-indigo-fg: #a5b4fc;
  --c-violet-tint: rgb(139 92 246 / 0.1);
  --shadow-sm: 0 1px 2px rgb(0 0 0 / 0.4);
  --shadow: 0 1px 3px rgb(0 0 0 / 0.5), 0 1px 2px rgb(0 0 0 / 0.3);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  font-size: 14px;
  background: var(--bg);
  color: var(--text);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Shell */
.app {
  display: grid;
  grid-template-columns: var(--sidebar-w) minmax(0, 1fr);
  min-height: 100vh;
  transition: grid-template-columns 0.2s;
}

.content {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 100vh;
}

/* Sidebar */
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: var(--space-4) var(--space-3);
  min-width: 0;
  overflow-y: auto;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-1) var(--space-2) var(--space-5);
}

.logo-mark {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 16px;
}

.logo-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.logo-text h1 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.025em;
  line-height: 1.2;
}

.subtitle {
  font-size: 12px;
  color: var(--text-muted);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  flex: 1;
}

.nav-link,
.collapse-toggle {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  background: transparent;
  border: 0;
  cursor: pointer;
  font-family: inherit;
  width: 100%;
  text-align: left;
  transition: background-color 0.15s, color 0.15s;
}

.nav-link:hover,
.collapse-toggle:hover {
  background: var(--bg);
  color: var(--text);
}

.nav-link.router-link-active {
  background: var(--accent-soft);
  color: var(--accent);
}

.nav-link.router-link-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 6px;
  bottom: 6px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--accent);
}

.nav-link:focus-visible,
.collapse-toggle:focus-visible,
.hamburger:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.nav-icon {
  flex-shrink: 0;
}

.collapse-toggle {
  margin-top: var(--space-3);
  border-top: 1px solid var(--border);
  border-radius: 0 0 var(--radius-sm) var(--radius-sm);
  padding-top: var(--space-3);
}

.chevron {
  transition: transform 0.2s;
}

/* Topbar */
.topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--topbar-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6);
  background: var(--surface);
  border-bottom: 1px solid var(--border);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-left: auto;
}

.theme-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
}

.theme-toggle:hover {
  background: var(--bg);
}

.theme-toggle:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.hamburger {
  display: none;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
}

.backdrop {
  position: fixed;
  inset: 0;
  z-index: 140;
  background: rgb(15 23 42 / 0.4);
}

/* Desktop and tablet: collapsed sidebar */
@media (min-width: 768px) {
  .app.collapsed {
    grid-template-columns: var(--sidebar-w-collapsed) minmax(0, 1fr);
  }

  .app.collapsed .logo-text,
  .app.collapsed .nav-label {
    position: absolute;
    width: 1px;
    height: 1px;
    margin: -1px;
    padding: 0;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
    border: 0;
  }

  .app.collapsed .sidebar {
    padding-left: var(--space-2);
    padding-right: var(--space-2);
  }

  .app.collapsed .sidebar-logo {
    justify-content: center;
    padding-left: 0;
    padding-right: 0;
  }

  .app.collapsed .nav-link,
  .app.collapsed .collapse-toggle {
    justify-content: center;
    padding-left: 0;
    padding-right: 0;
  }

  .app.collapsed .chevron {
    transform: rotate(180deg);
  }
}

/* Mobile drawer */
@media (max-width: 767px) {
  .app {
    grid-template-columns: minmax(0, 1fr);
  }

  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    z-index: 150;
    width: min(280px, 85vw);
    transform: translateX(-100%);
    transition: transform 0.2s;
  }

  .sidebar.open {
    transform: translateX(0);
  }

  .collapse-toggle {
    display: none;
  }

  .hamburger {
    display: inline-flex;
  }

  .topbar {
    padding: 0 var(--space-4);
  }

  .topbar-actions {
    gap: var(--space-2);
  }

  .topbar .profile-name,
  .topbar .language-label {
    display: none;
  }
}

.main-content {
  flex: 1;
  width: 100%;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: var(--space-6);
}

@media (max-width: 767px) {
  .main-content {
    padding: var(--space-4);
  }
}

.page-header {
  margin-bottom: var(--space-5);
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: var(--space-1);
  letter-spacing: -0.025em;
}

.page-header p {
  color: var(--text-muted);
  font-size: 14px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}

.stat-card {
  background: var(--surface);
  padding: var(--space-5);
  border-radius: var(--radius);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.2s;
}

.stat-card:hover {
  box-shadow: var(--shadow);
}

.stat-label {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.025em;
  font-variant-numeric: tabular-nums;
}

.stat-card.warning .stat-value {
  color: var(--warning);
}

.stat-card.success .stat-value {
  color: var(--success);
}

.stat-card.danger .stat-value {
  color: var(--danger);
}

.stat-card.info .stat-value {
  color: var(--info);
}

.card {
  background: var(--surface);
  border-radius: var(--radius);
  padding: var(--space-5);
  border: 1px solid var(--border);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--border);
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: -0.025em;
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

thead {
  background: var(--bg);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}

th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  font-weight: 600;
  color: var(--text-muted);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

td {
  padding: var(--space-3) var(--space-4);
  border-top: 1px solid var(--border);
  color: var(--text-2);
  font-size: 14px;
}

tbody tr {
  transition: background-color 0.15s ease;
}

tbody tr:hover {
  background: var(--bg);
}

.badge {
  display: inline-block;
  padding: var(--space-1) var(--space-3);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.badge.success { background: var(--c-green-bg); color: var(--c-green-fg); }
.badge.warning { background: var(--c-orange-bg); color: var(--c-orange-fg); }
.badge.danger { background: var(--c-red-bg); color: var(--c-red-fg); }
.badge.info { background: var(--c-blue-bg); color: var(--c-blue-fg); }
.badge.increasing { background: var(--c-green-bg); color: var(--c-green-fg); }
.badge.decreasing { background: var(--c-red-bg); color: var(--c-red-fg); }
.badge.stable { background: var(--c-indigo-bg); color: var(--c-indigo-fg); }
.badge.high { background: var(--c-red-bg); color: var(--c-red-fg); }
.badge.medium { background: var(--c-orange-bg); color: var(--c-orange-fg); }
.badge.low { background: var(--c-blue-bg); color: var(--c-blue-fg); }

.loading {
  text-align: center;
  padding: var(--space-7);
  color: var(--text-muted);
  font-size: 14px;
}

.error {
  background: var(--c-red-tint);
  border: 1px solid var(--c-red-bg);
  color: var(--c-red-fg);
  padding: var(--space-4);
  border-radius: 8px;
  margin: var(--space-4) 0;
  font-size: 14px;
}
</style>
