import cv2
import numpy as np

from models import Bounds, LayoutType


def find_first_non_overlapping_row(first_row, last_row, row_height, elements: list[Bounds], reverse=False):
    if not reverse:
        r = range(first_row, last_row - row_height + 1)
    else:
        r = range(last_row - row_height, first_row - 1, -1)

    for r1 in r:
        r2 = r1 + row_height
        overlapping_elements = len([e for e in elements if not (e.top > r2 or e.bottom < r1)])
        if overlapping_elements == 0:
            return r1

    return -1

def is_inside(inner_rect: Bounds, outer_rect: Bounds) -> bool:
    if inner_rect.left >= outer_rect.left and inner_rect.right <= outer_rect.right and inner_rect.top >= outer_rect.top and inner_rect.bottom <= outer_rect.bottom:
        return True

    return False


def has_elements_inside(rect: Bounds, elements: list[Bounds]):
    for e in elements:
        if e.left >= rect.left and e.right <= rect.right and e.top >= rect.top and e.bottom <= rect.bottom:
            return True

    return False


def detect_layout(im: cv2.typing.MatLike,
                  elements: list[Bounds],
                  search_area: Bounds | None = None,
                  mid_slice_w=20, mid_slice_var=0.1,
                  vert_slide_w=75, min_t_threshold=0.20) -> list[tuple[Bounds, LayoutType]]:

    page_height, page_width, _ = im.shape

    if search_area is None:
        search_area = Bounds(0, 0, page_height, page_width)

    elements = [e for e in elements if is_inside(e, search_area)]

    if not elements:
        return [(Bounds(top=search_area.top, left=search_area.left, bottom=search_area.bottom, right=search_area.right), LayoutType.DEFAULT)]

    y_top = min([element.top for element in elements])
    y_bottom = max([element.bottom for element in elements])
    x_slice_left = search_area.middle_x() - (mid_slice_w // 2)
    x_slice_right = search_area.middle_x() + (mid_slice_w // 2)

    mid_slice_variation = int((page_width * mid_slice_var) / 2)

    for offset in range(mid_slice_variation + 1):
        for sign in [-1, 1]:
            pix_offset = offset * sign

            mid_slice = im[y_top: y_bottom, x_slice_left + pix_offset: x_slice_right + pix_offset]

            if len(np.unique(mid_slice)) == 1:
                zones = [
                    (Bounds(top=y_top, left=search_area.left, bottom=y_bottom, right=x_slice_left + pix_offset), LayoutType.TWO_COLUMNS_LEFT),
                    (Bounds(top=y_top, left=x_slice_right + pix_offset, bottom=y_bottom, right=search_area.right), LayoutType.TWO_COLUMNS_RIGHT)
                ]

                if all([has_elements_inside(zone[0], elements) for zone in zones]):
                    return zones

    search_start = y_top + int((y_bottom - y_top) * min_t_threshold)
    horizontal_slice_row = find_first_non_overlapping_row(search_start, y_bottom, vert_slide_w, elements)

    if horizontal_slice_row >= 0:
        mid_slice = im[y_top: horizontal_slice_row, x_slice_left: x_slice_right]

        if len(np.unique(mid_slice)) == 1:
            zones = [
                (Bounds(top=search_area.top, left=search_area.left, bottom=horizontal_slice_row, right=x_slice_left), LayoutType.INVERTED_T_LEFT_UP),
                (Bounds(top=search_area.top, left=x_slice_right, bottom=horizontal_slice_row, right=search_area.right), LayoutType.INVERTED_T_RIGHT_UP),
                (Bounds(top=horizontal_slice_row, left=search_area.left, bottom=search_area.bottom, right=search_area.right), LayoutType.INVERTED_T_LOW)
            ]

            if all([has_elements_inside(zone[0], elements) for zone in zones]):
                return zones

    search_stop = y_bottom - int((y_bottom - y_top) * min_t_threshold)
    horizontal_slice_row = find_first_non_overlapping_row(y_top, search_stop, vert_slide_w, elements, reverse=True)

    if horizontal_slice_row >= 0:
        mid_slice = im[horizontal_slice_row: y_bottom, x_slice_left: x_slice_right]

        if len(np.unique(mid_slice)) == 1:
            zones = [
                (Bounds(top=search_area.top, left=search_area.left, bottom=horizontal_slice_row, right=search_area.right), LayoutType.T_UP),
                (Bounds(top=horizontal_slice_row, left=search_area.left, bottom=search_area.bottom, right=x_slice_left), LayoutType.T_LEFT_LOW),
                (Bounds(top=horizontal_slice_row, left=x_slice_right, bottom=search_area.bottom, right=search_area.right), LayoutType.T_RIGHT_LOW)
            ]

            if all([has_elements_inside(zone[0], elements) for zone in zones]):
                return zones

    return [(Bounds(top=search_area.top, left=search_area.left, bottom=search_area.bottom, right=search_area.right), LayoutType.DEFAULT)]


if __name__ == '__main__':
    import os
    from improved_chapterer import read_recognition_result

    input_data = "../input_data/raw_pages_3"
    input_json = "../outputs/example3/result-pdf-document-layout-analysis-gpu.json"
    output = "../outputs/example3/layout-gpu-pages"

    data, _, _ = read_recognition_result(input_json, 3000)

    top_limit = 296
    left_side_limit = 150
    bottom_limit = 4028
    right_side_limit = 2850

    for image_name in os.listdir(input_data):
        image = cv2.imread(f"{input_data}/{image_name}")
        image_num = int(image_name[image_name.find('-')+1:-4])

        print(f"Processing {image_name} ({image_num})")

        zones = detect_layout(
            image, [e.bounds for e in data if e.page_num == image_num],
            search_area=Bounds(top_limit, left_side_limit, bottom_limit, right_side_limit)
        )

        for bounds, layout in zones:
            cv2.rectangle(
                image,
                (bounds.left, bounds.top),
                (bounds.right, bounds.bottom),
                color=(0, 255, 0), thickness=3
            )

        cv2.imwrite(f"{output}/{image_name}", image)