import re

from data_ingest.entities.postprocess_models import (
    Bounds, LayoutType, Element, PostprocessResult,
    PostprocessPageResult, PostprocessPageZoneResult
)


def __cleanup_text(text: str) -> str:
    return re.sub(r'(\w+)- (\w+)', r'\1\2', text)


def __words_count(element: Element) -> int:
    return len(element.text.split(" "))


def __is_complete_sentence(element: Element) -> bool:
    return element.text.endswith('.')


def __is_section_header(element: Element) -> bool:
    return element.type_name == 'Section header'


def __find_references_title_index(all_elements: list[Element]) -> int:
    possible_titles = [
        'REFERENCE LIST',
        'REFERENCES'
    ]

    for possible_title in possible_titles:
        matches = [e for e in all_elements if __is_section_header(e) and e.text.upper() == possible_title]
        if len(matches) == 1:
            return matches[0].index

    return -1


def __is_list_item(element: Element) -> bool:
    return element.type_name == 'List item'


def __is_box_header(element: Element) -> bool:
    if not element.text.startswith("Box"):
        return False

    if __is_section_header(element):
        return True
    elif re.match(r"Box \d+ .*", element.text) and "|" in element.text:
        return True
    else:
        return False


def __is_text_chunk(element: Element) -> bool:
    return __words_count(element) > 7 or __is_box_header(element) or __is_list_item(element)


def __is_page_footer_or_header(element: Element) -> bool:
    return element.type_name in ['Page footer', 'Page header']


def __is_picture_or_table_element(element: Element) -> bool:
    if element.type_name in ['Picture', 'Table']:
        return True
    elif element.text.upper().startswith("SOURCE:") and __words_count(element) < 10:
        return True
    elif element.text.upper().startswith("SOURCES:") and __words_count(element) < 10:
        return True
    elif element.text.upper().startswith("NOTE:"):
        return True
    elif element.text.upper().startswith("NOTES:"):
        return True
    elif element.text.upper().startswith("NOTES AND SOURCES:"):
        return True
    elif element.text.upper().startswith("FIGURE") and element.type_name == "Caption":
        return True
    elif element.text.upper().startswith("TABLE") and element.type_name == "Caption":
        return True
    elif re.match(r"FIGURE \d+ .*", element.text.upper()):
        if "|" in element.text:
            return True
        else:
            return False
    elif re.match(r"TABLE \d+ .*", element.text.upper()):
        if "|" in element.text:
            return True
        else:
            return False
    else:
        return False


def __is_junk(element: Element) -> bool:
    if len(element.text) < 4:
        return True
    elif element.text.startswith("Suggested Citation:"):
        return True
    else:
        return False


def __is_inside(inner: Bounds, outer: Bounds, tol=10) -> bool:
    return (
        inner.left      >= outer.left   - tol and
        inner.right     <= outer.right  + tol and
        inner.top       >= outer.top    - tol and
        inner.bottom    <= outer.bottom + tol
    )


def __filter_out_junk_elements(elements: list[Element]) -> list[Element]:
    return [
        e for e in elements
        if not __is_picture_or_table_element(e) and not __is_page_footer_or_header(e) and not __is_junk(e)
    ]


def __postprocess_default_page(zone_elements: list[Element], width, height) -> tuple[list[str], str | None]:
    zone_elements = __filter_out_junk_elements(zone_elements)

    if not zone_elements:
        return [], None

    last_list_element = zone_elements[-1]
    last_geom_element = min(zone_elements, key=lambda e: (e.bounds.right - width) ** 2 + (e.bounds.bottom - height) ** 2)

    if last_list_element == last_geom_element and last_list_element.type_name == 'Text' and not __is_complete_sentence(last_list_element):
        continuation_element = last_list_element
        zone_elements = [e for e in zone_elements if e != continuation_element]
    else:
        continuation_element = None

    text_chunks = [__cleanup_text(e.text) for e in zone_elements if __is_text_chunk(e)]

    return text_chunks, __cleanup_text(continuation_element.text) if continuation_element else None


