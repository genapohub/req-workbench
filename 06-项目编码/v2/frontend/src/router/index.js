import { createRouter, createWebHistory } from 'vue-router'
import { session } from '../store/session'

const routes = [
  { path: '/login', name: 'login', component: () => import('../views/Login.vue'), meta: { public: true } },
  { path: '/submit/:projectId', name: 'public-submit', component: () => import('../views/PublicSubmit.vue'), meta: { public: true } },
  { path: '/', redirect: '/overview' },
  { path: '/dashboard', redirect: '/overview' },
  { path: '/overview', name: 'overview', component: () => import('../views/Dashboard.vue') },
  { path: '/projects', name: 'projects', component: () => import('../views/Projects.vue') },
  { path: '/requirements', name: 'requirements', component: () => import('../views/Requirements.vue') },
  { path: '/users', name: 'users', component: () => import('../views/Users.vue') },
  { path: '/audit-logs', name: 'audit-logs', component: () => import('../views/AuditLogs.vue') },
  { path: '/:pathMatch(.*)*', redirect: '/overview' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  if (to.meta.public) return true
  if (!session.user) return { path: '/login', query: { redirect: to.fullPath } }
  return true
})

export default router
