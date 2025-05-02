import json

from data_ingest.entities.postprocess_models import Element, Bounds

def read_json(json_file_path, rendered_page_width) -> list[Element]:
    with open(json_file_path) as f:
        data = json.loads(f.read())

        if not data:
            return []

        page_width = data[0]["page_width"]
        scaling_factor = rendered_page_width / page_width

        result = [
            Element(
                page_num=element["page_number"],
                index=i,
                bounds=Bounds(
                    top = int(element["top"] * scaling_factor),
                    left = int(element["left"] * scaling_factor),
                    bottom = int((element["top"] + element["height"]) * scaling_factor),
                    right = int((element["left"] + element["width"]) * scaling_factor)
                ),
                type_name=element["type"],
                text=element["text"]
            )
            for i, element in enumerate(data)
        ]

        return result