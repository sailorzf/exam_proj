// frontend/src/auth.js
const TOKEN_KEY = 'exam_token'
const ROLE_KEY = 'exam_role'
const USER_KEY = 'exam_username'
const ADMIN_KEY = 'exam_is_admin'

export function setAuth(token, role, username, isAdmin = false) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(ROLE_KEY, role)
  localStorage.setItem(USER_KEY, username)
  localStorage.setItem(ADMIN_KEY, String(isAdmin))
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(ROLE_KEY)
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(ADMIN_KEY)
}

export function getToken() { return localStorage.getItem(TOKEN_KEY) }
export function getRole() { return localStorage.getItem(ROLE_KEY) }
export function getUsername() { return localStorage.getItem(USER_KEY) }
export function isAdmin() { return localStorage.getItem(ADMIN_KEY) === 'true' }
export function isLoggedIn() { return !!getToken() }
export function isTeacher() { return getRole() === 'teacher' }
export function isStudent() { return getRole() === 'student' }
