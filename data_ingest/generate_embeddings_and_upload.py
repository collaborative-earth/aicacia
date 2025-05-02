import json

from data_ingest.entities.postprocess_models import PostprocessResult, PostprocessPageResult, PostprocessPageZoneResult


def __load_postprocess_result(json_str: str) -> PostprocessResult:
    return PostprocessResult.from_json(json_str)


def __join_paragraphs(postprocess_result: PostprocessResult) -> list[str]:
    result = []

    temp_last_text_fragment = None

    pages = postprocess_result.pages

    for page in pages:
        for zone in page.zones:
            if zone.paragraphs:
                if temp_last_text_fragment:
                    result.append(' '.join([zone.paragraphs[0], temp_last_text_fragment]))
                    if len(zone.paragraphs) > 1: result.extend(zone.paragraphs[1:])
                    temp_last_text_fragment = None
                else:
                    result.extend(zone.paragraphs)

            if zone.last_text_fragment:
                temp_last_text_fragment = zone.last_text_fragment

    return result


if __name__ == '__main__':
    with open('030203de-af98-4880-97a9-466d2318e33b.json', 'r') as f:
        postprocess_result = __load_postprocess_result(f.read())
        paragraphs = __join_paragraphs(postprocess_result)

        with open('temp.json', 'w') as o_f:
            o_f.write(json.dumps(paragraphs))