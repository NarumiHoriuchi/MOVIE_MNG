fetch("/api/videos")
  .then(res => res.json())
  .then(videos => {
    const list = document.getElementById("video-list");

    videos.forEach(v => {
      const card = document.createElement("div");
      card.className = "video-card";

      card.innerHTML = `
        <img src="${v.thumbnail_path || 'noimage.png'}">
        <div class="info">
          <div>${v.title}</div>
          <small>${v.channel || ''}</small>
        </div>
      `;

      list.appendChild(card);
    });
  })
  .catch(err => {
    console.error(err);
    alert("動画一覧の取得に失敗しました");
  });
