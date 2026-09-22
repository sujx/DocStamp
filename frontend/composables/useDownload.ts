export function useDownload() {
  function downloadBlob(data: Blob, filename: string, successMsg?: string) {
    const url = URL.createObjectURL(data);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    // 在点击的同一个任务里 revoke 会让部分浏览器直接取消下载，等下载启动后再回收
    setTimeout(() => {
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }, 100);
    if (successMsg && import.meta.client) {
      const toast = useToast();
      toast.add({ title: successMsg, color: "success" });
    }
  }

  return { downloadBlob };
}
