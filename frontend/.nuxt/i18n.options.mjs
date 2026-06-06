
// @ts-nocheck
import locale_zh_45CN_46json_1f0c5420 from "#nuxt-i18n/1f0c5420";
import locale_en_46json_9b0da3fe from "#nuxt-i18n/9b0da3fe";

export const localeCodes =  [
  "zh-CN",
  "en"
]

export const localeLoaders = {
  "zh-CN": [
    {
      key: "locale_zh_45CN_46json_1f0c5420",
      load: () => Promise.resolve(locale_zh_45CN_46json_1f0c5420),
      cache: true
    }
  ],
  en: [
    {
      key: "locale_en_46json_9b0da3fe",
      load: () => Promise.resolve(locale_en_46json_9b0da3fe),
      cache: true
    }
  ]
}

export const vueI18nConfigs = []

export const nuxtI18nOptions = {
  restructureDir: "i18n",
  experimental: {
    localeDetector: "",
    switchLocalePathLinkSSR: false,
    autoImportTranslationFunctions: false,
    typedPages: true,
    typedOptionsAndMessages: false,
    generatedLocaleFilePathFormat: "absolute",
    alternateLinkCanonicalQueries: false,
    hmr: true
  },
  bundle: {
    compositionOnly: true,
    runtimeOnly: false,
    fullInstall: true,
    dropMessageCompiler: false,
    optimizeTranslationDirective: true
  },
  compilation: {
    strictMessage: true,
    escapeHtml: false
  },
  customBlocks: {
    defaultSFCLang: "json",
    globalSFCScope: false
  },
  locales: [
    {
      code: "zh-CN",
      name: "中文",
      files: [
        {
          path: "/root/Project/docStamp/frontend/i18n/locales/zh-CN.json",
          cache: undefined
        }
      ]
    },
    {
      code: "en",
      name: "English",
      files: [
        {
          path: "/root/Project/docStamp/frontend/i18n/locales/en.json",
          cache: undefined
        }
      ]
    }
  ],
  defaultLocale: "zh-CN",
  defaultDirection: "ltr",
  routesNameSeparator: "___",
  trailingSlash: false,
  defaultLocaleRouteNameSuffix: "default",
  strategy: "no_prefix",
  lazy: false,
  langDir: "locales",
  rootRedirect: undefined,
  detectBrowserLanguage: {
    alwaysRedirect: false,
    cookieCrossOrigin: false,
    cookieDomain: null,
    cookieKey: "docstamp_lang",
    cookieSecure: false,
    fallbackLocale: "zh-CN",
    redirectOn: "root",
    useCookie: true
  },
  differentDomains: false,
  baseUrl: "",
  customRoutes: "page",
  pages: {},
  skipSettingLocaleOnNavigate: false,
  types: "composition",
  debug: false,
  parallelPlugin: false,
  multiDomainLocales: false,
  i18nModules: []
}

export const normalizedLocales = [
  {
    code: "zh-CN",
    name: "中文",
    files: [
      {
        path: "/root/Project/docStamp/frontend/i18n/locales/zh-CN.json",
        cache: undefined
      }
    ]
  },
  {
    code: "en",
    name: "English",
    files: [
      {
        path: "/root/Project/docStamp/frontend/i18n/locales/en.json",
        cache: undefined
      }
    ]
  }
]

export const NUXT_I18N_MODULE_ID = "@nuxtjs/i18n"
export const parallelPlugin = false
export const isSSG = true
export const hasPages = true

export const DEFAULT_COOKIE_KEY = "i18n_redirected"
export const DEFAULT_DYNAMIC_PARAMS_KEY = "nuxtI18nInternal"
export const SWITCH_LOCALE_PATH_LINK_IDENTIFIER = "nuxt-i18n-slp"
/** client **/

/** client-end **/