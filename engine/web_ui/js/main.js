let video;
let progressBar;
let timeDisplay;
let subtitle;
let frameCountDisplay;

let globalCurrentTime = 0;
let play_check = 0;
let currentMode = null;
let currentTask = null;
let filteredFrames = [];
let subtitles = [];

let selected_file = null
let video_name = null
let analyzed_video_infos = null

document.addEventListener("DOMContentLoaded", () => {
    // -------------------------------------------------
    imageInput = document.getElementById("imageFile");
    videoInput = document.getElementById('videoFile');
    dropArea = document.getElementById('drop-area');
    previewImage = document.getElementById("previewImage");
    video = document.getElementById('video');
    resetButton = document.getElementById('resetButton');
    analysisButton = document.getElementById("analysisButton");
    subtitleDiv = document.getElementById("subtitle");
    sampleTimeTF = document.getElementById("sampleTime");
    playVideoBtn = document.getElementById("playVideo");
    stopVideoBtn = document.getElementById("stopVideo");
    processTimeDiv = document.getElementById("processTime");
    timeDisplay = document.getElementById('timeDisplay');
    progressBar = document.getElementById('progressBar');
    progressContainer = document.getElementById('progressContainer');
    panoramaDiv = document.getElementById("panorama");
    excelVisDiv = document.getElementById('excelTableContainer')
    loadExcelBtn = document.getElementById('excel_button');
    resetExcelBtn = document.getElementById('excel_reset');

    // ----------------------------------------------------------------------
    // 새로 추가
    imageInput.addEventListener("change", () => {
        selected_file = imageInput.files[0];
        loadImageFile(selected_file)
    }); 

    // 영상 선택 시 영상 표시
    videoInput.addEventListener("change", () => {
        selected_file = videoInput.files[0];
        loadVideoFile(selected_file)
    });

    dropArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropArea.classList.add('highlight');
    });

    dropArea.addEventListener('dragleave', () => {
      dropArea.classList.remove('highlight');
    });

    dropArea.addEventListener('drop', (e) => {
      e.preventDefault();
      dropArea.classList.remove('highlight');
      selected_file = e.dataTransfer.files[0];
      handleFiles(selected_file);
    });

    // 선택된 파일 초기화
    resetButton.addEventListener("click", () => {
        resetFile()
    });

    analysisButton.addEventListener("click", () => {
        analysisFile()
    });

    playVideoBtn.addEventListener("click", () => {
        playVideo()
    });

    stopVideoBtn.addEventListener("click", () => {
        stopVideo()
    });

    loadExcelBtn.addEventListener("click", () => {
        loadExcelData()
    });

    resetExcelBtn.addEventListener("click", () => {
        excel_reset()
    });

    panoramaDiv.addEventListener('wheel', function (e) {
      // 세로 스크롤 시도를 가로 스크롤로 변환
      if (e.deltaY !== 0) {
        e.preventDefault();
        panoramaDiv.scrollLeft += e.deltaY;
      }
    });

    video.addEventListener('timeupdate', () => {
      const percent = (video.currentTime / video.duration) * 100;
      progressBar.style.width = percent + "%";

      if (!isNaN(video.duration)) {
        const current = formatTime(video.currentTime);
        const total = formatTime(video.duration);
        timeDisplay.textContent = `${current} / ${total}`;
      }

      // if (Math.floor(video.currentTime) in descript_dict) {
      //   console.log("자막이 표시됩니다.")
      //   subtitleDiv.textContent = descript_dict[Math.floor(video.currentTime)];
      // }
      analyzed_video_infos.forEach((video_info, idx)=>{
        time = video_info["time"]
        if(time == video.currentTime)
        {
          descript = video_info["result"]
          subtitleDiv.textContent = descript
          return
        }
      });
    })
});


