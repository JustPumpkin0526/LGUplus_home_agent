const uploadButton = document.getElementById("uploadButton");
const subtitleDiv = document.getElementById("subtitle");
const imageInput = document.getElementById("imageFile");
const videoInput = document.getElementById('videoFile');
const previewImage = document.getElementById("previewImage");
const resetButton = document.getElementById('resetButton');
const video = document.getElementById('video');
const progressBar = document.getElementById('progressBar');
const timeDisplay = document.getElementById('timeDisplay');

let currentMode = null;
let currentTask = null;

function formatTime(seconds) {
  const min = Math.floor(seconds / 60);
  const sec = Math.floor(seconds % 60);
  return `${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

video.addEventListener('timeupdate', () => {
  const percent = (video.currentTime / video.duration) * 100;
  progressBar.style.width = percent + "%";

  if (!isNaN(video.duration)) {
    const current = formatTime(video.currentTime);
    const total = formatTime(video.duration);
    timeDisplay.textContent = `${current} / ${total}`;
  }

  if (Math.floor(video.currentTime) in descript_dict) {
    subtitleDiv.textContent = descript_dict[Math.floor(video.currentTime)];
  }
  else {
    subtitleDiv.textContent = '여기에 자막이 표시됩니다.'
  }
})

imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];

  if (file && file.type.startsWith("image/")) {
    const reader = new FileReader();
    reader.onload = function (e) {
      previewImage.src = e.target.result;
      previewImage.style.display = "block";
      video.style.display = "none"; // 영상 숨김
      video.pause();
    };
    reader.readAsDataURL(file);
  }

  // 영상 비활성화
  if (imageInput.files.length > 0) {
    videoInput.disabled = true;
  } else {
    videoInput.disabled = false;
  }
});

// 영상 선택 시 영상 표시
videoInput.addEventListener("change", () => {
  const file = videoInput.files[0];
  if (file && file.type.startsWith("video/")) {
    const url = URL.createObjectURL(file);
    video.src = url;
    video.style.display = "block";
    previewImage.style.display = "none"; // 이미지 숨김
  }

  // 이미지 비활성화
  if (videoInput.files.length > 0) {
    imageInput.disabled = true;
  } else {
    imageInput.disabled = false;
  }
});

function resetFile() {
  videoInput.disabled = false;
  imageInput.disabled = false;
  videoInput.value = ''
  imageInput.value = ''
  previewImage.style.display = "none";
  video.style.display = "none";
  video.src = "";
  video.currentTime = 0;
  document.getElementById('excel_button').style.display = "block";
  subtitleDiv.textContent = "여기에 자막이 표시됩니다.";
}

let play_check = 0;
let changeTime = 0;
let descript_dict = {
  0 : "아기가 자는 중입니다.",
  20 : "아기가 자는 중입니다.",
  40 : "아기가 자는 중입니다.",
  60 : "아기가 자는 중입니다.",
  80 : "아기가 자는 중입니다.",
  100 : "아기가 자는 중입니다.",
  120 : "아기가 자는 중입니다.",
  140 : "아기가 자는 중입니다.",
  160 : "아기가 자는 중입니다.",
  180 : "아기가 자는 중입니다.",
  200 : "아기가 자는 중입니다.",
  220 : "아기가 자는 중입니다.",
  240 : "아기가 자는 중입니다.",
  260 : "아기가 자는 중입니다.",
  280 : "아기가 자는 중입니다.",
  300 : "아기가 자는 중입니다.",
  320 : "아기가 자는 중입니다.",
  340 : "아기가 자는 중입니다.",
  360 : "아기가 자는 중입니다.",
  380 : "아기가 자는 중입니다.",
  400 : "아기가 자는 중입니다.",
  420 : "아기가 자는 중입니다.",
  440 : "아기가 자는 중입니다.",
  460 : "아기가 자는 중입니다.",
  480 : "아기가 깨어 있습니다.",
  500 : "아기가 자는 중입니다.",
  520 : "아기가 자는 중입니다.",
  540 : "아기가 자는 중입니다.",
  560 : "아기가 자는 중입니다.",
  580 : "아기가 자는 중입니다.",
  600 : "아기가 자는 중입니다.",
  620 : "아기가 자는 중입니다.",
  640 : "아기가 자는 중입니다.",
  660 : "아기가 자는 중입니다.",
  680 : "아기가 자는 중입니다.",
  700 : "아기가 자는 중입니다.",
  720 : "아기가 자는 중입니다.",
  740 : "아기가 자는 중입니다.",
  760 : "아기가 자는 중입니다.",
  780 : "아기가 자는 중입니다.",
  800 : "아기가 자는 중입니다.",
  820 : "아기가 자는 중입니다.",
  840 : "아기가 자는 중입니다.",
  860 : "아기가 자는 중입니다.",
  880 : "아기가 자는 중입니다.",
  900 : "아기가 자는 중입니다.",
  920 : "아기가 자는 중입니다.",
  940 : "아기가 자는 중입니다.",
  960 : "아기가 자는 중입니다.",
  980 : "아기가 자는 중입니다.",
  1000 : "아기가 자는 중입니다.",
  1020 : "아기가 자는 중입니다.",
  1040 : "아기가 자는 중입니다.",
  1060 : "아기가 자는 중입니다.",
  1080 : "아기가 자는 중입니다.",
  1100 : "아기가 자는 중입니다.",
  1120 : "아기가 자는 중입니다.",
  1140 : "아기가 자는 중입니다.",
  1160 : "아기가 자는 중입니다.",
  1180 : "아기가 자는 중입니다.",
  1200 : "아기가 자는 중입니다.",
  1220 : "아기가 자는 중입니다.",
  1240 : "아기가 자는 중입니다.",
  1260 : "아기가 자는 중입니다.",
  1280 : "아기가 자는 중입니다.",
  1300 : "아기가 자는 중입니다.",
  1320 : "아기가 자는 중입니다.",
  1340 : "아기가 자는 중입니다.",
  1360 : "아기가 자는 중입니다.",
  1380 : "아기가 자는 중입니다.",
  1400 : "아기가 자는 중입니다.",
  1420 : "아기가 자는 중입니다.",
  1440 : "아기가 자는 중입니다.",
  1460 : "아기가 자는 중입니다.",
  1480 : "아기가 깨어 있습니다.",
  1500 : "아기가 자는 중입니다.",
  1520 : "아기가 자는 중입니다.",
  1540 : "아기가 깨어 있습니다.",
  1560 : "아기가 깨어 있습니다.",
  1580 : "아기가 자는 중입니다.",
  1600 : "아기가 자는 중입니다.",
  1620 : "아기가 깨어 있습니다.",
  1640 : "아기가 자는 중입니다.",
  1660 : "아기가 자는 중입니다.",
  1680 : "아기가 자는 중입니다.",
  1700 : "아기가 자는 중입니다.",
  1720 : "아기가 자는 중입니다."
}

let = sample_list

async function playvideo() {
  const video_option = document.querySelector("select[name=video_option] option:checked").value
  check_text = "";
  if (play_check == 0) {
    if (video_option == "none") {
      alert("영상 재생 방식을 선택해주세요.");
      return;
    }
    else if (video_option == "normal") {
      if (currentMode === "normal") return;
      await stopCurrentTask();
      currentMode = "normal";
      video.play();
    }
    else if (video_option == "sample_play") {
      if (!document.getElementById('sampleTime').value) {
        alert("샘플 간격을 입력하시오.");
        return;
      }
      if (currentMode === "sample") return;
      await stopCurrentTask();
      currentMode = "sample";

      let cancel = false;
      currentTask = { cancel: () => cancel = true };

      while (video.currentTime <= video.duration) {
        if (cancel) return;
        video.currentTime += Number(document.getElementById('sampleTime').value);
        await new Promise(resolve => video.onseeked = () => resolve());
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

    }
    else if (video_option == "change_play") {
      if (!descript_dict) {
        alert("먼저 영상을 업로드하여 분석을 완료해주세요.");
        return;
      }
      if (currentMode === "change") return;
      await stopCurrentTask();
      currentMode = "change";

      let cancel = false;
      currentTask = { cancel: () => cancel = true };
      while (changeTime <= video.duration) {
        if (cancel) return;
        if (descript_dict[changeTime] != check_text) {
          check_text = descript_dict[changeTime];
          video.currentTime = changeTime;
          await new Promise(resolve => video.onseeked = () => resolve());
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        changeTime += Number(document.getElementById("sampleTime").value);

        if (changeTime >= video.duration) {
          video.currentTime = video.duration;
        }
      }

    }
    else if (video_option == "sleep_time_play") {
      if (!descript_dict) {
        alert("먼저 영상을 업로드하여 분석을 완료해주세요.");
        return;
      }
      if (currentMode === "sleep_time") return;
      await stopCurrentTask();
      currentMode = "sleep_time";

      let cancel = false;
      currentTask = { cancel: () => cancel = true };

      while (changeTime <= video.duration) {

        if (cancel) return;

        if (descript_dict[changeTime] != check_text) {
          if (descript_dict[changeTime] == "아기가 자는 중입니다.") {
            let video_playing = true;
            check_text = descript_dict[changeTime];
            video.currentTime = changeTime;
            video.play(); 
            await new Promise(resolve => video.onseeked = () => resolve());
            await new Promise(resolve => setTimeout(resolve, Number(document.getElementById('sleepTime').value) * 1000));
            video.pause();
          }
          if (descript_dict[changeTime] == "아기가 깨어 있습니다.") {
            let video_playing = true;
            video.play();
          }
          else {
            setTimeout(function () {
              changeTime++;
            }, 1000);
          }
        }
      }
    }
  }
  else {
    play_check = 0;
    video.pause();
    video.currentTime = 0;
  }
}

async function stopvideo() {
  changeTime = 0;
  currentMode = null;
  video.currentTime = 0;
  video.pause();
  await stopCurrentTask();
}

async function stopCurrentTask() {
  if (currentTask && typeof currentTask.cancel === "function") {
    currentTask.cancel();
  }
  await new Promise(resolve => setTimeout(resolve, 100));
  currentMode = null;
}

uploadButton.addEventListener("click", () => {

  const img_file = imageInput.files[0];
  const vid_file = videoInput.files[0];
  if (!img_file && !vid_file) {
    alert("파일을 선택해주세요.");
    return;
  }

  if (imageInput.disabled == false) {
    const formData = new FormData();
    formData.append("file", img_file);

    fetch("/upload_image", {
      method: "POST",
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        console.log("서버 응답:", data);
        if (data.descript) {
          subtitleDiv.textContent = data.descript;
        } else {
          subtitleDiv.textContent = "분석 결과를 불러올 수 없습니다.";
        }
      })
      .catch(error => {
        console.error("에러 발생:", error);
        subtitleDiv.textContent = "서버 요청 중 오류가 발생했습니다.";
      });
  }

  if (videoInput.disabled == false) {
    subtitleDiv.textContent = "샘플 데이터 제작 중...";

    const formData = new FormData();
    formData.append("file", vid_file);
    const sampleTime = document.getElementById("sampleTime").value;
    if (!sampleTime) {
      alert("샘플 간격을 입력해주세요.");
      return;
    }
    formData.append("sample_time", sampleTime);

    fetch("/get_sample", {
      method: "POST",
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        console.log("서버 응답:", data);
        if (data) {
          sample_list = data.sample_list;
          subtitleDiv.textContent = "영상 분석 중...";
          formData = new FormData();
          formData.append("sample_list", sample_list);
          fetch("/vlm_query", {
            method: "POST",
            body: formData
          })
            .then(response => response.json())
            .then(data =>{
              if (data){
                descript_dict = data.descript_dict
              }
            })
        } else {
          subtitleDiv.textContent = "샘플 데이터 제작에 실패했습니다.";
        }
      })
      .catch(error => {
        console.error("에러 발생:", error);
        subtitleDiv.textContent = "서버 요청 중 오류가 발생했습니다.";
      });
  }
});

async function loadExcelData() {
  const vid_file = videoInput.files[0];

  if (!vid_file) {
    alert("동영상을 선택해주세요.");
    return;
  }

  document.getElementById('excel_button').style.display = 'none'

  const formData = new FormData();
  formData.append("file", vid_file);

  const response = await fetch('/excel_data', {
    method: "POST",
    body: formData
  });

  const result = await response.json();
  const container = document.getElementById('excelTableContainer');
  container.innerHTML = '';
  const table = document.createElement('table');
  table.style.borderCollapse = 'collapse';
  table.style.width = '100%';
  table.style.fontSize = '14px';
  table.style.border = '1px solid #ccc';
  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');
  result.columns.forEach(col => {
    const th = document.createElement('th');
    th.textContent = col;
    th.style.padding = '8px';
    th.style.border = '1px solid #ccc';
    th.style.backgroundColor = '#f0f0f0';
    th.style.textAlign = 'left';
    headerRow.appendChild(th);
  });
  thead.appendChild(headerRow);
  table.appendChild(thead);
  const tbody = document.createElement('tbody');
  result.data.forEach(row => {
    const tr = document.createElement('tr');
    row.forEach((cell, colIndex) => {
      const td = document.createElement('td');
      td.style.padding = '8px';
      td.style.border = '1px solid #ccc';
      if (colIndex === 0 && typeof cell === 'string' && cell.trim() !== '') {
        const img = document.createElement('img');
        img.src = cell.trim();
        img.style.height = '80px';
        img.style.objectFit = 'contain';
        td.appendChild(img);
      } else {
        td.textContent = cell !== null ? cell : '';
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  container.appendChild(table);
}