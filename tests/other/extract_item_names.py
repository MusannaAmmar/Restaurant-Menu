"""Extract food item names from a menu JSON-like dict.

Provides `extract_food_item_names(payload)` which returns the item names found
under `data -> data -> menus -> sections -> items`.
"""

from pathlib import Path
import json


def extract_food_item_names(payload: dict) -> list:
	"""Return a list of item names from the given payload.

	Args:
		payload: Parsed menu response dict.

	Returns:
		List of item name strings.
	"""
	data_root = payload.get("data", {}).get("data", {})
	menus = data_root.get("menus", []) or []
	names = []
	for menu in menus:
		for section in (menu.get("sections", []) or []):
			for item in (section.get("items", []) or []):
				name = item.get("name")
				if isinstance(name, str) and name.strip():
					names.append(name.strip())
	return names


if __name__ == "__main__":
	# Example usage: read from tests/other/sample.json and print the list
	sample_path = Path(__file__).with_name("sample.json")
	if sample_path.exists():
		with sample_path.open("r", encoding="utf-8") as f:
			payload = json.load(f)
		print(extract_food_item_names(payload))
	else:
		print("sample.json not found next to this file.")

# python tests/other/extract_item_names.py