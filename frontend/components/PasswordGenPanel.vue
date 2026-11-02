<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Random Password Card -->
    <UCard>
      <template #header>
        <div>
          <h2 class="text-lg font-semibold text-text-primary">{{ $t('passwordGen.random.title') }}</h2>
          <p class="text-sm text-text-secondary mt-1">{{ $t('passwordGen.random.desc') }}</p>
        </div>
      </template>

      <!-- Length slider -->
      <UFormGroup :label="$t('passwordGen.random.length')" class="mb-5">
        <div class="flex items-center gap-3">
          <URange v-model="randomLength" :min="8" :max="64" class="flex-1" />
          <span class="min-w-[40px] text-center text-brand-700 font-semibold">{{ randomLength }}</span>
        </div>
      </UFormGroup>

      <!-- Character types -->
      <UFormGroup :label="$t('passwordGen.random.charTypes')" class="mb-5">
        <div class="grid grid-cols-2 gap-2">
          <label
            v-for="type in charTypes"
            :key="type.key"
            class="toggle-item"
            :class="{ active: randomClasses[type.key] }"
          >
            <UCheckbox v-model="randomClasses[type.key]" />
            <span class="text-sm">{{ $t(`passwordGen.random.${type.key}`) }}</span>
          </label>
        </div>
      </UFormGroup>

      <!-- Exclude ambiguous -->
      <UFormGroup class="mb-5">
        <label class="toggle-item">
          <UCheckbox v-model="randomExcludeAmbiguous" />
          <span class="text-sm">{{ $t('passwordGen.random.excludeAmbiguous') }}</span>
        </label>
      </UFormGroup>

      <!-- Count slider -->
      <UFormGroup :label="$t('passwordGen.random.count')" class="mb-5">
        <div class="flex items-center gap-3">
          <URange v-model="randomCount" :min="1" :max="20" class="flex-1" />
          <span class="min-w-[40px] text-center text-brand-700 font-semibold">{{ randomCount }}</span>
        </div>
      </UFormGroup>

      <!-- Buttons -->
      <div class="flex gap-3">
        <UButton color="primary" @click="generateRandom">{{ $t('passwordGen.random.generate') }}</UButton>
        <UButton color="neutral" variant="outline" @click="clearRandom">{{ $t('passwordGen.random.clear') }}</UButton>
      </div>

      <!-- Results -->
      <div class="mt-6">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium text-text-primary">{{ $t('passwordGen.random.result') }}</span>
          <UBadge v-if="entropy > 0" color="primary" variant="soft">{{ entropy.toFixed(1) }} bit</UBadge>
        </div>

        <div v-if="randomPasswords.length === 0" class="empty-state">
          {{ $t('passwordGen.random.empty') }}
        </div>

        <div v-else class="space-y-2">
          <div v-for="(pwd, idx) in randomPasswords" :key="idx" class="password-item">
            <span class="password-text">{{ pwd }}</span>
            <UButton size="xs" variant="ghost" @click="copyPassword(pwd, idx)">
              {{ copiedIdx === idx ? $t('passwordGen.common.copied') : $t('passwordGen.common.copy') }}
            </UButton>
          </div>
        </div>
      </div>
    </UCard>

    <!-- Deterministic Password Card -->
    <UCard>
      <template #header>
        <div>
          <h2 class="text-lg font-semibold text-text-primary">{{ $t('passwordGen.deterministic.title') }}</h2>
          <p class="text-sm text-text-secondary mt-1">{{ $t('passwordGen.deterministic.desc') }}</p>
        </div>
      </template>

      <!-- Variable name -->
      <UFormGroup :label="$t('passwordGen.deterministic.name')" class="mb-5">
        <UInput v-model="detName" :placeholder="$t('passwordGen.deterministic.namePlaceholder')" />
      </UFormGroup>

      <!-- Salt with visibility toggle -->
      <UFormGroup :label="$t('passwordGen.deterministic.salt')" class="mb-5">
        <div class="relative">
          <UInput
            v-model="detSalt"
            :type="saltVisible ? 'text' : 'password'"
            :placeholder="$t('passwordGen.deterministic.saltPlaceholder')"
            class="pr-11"
          />
          <button
            type="button"
            class="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded hover:bg-muted transition-colors duration-150"
            :aria-label="$t('passwordGen.deterministic.toggleVisibility')"
            @click="saltVisible = !saltVisible"
          >
            <UIcon
              :name="saltVisible ? 'i-heroicons-eye-slash' : 'i-heroicons-eye'"
              class="w-5 h-5 text-text-tertiary"
            />
          </button>
        </div>
      </UFormGroup>

      <!-- Length slider -->
      <UFormGroup :label="$t('passwordGen.deterministic.length')" class="mb-5">
        <div class="flex items-center gap-3">
          <URange v-model="detLength" :min="8" :max="128" class="flex-1" />
          <span class="min-w-[40px] text-center text-brand-700 font-semibold">{{ detLength }}</span>
        </div>
      </UFormGroup>

      <!-- Character types -->
      <UFormGroup :label="$t('passwordGen.deterministic.charTypes')" class="mb-5">
        <div class="grid grid-cols-2 gap-2">
          <label
            v-for="type in charTypes"
            :key="type.key"
            class="toggle-item"
            :class="{ active: detClasses[type.key] }"
          >
            <UCheckbox v-model="detClasses[type.key]" />
            <span class="text-sm">{{ $t(`passwordGen.deterministic.${type.key}`) }}</span>
          </label>
        </div>
      </UFormGroup>

      <!-- Exclude ambiguous -->
      <UFormGroup class="mb-5">
        <label class="toggle-item">
          <UCheckbox v-model="detExcludeAmbiguous" />
          <span class="text-sm">{{ $t('passwordGen.deterministic.excludeAmbiguous') }}</span>
        </label>
      </UFormGroup>

      <!-- Buttons -->
      <div class="flex gap-3">
        <UButton color="primary" :loading="detGenerating" @click="generateDeterministic">
          {{ $t('passwordGen.deterministic.generate') }}
        </UButton>
        <UButton color="neutral" variant="outline" @click="clearDeterministic">
          {{ $t('passwordGen.deterministic.clear') }}
        </UButton>
      </div>

      <!-- Results -->
      <div class="mt-6">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium text-text-primary">{{ $t('passwordGen.deterministic.result') }}</span>
        </div>

        <div v-if="!detPassword" class="empty-state">
          {{ $t('passwordGen.deterministic.empty') }}
        </div>

        <div v-else class="password-item">
          <span class="password-text">{{ detPassword }}</span>
          <UButton size="xs" variant="ghost" @click="copyPassword(detPassword, 'det')">
            {{ copiedIdx === 'det' ? $t('passwordGen.common.copied') : $t('passwordGen.common.copy') }}
          </UButton>
        </div>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import {
  buildPool,
  calculateEntropy,
  generateRandomPassword,
  generateDeterministicPassword
} from '~/composables/usePasswordGen';

