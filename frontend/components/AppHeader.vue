<template>
  <header
    class="fixed top-0 left-0 right-0 z-50 border-b flex items-center justify-between px-4 h-16 pt-[env(safe-area-inset-top)]"
    style="background: rgba(255,255,255,0.85); backdrop-filter: blur(16px); border-color: #e8e6d8;"
  >
    <div class="flex items-center gap-3">
      <img src="/logo.svg" alt="鹊随金印" class="h-8 w-8" />
      <span class="text-lg font-bold" :style="{ color: 'var(--color-text-primary)' }">鹊随金印</span>
      <span class="text-xs px-2 py-0.5 rounded font-medium ml-1" style="background: rgba(0,138,61,0.08); color: #008a3d;">
        {{ $t("header.subtitle") }}
      </span>
    </div>
    <LanguageSwitcher />
  </header>
</template>
