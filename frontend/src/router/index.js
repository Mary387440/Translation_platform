import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const Login = () => import('../views/Login.vue')
const ReaderLayout = () => import('../layouts/ReaderLayout.vue')
const AdminLayout = () => import('../layouts/AdminLayout.vue')
const BookStore = () => import('../views/reader/BookStore.vue')
const WorkReader = () => import('../views/WorkReader.vue')
const WorksManage = () => import('../views/admin/WorksManage.vue')
const Dashboard = () => import('../views/Dashboard.vue')
const DocsList = () => import('../views/DocsList.vue')
const DocReader = () => import('../views/DocReader.vue')
const OcrTool = () => import('../views/OcrTool.vue')
const Evaluations = () => import('../views/admin/Evaluations.vue')
const Datasets = () => import('../views/Datasets.vue')
const Glossary = () => import('../views/Glossary.vue')
const Favorites = () => import('../views/Favorites.vue')
const Settings = () => import('../views/Settings.vue')
const Discussion = () => import('../views/Discussion.vue')
const DiscussionDetail = () => import('../views/DiscussionDetail.vue')
const AdminDiscussionManage = () => import('../views/admin/DiscussionManage.vue')
const Home = () => import('../views/Home.vue')

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { public: true },
  },
  {
    path: '/',
    component: ReaderLayout,
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/home' },
      { path: 'home', name: 'Home', component: Home },
      { path: 'books', name: 'BookStore', component: BookStore },
      {
        path: 'books/:workId/chapter/:chapterId',
        name: 'ReaderWorkReader',
        component: WorkReader,
        meta: { mode: 'reader' },
        props: true,
      },
      { path: 'favorites', name: 'Favorites', component: Favorites },
      { path: 'discussions', name: 'Discussions', component: Discussion },
      { path: 'discussions/:id', name: 'DiscussionDetail', component: DiscussionDetail, props: true },
      { path: 'settings', name: 'ReaderSettings', component: Settings },
    ],
  },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', name: 'AdminDashboard', component: Dashboard },
      { path: 'works', name: 'AdminWorks', component: WorksManage },
      {
        path: 'works/:workId/chapter/:chapterId',
        name: 'AdminWorkReader',
        component: WorkReader,
        meta: { mode: 'admin' },
        props: true,
      },
      { path: 'datasets', name: 'AdminDatasets', component: Datasets },
      { path: 'glossary', name: 'AdminGlossary', component: Glossary },
      { path: 'docs', name: 'AdminDocs', component: DocsList },
      {
        path: 'docs/:id/read',
        name: 'AdminDocReader',
        component: DocReader,
        props: true,
      },
      { path: 'ocr', name: 'AdminOcr', component: OcrTool },
      { path: 'evals', name: 'AdminEvals', component: Evaluations },
      { path: 'discussions', name: 'AdminDiscussions', component: AdminDiscussionManage },
      { path: 'settings', name: 'AdminSettings', component: Settings },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Vue Router 4 推荐：直接 return 目标，不再使用 next 回调
router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    return true
  }

  if (to.meta.requiresAuth && !auth.token) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (to.meta.requiresAdmin && auth.user?.role !== 'admin') {
    return '/books'
  }

  return true
})

export default router
