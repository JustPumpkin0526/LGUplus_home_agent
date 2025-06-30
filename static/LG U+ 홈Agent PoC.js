const uploadButton = document.getElementById("uploadButton");
const subtitleDiv = document.getElementById("subtitle");
const imageInput = document.getElementById("imageFile");
const videoInput = document.getElementById('videoFile');
const previewImage = document.getElementById("previewImage");
const resetButton = document.getElementById('resetButton');
const video = document.getElementById('video');
const progressBar = document.getElementById('progressBar');
const timeDisplay = document.getElementById('timeDisplay');
const processTimeDiv = document.getElementById("processTime");

let processCheck = false;

let file_type = "";

let currentMode = null;
let currentTask = null;

let check_text = "";

let play_check = 0;
let changeTime = 0;
let descript_dict;
let progressContainer = document.getElementById('progressContainer');
let sample_list;
let sampleTime = document.getElementById("sampleTime");
let change_dict = {};


// 시간 HH:MM:SS 형태로 변환
function formatTime(seconds) {
  const hour = Math.floor(seconds / 60 / 60);
  const min = Math.floor(seconds / 60);
  const sec = Math.floor(seconds % 60);
  return `${String(hour).padStart(2, '0')}:${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

//비동기 작업 및 현재 작업 중단 함수
async function stopCurrentTask() {
  if (currentTask && typeof currentTask.cancel === "function") {
    currentTask.cancel();
  }
  await new Promise(resolve => setTimeout(resolve, 100));
  currentMode = null;
}

//아기 수면 상태 전환 시점의 description 및 시간 정보 저장 함수
async function sleepChangeCheck() {
  while (changeTime <= video.duration) {
    if (descript_dict[changeTime]["sleep"] != check_text) {
      change_dict[changeTime] = descript_dict[changeTime]["sleep"];
      check_text = descript_dict[changeTime]["sleep"];
    }
    changeTime += Number(document.getElementById("sampleTime").value);
  }
  changeTime = 0;
}

//타임 라인, 자막 처리 기능
video.addEventListener('timeupdate', () => {
  const percent = (video.currentTime / video.duration) * 100;
  progressBar.style.width = percent + "%";

  if (!isNaN(video.duration)) {
    const current = formatTime(video.currentTime);
    const total = formatTime(video.duration);
    timeDisplay.textContent = `${current} / ${total}`;
  }

  if (Math.floor(video.currentTime) in descript_dict) {
    console.log("자막이 표시됩니다.")
    subtitleDiv.textContent = descript_dict[Math.floor(video.currentTime)]["descript"];
  }
})

// 이미지 파일 삽입 시 띄우는 기능
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

//업로드 파일 분석 기능
async function startAnalyze() {
  const startTime = Date.now();

  document.getElementById("panorama").innerHTML = "";

  excel_reset()

  processCheck = false;

  const intervalId = setInterval(() => {
    const elapsedSec = Math.floor((Date.now() - startTime) / 1000);
    const sec = elapsedSec % 60;
    const min = Math.floor(elapsedSec / 60);
    const hour = Math.floor(min / 60);
    processTimeDiv.textContent = `분석 프로세스 소요 시간 : ${hour}시 ${min}분 ${sec}초`;
  }, 100);

  try {
    const img_file = imageInput.files[0];
    const vid_file = videoInput.files[0];

    if (!img_file && !vid_file) {
      alert("파일을 선택해주세요.");
      return;
    }

    if (!sampleTime.value) {
      alert("샘플 간격을 입력해주세요.");
      return;
    }

    if (imageInput.disabled === false) {
      const formData = new FormData();
      formData.append("file", img_file);
      const imgRes = await fetch("/upload_image", {
        method: "POST",
        body: formData
      });
      const imgData = await imgRes.json();
      subtitleDiv.textContent = imgData.descript || "분석 결과를 불러올 수 없습니다.";
    }

    if (videoInput.disabled === false) {
      subtitleDiv.textContent = "샘플 데이터 제작 중...";
      const formData = new FormData();
      formData.append("file", vid_file);
      formData.append("sample_time", sampleTime.value);
      const sampleRes = await fetch("/get_sample", {
        method: "POST",
        body: formData
      });
      const sampleData = await sampleRes.json();
      if (!sampleData) {
        subtitleDiv.textContent = "샘플 데이터 제작 실패";
        return;
      }

      sample_list = sampleData.sample_list;

      console.log(sample_list);

      subtitleDiv.textContent = "영상 분석 중...";
      const vlmForm = new FormData();
      vlmForm.append("sample_list", JSON.stringify(sample_list));
      const vlmRes = await fetch("/vlm_query", {
        method: "POST",
        body: vlmForm
      });
      const vlmData = await vlmRes.json();
      if (!vlmData) {
        subtitleDiv.textContent = "영상 분석 실패.";
        return;
      }

      descript_dict = vlmData.descript_dict;

      subtitleDiv.textContent = "엑셀 파일 생성 중...";
      const excelForm = new FormData();
      excelForm.append("file", vid_file);
      excelForm.append("sample_list", JSON.stringify(sample_list));
      excelForm.append("descript_dict", JSON.stringify(descript_dict));
      const excelRes = await fetch("/make_excel", {
        method: "POST",
        body: excelForm
      });
      await excelRes.json();

      subtitleDiv.textContent = "엑셀 파일 생성 완료.";
      processCheck = true;

      await sleepChangeCheck();
      await addMarkersToProgressBar(Object.keys(change_dict));
      makeThumbnail();
    }
  } catch (err) {
    console.error("에러 발생:", err);
    subtitleDiv.textContent = "처리 중 오류가 발생했습니다.";
  } finally {
    clearInterval(intervalId); 
  }
}

//파일 초기화 기능
function resetFile() {
  videoInput.disabled = false;
  imageInput.disabled = false;
  videoInput.value = ''
  imageInput.value = ''
  previewImage.style.display = "none";
  video.style.display = "none";
  video.src = "";
  video.currentTime = 0;
  subtitleDiv.textContent = "여기에 자막이 표시됩니다.";
  progressBar.style.width = "0%";
  timeDisplay.textContent = "00:00 / 00:00";
  document.getElementById("panorama").innerHTML = "";
  document.getElementById("progressBar").innerHTML = "";
  processTimeDiv.textContent = `분석 프로세스 소요 시간 : -초`;
  processCheck = false;
}

//표 불러오기 기능
async function loadExcelData() {
  const vid_file = videoInput.files[0];

  if (!vid_file) {
    alert("동영상을 선택해주세요.");
    return;
  }
  if (!processCheck) {
    alert("분석 결과가 없습니다. 분석을 끝마치고 다시 실행해주세요.");
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
  document.getElementById('excel_reset').style.display = 'block'
}

//표 초기화 기능
async function excel_reset() {
  const container = document.getElementById('excelTableContainer');
  container.innerHTML = '';
  document.getElementById('excel_button').style.display = 'block';
  document.getElementById('excel_reset').style.display = 'none'

}

//영상 재생 기능
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
      if (!processCheck) {
        alert("먼저 영상을 업로드하여 분석을 완료해주세요.");
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
      if (!processCheck) {
        alert("먼저 영상을 업로드하여 분석을 완료해주세요.");
        return;
      }
      if (currentMode === "change") return;
      await stopCurrentTask();
      currentMode = "change";

      let cancel = false;
      currentTask = { cancel: () => cancel = true };
      for(var key in change_dict){
        if (cancel) return;
        video.currentTime = key;
        await new Promise(resolve => video.onseeked = () => resolve());
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

    }

    else if (video_option == "sleep_time_play") {

      if (!processCheck) {
        alert("먼저 영상을 업로드하여 분석을 완료해주세요.");
        return;
      }
      if (currentMode === "sleep_time") return;
      await stopCurrentTask();
      currentMode = "sleep_time";

      let cancel = false;
      currentTask = { cancel: () => cancel = true };

      console.log(change_dict);
      for (var key in change_dict) {
        if (cancel) return;
        video.currentTime = key;
        if (change_dict[key]["sleep"] == "아기가 자는 중입니다.") {
          if (cancel) return;
          video.play();
          await new Promise(resolve => video.onseeked = () => resolve());
          await new Promise(resolve => setTimeout(resolve, Number(document.getElementById("sleepTime").value) * 1000));
          video.pause();
        }
        else if (change_dict[key]["sleep"]  == "아기가 깨어 있습니다.") {
          if (cancel) return;
          video.play();
          await new Promise(resolve => video.onseeked = () => resolve());
          await new Promise(resolve => setTimeout(resolve, 1000));

          while (subtitleDiv.textContent !== "아기가 자는 중입니다.") {
            if (cancel) return;
            await new Promise(resolve => setTimeout(resolve, 1000));
          }
          video.pause();
        }
      }
    }
  } else {
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

async function addMarkersToProgressBar(change_dict) {
  document.querySelectorAll('.marker').forEach(m => m.remove());

  if (!video.duration || video.duration === Infinity) return;

  const tooltip = document.createElement('div');
  tooltip.id = 'markerTooltip';
  tooltip.style.position = 'absolute';
  tooltip.style.padding = '4px 8px';
  tooltip.style.fontSize = '12px';
  tooltip.style.backgroundColor = 'black';
  tooltip.style.color = 'white';
  tooltip.style.borderRadius = '4px';
  tooltip.style.pointerEvents = 'none';
  tooltip.style.opacity = 0;
  tooltip.style.transition = 'opacity 0.2s';
  tooltip.style.zIndex = 5;
  document.body.appendChild(tooltip);

  change_dict.forEach(time => {
    const marker = document.createElement('div');
    marker.classList.add('marker');
    const percent = (time / video.duration) * 100;
    marker.style.left = `${percent}%`;

    marker.addEventListener('click', async (e) => {
      await stopCurrentTask();
      currentMode = null;
      video.pause();
      video.currentTime = time;
      subtitle.textContent = ``;
    });

    marker.addEventListener('mouseover', (e) => {
      let currentTime = formatTime(time);
      const subText = descript_dict[time]["descript"] + ' 현재 시간: ' + currentTime;
      tooltip.textContent = subText;
      const rect = e.target.getBoundingClientRect();
      tooltip.style.left = `${rect.left + window.scrollX}px`;
      tooltip.style.top = `${rect.top + window.scrollY - 28}px`;
      tooltip.style.opacity = 1;
    });

    marker.addEventListener('mouseout', () => {
      tooltip.style.opacity = 0;
    });

    progressContainer.appendChild(marker);
  });
}

async function makeThumbnail() {
  const panorama = document.getElementById("panorama");
  panorama.innerHTML = ""; // 기존 썸네일 초기화

  Object.keys(change_dict).forEach(timeStr => {
    const time = parseInt(timeStr);

    // sample_list에서 Time이 일치하는 항목을 찾음
    const matched = sample_list.find(item => item.Time === time);
    if (!matched) return;

    const img = document.createElement("img");
    img.src = matched.File_path; // 경로 지정
    img.title = `${formatTime(time)} - ${change_dict[time]}`;
    img.style.margin = "5px";
    img.style.height = "80px";
    img.style.cursor = "pointer";

    img.addEventListener("click", () => {
      video.currentTime = time;
    });

    panorama.appendChild(img);
  });
}