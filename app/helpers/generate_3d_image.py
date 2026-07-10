import os
import replicate
from urllib.request import urlopen
from replicate.helpers import FileOutput
from typing import Optional


# async def generate_flux_kontext_image(
# 	prompt: str,
# 	input_path: Optional[str]=None,
# 	aspect_ratio: str = "match_input_image",
# 	output_format: str = "jpg",
# 	safety_tolerance: int = 2,
# 	api_token: str | None = None,
# ) -> str:
# 	"""Run black-forest-labs/flux-kontext-pro and save the result to disk.

# 	Returns the first URL to the generated image.
# 	"""
# 	if api_token:
# 		os.environ["REPLICATE_API_TOKEN"] = api_token

# 	with open(input_path, "rb") as input_image:
# 		output = replicate.run(
# 			"black-forest-labs/flux-kontext-pro",
# 			input={
# 				"prompt": prompt,
# 				"input_image": input_image,
# 				"aspect_ratio": aspect_ratio,
# 				"output_format": output_format,
# 				"safety_tolerance": safety_tolerance
# 			}
# 		)

# 	return output


def generate_flux_kontext_image(
    prompt: str,
    input_path: Optional[str] = None,
    aspect_ratio: str = "match_input_image",
    output_format: str = "jpg",
    safety_tolerance: int = 2,
    api_token: Optional[str] = None,
) -> str:
    """
    Generate an image using black-forest-labs/flux-kontext-pro on Replicate.

    - If `input_path` is provided: performs **image-to-image** generation.
    - If `input_path` is None: performs **text-to-image** generation.
    - Returns: URL (or path) to the generated image.
    """

    if api_token:
        os.environ["REPLICATE_API_TOKEN"] = api_token

    # Build input dynamically depending on whether we have an image
    model_input = {
        "prompt": prompt,
        "aspect_ratio": aspect_ratio,
        "output_format": output_format,
        "safety_tolerance": safety_tolerance,
    }

    if input_path:
        # 🟢 Image-to-image mode
        with open(input_path, "rb") as input_image:
            model_input["input_image"] = input_image
            output = replicate.run(
                "black-forest-labs/flux-kontext-pro",
                input=model_input)
            
    else:
        # 🟢 Text-to-image mode
        output = replicate.run(
            "black-forest-labs/flux-kontext-pro",
            input=model_input
        )

    # Replicate usually returns a list of URLs
    if isinstance(output, list) and output:
        return output[0]
    return output


# if __name__ == "__main__":
# 	# Example usage
# 	url = generate_flux_kontext_image(
# 		prompt="make 3d version of only forth hot dog",
# 		input_image="https://i.ibb.co/gZYgB0Pc/sample.png",
# 		aspect_ratio="match_input_image",
# 		output_format="jpg",
# 		safety_tolerance=2,
# 		output_path="my-image.png",
# 		# Or set the token in environment beforehand
# 		api_token=os.environ.get("REPLICATE_API_TOKEN"),
# 	)
# 	print(url)