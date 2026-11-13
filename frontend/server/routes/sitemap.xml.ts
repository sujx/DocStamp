import { TOOLS } from "../../composables/tools.config";
import { buildSitemapUrls, renderSitemapXml } from "../utils/sitemap";

export default defineEventHandler((event) => {
  setHeader(event, "content-type", "application/xml; charset=utf-8");
  return renderSitemapXml(buildSitemapUrls(TOOLS), new Date().toISOString().slice(0, 10));
});
