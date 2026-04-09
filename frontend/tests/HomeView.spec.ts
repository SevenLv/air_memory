import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHashHistory } from 'vue-router'
import ElementPlus from 'element-plus'
import HomeView from '../src/views/HomeView.vue'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [{ path: '/', component: HomeView }],
})

describe('HomeView', () => {
  it('可以正常挂载', async () => {
    const wrapper = mount(HomeView, {
      global: {
        plugins: [router, ElementPlus],
      },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('显示欢迎内容', async () => {
    const wrapper = mount(HomeView, {
      global: {
        plugins: [router, ElementPlus],
      },
    })
    expect(wrapper.text()).toContain('AIR Memory')
  })
})
