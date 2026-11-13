<template>
  <article class="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-14">
    <div class="text-brand-600">
      <SectionKicker :text="$t('guide.pdfRedact.kicker')" />
    </div>

    <h1 class="font-official mt-3 text-[30px] font-extrabold leading-snug tracking-wide text-primary sm:text-[34px]">
      {{ $t("guide.pdfRedact.title") }}
    </h1>

    <p class="mt-3 text-[13px] text-tertiary">
      <time datetime="2026-11-13">{{ $t("guide.pdfRedact.published") }}</time>
      · {{ $t("guide.pdfRedact.reading") }}
      · {{ $t("guide.pdfRedact.toolLabel") }}
      <NuxtLink to="/pdf-redact" class="text-brand-600 no-underline hover:underline">{{ $t("pdfRedact.title") }}</NuxtLink>
    </p>

    <p
      v-if="locale !== 'zh-CN'"
      class="mt-6 rounded-lg border border-default bg-muted px-4 py-3 text-sm text-secondary"
    >
      {{ $t("guide.pdfRedact.localeNotice") }}
    </p>

    <div class="mt-8 text-[15px] leading-[1.9] text-secondary">
      <p>
        每年都有单位把红头文件里的敏感字段用黑色矩形「涂掉」后对外公开，几天后发现有流传版本能直接复制出被涂的号码。问题不在鼠标，在于对 PDF 的理解。
      </p>

      <h2 class="font-official mt-10 text-[20px] font-bold text-primary">一、黑框为什么挡不住</h2>
      <p class="mt-3">
        PDF 是分层结构：文字内容是一层，你画的黑色矩形是<b class="text-primary">另一层盖在上面的图形对象</b>。视觉上它挡住了字，数据上原字一个都没少——全选复制、提取文本、甚至 Ctrl+F 搜索，被「涂掉」的内容都原样在场。
      </p>

      <h2 class="font-official mt-10 text-[20px] font-bold text-primary">二、真脱敏要做两步</h2>
      <p class="mt-3">
        <b class="text-primary">第一步：删除。</b>对目标区域执行 PDF 级的 redaction，把矩形覆盖范围内的文字对象删掉。这一步做完，即使不盖任何东西，字也已经不存在了。
      </p>
      <p class="mt-3">
        <b class="text-primary">第二步：遮盖。</b>删除后原位置会留下一个空白洞，看图的人仍能猜到这里曾有信息。所以还要把该区域渲染成马赛克贴回去。顺序不能反：先删后盖，盖只是视觉收尾。
      </p>

      <h2 class="font-official mt-10 text-[20px] font-bold text-primary">三、本工具实际做了什么</h2>
      <ul class="mt-3 list-disc space-y-2 pl-5">
        <li>两种标记方式：在页面上拖拽框选，或按关键词 / 正则在全文里批量定位。内置手机号、身份证号、银行卡号模板，单次最多返回 500 处。</li>
        <li>执行时对每个标记区域：先截取该区域的位图并像素化，再删除区域内的文字对象，最后把马赛克贴回原位。</li>
        <li>生成一份新的 PDF，原文件不改动；同时清掉文档元数据、嵌入附件和无用对象。</li>
        <li>自动复检：重新打开产物，对每个标记区域再提取一次文字。仍能提取到字的区域会写进报告，提示人工复核。</li>
      </ul>

      <h2 class="font-official mt-10 text-[20px] font-bold text-primary">四、必须知道的局限：图片页</h2>
      <p class="mt-3">
        本工具删除的是<b class="text-primary">文字层</b>，图片本身不删。对扫描件或整页是图片的 PDF，马赛克只是盖在上面：<b class="text-primary">图片的原始像素仍在文件里</b>，用图片提取工具仍能拿到被遮的内容。报告里的「图片型页面上的标记」就是提醒你，有多少个标记落在这种页面上；复检也只检查文字层，覆盖不到图片像素。
      </p>
      <p class="mt-3">
        这类文件需要额外处理：先 OCR 转成带文字层的版本再脱敏，或用其他方式把这一页真正重绘 / 裁掉。不要把本工具的输出当作对扫描件的完整脱敏。
      </p>
      <p class="mt-3">
        关键词搜索同样依赖文字层。所搜页面没有文字层时，工具会直接提示改用手动框选——搜索不到不等于没有内容。
      </p>

      <h2 class="font-official mt-10 text-[20px] font-bold text-primary">五、怎么用</h2>
      <ol class="mt-3 list-decimal space-y-2 pl-5">
        <li>打开 <NuxtLink to="/pdf-redact" class="text-brand-600 no-underline hover:underline">PDF 脱敏</NuxtLink>，拖入文件。仅支持 .pdf，单文件最大 100 MB；加密 PDF 请先解密。</li>
        <li>用关键词搜索或手动框选标记敏感区域，逐页确认没有漏标。</li>
        <li>选择马赛克颗粒，执行脱敏，等待报告。</li>
        <li>看报告四项：标记区域、成功脱敏、图片型页面上的标记、复检结果。复检提示仍有文字的区域，逐个人工处理。</li>
        <li>下载产物；临时文件由服务端清理，不会留在浏览器里。</li>
      </ol>

      <h2 class="font-official mt-10 text-[20px] font-bold text-primary">六、常见翻车姿势</h2>
      <ul class="mt-3 list-disc space-y-2 pl-5">
        <li>截图后在图片上画黑框，再插回 Word 转 PDF——原来那份 PDF 若还留在系统里，等于没删。</li>
        <li>只处理正文。文档属性、嵌入附件、正文之外的批注和修订也可能带敏感信息；本工具会清元数据与附件，其余仍需发布前人工确认。</li>
        <li>关键词漏掉变体写法，比如手机号中间加空格、全角数字。换正则逐个试，别只搜一遍就收工。</li>
        <li>最隐蔽的一种：本地删完就放心，把「删过」的原件连同产物一起发了出去。</li>
      </ul>
    </div>

    <div class="card mt-10 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p class="font-official text-base font-bold text-primary">{{ $t("guide.pdfRedact.ctaTitle") }}</p>
        <p class="mt-1 text-[13px] leading-relaxed text-secondary">{{ $t("guide.pdfRedact.ctaBody") }}</p>
      </div>
      <NuxtLink
        to="/pdf-redact"
        class="inline-flex min-h-[44px] flex-none items-center justify-center whitespace-nowrap rounded-lg bg-brand-500 px-4 text-sm font-semibold text-white no-underline transition-colors duration-200 hover:bg-brand-600"
      >{{ $t("guide.pdfRedact.ctaButton") }}</NuxtLink>
    </div>

    <p class="mt-8 text-[12px] leading-relaxed text-tertiary">
      文中行为以当前部署版本为准。标准原文见
      <a
        href="/GBT9704-2012.pdf"
        target="_blank"
        rel="noopener"
        class="text-brand-600 no-underline hover:underline"
      >GB/T 9704-2012</a>。
    </p>
  </article>
</template>

<script setup lang="ts">
import SectionKicker from "~/components/landing/SectionKicker.vue";

definePageMeta({ layout: "landing" });

const { t, locale } = useI18n();

useHead({
  title: computed(() => t("guide.pdfRedact.metaTitle")),
  meta: [
    { name: "description", content: computed(() => t("guide.pdfRedact.metaDescription")) },
    { name: "keywords", content: computed(() => t("guide.pdfRedact.metaKeywords")) },
    { property: "og:title", content: computed(() => t("guide.pdfRedact.metaTitle")) },
    { property: "og:description", content: computed(() => t("guide.pdfRedact.metaDescription")) },
    { property: "og:type", content: "article" },
    { property: "og:url", content: "https://doc.sujx.net/guide/pdf-redact" },
  ],
});
</script>
