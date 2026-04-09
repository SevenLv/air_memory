import { createRouter, createWebHashHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import MemoriesView from '../views/MemoriesView.vue'
import LogsView from '../views/LogsView.vue'
import FeedbackView from '../views/FeedbackView.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/memories',
      name: 'memories',
      component: MemoriesView,
    },
    {
      path: '/logs',
      name: 'logs',
      component: LogsView,
    },
    {
      path: '/feedback',
      name: 'feedback',
      component: FeedbackView,
    },
  ],
})

export default router
