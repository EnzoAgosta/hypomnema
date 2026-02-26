<script setup lang="ts">
import DefaultTheme from 'vitepress/theme'
import { onMounted, ref } from 'vue'
import NotFound from './NotFound.vue'

const { Layout } = DefaultTheme

const mounted = ref(false)

onMounted(() => {
  mounted.value = true
})

</script>

<template>
  <Layout>
    <template #not-found>
      <NotFound />
    </template>

    <template #home-hero-before>
      <div class="zen-background" v-if="mounted">
        <div class="bamboo-lines">
          <span class="line"></span>
          <span class="line"></span>
          <span class="line"></span>
        </div>
      </div>
    </template>

  </Layout>
</template>

<style scoped>
.zen-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
}

.bamboo-lines {
  position: absolute;
  left: 8%;
  top: 20%;
  height: 60%;
  display: flex;
  gap: 1.5rem;
  opacity: 0;
  animation: bambooAppear 1s ease-out 0.5s forwards;
}

.bamboo-lines .line {
  width: 3px;
  height: 100%;
  background: linear-gradient(to bottom,
      transparent,
      var(--zen-matcha) 20%,
      var(--zen-matcha) 80%,
      transparent);
  opacity: 0.15;
}

.bamboo-lines .line:nth-child(2) {
  height: 80%;
  opacity: 0.1;
}

.bamboo-lines .line:nth-child(3) {
  height: 60%;
  opacity: 0.08;
}

@keyframes bambooAppear {
  to {
    opacity: 1;
  }
}

@keyframes dotAppear {
  to {
    opacity: 0.4;
  }
}


/* Responsive */
@media (max-width: 960px) {
  .bamboo-lines {
    display: none;
  }
}
</style>
