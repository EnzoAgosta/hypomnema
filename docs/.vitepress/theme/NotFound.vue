<script setup lang="ts">
import { useData } from 'vitepress'
import { ref, onMounted } from 'vue'

const { lang } = useData()
const mounted = ref(false)

onMounted(() => {
  mounted.value = true
})
</script>

<template>
  <div class="not-found">
    <div class="content" v-if="mounted">
      <!-- Enso circle with 404 inside -->
      <div class="enso-container">
        <svg class="enso" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
          <circle 
            cx="100" 
            cy="100" 
            r="75" 
            fill="none" 
            stroke="currentColor"
            stroke-width="6"
            stroke-linecap="round"
            stroke-dasharray="380 471"
            transform="rotate(-40 100 100)"
          />
        </svg>
        <span class="error-number">404</span>
      </div>
      
      <!-- Vertical separator -->
      <div class="separator"></div>
      
      <!-- Message - haiku-like brevity -->
      <div class="message">
        <p class="main" v-if="lang === 'en'">
          The path you seek<br/>
          does not exist here
        </p>
        <p class="main" v-else-if="lang === 'fr'">
          Le chemin que vous cherchez<br/>
          n'existe pas ici
        </p>
        <p class="main" v-else-if="lang === 'es'">
          El camino que buscas<br/>
          no existe aquí
        </p>
        <p class="main" v-else>
          The path you seek<br/>
          does not exist here
        </p>
        
        <p class="sub" v-if="lang !== 'en'">
          This page awaits translation
        </p>
      </div>
      
      <!-- Action -->
      <a href="/en/" class="action">
        <span class="action-text">Return</span>
        <svg class="arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
      </a>
    </div>
    
    <!-- Subtle decorative elements -->
    <div class="decoration left-line"></div>
    <div class="decoration right-line"></div>
    <div class="decoration ink-mark"></div>
  </div>
</template>

<style scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--zen-space-lg, 4rem);
  position: relative;
  overflow: hidden;
  background: var(--zen-washi, #faf9f6);
}

.dark .not-found {
  background: var(--vp-c-bg);
}

/* Content container */
.content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  max-width: 400px;
  position: relative;
  z-index: 1;
  animation: contentAppear 0.8s ease-out;
}

@keyframes contentAppear {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Enso circle container */
.enso-container {
  position: relative;
  width: 180px;
  height: 180px;
  margin-bottom: var(--zen-space-md, 2rem);
}

.enso {
  width: 100%;
  height: 100%;
  color: var(--zen-matcha, #6b8e4e);
  opacity: 0.7;
}

.dark .enso {
  color: var(--zen-matcha-light, #8fb06a);
}

.error-number {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-family: var(--zen-font-display, 'Cormorant Garamond', serif);
  font-size: 2.5rem;
  font-weight: 300;
  color: var(--zen-ink, #1a1a18);
  letter-spacing: 0.1em;
}

.dark .error-number {
  color: #f0f0f0;
}

/* Separator */
.separator {
  width: 1px;
  height: 40px;
  background: var(--zen-matcha, #6b8e4e);
  opacity: 0.3;
  margin-bottom: var(--zen-space-md, 2rem);
}

.dark .separator {
  background: var(--zen-matcha-light, #8fb06a);
}

/* Message */
.message {
  margin-bottom: var(--zen-space-md, 2rem);
}

.message .main {
  font-family: var(--zen-font-display, 'Cormorant Garamond', serif);
  font-size: 1.375rem;
  font-weight: 400;
  line-height: 1.8;
  color: var(--zen-ink, #1a1a18);
  letter-spacing: 0.02em;
  margin: 0;
}

.dark .message .main {
  color: #f0f0f0;
}

.message .sub {
  font-family: var(--vp-font-family-base, sans-serif);
  font-size: 0.875rem;
  font-weight: 300;
  color: var(--zen-ink-muted, #6a6a68);
  margin-top: var(--zen-space-sm, 1rem);
  letter-spacing: 0.05em;
}

.dark .message .sub {
  color: var(--vp-c-text-3);
}

/* Action */
.action {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.625rem 1.25rem;
  font-family: var(--vp-font-family-base, sans-serif);
  font-size: 0.8125rem;
  font-weight: 400;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--zen-matcha, #6b8e4e);
  text-decoration: none;
  border: 1px solid var(--zen-matcha);
  border-radius: 0;
  transition: all 0.3s ease;
}

.dark .action {
  color: var(--zen-matcha-light, #8fb06a);
  border-color: var(--zen-matcha-light, #8fb06a);
}

.action:hover {
  background: var(--zen-matcha);
  color: var(--zen-washi, #faf9f6);
}

.dark .action:hover {
  background: var(--zen-matcha-light);
  color: var(--vp-c-bg);
}

.action .arrow {
  width: 16px;
  height: 16px;
  transition: transform 0.3s ease;
}

.action:hover .arrow {
  transform: translateX(-4px);
}

/* Decorative elements */
.decoration {
  position: absolute;
  pointer-events: none;
}

.left-line,
.right-line {
  width: 1px;
  height: 100px;
  background: var(--zen-matcha, #6b8e4e);
  opacity: 0;
  animation: lineAppear 1s ease-out forwards;
}

.left-line {
  left: 10%;
  top: 20%;
  animation-delay: 0.5s;
}

.right-line {
  right: 10%;
  bottom: 20%;
  height: 150px;
  animation-delay: 0.7s;
}

.dark .left-line,
.dark .right-line {
  background: var(--zen-matcha-light, #8fb06a);
}

@keyframes lineAppear {
  to { opacity: 0.15; }
}

.ink-mark {
  width: 8px;
  height: 8px;
  background: var(--zen-matcha, #6b8e4e);
  border-radius: 50%;
  bottom: 15%;
  left: 15%;
  opacity: 0;
  animation: markAppear 0.5s ease-out 1s forwards;
}

.dark .ink-mark {
  background: var(--zen-matcha-light, #8fb06a);
}

@keyframes markAppear {
  to { opacity: 0.3; }
}

/* Responsive */
@media (max-width: 640px) {
  .not-found {
    padding: var(--zen-space-md, 2rem);
  }
  
  .enso-container {
    width: 140px;
    height: 140px;
  }
  
  .error-number {
    font-size: 2rem;
  }
  
  .message .main {
    font-size: 1.125rem;
  }
  
  .decoration {
    display: none;
  }
}
</style>
