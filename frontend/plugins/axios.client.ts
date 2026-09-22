import axios from "axios";

export default defineNuxtPlugin(() => {
  if (import.meta.dev) {
    axios.defaults.baseURL = "http://localhost:5000";
  }

  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      const status = error.response?.status;
      if (status === 401) {
        const toast = useToast();
        toast.add({ title: "登录已过期，请重新登录", color: "warning" });
      }
      return Promise.reject(error);
    },
  );
});
