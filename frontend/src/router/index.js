import {createRouter, createWebHistory} from 'vue-router'
import ChargeView from '../views/ChargeView.vue'
import StatusView from '../views/StatusView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/log',
      name: 'chargelog',
      component: ChargeView
    },
    {
      path: '/status',
      alias: '/',
      name: 'status',
      component: StatusView
    }
  ]
})

export default router
