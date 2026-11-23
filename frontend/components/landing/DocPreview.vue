<template>
  <div class="doc-sheet" aria-hidden="true">
    <div class="letterhead">
      <p class="lh-title font-official">{{ $t("landing.hero.doc.head") }}</p>
      <p class="lh-no">{{ $t("landing.hero.doc.no") }}</p>
      <div class="lh-rule" />
    </div>

    <p class="doc-sheet__title">{{ $t("landing.hero.doc.title") }}</p>
    <p class="doc-sheet__to">{{ $t("landing.hero.doc.to") }}</p>
    <p class="doc-sheet__para">{{ $t("landing.hero.doc.body1") }}</p>
    <p class="doc-sheet__para">{{ $t("landing.hero.doc.body2") }}</p>

    <div class="doc-sheet__sign">
      <p class="doc-sheet__para">{{ $t("landing.hero.doc.sign") }}</p>
      <p class="doc-sheet__date">{{ $t("landing.hero.doc.date") }}</p>
      <span class="doc-sheet__stamp">印</span>
    </div>
  </div>
</template>
