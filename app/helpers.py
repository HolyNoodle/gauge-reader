import cv2
import numpy as np

def find_needle(
    image: cv2.typing.MatLike,
    ellipse: cv2.typing.MatLike,
    threshold_value: int,
    threshold_brightness: int,
    minLineLength: int,
    maxLineGap: int,
    reverse: bool = False,
):
    gray2 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mode = cv2.THRESH_BINARY if reverse else cv2.THRESH_BINARY_INV

    _, dst2 = cv2.threshold(gray2, threshold_value, threshold_brightness, mode)

    lines = cv2.HoughLinesP(
        image=dst2,
        rho=3,
        theta=np.pi / 180,
        threshold=100,
        minLineLength=minLineLength,
        maxLineGap=maxLineGap,
    )
  
    center = ellipse[0]
    radiusX = ellipse[1][0] / 2
    radiusY = ellipse[1][1] / 2
    filtered_lines = []
    dists = []

    if lines is None:
        return (None, [], [], dst2)

    line_lengths = []

    # Filter lines that are close to the center
    for line in lines:
        x1, y1, x2, y2 = line[0]
        distance1 = np.sqrt((x1 - center[0]) ** 2 + (y1 - center[1]) ** 2)
        distance2 = np.sqrt((x2 - center[0]) ** 2 + (y2 - center[1]) ** 2)

        min_dist = min(distance1, distance2)
        max_dist = max(distance1, distance2)
        dists.append(min_dist)

        line_contour = np.array([[x1, y1], [x2, y2]])
        is_center_on_line = cv2.pointPolygonTest(line_contour, center, False) >= 0

        length = np.linalg.norm([x2 - x1, y2 - y1])

        # Check if the center of the ellipse is on the line
        center_radius = max(radiusX, radiusY)
        if (is_center_on_line or min_dist < center_radius * 0.40) and (
            max_dist < center_radius * 1.1 and max_dist > center_radius * 0.6
        ):
            line_lengths.append(length)
            filtered_lines.append(line)

    if len(line_lengths) == 0:
        return (None, filtered_lines, lines, dst2)

    longest_line_index = max(range(len(filtered_lines)), key=lambda x: line_lengths[x])

    x1, y1, x2, y2 = filtered_lines[longest_line_index][0]

    # Calculate distances from the center to the endpoints of the longest line
    distance_to_x1_y1 = np.sqrt((x1 - center[0]) ** 2 + (y1 - center[1]) ** 2)
    distance_to_x2_y2 = np.sqrt((x2 - center[0]) ** 2 + (y2 - center[1]) ** 2)

    # Determine the point that is further away from the center
    if distance_to_x1_y1 > distance_to_x2_y2:
        furthest_point = (int(x1), int(y1))
    else:
        furthest_point = (int(x2), int(y2))

    return (furthest_point, filtered_lines, lines, dst2)


def calculate_gauge_value(
    ellipse: cv2.typing.MatLike,
    needle: float,
    start_gauge_angle: int,
    end_gauge_angle: int,
    start_range: int,
    end_range: int,
):
    start_angle_rad = np.deg2rad(start_gauge_angle)
    end_angle_rad = np.deg2rad(end_gauge_angle)

    center = ellipse[0]
    needle_angle_rad = np.arctan2(needle[1] - center[1], needle[0] - center[0])
    needle_angle = np.degrees(needle_angle_rad)
    needle_angle_rad = np.deg2rad(needle_angle)

    if needle_angle_rad < 0:
        needle_angle_rad += 2 * np.pi

    distance = needle_angle_rad - start_angle_rad

    gauge_actual_size = end_angle_rad - start_angle_rad
    ratio = distance / gauge_actual_size

    return ratio * (end_range - start_range) + start_range


class GaugeValueExtractor:
    def __init__(
        self,
        crop_top_left: cv2.typing.Point,
        crop_bottom_right: cv2.typing.Point,
        threshold_value: int,
        threshold_brightness: int,
        threshold_reverse: bool,
        minLineLength: int,
        maxLineGap: int,
        start_gauge_angle: int,
        end_gauge_angle: int,
        start_range: int,
        end_range: int,
        ellipse: cv2.typing.MatLike,
    ):
        self.crop_top_left = crop_top_left
        self.crop_bottom_right = crop_bottom_right
        self.threshold_value = threshold_value
        self.threshold_brightness = threshold_brightness
        self.threshold_reverse = threshold_reverse
        self.minLineLength = minLineLength
        self.maxLineGap = maxLineGap
        self.start_gauge_angle = start_gauge_angle
        self.end_gauge_angle = end_gauge_angle
        self.start_range = start_range
        self.end_range = end_range
        self.ellipse = ellipse

    def extract_value(
        self,
        image: cv2.typing.MatLike,
    ):
        cropped = image[self.crop_top_left[1]:self.crop_bottom_right[1], self.crop_top_left[0]:self.crop_bottom_right[0]]
        cropped = cropped.copy()

        needle, _, _, _ = find_needle(
            cropped,
            self.ellipse,
            self.threshold_value,
            self.threshold_brightness,
            self.minLineLength,
            self.maxLineGap,
            self.threshold_reverse,
        )

        if needle is None:
            return None
        
        return calculate_gauge_value(
            self.ellipse,
            needle,
            self.start_gauge_angle,
            self.end_gauge_angle,
            self.start_range,
            self.end_range,
        )
    
    def draw_debug_image(self, image: cv2.typing.MatLike):
        cropped = image[self.crop_top_left[1]:self.crop_bottom_right[1], self.crop_top_left[0]:self.crop_bottom_right[0]]
        cropped = cropped.copy()

        needle, filtered, lines, dst2 = find_needle(
            cropped,
            self.ellipse,
            self.threshold_value,
            self.threshold_brightness,
            self.minLineLength,
            self.maxLineGap,
            self.threshold_reverse,
        )

        cv2.ellipse(dst2, self.ellipse, (0, 255, 0), 2)

        # Draw all lines on dst2
        for line in lines:
            x1, y1, x2, y2 = line[0]
            cv2.line(dst2, (x1, y1), (x2, y2), (255, 0, 0), 1)

        # Draw filtered lines on dst2
        for line in filtered:
            x1, y1, x2, y2 = line[0]
            cv2.line(dst2, (x1, y1), (x2, y2), (0, 255, 0), 2)

        if needle is None:
            return None, dst2

        cv2.circle(cropped, needle, 5, (0, 0, 255), -1)

        # Draw the ellipse
        cv2.ellipse(cropped, self.ellipse, (0, 255, 0), 2)

        # Draw the start and end angles
        center = self.ellipse[0]
        radius = max(self.ellipse[1]) / 2

        start_angle_rad = np.deg2rad(self.start_gauge_angle)
        end_angle_rad = np.deg2rad(self.end_gauge_angle)

        start_point = (
            int(center[0] + radius * np.cos(start_angle_rad)),
            int(center[1] + radius * np.sin(start_angle_rad)),
        )
        end_point = (
            int(center[0] + radius * np.cos(end_angle_rad)),
            int(center[1] + radius * np.sin(end_angle_rad)),
        )

        cv2.line(cropped, center, start_point, (255, 0, 0), 2)
        cv2.line(cropped, center, end_point, (255, 0, 0), 2)

        # Draw the needle
        cv2.line(cropped, center, needle, (0, 0, 255), 2)

        return cropped, dst2
        
