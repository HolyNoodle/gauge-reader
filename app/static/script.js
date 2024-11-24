const config = {
  crop: {
    top_left: {
      x: 180,
      y: 90,
    },
    bottom_right: {
      x: 330,
      y: 280,
    },
  },
  center: {
    x: 72,
    y: 100,
  },
  axis: {
    x: 131,
    y: 180,
  },
  start_angle: 144.5,
  end_angle: 404.0,
  start_range: 0.4,
  end_range: 10,
  min_line_length: 10,
  max_line_gap: 1,
  threshold_value: 90,
  threshold_brightness: 255,
  min_line_length: 40,
  max_line_gap: 1,
  threshold_reverse: false,
};

const getGaugeValue = (file, config) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onloadend = () => {
      const base64String = reader.result
        .replace("data:", "")
        .replace(/^.+,/, "");
      fetch("http://localhost:8000/gauge_value", {
        method: "POST",
        body: JSON.stringify({
          image: base64String,
          config,
        }),
        headers: {
          "Content-type": "application/json",
        },
      })
        .then((data) => {
          data.json().then((data) => resolve(data.value));
        })
        .catch(reject);
    };

    reader.readAsDataURL(file);
  });
};

const get_last_images = () => {
  return new Promise((resolve, reject) => {
    fetch("http://localhost:8000/last_images")
      .then((data) => {
        data.json().then(resolve).catch(reject);
      })
      .catch(reject);
  });
};

const getGaugeDebugInfo = (file, config) => {
  return new Promise((resolve, reject) => {
    fetch("http://localhost:8000/debug_image", {
      method: "POST",
      body: JSON.stringify({
        image: file,
        config,
      }),
      headers: {
        "Content-type": "application/json",
      },
    })
      .then((data) => {
        data.json().then(resolve).catch(reject);
      })
      .catch(reject);
  });
};

const executeButton = document.getElementById("execute");
const valueResult = document.getElementById("value");
const debugImage = document.getElementById("debug_image");
const thresholdImage = document.getElementById("threshold_image");
const fileInput = document.getElementById("file_input");
const inputImage = document.getElementById("input_image");
const configInput = document.getElementById("config");
const actions = document.getElementById("actions");
const selectCropStart = document.getElementById("select_crop_start");
const selectCropEnd = document.getElementById("select_crop_end");
const selectCenter = document.getElementById("select_center");
const selectStartAngle = document.getElementById("select_start_angle");
const selectEndAngle = document.getElementById("select_end_angle");

executeButton.addEventListener("click", () => {
  const file = inputImage.src.replace("data:image/png;base64,", "");
  const config = JSON.parse(configInput.value);

  getGaugeDebugInfo(file, config).then((debugInfo) => {
    debugImage.src = `data:image/png;base64,${debugInfo.image}`;
    thresholdImage.src = `data:image/png;base64,${debugInfo.debug}`;
    valueResult.innerText = debugInfo.value;
  });
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];

  const reader = new FileReader();
  reader.onloadend = () => {
    inputImage.src = reader.result;

    actions.style.display = "flex";
  };

  reader.readAsDataURL(file);
});

configInput.value = JSON.stringify(config, null, 2);

selectCropStart.addEventListener("click", () => {
  const listener = (e) => {
    const config = JSON.parse(configInput.value);
    const rect = inputImage.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    config.crop.top_left.x = math.round(x);
    config.crop.top_left.y = math.round(y);

    configInput.value = JSON.stringify(config, null, 2);

    inputImage.removeEventListener("click", listener);
  };

  inputImage.addEventListener("click", listener);
});

selectCropEnd.addEventListener("click", () => {
  const listener = (e) => {
    const config = JSON.parse(configInput.value);
    const rect = inputImage.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    config.crop.bottom_right.x = Math.round(x);
    config.crop.bottom_right.y = Math.round(y);

    configInput.value = JSON.stringify(config, null, 2);

    inputImage.removeEventListener("click", listener);
  };

  inputImage.addEventListener("click", listener);
});

selectCenter.addEventListener("click", () => {
  const listener = (e) => {
    const config = JSON.parse(configInput.value);
    const rect = inputImage.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    config.center.x = Math.round(x) - config.crop.top_left.x;
    config.center.y = Math.round(y) - config.crop.top_left.y;

    configInput.value = JSON.stringify(config, null, 2);

    inputImage.removeEventListener("click", listener);
  };

  inputImage.addEventListener("click", listener);
});

selectStartAngle.addEventListener("click", () => {
  const listener = (e) => {
    const config = JSON.parse(configInput.value);
    const rect = inputImage.getBoundingClientRect();
    const x = e.clientX - rect.left - config.crop.top_left.x;
    const y = e.clientY - rect.top - config.crop.top_left.y;

    config.start_angle =
      Math.atan2(y - config.center.y, x - config.center.x) * (180 / Math.PI);

    if (config.start_angle < 0) {
      config.start_angle += 360;
    }

    configInput.value = JSON.stringify(config, null, 2);

    inputImage.removeEventListener("click", listener);
  };

  inputImage.addEventListener("click", listener);
});

selectEndAngle.addEventListener("click", () => {
  const listener = (e) => {
    const config = JSON.parse(configInput.value);
    const rect = inputImage.getBoundingClientRect();
    const x = e.clientX - rect.left - config.crop.top_left.x;
    const y = e.clientY - rect.top - config.crop.top_left.y;

    config.end_angle =
      Math.atan2(y - config.center.y, x - config.center.x) * (180 / Math.PI);

    if (config.end_angle < 0) {
      config.end_angle += 360;
    }

    if (config.end_angle < config.start_angle) {
      config.end_angle += 360;
    }

    configInput.value = JSON.stringify(config, null, 2);

    inputImage.removeEventListener("click", listener);
  };

  inputImage.addEventListener("click", listener);
});

get_last_images().then((data) => {
  data.images.forEach((image) => {
    const img = document.createElement("img");
    img.src = `data:image/png;base64,${image.content}`;
    document.body.appendChild(img);

    img.addEventListener("click", () => {
      inputImage.src = img.src;

      actions.style.display = "flex";
    });
  });
});
