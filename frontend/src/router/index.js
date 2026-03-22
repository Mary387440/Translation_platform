import { createRouter, createWebHistory } from 'vue-router'

const Login = () => import('../views/Login.vue')
const Dashboard = () => import('../views/Dashboard.vue')
const Works = () => import('../views/Works.vue')
const WorkReader = () => import('../views/WorkReader.vue')
const DocsList = () => import('../views/DocsList.vue')
const DocReader = () => import('../views/DocReader.vue')
const OcrTool = () => import('../views/OcrTool.vue')
const Datasets = () => import('../views/Datasets.vue')
const Glossary = () => import('../views/Glossary.vue')
const Favorites = () => import('../views/Favorites.vue')
const Settings = () => import('../views/Settings.vue')

const routes = [
  { path: '/login', name: 'Login', component: Login },
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/works', name: 'Works', component: Works },
  {
    path: '/works/:workId/chapter/:chapterId',
    name: 'WorkReader',
    component: WorkReader,
    props: true,
  },
  { path: '/ocr', name: 'OcrTool', component: OcrTool },
  { path: '/docs', name: 'DocsList', component: DocsList },
  { path: '/docs/:id/read', name: 'DocReader', component: DocReader, props: true },
  { path: '/datasets', name: 'Datasets', component: Datasets },
  { path: '/glossary', name: 'Glossary', component: Glossary },
  { path: '/favorites', name: 'Favorites', component: Favorites },
  { path: '/settings', name: 'Settings', component: Settings },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

