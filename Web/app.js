const status = document.getElementById("status");

document.getElementById("watcher").addEventListener("change", (e) => {
  status.textContent = "中継フォルダ監視中";

  setInterval(() => {
    // 実際は File API で一覧を読む
    status.textContent = "チェック中...";
  }, 1000);
});