def __postprocess_two_column_zone(zone_elements: list[Element]) -> tuple[list[str], str | None]:
    zone_elements = __filter_out_junk_elements(zone_elements)

    if not zone_elements:
        return [], None

    last_list_element = zone_elements[-1]
    last_geom_element = max(zone_elements, key=lambda e: e.bounds.bottom)

    if last_list_element == last_geom_element and last_list_element.type_name == 'Text' and not __is_complete_sentence(last_list_element):
        continuation_element = last_list_element
        zone_elements = [e for e in zone_elements if e != continuation_element]
    else:
        continuation_element = None

    text_chunks = [__cleanup_text(e.text) for e in zone_elements if __is_text_chunk(e)]

    return text_chunks, __cleanup_text(continuation_element.text) if continuation_element else None


def __postprocess_t_zone(zone_elements: list[Element]) -> tuple[list[str], str | None]:
    zone_elements = __filter_out_junk_elements(zone_elements)

    if not zone_elements:
        return [], None

    last_list_element = zone_elements[-1]
    last_geom_element = max(zone_elements, key=lambda e: e.bounds.bottom)

    if last_list_element == last_geom_element and last_list_element.type_name == 'Text' and not __is_complete_sentence(last_list_element):
        continuation_element = last_list_element
        zone_elements = [e for e in zone_elements if e != continuation_element]
    else:
        continuation_element = None

    text_chunks = [__cleanup_text(e.text) for e in zone_elements if __is_text_chunk(e)]

    return text_chunks, __cleanup_text(continuation_element.text) if continuation_element else None


def __postprocess_ref_section(elements: list[Element], ref_start=-1) -> tuple[list[str], bool]:
    ref_stop = next((i for i, e in enumerate(elements) if i > ref_start and __is_section_header(e)), None)

    if ref_stop is not None:
        refs = [__cleanup_text(e.text) for i, e in enumerate(__filter_out_junk_elements(elements[:ref_stop])) if i > ref_start]
        return refs, True
    else:
        refs = [__cleanup_text(e.text) for i, e in enumerate(__filter_out_junk_elements(elements)) if i > ref_start]
        return refs, False


def postprocess(all_elements: list[Element], page_layouts: dict[int, list[tuple[Bounds, LayoutType]]], width, height) -> PostprocessResult:
    result = PostprocessResult([], [])

    in_ref_section = False
    stop = False
    ref_title_index = __find_references_title_index(all_elements)

    for page_number in range(1, len(page_layouts) + 1):
        if stop: break

        page_layout = page_layouts[page_number]
        page_elements = [e for e in all_elements if e.page_num == page_number]
        page_result = PostprocessPageResult(page_number, [])

        for zone_box, zone_type in page_layout:
            if stop: break

            zone_elements = [e for e in page_elements if __is_inside(e.bounds, zone_box)]

            if in_ref_section:
                refs, is_ref_section_ended = __postprocess_ref_section(zone_elements)
                result.references.extend(refs)
                if is_ref_section_ended:
                    # Don't process the article after references section ended
                    stop = True
            else:
                if ref_start := next((i for i, e in enumerate(zone_elements) if e.index == ref_title_index), None) is not None:
                    refs, is_ref_section_ended = __postprocess_ref_section(zone_elements, ref_start=ref_start)
                    result.references.extend(refs)

                    if is_ref_section_ended:
                        # Don't process the article after references section ended
                        stop = True
                    else:
                        zone_elements = zone_elements[:ref_start]
                        in_ref_section = True

                if stop: break

                paragraphs, last_text_fragment = None, None

                if zone_type == LayoutType.DEFAULT:
                    paragraphs, last_text_fragment = __postprocess_default_page(zone_elements, width, height)
                elif zone_type == LayoutType.TWO_COLUMNS_LEFT or zone_type == LayoutType.TWO_COLUMNS_RIGHT:
                    paragraphs, last_text_fragment = __postprocess_two_column_zone(zone_elements)
                elif zone_type == LayoutType.T_LEFT_LOW or zone_type == LayoutType.T_RIGHT_LOW:
                    paragraphs, last_text_fragment = __postprocess_t_zone(zone_elements)
                elif zone_type == LayoutType.INVERTED_T_LEFT_UP or zone_type == LayoutType.INVERTED_T_RIGHT_UP:
                    paragraphs, last_text_fragment = __postprocess_t_zone(zone_elements)

                page_result.zones.append(PostprocessPageZoneResult(zone_type, paragraphs, last_text_fragment))

        result.pages.append(page_result)

    return result
