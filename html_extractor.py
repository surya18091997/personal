from dataclasses import dataclass
from enum import Enum

from lxml import etree, html

ItemType = Enum("ItemType", ["ITEM", "LIST"])
OutputType = Enum(
    "OutputType",
    ["TEXT", "HTML", "JSON", "TABLE", "TABLE_ARRAY", "TABLE_JSON", "ATTRIBUTE"],
)


@dataclass
class Config:
    selector: str
    type: ItemType
    output: OutputType
    attribute: str = None

    def __init__(self, selector, type="item", output="text"):
        self.selector = selector
        self.type = ItemType[type.upper()]
        if output.startswith("@"):
            self.output = OutputType.ATTRIBUTE
            self.attribute = output[1:]
        else:
            self.output = OutputType[output.upper()]


def _parse_config(config: dict) -> dict:
    parsed_config = {}
    for attr, rule in config.items():
        if isinstance(rule, str):
            parsed_config[attr] = Config(selector=rule)
        else:
            parsed_config[attr] = Config(**rule)
    return parsed_config


def _element_to_dict(element):
    """
    Convert an lxml element into a dict.
    """
    if element.tag is etree.Comment:
        return

    result = {}
    for key, attr in element.items():
        result[f"@{key}"] = attr

    for node in element:
        key = node.tag
        if key is etree.Comment:
            continue
        value = _element_to_dict(node)
        # if value
        prev_value = result.get(key)
        if isinstance(prev_value, list):
            result[key].append(value)
        elif prev_value:
            result[key] = [prev_value, value]
        else:
            result[key] = value

    text = element.text and element.text.strip()
    if result and text:
        result["#text"] = text
    return result or text or None


def _extract_table_object(table_element, stringify):
    """Extract HTML table as objects with header based keys"""
    table_data = []
    rows = table_element.xpath("./tr | ./thead/tr | ./tbody/tr")
    if rows:
        headers = [
            header.text_content().strip() for header in rows[0].xpath("./td | ./th")
        ]
        for row in rows[1:]:
            row_data = {}
            for index, cell in enumerate(row.xpath("./td | ./th")):
                row_data[headers[index]] = (
                    cell.text_content().strip() if stringify else _element_to_dict(cell)
                )
            table_data.append(row_data)
    return table_data


def _extract_table_array(table_element):
    """Extract HTML table as an array of arrays"""
    table_data = []
    rows = table_element.xpath("./tr | ./thead/tr | ./tbody/tr")
    for row in rows:
        row_data = [cell.text_content().strip() for cell in row.xpath("./td | ./th")]
        table_data.append(row_data)
    return table_data


def _extract_item(rule, entity):
    if rule.output is OutputType.TEXT:
        content = entity.text_content().strip()
    elif rule.output is OutputType.HTML:
        content = etree.tostring(entity)
    elif rule.output is OutputType.JSON:
        content = _element_to_dict(entity)
    elif rule.output in [OutputType.TABLE, OutputType.TABLE_JSON]:
        content = _extract_table_object(
            entity, stringify=rule.output is OutputType.TABLE
        )
    elif rule.output is OutputType.TABLE_ARRAY:
        content = _extract_table_array(entity)
    elif rule.output == OutputType.ATTRIBUTE:
        content = entity.get(rule.attribute)
    return content


def extract(config: dict, html_content: str) -> dict:
    html_tree = html.fromstring(html_content)
    output = {}
    config = _parse_config(config)
    for attr, rule in config.items():
        entities = html_tree.xpath(rule.selector)
        if not entities:
            content = None
        elif rule.type == ItemType.ITEM:
            content = _extract_item(rule, entities[0])
        elif rule.type == ItemType.LIST:
            content = [_extract_item(rule, entity) for entity in entities]
        output[attr] = content
    return output
