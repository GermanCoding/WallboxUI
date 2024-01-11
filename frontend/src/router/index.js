import {createRouter, createWebHistory} from 'vue-router'
import ChargeView from '../views/ChargeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/log',
      alias: '/',
      name: 'chargelog',
      component: ChargeView
    },
    {
      path: '/template',
      name: 'template',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../components/Template.vue')
    }
  ]
})

export default router
