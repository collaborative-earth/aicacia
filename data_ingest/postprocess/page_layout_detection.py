import os
import cv2
import numpy as np

from data_ingest.postprocess.models import Bounds, LayoutType, Element

VERTICAL_SLICE_WIDTH = 20

VERTICAL_SLICE_Y_BORDER_THRESHOLD = 0.15


def __is_inside(inner: Bounds, outer: Bounds) -> bool:
    if inner.left >= outer.left and inner.right <= outer.right and inner.top >= outer.top and inner.bottom <= outer.bottom:
        return True

    return False


def __has_elements_inside(outer: Bounds, elements: list[Bounds]):
    for e in elements:
        if __is_inside(e, outer):
            return True

    return False


def __most_frequent_colour(page_image: cv2.typing.MatLike):
    small_page_image = cv2.resize(page_image, (100, 100))
    pixels = small_page_image.reshape(-1, 3)
    values, counts = np.unique(pixels, axis=0, return_counts=True)
    most_frequent_colour = values[np.argmax(counts)]
    return most_frequent_colour


def __are_pixels_same_colour(image: cv2.typing.MatLike, colour) -> bool:
    pixels = image.reshape(-1, 3)
    unique_colors = np.unique(pixels, axis=0)
    unique_count, _ = unique_colors.shape

    if unique_count > 1:
        return False
    elif np.all(unique_colors == colour):
        return True
    else:
        return False


def __first_upward_row_different_from_colour(top, bottom, left, right, image: cv2.typing.MatLike, colour, mid_row=None) -> int:
    if not mid_row:
        mid_row = (bottom + top) // 2

    for r in range(mid_row, top, -1):
        if not __are_pixels_same_colour(image[r][left: right], colour):
            return r

    return 0


def __first_downward_row_different_from_colour(top, bottom, left, right, image: cv2.typing.MatLike, colour, mid_row=None) -> int:
    if not mid_row:
        mid_row = (bottom + top) // 2

    for r in range(mid_row, bottom):
        if not __are_pixels_same_colour(image[r][left: right], colour):
            return r

    return bottom


def __first_upward_slice_row_intersecting_box(top, bottom, left, right, page_boxes: list[Bounds], mid_row=None) -> int:
    horizontally_intersecting_page_boxes = [box for box in page_boxes if not (box.right < left or box.left > right)]

    if not mid_row:
        mid_row = (bottom + top) // 2

    # Check if any box contains mid_row point
    if any([box.bottom >= mid_row >= box.top for box in horizontally_intersecting_page_boxes]):
        return mid_row

    # If not, pick the closest from above
    upper_page_boxes = [box for box in horizontally_intersecting_page_boxes if box.bottom < mid_row]

    if upper_page_boxes:
        bound = min(upper_page_boxes, key=lambda box: mid_row - box.bottom)
        return bound.bottom
    else:
        return top


def __first_downward_slice_row_intersecting_box(top, bottom, left, right, page_boxes: list[Bounds], mid_row=None) -> int:
    horizontally_intersecting_page_boxes = [box for box in page_boxes if not (box.right < left or box.left > right)]

    if not mid_row:
        mid_row = (bottom + top) // 2

    # Check if any box contains mid_row point
    if any([box.bottom >= mid_row >= box.top for box in horizontally_intersecting_page_boxes]):
        return mid_row

    # If not, pick the closest from below
    lower_page_boxes = [box for box in horizontally_intersecting_page_boxes if box.top > mid_row]

    if lower_page_boxes:
        bound = min(lower_page_boxes, key=lambda box: box.top - mid_row)
        return bound.top
    else:
        return bottom


