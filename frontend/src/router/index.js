import { createRouter, createWebHistory } from 'vue-router'

const Login = () => import('../views/Login.vue')
const Dashboard = () => import('../views/Dashboard.vue')
const DocsList = () => import('../views/DocsList.vue')
const DocReader = () => import('../views/DocReader.vue')
const Glossary = () => import('../views/Glossary.vue')
const Favorites = () => import('../views/Favorites.vue')
const Settings = () => import('../views/Settings.vue')

const routes = [
  { path: '/login', name: 'Login', component: Login },
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/docs', name: 'DocsList', component: DocsList },
  { path: '/docs/:id/read', name: 'DocReader', component: DocReader, props: true },
  { path: '/glossary', name: 'Glossary', component: Glossary },
  { path: '/favorites', name: 'Favorites', component: Favorites },
  { path: '/settings', name: 'Settings', component: Settings },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router

