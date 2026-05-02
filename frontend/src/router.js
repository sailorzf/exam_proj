// frontend/src/router.js
import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, isTeacher, isStudent } from './auth'

const routes = [
  { path: '/login', component: () => import('./views/Login.vue') },
  {
    path: '/teacher', component: () => import('./components/NavBar.vue'),
    meta: { requiresAuth: true, role: 'teacher' },
    children: [
      { path: '', redirect: '/teacher/questions' },
      { path: 'questions', component: () => import('./views/teacher/QuestionBank.vue') },
      { path: 'papers', component: () => import('./views/teacher/PaperBuilder.vue') },
      { path: 'exams', component: () => import('./views/teacher/ExamManager.vue') },
      { path: 'submissions', component: () => import('./views/teacher/Submissions.vue') },
      { path: 'submissions/grade/:id', component: () => import('./views/teacher/Grading.vue') },
      { path: 'grades', component: () => import('./views/teacher/Grades.vue') },
      { path: 'admin', component: () => import('./views/admin/Users.vue') },
    ],
  },
  {
    path: '/student', component: () => import('./components/NavBar.vue'),
    meta: { requiresAuth: true, role: 'student' },
    children: [
      { path: '', redirect: '/student/exams' },
      { path: 'exams', component: () => import('./views/student/ExamList.vue') },
      { path: 'exam/:id', component: () => import('./views/student/ExamView.vue') },
      { path: 'results', component: () => import('./views/student/Results.vue') },
    ],
  },
  { path: '/', redirect: '/login' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !isLoggedIn()) return '/login'
  if (to.meta.role === 'teacher' && !isTeacher()) return '/login'
  if (to.meta.role === 'student' && !isStudent()) return '/login'
})

export default router
