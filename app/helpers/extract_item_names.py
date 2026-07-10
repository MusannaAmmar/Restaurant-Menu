"""Extract food item names from a menu JSON-like dict.

Provides `extract_food_item_names(payload)` which returns the item names found
under `data -> data -> menus -> sections -> items`.
"""




# @time_function('extract_food_names')
async def extract_food_item_names(payload):
	"""Return a list of item names from the given payload.

	Args:
		payload: Parsed menu response dict.

	Returns:
		List of item name strings.
	"""
	# print('payload.get("data", {}).get("data", {})', payload)
	data_root = payload
	menus = data_root.get("menus", []) or []
	names = []
	for menu in menus:
		for section in (menu.get("sections", []) or []):
			for item in (section.get("items", []) or []):
				name = item.get("name")
				# print('name', name)
				if isinstance(name, str) and name.strip():
					names.append(name.strip())
	return names