const { t } = useI18n();
const toast = useToast();

// Random password state
const randomLength = ref(20);
const randomCount = ref(5);
const randomClasses = ref({
  uppercase: true,
  lowercase: true,
  digits: true,
  symbols: true
});
const randomExcludeAmbiguous = ref(false);
const randomPasswords = ref<string[]>([]);
const copiedIdx = ref<number | 'det' | null>(null);

// Computed entropy for random password
const entropy = computed(() => {
  const pool = buildPool({
    ...randomClasses.value,
    excludeAmbiguous: randomExcludeAmbiguous.value
  });
  return calculateEntropy(randomLength.value, pool.length);
});

// Deterministic password state
const detName = ref('');
const detSalt = ref('');
const detLength = ref(50);
const detClasses = ref({
  uppercase: true,
  lowercase: true,
  digits: true,
  symbols: true
});
const detExcludeAmbiguous = ref(false);
const detPassword = ref<string | null>(null);
const detGenerating = ref(false);
const saltVisible = ref(false);

// Character type definitions
const charTypes = [
  { key: 'uppercase' },
  { key: 'lowercase' },
  { key: 'digits' },
  { key: 'symbols' }
];

// Generate random passwords
function generateRandom() {
  const pool = buildPool({
    ...randomClasses.value,
    excludeAmbiguous: randomExcludeAmbiguous.value
  });

  const anySelected = Object.values(randomClasses.value).some(v => v);
  if (!anySelected) {
    toast.add({ title: t('passwordGen.common.errorNoClass'), color: 'red' });
    return;
  }

  const passwords: string[] = [];
  for (let i = 0; i < randomCount.value; i++) {
    passwords.push(
      generateRandomPassword(
        randomLength.value,
        pool,
        randomClasses.value,
        randomExcludeAmbiguous.value
      )
    );
  }
  randomPasswords.value = passwords;
}

function clearRandom() {
  randomPasswords.value = [];
}

// Generate deterministic password
async function generateDeterministic() {
  if (!detName.value.trim() || !detSalt.value.trim()) {
    toast.add({ title: t('passwordGen.common.errorNoInput'), color: 'red' });
    return;
  }

  const pool = buildPool({
    ...detClasses.value,
    excludeAmbiguous: detExcludeAmbiguous.value
  });

  const anySelected = Object.values(detClasses.value).some(v => v);
  if (!anySelected) {
    toast.add({ title: t('passwordGen.common.errorNoClass'), color: 'red' });
    return;
  }

  detGenerating.value = true;
  try {
    detPassword.value = await generateDeterministicPassword(
      detName.value.trim(),
      detSalt.value.trim(),
      detLength.value,
      pool,
      detClasses.value,
      detExcludeAmbiguous.value
    );
  } finally {
    detGenerating.value = false;
  }
}

function clearDeterministic() {
  detPassword.value = null;
}

// Copy password to clipboard
async function copyPassword(pwd: string, idx: number | 'det') {
  try {
    await navigator.clipboard.writeText(pwd);
    copiedIdx.value = idx;
    setTimeout(() => {
      copiedIdx.value = null;
    }, 2000);
  } catch (err) {
    console.error('Failed to copy:', err);
  }
}
</script>

<style scoped>
.toggle-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: var(--color-muted);
  border: 1px solid var(--color-border-default);
  border-radius: 8px;
  cursor: pointer;
  min-height: 40px;
  transition: background-color 0.15s, border-color 0.15s;
}

.toggle-item:hover {
  background: var(--color-brand-soft);
}

.toggle-item.active {
  background: var(--color-brand-soft);
  border-color: var(--color-brand-500);
}

.password-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
background: var(--color-muted);
  border: 1px solid var(--color-border-default);
  border-radius: 8px;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Fira Code', monospace;
  font-size: 14px;
  min-height: 44px;
}

.password-text {
  flex: 1;
  word-break: break-all;
  user-select: all;
}

.empty-state {
  text-align: center;
  padding: 32px 16px;
  color: var(--color-text-tertiary);
  font-size: 13px;
}
</style>
