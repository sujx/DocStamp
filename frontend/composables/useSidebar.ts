/**
 * Shared sidebar state.
 *
 * The sidebar is a fixed floating panel, so the content shell must know its
 * width to stay clear of it. Layout and Sidebar are siblings, so this lives in
 * Nuxt shared state — a parent cannot inject a value provided by its child.
 */

const COLLAPSED_WIDTH = 72;
const EXPANDED_WIDTH = 256;
const PANEL_INSET = 12;
// Mobile: clears the fixed hamburger button (left-4 + size-10 + gap)
const MOBILE_GUTTER = 76;
const MOBILE_QUERY = "(max-width: 1023px)";
const STORAGE_KEY = "sidebar_collapsed";

let mediaQueryBound = false;

export function useSidebar() {
  // SSR-safe defaults. The real values come from browser APIs after hydration —
  // useState is seeded from the SSR payload, so initializers cannot read them.
  const collapsed = useState("sidebar_collapsed", () => true);
  const isMobile = useState("sidebar_mobile", () => false);

  onMounted(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved !== null) collapsed.value = saved !== "false";
    isMobile.value = window.matchMedia(MOBILE_QUERY).matches;
  });

  if (import.meta.client && !mediaQueryBound) {
    mediaQueryBound = true;
    window.matchMedia(MOBILE_QUERY).addEventListener("change", (e) => {
      isMobile.value = e.matches;
    });
  }

  /** Left offset the content shell needs so the panel never covers it. */
  const shellOffset = computed(() => {
    if (isMobile.value) return MOBILE_GUTTER;
    return (collapsed.value ? COLLAPSED_WIDTH : EXPANDED_WIDTH) + PANEL_INSET;
  });

  function toggleCollapsed() {
    collapsed.value = !collapsed.value;
    if (import.meta.client) {
      localStorage.setItem(STORAGE_KEY, String(collapsed.value));
    }
  }

  return { collapsed, isMobile, shellOffset, toggleCollapsed };
}
