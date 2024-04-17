"""
Textract Parser and HOCR Generator

This script sneds an image to AWS Textract and generates an HOCR file and a plain text transcript.
The HOCR (HTML-based OCR) output is an HTML representation of the text and its position on the page,
and the plain text transcript is just the extracted text without positional data.

Usage:
    python script_name.py path_to_image

    `path_to_image` should be the local path to the image file you want to process.

Functionality:
1. Check the validity of the provided image path.
2. Fetch the dimensions of the image.
3. Call AWS Textract to process the image and retrieve the OCR results.
4. Parse the Textract results to generate an organized structure.
5. Generate and save an HOCR file based on the parsed Textract results.
6. Generate and save a plain text transcript of the Textract results.
"""

import os
import sys
from PIL import Image
from textractcaller import call_textract
from yattag import Doc, indent


def get_block_by_id(result, block_id):
    """
    Retrieve block from Textract result by its ID.

    :param result: The Textract result JSON.
    :param block_id: The ID of the desired block.
    :return: Block matching the provided ID or None if not found.
    """
    for block in result["Blocks"]:
        if block["Id"] == block_id:
            return block
    return None


def parse_block(block, result):
    """
    Parse a block from Textract result to extract relevant information.

    :param block: A block from the Textract result.
    :param result: The entire Textract result JSON.
    :return: Parsed block data.
    """
    block_data = {
        "BlockType": block["BlockType"],
        "Confidence": block["Confidence"],
        "Text": block["Text"],
        "BoundingBox": block["Geometry"]["BoundingBox"],
        "Polygon": [{"X": point["X"], "Y": point["Y"]} for point in block["Geometry"]["Polygon"]],
        "Words": {}
    }

    for word_id in block.get("Relationships", [{}])[0].get("Ids", []):
        word_block = get_block_by_id(result, word_id)
        if word_block:
            block_data["Words"][word_id] = {
                "BlockType": word_block["BlockType"],
                "Confidence": word_block["Confidence"],
                "Text": word_block["Text"],
                "TextType": word_block.get("TextType"),
                "BoundingBox": word_block["Geometry"]["BoundingBox"],
                "Polygon": [{"X": point["X"], "Y": point["Y"]} for point in word_block["Geometry"]["Polygon"]]
            }
    return block_data


def parse_results(result):
    """
    Parse Textract result to organize data by page and line.

    :param result: The Textract result JSON.
    :return: Organized result data by page and line.
    """
    result_data = {}

    for block in result["Blocks"]:
        if block["BlockType"] == "PAGE":
            page_number = block.get("Page", 1)  # Default to page 1 if "Page" key doesn't exist
            result_data[page_number] = {}

        elif block["BlockType"] == "LINE":
            page_number = block.get("Page", 1)  # Default to page 1 if "Page" key doesn't exist
            if page_number not in result_data:
                result_data[page_number] = {}
            result_data[page_number][block["Id"]] = parse_block(block, result)

    return result_data


def render_html(result_data, pic_w=1000, pic_h=1000):
    """
    Render parsed Textract data as an HOCR HTML document.

    :param result_data: The parsed data organized by page and line.
    :param pic_w: Width of the image being processed.
    :param pic_h: Height of the image being processed.
    :return: HOCR formatted string.
    """
    doc, tag, text = Doc().tagtext()
    with tag('html'):
        with tag('body'):
            for page, lines in result_data.items():
                with tag('div', klass="ocr_page", id=f"page_{page}"):
                    for line_id, line in lines.items():
                        with tag('div', 
                                 ('title', f'bbox {int(line["BoundingBox"]["Left"]*pic_w)} {int(line["BoundingBox"]["Top"]*pic_h)} {int(line["BoundingBox"]["Left"]*pic_w + line["BoundingBox"]["Width"]*pic_w)} {int(line["BoundingBox"]["Top"]*pic_h + line["BoundingBox"]["Height"]*pic_h)}; x_wconf {int(line["Confidence"])}'),
                                 klass='ocr_line'):
                            for word_id, word in line["Words"].items():
                                with tag('span', 
                                         ('title', f'bbox {int(word["BoundingBox"]["Left"]*pic_w)} {int(word["BoundingBox"]["Top"]*pic_h)} {int(word["BoundingBox"]["Left"]*pic_w + word["BoundingBox"]["Width"]*pic_w)} {int(word["BoundingBox"]["Top"]*pic_h + word["BoundingBox"]["Height"]*pic_h)}; x_wconf {int(word["Confidence"])}'),
                                         klass='ocrx_word'):
                                    text(word["Text"] + ' ')
    return doc


def get_transcript(result):
    """
    Extract transcript from Textract result.

    :param result: The Textract result JSON.
    :return: Transcript string.
    """
    return "\n".join(block["Text"] for block in result["Blocks"] if block["BlockType"] == "LINE")


def main(input_document_url):
    """
    Main function to process an image with Textract, then generate HOCR and transcript outputs.

    :param input_document_url: Path to the input image/document.
    """
    if not os.path.exists(input_document_url):
        print(f"The file '{input_document_url}' does not exist.")
        return

    with Image.open(input_document_url) as img:
        img_width, img_height = img.size
        print(f"Image width: {img_width} Image height: {img_height}")

    print("Calling Textract...")
    textract_json = call_textract(input_document=input_document_url)

    print("\nProcessing Textract Results...")
    result_data = parse_results(textract_json)
    doc = render_html(result_data, img_width, img_height)

    document_name = os.path.splitext(input_document_url)[0]
    document_name = document_name.split("/")[-1]
    with open(f'{document_name}.hocr', 'w') as f:
        print(indent(doc.getvalue()), file=f)
    print(f"Results printed out {document_name}.hocr")

    with open(f'{document_name}.txt', 'w') as f:
        print(get_transcript(textract_json), file=f)
    print(f"Transcript printed out {document_name}.txt")
    print("Done")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Please provide the image file path as a command-line argument.")
        sys.exit(1)

    main(sys.argv[1])
