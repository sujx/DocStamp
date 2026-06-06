export function useDownload() {
  function downloadBlob(data: Blob, filename: string, successMsg: string) {
    const url = URL.createObjectURL(data);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    if (import.meta.client) {
      const toast = useToast();
      toast.add({ title: successMsg, color: "success" });
    }
  }

  function showError(e: any) {
    const msg = e.response?.data?.error || e.message || "Unknown error";
    if (import.meta.client) {
      const toast = useToast();
      toast.add({ title: msg, color: "error" });
    }
  }

  return { downloadBlob, showError };
}
