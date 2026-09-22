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

  return { downloadBlob };
}
