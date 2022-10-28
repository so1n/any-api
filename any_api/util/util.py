from string import Formatter
from typing import List


def get_key_from_template(template_str: str) -> List[str]:
    return [i[1] for i in Formatter().parse(template_str) if i[1] is not None]
