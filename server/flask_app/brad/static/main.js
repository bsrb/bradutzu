function main() {
  if (window.location.pathname === "/") {
    setInterval(update_now_playing, 2000);
  }
}

function update_now_playing() {
  const now_playing = document.getElementById("currentlyPlaying");
  fetch("/nowplaying")
    .then((response) => {
      if (!response.ok) {
        return Promise.reject(response);
      }
      return response.json();
    })
    .then((data) => {
      now_playing.innerHTML = data.data;
    })
    .catch((error) => {
      now_playing.innerHTML = "Error fetching data: " + error;
    });
}

function upload_file() {
  const upload_status = document.getElementById("uploadStatus");
  upload_status.classList.add("hidden");

  // Check if we have input
  const animation_name = document.getElementById("animationName");
  if (animation_name.value === "") {
    upload_status.innerHTML = "Animation name must not be empty.";
    upload_status.classList.remove("hidden");
    return;
  }
  const animation_file = document.getElementById("animationFile");
  if (animation_file.files.length === 0) {
    upload_status.innerHTML = "You must select an animation file.";
    upload_status.classList.remove("hidden");
    return;
  }
  // We're good, upload
  upload_status.innerHTML = "Uploading...";
  upload_status.classList.remove("hidden");

  upload_button = document.getElementById("uploadButton");
  upload_button.disabled = true;

  const test_only = document.getElementById("testOnly");

  var payload = new FormData();
  payload.append("filecontent", animation_file.files[0]);
  payload.append("filename", animation_name.value);
  payload.append("test", test_only.checked);
  fetch("/upload", {
    method: "POST",
    body: payload,
  })
    .then((response) => {
      if (!response.ok) {
        return Promise.reject(response);
      }
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        if (test_only.checked) {
          upload_status.innerHTML = data.message;
          upload_status.classList.remove("hidden");
          upload_button.disabled = false;
        } else {
          location.reload();
        }
      } else {
        upload_status.innerHTML = data.message;
        upload_status.classList.remove("hidden");
        upload_button.disabled = false;
      }
    })
    .catch((response) => {
      upload_status.innerHTML = "There was an error uploading the file...";
      upload_status.classList.remove("hidden");
      upload_button.disabled = false;
    });
}

function download_file(id) {
  window.location.href = "/download/" + id;
}

var first_click_id = "";
function delete_file(id) {
  if (first_click_id === id) {
    window.location.href = "/delete/" + id;
  } else {
    delete_button = document.getElementById("delete" + id);
    delete_button.innerHTML = "Click again";
    first_click_id = id;
  }
}
