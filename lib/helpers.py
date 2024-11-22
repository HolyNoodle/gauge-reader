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

def find_needle(image: cv2.typing.MatLike, ellipse: cv2.typing.MatLike, threshold_value: int, threshold_brightness: int, minLineLength:int, maxLineGap: int):
  gray2 = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
  _, dst2 = cv2.threshold(gray2, threshold_value, threshold_brightness, cv2.THRESH_BINARY_INV)

  lines = cv2.HoughLinesP(image=dst2, rho=3, theta=np.pi / 180, threshold=100,minLineLength=minLineLength, maxLineGap=maxLineGap)

  radiusX = ellipse[1][0] / 2
  radiusY = ellipse[1][1] / 2
  filtered_lines = []
  dists = []

  # Filter lines that are close to the center
  for line in lines:
    x1, y1, x2, y2 = line[0]
    distance1 = np.sqrt((x1 - radiusX)**2 + (y1 - radiusY)**2)
    distance2 = np.sqrt((x2 - radiusX)**2 + (y2 - radiusY)**2)

    min_dist = min(distance1, distance2)
    dists.append(min_dist)

    # center_radius = max(ellipse[1])
    # if min_dist < center_radius * 0.1:
    filtered_lines.append(line)

  # if len(filtered_lines) == 0:
  #   return (None, [], lines)
  
  # Compute the length of each filtered line
  line_lengths = [np.linalg.norm([line[0][2] - line[0][0], line[0][3] - line[0][1]]) for line in filtered_lines]
  line_lengths = [line_lengths[x] * 0.1 * 1/(dists[x]) for x in range(len(line_lengths))]

  longest_line_index = max(range(len(filtered_lines)), key=lambda x: line_lengths[x])

  x1, y1, x2, y2 = filtered_lines[longest_line_index][0]

  # Calculate distances from the center to the endpoints of the longest line
  distance_to_x1_y1 = np.sqrt((x1 - radiusX)**2 + (y1 - radiusY)**2)
  distance_to_x2_y2 = np.sqrt((x2 - radiusX)**2 + (y2 - radiusY)**2)

  # Determine the point that is further away from the center
  if distance_to_x1_y1 > distance_to_x2_y2:
    furthest_point = (int(x1), int(y1))
  else:
    furthest_point = (int(x2), int(y2))

  return (furthest_point, filtered_lines, lines)

def calculate_gauge_value(ellipse: cv2.typing.MatLike, needle: cv2.typing.Point, start_gauge_angle: int, end_gauge_angle: int, start_range: int, end_range: int):
    center = ellipse[0]

    radius_x = ellipse[1][0] / 2
    radius_y = ellipse[1][1] / 2

    start_angle_rad = np.deg2rad(start_gauge_angle)
    end_angle_rad = np.deg2rad(end_gauge_angle)

    start_point = (int(center[0] + radius_x * np.cos(start_angle_rad) ),
          int(center[1] - radius_y * np.sin(start_angle_rad)))
    end_point = (int(center[0] + radius_x * np.cos(end_angle_rad)),
          int(center[1] - radius_y * np.sin(end_angle_rad)))

    ellipsis_perimeter_length = 2 * np.pi * np.sqrt((radius_x ** 2 + radius_y ** 2) / 2)

    distance = np.linalg.norm(np.array(needle) - np.array(start_point))
    distance_ignored = np.linalg.norm(np.array(end_point) - np.array(start_point))
    ratio = distance / (ellipsis_perimeter_length - distance_ignored)

    return ratio * (end_range - start_range) + start_range