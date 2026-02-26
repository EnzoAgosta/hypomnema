import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Hypomnema',
  description: 'A Python library for reading and writing TMX translation memory files',
  
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
    ['meta', { name: 'theme-color', content: '#faf9f6' }],
    ['meta', { name: 'og:type', content: 'website' }],
    ['meta', { name: 'og:title', content: 'Hypomnema | TMX for Python' }],
    ['meta', { name: 'og:description', content: 'Type-safe, policy-driven, zero-dependency TMX 1.4b library' }],
    ['meta', { name: 'og:image', content: '/og-image.svg' }],
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
  ],
  
  locales: {
    en: {
      label: 'English',
      lang: 'en',
      themeConfig: {
        nav: [
          { text: 'Tutorial', link: '/en/tutorial/' },
          { text: 'Cookbook', link: '/en/cookbook/' },
          { text: 'API Reference', link: '/en/api/' },
          { text: 'Advanced', link: '/en/advanced/' },
        ],
        sidebar: {
          '/en/tutorial/': [
            {
              text: 'Tutorial',
              items: [
                { text: 'Introduction', link: '/en/tutorial/' },
                { text: 'Installation', link: '/en/tutorial/01-installation' },
                { text: 'Your First TMX', link: '/en/tutorial/02-your-first-tmx' },
                { text: 'Creating TMX Files', link: '/en/tutorial/03-creating-tmx' },
                { text: 'Working with Variants', link: '/en/tutorial/04-working-with-variants' },
                { text: 'Inline Markup', link: '/en/tutorial/05-inline-markup' },
                { text: 'Saving Files', link: '/en/tutorial/06-saving-files' },
                { text: 'Streaming Large Files', link: '/en/tutorial/07-streaming' },
                { text: 'Error Handling', link: '/en/tutorial/08-error-handling' },
                { text: 'Backends', link: '/en/tutorial/09-backends' },
              ],
            },
          ],
          '/en/cookbook/': [
            {
              text: 'Cookbook',
              items: [
                { text: 'Introduction', link: '/en/cookbook/' },
                { text: 'CSV to TMX', link: '/en/cookbook/csv-to-tmx' },
                { text: 'TMX Statistics', link: '/en/cookbook/tmx-statistics' },
                { text: 'Merge TMX Files', link: '/en/cookbook/merge-tmx-files' },
                { text: 'Split by Language', link: '/en/cookbook/split-tmx-by-language' },
                { text: 'Filter by Date', link: '/en/cookbook/filter-by-date' },
                { text: 'Extract Plain Text', link: '/en/cookbook/extract-plain-text' },
                { text: 'Validate TMX', link: '/en/cookbook/validate-tmx' },
                { text: 'Convert Between Tools', link: '/en/cookbook/convert-between-tools' },
              ],
            },
          ],
          '/en/api/': [
            {
              text: 'API Reference',
              items: [
                { text: 'Overview', link: '/en/api/' },
                { text: 'Core (load/dump)', link: '/en/api/core' },
                { text: 'Helpers', link: '/en/api/helpers' },
              ],
            },
            {
              text: 'Types',
              collapsed: false,
              items: [
                { text: 'Overview', link: '/en/api/types/' },
                { text: 'Tmx', link: '/en/api/types/tmx' },
                { text: 'Header', link: '/en/api/types/header' },
                { text: 'Tu', link: '/en/api/types/tu' },
                { text: 'Tuv', link: '/en/api/types/tuv' },
                { text: 'Prop', link: '/en/api/types/prop' },
                { text: 'Note', link: '/en/api/types/note' },
                { text: 'Enums', link: '/en/api/types/enums' },
                {
                  text: 'Inline Elements',
                  collapsed: true,
                  items: [
                    { text: 'Overview', link: '/en/api/types/inline/' },
                    { text: 'Bpt', link: '/en/api/types/inline/bpt' },
                    { text: 'Ept', link: '/en/api/types/inline/ept' },
                    { text: 'It', link: '/en/api/types/inline/it' },
                    { text: 'Ph', link: '/en/api/types/inline/ph' },
                    { text: 'Hi', link: '/en/api/types/inline/hi' },
                    { text: 'Sub', link: '/en/api/types/inline/sub' },
                  ],
                },
              ],
            },
            {
              text: 'Policy',
              collapsed: true,
              items: [
                { text: 'Overview', link: '/en/api/policy/' },
                { text: 'Deserialization', link: '/en/api/policy/deserialization' },
                { text: 'Serialization', link: '/en/api/policy/serialization' },
              ],
            },
            {
              text: 'Backends',
              collapsed: true,
              items: [
                { text: 'Overview', link: '/en/api/backends/' },
                { text: 'Standard', link: '/en/api/backends/standard' },
                { text: 'Lxml', link: '/en/api/backends/lxml' },
              ],
            },
            { text: 'Errors', link: '/en/api/errors' },
          ],
          '/en/advanced/': [
            {
              text: 'Advanced',
              items: [
                { text: 'Introduction', link: '/en/advanced/' },
                { text: 'Duck Typing', link: '/en/advanced/duck-typing' },
                { text: 'Custom Handlers', link: '/en/advanced/custom-handlers' },
                { text: 'Custom Backends', link: '/en/advanced/custom-backends' },
                { text: 'Namespaces', link: '/en/advanced/namespaces' },
              ],
            },
          ],
        },
        editLink: {
          pattern: 'https://github.com/anomalyco/hypomnema/edit/main/docs/:path',
          text: 'Edit this page on GitHub',
        },
      },
    },
    fr: {
      label: 'Français',
      lang: 'fr',
      link: '/fr/',
      themeConfig: {
        nav: [
          { text: 'Tutoriel', link: '/fr/tutorial/' },
          { text: 'Recettes', link: '/fr/cookbook/' },
          { text: 'API', link: '/fr/api/' },
          { text: 'Avancé', link: '/fr/advanced/' },
        ],
      },
    },
    es: {
      label: 'Español',
      lang: 'es',
      link: '/es/',
      themeConfig: {
        nav: [
          { text: 'Tutorial', link: '/es/tutorial/' },
          { text: 'Recetas', link: '/es/cookbook/' },
          { text: 'API', link: '/es/api/' },
          { text: 'Avanzado', link: '/es/advanced/' },
        ],
      },
    },
  },

  themeConfig: {
    logo: '/logo.svg',
    socialLinks: [
      { icon: 'github', link: 'https://github.com/anomalyco/hypomnema' },
    ],
    search: {
      provider: 'local',
    },
  },
})
