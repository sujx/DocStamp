<template>
  <div
    class="clock-container"
    role="timer"
    :aria-label="`${$t('common.currentTime')} ${time.hours}:${time.minutes}:${time.seconds}`"
  >
    <div class="digit-group">
      <div class="digit">
        <span v-for="i in 7" :key="'h1-'+i" class="seg" :class="{ on: segs(time.hours[0]).includes(i) }" />
      </div>
      <div class="digit">
        <span v-for="i in 7" :key="'h2-'+i" class="seg" :class="{ on: segs(time.hours[1]).includes(i) }" />
      </div>
    </div>

    <div class="colon" aria-hidden="true" />

    <div class="digit-group">
      <div class="digit">
        <span v-for="i in 7" :key="'m1-'+i" class="seg" :class="{ on: segs(time.minutes[0]).includes(i) }" />
      </div>
      <div class="digit">
        <span v-for="i in 7" :key="'m2-'+i" class="seg" :class="{ on: segs(time.minutes[1]).includes(i) }" />
      </div>
    </div>

    <div class="colon" aria-hidden="true" />

    <div class="digit-group">
      <div class="digit">
        <span v-for="i in 7" :key="'s1-'+i" class="seg" :class="{ on: segs(time.seconds[0]).includes(i) }" />
      </div>
      <div class="digit">
        <span v-for="i in 7" :key="'s2-'+i" class="seg" :class="{ on: segs(time.seconds[1]).includes(i) }" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  digitColor?: string
  offColor?: string
  glowColor?: string
}>(), {
  digitColor: 'var(--color-brand-700)',
  offColor: 'var(--color-border-default)',
  glowColor: 'rgba(0,138,61,0.25)',
});

const time = ref({ hours: '00', minutes: '00', seconds: '00' });

// 7-segment patterns: segments 1-7 (top, upper-right, lower-right, bottom, lower-left, upper-left, middle)
const patterns: Record<number, number[]> = {
  0: [1,2,3,4,5,6],
  1: [2,3],
  2: [1,2,7,5,4],
  3: [1,2,7,3,4],
  4: [6,7,2,3],
  5: [1,6,7,3,4],
  6: [1,3,4,5,6,7],
  7: [1,2,3],
  8: [1,2,3,4,5,6,7],
  9: [1,2,3,4,6,7],
};

function segs(d: string): number[] {
  const n = parseInt(d);
  return isNaN(n) ? [] : patterns[n];
}

let timer: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
  timer = setInterval(() => {
    const now = new Date();
    time.value = {
      hours: String(now.getHours()).padStart(2, '0'),
      minutes: String(now.getMinutes()).padStart(2, '0'),
      seconds: String(now.getSeconds()).padStart(2, '0'),
    };
  }, 1000);
});

onUnmounted(() => { if (timer) clearInterval(timer); });
</script>

<style scoped>
.clock-container {
  display: inline-flex;
  align-items: center;
  gap: 0;
  padding: clamp(0.5rem, 2vw, 0.875rem) clamp(1rem, 4vw, 1.75rem);
  border-radius: var(--radius-lg, 14px);
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
  max-width: min(100%, 28rem);
}

.digit-group { display: flex; gap: clamp(1px, 0.5vw, 4px); }

/* Each digit container — responsive via rem */
.digit {
  position: relative;
  width: clamp(2.25rem, 5vw, 3.375rem);
  height: clamp(3.75rem, 9vw, 6rem);
  margin: 0 clamp(0px, 0.25vw, 2px);
}

/* Segment base — off state, warm beige */
.seg {
  position: absolute;
  border-radius: clamp(2px, 0.4vw, 4px);
  background: v-bind(offColor);
  opacity: 0.5;
  transition: opacity 0.1s ease, background 0.15s ease;
}

/* Active segment — brand green */
.seg.on {
  background: v-bind(digitColor);
  opacity: 1;
  box-shadow: 0 0 clamp(2px, 0.5vw, 6px) v-bind(glowColor);
}

/* Segment 1: top horizontal */
.seg:nth-child(1) {
  top: 3%; left: 18%; right: 18%; height: 7%;
}
/* Segment 2: upper-right vertical */
.seg:nth-child(2),
.seg:nth-child(3) {
  top: 12%; right: 3%; width: 13%; height: 37%;
}
/* Segment 3: lower-right vertical */
.seg:nth-child(3) {
  top: auto; bottom: 12%;
}
/* Segment 4: bottom horizontal */
.seg:nth-child(4) {
  bottom: 3%; left: 18%; right: 18%; height: 7%;
}
/* Segment 5: lower-left vertical */
.seg:nth-child(5),
.seg:nth-child(6) {
  bottom: 12%; left: 3%; width: 13%; height: 37%;
}
/* Segment 6: upper-left vertical */
.seg:nth-child(6) {
  bottom: auto; top: 12%;
}
/* Segment 7: middle horizontal */
.seg:nth-child(7) {
  top: 50%; left: 18%; right: 18%; height: 7%;
  transform: translateY(-50%);
}

/* Colon separator: responsive sizing */
.colon {
  width: clamp(6px, 1.2vw, 12px);
  height: clamp(18px, 3.5vw, 36px);
  position: relative;
  margin: 0 clamp(3px, 0.6vw, 6px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: clamp(8px, 1.5vw, 16px);
}
.colon::before,
.colon::after {
  content: '';
  width: clamp(4px, 0.8vw, 8px);
  height: clamp(4px, 0.8vw, 8px);
  border-radius: 50%;
  background: v-bind(digitColor);
  animation: colon-blink 1s step-end infinite;
}
.colon::after { animation-delay: 0.5s; }

@keyframes colon-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .seg { opacity: 0.3; }
  .seg.on { opacity: 1; }
}
</style>
