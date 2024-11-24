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

const getGaugeDebugInfo = (file, config) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onloadend = () => {
      const base64String = reader.result
        .replace("data:", "")
        .replace(/^.+,/, "");
      fetch("http://localhost:8000/debug_image", {
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
          data.json().then(resolve).catch(reject);
        })
        .catch(reject);
    };

    reader.readAsDataURL(file);
  });
};

const executeButton = document.getElementById("execute");
const valueResult = document.getElementById("value");
const debugImage = document.getElementById("debug_image");
const thresholdImage = document.getElementById("threshold_image");
const fileInput = document.getElementById("file_input");
const inputImage = document.getElementById("input_image");
const configInput = document.getElementById("config");

executeButton.addEventListener("click", () => {
  const file = fileInput.files[0];
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
  };

  reader.readAsDataURL(file);
});

configInput.value = JSON.stringify(config, null, 2);