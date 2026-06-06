import axios from "axios";

export default defineNuxtPlugin(() => {
  // In dev mode, bypass Nuxt proxy and connect directly to Flask backend
  if (import.meta.dev) {
    axios.defaults.baseURL = "http://localhost:5000";
  }
});