// 시간 HH:MM:SS 형태로 변환
function formatTime(seconds) {
  const min = Math.floor(seconds / 60);
  const sec = Math.floor(seconds % 60);
  return `${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

async function loadImageFile(file){
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
}

async function loadVideoFile(file){    
    if (file && file.type.startsWith("video/")) {
        const url = URL.createObjectURL(file);
        video.src = url;
        video_name = file.name
        video.style.display = "block";
        previewImage.style.display = "none"; // 이미지 숨김
    }

    // 이미지 비활성화
    if (videoInput.files.length > 0) {
        imageInput.disabled = true;
    } else {
        imageInput.disabled = false;
    }
}

// 파일을 input[type="file"]에 주입하는 유틸리티
function setFilesToInput(inputElement, file) {
  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(file);
  inputElement.files = dataTransfer.files;
}

function handleFiles(file) {
  console.log("?")
  if (file && file.type.startsWith("image/")) {
    console.log("image")
    setFilesToInput(imageInput, file);
    loadImageFile(file)
  }
  else if (file && file.type.startsWith("video/")) {
    console.log("video")
    setFilesToInput(videoInput, file);
    console.log(videoInput.files[0].name)
    loadVideoFile(file)
  }
}

async function resetFile() {
    videoInput.disabled = false;
    imageInput.disabled = false;
    videoInput.value = ''
    imageInput.value = ''
    selected_file = null
    // previewImage.style.display = "none";
    // video.style.display = "none";
    video.src = "";
    video.currentTime = 0;
    analyzed_video_infos = null
    loadExcelBtn.style.display = "block";
    subtitleDiv.textContent = "여기에 자막이 표시됩니다.";
    progressBar.style.width = "0%";
    timeDisplay.textContent = "00:00 / 00:00";
    while (panoramaDiv.firstChild) {
      panoramaDiv.removeChild(panoramaDiv.firstChild);
    } 
    panoramaDiv.innerHTML = "";
    progressBar.innerHTML = "";
    excel_reset()
    processTimeDiv.textContent = '분석 프로세스 소요 시간 : -초';
}

async function analysisImageFile(img_file)
{
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

async function videoSampling(video_file, sample_time)
{
    subtitleDiv.textContent = "비디오 샘플링 중...";

    const formData = new FormData();
    formData.append("file", video_file);
    formData.append("sampling_interval", sample_time);
    const sampleRes = await fetch("/get_sample", {
      method: "POST",
      body: formData
    });
    const sampleData = await sampleRes.json();
    if (!sampleData) {
      subtitleDiv.textContent = "샘플 데이터 제작 실패";
      return;
    }

    return sampleData.sample_list
}

async function videoAnalyzing(video_name, sample_list)
{
    subtitleDiv.textContent = "영상 분석 중...";
      const vlmForm = new FormData();
      vlmForm.append("video_name", video_name);
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

    return vlmData.descript_dict
}

async function geneVideoAnalyzedResultExcel(video_name, descript_dict)
{
    subtitleDiv.textContent = "엑셀 파일 생성 중...";
      const excelForm = new FormData();
      excelForm.append("video_name", video_name);
      excelForm.append("video_infos", JSON.stringify(descript_dict));
      const excelRes = await fetch("/make_excel", {
        method: "POST",
        body: excelForm
      });

    subtitleDiv.textContent = "엑셀 파일 생성 완료.";

    return excelRes.json()
}

async function analysisFile(){
  const startTime = Date.now();
  const intervalId = setInterval(() => {
    const elapsedSec = Math.floor((Date.now() - startTime) / 1000);
    const sec = elapsedSec % 60;
    const min = Math.floor(elapsedSec / 60);
    const hour = Math.floor(min / 60);
    processTimeDiv.textContent = `분석 프로세스 소요 시간 : ${hour}시 ${min}분 ${sec}초`;
  }, 100);

    if(imageInput.disabled == false)
    {
        const img_file = selected_file;
        analysisImageFile(selected_file)
    }
    else if(videoInput.disabled == false)
    {
        console.log("analysisFile - video")
        const video_file = selected_file;

        if(!sampleTimeTF.value)
        {
          alert("샘플 간격을 입력해주세요.");
          return;
        }

        video_infos = await videoSampling(video_file, sampleTimeTF.value)
        video_infos = await videoAnalyzing(video_name, video_infos)
        excel_res = await geneVideoAnalyzedResultExcel(video_name, video_infos)

        scene_changed_video_infos = await sleepChangeCheck(video_infos);
        await addMarkersToProgressBar(scene_changed_video_infos);
        await makeThumbnail(scene_changed_video_infos);
        analyzed_video_infos = scene_changed_video_infos
        subtitleDiv.textContent = "영상 분석 완료.";
    }
    else
    {
        alert("파일을 선택해주세요.");
        return;
    }

    clearInterval(intervalId); // ✅ 타이머 종료는 항상 보장
}

//아기 수면 상태 전환 시점의 description 및 시간 정보 저장 함수
async function sleepChangeCheck(video_infos) {
  change_time = 0
  prev_descript = ""
  scene_changed_video_infos = []
  video_infos.forEach((video_info, idx) => {
    descript = video_info["result"]
    if(descript !== prev_descript)
    {
      scene_changed_video_infos.push(video_info)
      prev_descript = descript
    }
  });

  return scene_changed_video_infos
}

async function addMarkersToProgressBar(changed_scene_video_infos) {
    document.querySelectorAll('.marker').forEach(m => m.remove());

    if (!video.duration || video.duration === Infinity) return;

    let tooltip = document.getElementById('markerTooltip');
    if (!tooltip) {
        tooltip = document.createElement('div');
        tooltip.id = 'markerTooltip';
        document.body.appendChild(tooltip);
    }

    // const change_times = Object.keys(changed_scene_dict).map(Number);

   changed_scene_video_infos.forEach((video_info, idx) => {
        let time = video_info["time"];
        let timestamp = video_info["timestamp"];
        let descript = video_info["result"]
        
        const marker = document.createElement('div');
        marker.classList.add('marker');
        
        const percent = (time / video.duration) * 100;
        marker.style.left = `${percent}%`;

        marker.addEventListener('click', async (e) => {
            await stopCurrentTask();
            currentMode = null;
            video.pause();
            video.currentTime = time;
            subtitleDiv.textContent = '';
        });

        marker.addEventListener('mouseover', (e) => {
            const subText = descript + ' 현재 시간: ' + timestamp;
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

async function makeThumbnail(changed_scene_video_infos, sample_list) {
  panoramaDiv.innerHTML = ""; // 기존 썸네일 초기화

  if (!changed_scene_video_infos) return;

  // sample_list → Map 으로 변환 (Time → item)
  // const sampleMap = new Map(sample_list.map(item => [item.Time, item]));

  const fragment = document.createDocumentFragment();

  console.log(changed_scene_video_infos)

  changed_scene_video_infos.forEach((video_info, idx) => {
    const time = video_info["time"];
    const timestamp = video_info["timestamp"]
    const descript = video_info["descript"]
    const img_path = video_info["img_path"]

    const img = document.createElement("img");
    img.src = img_path;
    img.title = `${timestamp} - ${descript}`;
    img.classList.add("thumbnail-img");
    img.dataset.time = time;

    img.addEventListener("click", () => {
      video.currentTime = time;
    });

    fragment.appendChild(img);
  });

  panoramaDiv.appendChild(fragment);
}

async function playVideo() {
  console.log("play btn is clicked");
  const video_option = document.querySelector("select[name=video_option] option:checked").value;
  check_text = "";

  if (play_check == 0) {
    if (video_option == "none") {
      alert("영상 재생 방식을 선택해주세요.");
      return;
    }

    // 여기 추가 (모든 재생 방식 공통으로 영상 처음부터 시작)
    const video = document.getElementById('video');
    await new Promise(resolve => {
      if (!isNaN(video.duration)) {
        video.currentTime = 0;
        resolve();
      } else {
        video.addEventListener('loadedmetadata', () => {
          video.currentTime = 0;
          resolve();
        }, { once: true });
      }
    });

    if (video_option == "normal") {
      console.log("전체 재생");
      // if (currentMode === "normal") return;
      await stopCurrentTask();
      currentMode = "normal";
      video.play();
    }
    else if (video_option == "sample_play") {
      console.log("샘플 재생");

      if (!document.getElementById('sampleTime').value) {
        alert("샘플 간격을 입력하시오.");
        return;
      }
      // if (currentMode === "sample") return;
      await stopCurrentTask();
      currentMode = "sample";

      let cancel = false;
      currentTask = { cancel: () => cancel = true };

      const sampleInterval = Number(document.getElementById('sampleTime').value);
      
      while (video.currentTime < video.duration) {
        if (cancel) return;

        let nextTime = video.currentTime + sampleInterval;
        if (nextTime > video.duration) {
          nextTime = video.duration;
        }

        video.currentTime = nextTime;

        await new Promise(resolve => {
          function onSeeked() {
            video.removeEventListener('seeked', onSeeked);
            resolve();
          }
          video.addEventListener('seeked', onSeeked);
        });

        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    else if (video_option == "change_play") {
      console.log("전환 시점 재생");
      if (!analyzed_video_infos) {
        alert("먼저 영상을 업로드하여 분석을 완료해주세요.");
        return;
      }
      // if (currentMode === "change") return;
      await stopCurrentTask();
      currentMode = "change";

      let cancel = false;
      currentTask = { cancel: () => cancel = true };

      changeTime = 0;
      prev_descript = ""
      for (let i = 0; i < analyzed_video_infos.length; i++) {
        const video_info = analyzed_video_infos[i];

        if (cancel) return;
        let time = video_info["time"];
        let timestamp = video_info["timestamp"];
        let descript = video_info["result"];
        video.currentTime = time;
        video.play();
        await new Promise(resolve => video.onseeked = () => resolve());
        await new Promise(resolve => setTimeout(resolve, 1000));
        video.pause();
      }
    }
    else if (video_option == "sleep_time_play") {
      console.log("결과 재생");
      if (!analyzed_video_infos) {
        alert("먼저 영상을 업로드하여 분석을 완료해주세요.");
        return;
      }
      // if (currentMode === "sleep_time") return;
      await stopCurrentTask();
      currentMode = "sleep_time";

      let cancel = false;
      currentTask = { cancel: () => cancel = true };

      for (let i = 0; i < analyzed_video_infos.length; i++) {
          const video_info = analyzed_video_infos[i];

          if (cancel) return;
          let time = video_info["time"];
          let timestamp = video_info["timestamp"];
          let descript = video_info["result"];
          video.currentTime = time;
          console.log(time)
          console.log(descript)

          if (descript == "Sleep") {
            if (cancel) return;
            video.currentTime = time
            console.log(10)
            video.play();
            await new Promise(resolve => video.onseeked = () => resolve());
            await new Promise(resolve => setTimeout(resolve, Number(document.getElementById("sleepTime").value * 1000)));
            video.pause();
          } 
          else {
            if (cancel) return;
            let next_time = 0
            for (let j = i+1; j < analyzed_video_infos.length; j++) {
              const video_info = analyzed_video_infos[j];

              if (cancel) return;
              let j_time = video_info["time"];
              let j_timestamp = video_info["timestamp"];
              let j_descript = video_info["result"];

              if(j == analyzed_video_infos.length - 1)
              {
                next_time = video.duration
              }
              else if(j_descript == "Sleep")
              {
                next_time = j_time
              }
            }
            run_time = next_time - video.currentTime
            console.log(run_time)
            video.currentTime = time
            video.play();
            await new Promise(resolve => video.onseeked = () => resolve());
            await new Promise(resolve => setTimeout(resolve, run_time * 1000));
            video.pause();
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

async function stopVideo() {
  console.log("stop btn is clicked")
  changeTime = 0;
  currentMode = null;
  video.currentTime = 0;
  video.pause();
  await stopCurrentTask();
}

async function loadExcelData() {
  const video_file = videoInput.files[0];

  if (!video_file) {
    alert("동영상을 선택해주세요.");
    return;
  }

  loadExcelBtn.style.display = 'none';

  const formData = new FormData();
  formData.append("file", video_file);

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
  table.style.border = 'none';  // 테두리는 th/td에서만

  const thead = document.createElement('thead');
  const headerRow = document.createElement('tr');

  result.columns.forEach(col => {
    const th = document.createElement('th');
    th.textContent = col;
    th.style.padding = '12px 8px';
    th.style.border = '1px solid #ddd';
    th.style.backgroundColor = '#f4f6fa';
    th.style.textAlign = 'left';
    th.style.position = 'sticky';
    th.style.top = '0';
    th.style.zIndex = '2';
    headerRow.appendChild(th);
  });

  thead.appendChild(headerRow);
  table.appendChild(thead);

  const tbody = document.createElement('tbody');
  result.data.forEach(row => {
    const tr = document.createElement('tr');
    row.forEach((cell, colIndex) => {
      const td = document.createElement('td');
      td.style.padding = '10px 8px';
      td.style.border = '1px solid #eee';
      td.style.color = '#222';

      if (colIndex === 0 && typeof cell === 'string' && cell.trim() !== '') {
        const img = document.createElement('img');
        img.src = cell.trim();
        img.style.height = '80px';
        img.style.objectFit = 'contain';
        img.style.display = 'block';
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

  resetExcelBtn.style.display = 'block';
}

async function excel_reset() {
  // const container = document.getElementById('excelTableContainer');
  excelVisDiv.innerHTML = '';
  loadExcelBtn.style.display = 'block';
  resetExcelBtn.style.display = 'none'

}

//비동기 작업 및 현재 작업 중단 함수
async function stopCurrentTask() {
  if (currentTask && typeof currentTask.cancel === "function") {
    currentTask.cancel();
  }
  await new Promise(resolve => setTimeout(resolve, 100));
  currentMode = null;
}