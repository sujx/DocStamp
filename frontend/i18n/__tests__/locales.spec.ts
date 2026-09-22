import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const LOCALES = ["zh-CN", "en"];
const SKIP_DIRS = new Set(["node_modules", ".nuxt", ".output", "dist", ".git", "__pycache__"]);

function sourceFiles(dir: string, out: string[] = []): string[] {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (SKIP_DIRS.has(entry.name)) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) sourceFiles(full, out);
    else if (/\.(vue|ts|js|mjs)$/.test(entry.name) && !full.includes(`i18n${path.sep}locales`)) out.push(full);
  }
  return out;
}

function flatten(value: unknown, prefix = "", out = new Map<string, string>()): Map<string, string> {
  for (const [key, child] of Object.entries(value as Record<string, unknown>)) {
    const dotted = prefix ? `${prefix}.${key}` : key;
    if (child && typeof child === "object" && !Array.isArray(child)) flatten(child, dotted, out);
    else out.set(dotted, String(child));
  }
  return out;
}

function loadLocale(locale: string): Record<string, unknown> {
  return JSON.parse(fs.readFileSync(path.join(ROOT, "i18n/locales", `${locale}.json`), "utf8"));
}

const keys = Object.fromEntries(LOCALES.map((l) => [l, flatten(loadLocale(l))]));
const sections = new Set(Object.keys(loadLocale("zh-CN")));

// Keys reach the UI either as t("a.b") calls or as data literals a component
// later feeds to t() (tools.config.ts label/desc). Both are quoted dotted
// strings whose root is a locale section, so one scan covers them.
function referencedKeys(): Set<string> {
  const out = new Set<string>();
  for (const file of sourceFiles(ROOT)) {
    const text = fs.readFileSync(file, "utf8");
    for (const match of text.matchAll(/["'`]([A-Za-z][\w-]*(?:\.[\w-]+)+)["'`]/g)) {
      const literal = match[1]!;
      if (sections.has(literal.split(".")[0]!)) out.add(literal);
    }
  }
  return out;
}

// A key assembled at runtime is invisible to the literal scan above, which would
// silently make the dead-key audit wrong. The trigger is a locale section name
// followed by "." inside the static text of an interpolated template literal —
// whether that is a direct t() call on built-up text, or a label stored on a
// config object for a component to feed to t() later.
function dynamicKeySites(): string[] {
  const sites: string[] = [];
  for (const file of sourceFiles(ROOT)) {
    const text = fs.readFileSync(file, "utf8");
    for (const match of text.matchAll(/`([^`]*)`/gs)) {
      const body = match[1]!;
      if (!body.includes("${")) continue;
      const building = body
        .split(/\$\{[^}]*\}/)
        .flatMap((fragment) => fragment.match(/[A-Za-z][\w-]*\./g) ?? [])
        .filter((prefix) => sections.has(prefix.slice(0, -1)));
      if (!building.length) continue;
      const line = text.slice(0, match.index).split("\n").length;
      sites.push(`${path.relative(ROOT, file)}:${line}: \`${body}\``);
    }
  }
  return sites;
}

const refs = referencedKeys();

// A literal reference also covers every key nested under it.
const referenced = new Set<string>();
for (const ref of refs) {
  if (keys["zh-CN"]!.has(ref)) referenced.add(ref);
  for (const key of keys["zh-CN"]!.keys()) if (key.startsWith(`${ref}.`)) referenced.add(key);
}

describe("i18n locales", () => {
  it("keeps both locales in sync", () => {
    const [zh, en] = LOCALES.map((l) => keys[l]!);
    expect([...zh.keys()].filter((k) => !en.has(k)), "missing from en").toEqual([]);
    expect([...en.keys()].filter((k) => !zh.has(k)), "missing from zh-CN").toEqual([]);
  });

  it("scans the frontend for key references", () => {
    // Without this the two audits below pass vacuously if the scan breaks.
    expect(refs.size, "no i18n key literals found — the scanner is broken, not the locales").toBeGreaterThan(150);
    expect(refs.has("common.success")).toBe(true);
  });

  it("has no key that nothing references", () => {
    const dead = [...keys["zh-CN"]!.keys()].filter((k) => !referenced.has(k));
    expect(dead, `unreferenced i18n keys — delete them from both locales:\n${dead.join("\n")}`).toEqual([]);
  });

  it("has no reference to a key that does not exist", () => {
    const missing = [...refs].filter(
      (ref) => !keys["zh-CN"]!.has(ref) && ![...keys["zh-CN"]!.keys()].some((k) => k.startsWith(`${ref}.`)),
    );
    expect(missing, `referenced but undefined i18n keys:\n${missing.join("\n")}`).toEqual([]);
  });

  it("never builds a key from a template literal", () => {
    // The audits above only see literals, so dynamic construction would make
    // their findings wrong.
    expect(dynamicKeySites()).toEqual([]);
  });
});