def __detect(page_image: cv2.typing.MatLike, page_boxes: list[Bounds]) -> list[tuple[Bounds, LayoutType]]:
    search_area = Bounds(top=0, left=0, bottom=page_image.shape[0], right=page_image.shape[1])

    # If no elements are on page, return empty list
    if not page_boxes:
        return []

    # Set up vertical slice bounds
    y_top = min([element.top for element in page_boxes])
    y_bottom = max([element.bottom for element in page_boxes])
    vertical_slice_left = search_area.center_x() - (VERTICAL_SLICE_WIDTH // 2)
    vertical_slice_right = search_area.center_x() + (VERTICAL_SLICE_WIDTH // 2)

    background_colour = __most_frequent_colour(page_image)

    # Check if all colours in vertical slice are the same and both columns are not empty
    if __are_pixels_same_colour(page_image[y_top: y_bottom, vertical_slice_left: vertical_slice_right], background_colour):
        page_zones = [
            (Bounds(top=y_top, left=search_area.left, bottom=y_bottom, right=vertical_slice_left), LayoutType.TWO_COLUMNS_LEFT),
            (Bounds(top=y_top, left=vertical_slice_right, bottom=y_bottom, right=search_area.right), LayoutType.TWO_COLUMNS_RIGHT)
        ]

        if all([__has_elements_inside(zone[0], page_boxes) for zone in page_zones]):
            return page_zones

    # Check if there's a white slice in the middle of sufficient height
    height = y_bottom - y_top

    mid = (y_top + y_bottom) // 2

    slice_upper_border = max(
        __first_upward_row_different_from_colour(y_top, y_bottom, vertical_slice_left, vertical_slice_right, page_image, background_colour, mid_row=mid),
        __first_upward_slice_row_intersecting_box(y_top, y_bottom, vertical_slice_left, vertical_slice_right, page_boxes, mid_row=mid)
    )

    slice_lower_border = min(
        __first_downward_row_different_from_colour(y_top, y_bottom, vertical_slice_left, vertical_slice_right, page_image, background_colour, mid_row=mid),
        __first_downward_slice_row_intersecting_box(y_top, y_bottom, vertical_slice_left, vertical_slice_right, page_boxes, mid_row=mid)
    )

    if slice_upper_border <= y_top + height * VERTICAL_SLICE_Y_BORDER_THRESHOLD and slice_lower_border >= y_bottom - height * VERTICAL_SLICE_Y_BORDER_THRESHOLD:
        page_zones = [
            (Bounds(top=slice_upper_border, left=search_area.left, bottom=slice_lower_border, right=vertical_slice_left), LayoutType.TWO_COLUMNS_LEFT),
            (Bounds(top=slice_upper_border, left=vertical_slice_right, bottom=slice_lower_border, right=search_area.right), LayoutType.TWO_COLUMNS_RIGHT)
        ]

        return page_zones

    # Check starting from 1/4 height point if page is "inverted T"-shaped
    mid = int(y_top + (y_bottom - y_top) * 0.25)

    slice_upper_border = max(
        __first_upward_row_different_from_colour(y_top, y_bottom, vertical_slice_left, vertical_slice_right, page_image, background_colour, mid_row=mid),
        __first_upward_slice_row_intersecting_box(y_top, y_bottom, vertical_slice_left, vertical_slice_right, page_boxes, mid_row=mid)
    )

    slice_lower_border = min(
        __first_downward_row_different_from_colour(y_top, y_bottom, vertical_slice_left, vertical_slice_right, page_image, background_colour, mid_row=mid),
        __first_downward_slice_row_intersecting_box(y_top, y_bottom, vertical_slice_left, vertical_slice_right, page_boxes, mid_row=mid)
    )

    if slice_upper_border <= y_top + height * VERTICAL_SLICE_Y_BORDER_THRESHOLD:
        page_zones = [
            (Bounds(top=slice_upper_border, left=search_area.left, bottom=slice_lower_border, right=vertical_slice_left), LayoutType.INVERTED_T_LEFT_UP),
            (Bounds(top=slice_upper_border, left=vertical_slice_right, bottom=slice_lower_border, right=search_area.right), LayoutType.INVERTED_T_RIGHT_UP),
            (Bounds(top=slice_lower_border, left=search_area.left, bottom=search_area.bottom, right=search_area.right), LayoutType.INVERTED_T_LOW)
        ]

        if all([__has_elements_inside(zone[0], page_boxes) for zone in page_zones]):
            return page_zones

    # Check starting from 3/4 height point if page is "T"-shaped
    mid = int(y_top + (y_bottom - y_top) * 0.75)

    slice_upper_border = max(
        __first_upward_row_different_from_colour(y_top, y_bottom, vertical_slice_left, vertical_slice_right, page_image, background_colour, mid_row=mid),
        __first_upward_slice_row_intersecting_box(y_top, y_bottom, vertical_slice_left, vertical_slice_right, page_boxes, mid_row=mid)
    )

    slice_lower_border = min(
        __first_downward_row_different_from_colour(y_top, y_bottom, vertical_slice_left, vertical_slice_right, page_image, background_colour, mid_row=mid),
        __first_downward_slice_row_intersecting_box(y_top, y_bottom, vertical_slice_left, vertical_slice_right, page_boxes, mid_row=mid)
    )

    if slice_lower_border >= y_bottom - height * VERTICAL_SLICE_Y_BORDER_THRESHOLD:
        page_zones = [
            (Bounds(top=search_area.top, left=search_area.left, bottom=slice_upper_border, right=search_area.right), LayoutType.T_UP),
            (Bounds(top=slice_upper_border, left=search_area.left, bottom=slice_lower_border, right=vertical_slice_left), LayoutType.T_LEFT_LOW),
            (Bounds(top=slice_upper_border, left=vertical_slice_right, bottom=slice_lower_border, right=search_area.right), LayoutType.T_RIGHT_LOW)
        ]

        if all([__has_elements_inside(zone[0], page_boxes) for zone in page_zones]):
            return page_zones

    # Return whole search area by default
    return [(search_area, LayoutType.DEFAULT)]


def detect_pages_layout(images_dir, all_elements: list[Element]) -> dict[int, list[tuple[Bounds, LayoutType]]]:
    result = {}

    for file_name in os.listdir(images_dir):
        page_image = cv2.imread(f"{images_dir}/{file_name}")
        page_number = int(file_name[file_name.find('-') + 1:-4])
        page_boxes = [e.bounds for e in all_elements if e.page_num == page_number]

        #print(f"Processing page #{page_number}...")
        page_zones = __detect(page_image, page_boxes)
        result[page_number] = page_zones

    return result