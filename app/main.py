from fastapi import FastAPI
from fastapi import Form
from pydantic import BaseModel

from typing import Any

import cv2
import numpy as np

from helpers import GaugeValueExtractor
import base64
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/app", StaticFiles(directory="static", html=True), name="static")

class Point(BaseModel):
    x: int
    y: int


class CropConfig(BaseModel):
    top_left: Point
    bottom_right: Point


class GaugeConfig(BaseModel):
    crop: CropConfig
    center: Point
    axis: Point
    start_angle: float
    end_angle: float
    start_range: float = 0
    end_range: float = 100
    min_line_length: int = 100
    max_line_gap: int = 10
    threshold_value: int = 120
    threshold_brightness: int = 255
    threshold_reverse: bool = False


class InputImage(BaseModel):
    config: GaugeConfig
    image: str


@app.post("/gauge_value")
async def get_gauge_value(params: InputImage):
    extractor = GaugeValueExtractor(
        (params.config.crop.top_left.x, params.config.crop.top_left.y),
        (params.config.crop.bottom_right.x, params.config.crop.bottom_right.y),
        params.config.threshold_value,
        params.config.threshold_brightness,
        params.config.threshold_reverse,
        params.config.min_line_length,
        params.config.max_line_gap,
        params.config.start_angle,
        params.config.end_angle,
        params.config.start_range,
        params.config.end_range,
        (
            (params.config.center.x, params.config.center.y),
            (params.config.axis.x, params.config.axis.y),
            0,
        ),
    )

    image_data = base64.b64decode(params.image)

    np_arr = np.frombuffer(image_data, np.uint8)
    cv2_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    return {"value": extractor.extract_value(cv2_image)}


@app.post("/debug_image")
async def get_debug_image(params: InputImage):
    extractor = GaugeValueExtractor(
        (params.config.crop.top_left.x, params.config.crop.top_left.y),
        (params.config.crop.bottom_right.x, params.config.crop.bottom_right.y),
        params.config.threshold_value,
        params.config.threshold_brightness,
        params.config.threshold_reverse,
        params.config.min_line_length,
        params.config.max_line_gap,
        params.config.start_angle,
        params.config.end_angle,
        params.config.start_range,
        params.config.end_range,
        (
            (params.config.center.x, params.config.center.y),
            (params.config.axis.x, params.config.axis.y),
            0,
        ),
    )

    image_data = base64.b64decode(params.image)
    np_arr = np.frombuffer(image_data, np.uint8)
    cv2_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    debug_image, dst2 = extractor.draw_debug_image(cv2_image)
    base_64_image = base64.b64encode(cv2.imencode(".jpg", debug_image)[1]).decode() if debug_image is not None else None
    base_64_dst2 = base64.b64encode(cv2.imencode(".jpg", dst2)[1]).decode()

    return {
        "value": extractor.extract_value(cv2_image),
        "image": base_64_image,
        "debug": base_64_dst2,
    }
