// frontend/src/auth.js
const TOKEN_KEY = 'exam_token'
const ROLE_KEY = 'exam_role'
const USER_KEY = 'exam_username'

export function setAuth(token, role, username) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(ROLE_KEY, role)
  localStorage.setItem(USER_KEY, username)
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(ROLE_KEY)
  localStorage.removeItem(USER_KEY)
}

export function getToken() { return localStorage.getItem(TOKEN_KEY) }
export function getRole() { return localStorage.getItem(ROLE_KEY) }
export function getUsername() { return localStorage.getItem(USER_KEY) }
export function isLoggedIn() { return !!getToken() }
export function isTeacher() { return getRole() === 'teacher' }
export function isStudent() { return getRole() === 'student' }
