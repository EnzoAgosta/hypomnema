import { h } from 'vue'
import type { Theme } from 'vitepress'
import DefaultTheme from 'vitepress/theme'
import NotFound from './NotFound.vue'
import Layout from './Layout.vue'
import './style.css'

export default {
  extends: DefaultTheme,
  Layout: () => h(Layout),
  enhanceApp({ app }) {
    // View transitions are handled purely via CSS for simplicity
    // The CSS rules will provide smooth animations when supported
  },
} satisfies Theme
