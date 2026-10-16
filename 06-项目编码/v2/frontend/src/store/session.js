import { reactive } from 'vue'

const KEY = 'wb_v2_session'

const session = reactive({
  user: null,
  permissions: [],
  menus: [],
  token: '',
  loaded: false,
})

function load() {
  try {
    const raw = localStorage.getItem(KEY)
    if (raw) {
      const data = JSON.parse(raw)
      session.user = data.user
      session.permissions = data.permissions || []
      session.menus = data.menus || []
      session.token = data.token || ''
    }
  } catch (e) {
    /* ignore */
  }
  session.loaded = true
}

function setSession(data) {
  session.user = data.user
  session.permissions = data.permissions || []
  session.menus = data.menus || []
  session.token = data.token || session.token || ''
  localStorage.setItem(KEY, JSON.stringify({ user: data.user, permissions: session.permissions, menus: session.menus, token: session.token }))
}

function clearSession() {
  session.user = null
  session.permissions = []
  session.menus = []
  session.token = ''
  localStorage.removeItem(KEY)
}

function hasPerm(perm) {
  return session.permissions.includes(perm)
}

load()

export { session, setSession, clearSession, hasPerm, load }
