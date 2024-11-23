import cv2
import numpy as np

def find_ellipses(image: cv2.typing.MatLike, number_of_shape_countours_threshold: int):
  # Convert the image to grayscale
  gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

  # Apply a threshold filter
  _, threshold_image = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

  # Find contours in the threshold image
  contours, _ = cv2.findContours(threshold_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

  ellipses = []
  # Loop over the contours
  for contour in contours:
      # Fit an ellipse to the contour
      if len(contour) >= number_of_shape_countours_threshold:
          ellipse = cv2.fitEllipse(contour)
          
          ellipses.append(ellipse)
      
  return ellipses

def crop_image_to_ellipsis(ellipse: cv2.typing.MatLike, source: cv2.typing.MatLike):
  top_left_x = int(ellipse[0][0] - ellipse[1][0] / 2)
  top_left_y = int(ellipse[0][1] - ellipse[1][1] / 2)
  bottom_right_x = int(ellipse[0][0] + ellipse[1][0] / 2)
  bottom_right_y = int(ellipse[0][1] + ellipse[1][1] / 2)

  # Crop the image to the bounding box
  cropped_image = source[top_left_y:bottom_right_y, top_left_x:bottom_right_x].copy()

  new_center = (int(ellipse[0][0] - top_left_x), int(ellipse[0][1] - top_left_y))
  new_size = (ellipse[1][0], ellipse[1][1])
  new_ellipse = (new_center, new_size, ellipse[2])

  return (cropped_image, new_ellipse, (top_left_x, top_left_y, bottom_right_x, bottom_right_y))

def find_needle(image: cv2.typing.MatLike, ellipse: cv2.typing.MatLike, threshold_value: int, threshold_brightness: int, minLineLength:int, maxLineGap: int, reverse: bool = False):
  gray2 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  mode = cv2.THRESH_BINARY if reverse else cv2.THRESH_BINARY_INV

  _, dst2 = cv2.threshold(gray2, threshold_value, threshold_brightness, mode)

  lines = cv2.HoughLinesP(image=dst2, rho=3, theta=np.pi / 180, threshold=100, minLineLength=minLineLength, maxLineGap=maxLineGap)

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
    distance1 = np.sqrt((x1 - center[0])**2 + (y1 - center[1])**2)
    distance2 = np.sqrt((x2 - center[0])**2 + (y2 - center[1])**2)

    min_dist = min(distance1, distance2)
    max_dist = max(distance1, distance2)
    dists.append(min_dist)

    line_contour = np.array([[x1, y1], [x2, y2]])
    is_center_on_line = cv2.pointPolygonTest(line_contour, center, False) >= 0

    length = np.linalg.norm([x2 - x1, y2 - y1])

    # Check if the center of the ellipse is on the line
    center_radius = max(radiusX, radiusY)
    if (is_center_on_line or min_dist < center_radius * 0.40) and (max_dist < center_radius * 1.1 and max_dist > center_radius * 0.6):
      line_lengths.append(length)
      filtered_lines.append(line)

  if len(line_lengths) == 0:
    return (None, filtered_lines, lines, dst2)

  longest_line_index = max(range(len(filtered_lines)), key=lambda x: line_lengths[x])

  x1, y1, x2, y2 = filtered_lines[longest_line_index][0]

  # Calculate distances from the center to the endpoints of the longest line
  distance_to_x1_y1 = np.sqrt((x1 - center[0])**2 + (y1 - center[1])**2)
  distance_to_x2_y2 = np.sqrt((x2 - center[0])**2 + (y2 - center[1])**2)

  # Determine the point that is further away from the center
  if distance_to_x1_y1 > distance_to_x2_y2:
    furthest_point = (int(x1), int(y1))
  else:
    furthest_point = (int(x2), int(y2))

  return (furthest_point, filtered_lines, lines, dst2)

def calculate_gauge_value(ellipse: cv2.typing.MatLike, needle: cv2.typing.Point, start_gauge_angle: int, end_gauge_angle: int, start_range: int, end_range: int):
    center = ellipse[0]

    radius_x = ellipse[1][0] / 2
    radius_y = ellipse[1][1] / 2

    start_angle_rad = np.radians(start_gauge_angle)
    end_angle_rad = np.radians(end_gauge_angle)

    start_point = (int(center[0] + radius_x * np.cos(start_angle_rad) ),
          int(center[1] - radius_y * np.sin(start_angle_rad)))
    end_point = (int(center[0] + radius_x * np.cos(end_angle_rad)),
          int(center[1] - radius_y * np.sin(end_angle_rad)))
    
    print(start_point, end_point, needle)

    ellipsis_perimeter_length = 2 * np.pi * np.sqrt((radius_x ** 2 + radius_y ** 2) / 2)

    needle_angle = abs(np.arctan2(needle[1] - center[1], needle[0] - center[0]))

    distance = abs(needle_angle - start_angle_rad) #np.sqrt((needle[0] - start_point[0])**2 + (needle[1] - start_point[1])**2)
    distance_ignored = abs(end_angle_rad - start_angle_rad) #np.sqrt((start_point[0] - end_point[0])**2 + (start_point[1] - end_point[1])**2)

    gauge_actual_size = 2 * np.pi - distance_ignored #ellipsis_perimeter_length - distance_ignored
    ratio = distance / gauge_actual_size

    print(distance, distance_ignored, ellipsis_perimeter_length, ratio, gauge_actual_size)

    return ratio * (end_range - start_range) + start_range
