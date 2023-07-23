from pathlib import Path
import fitz
import glob
from PIL import Image
import io

import torch
import numpy as np
import pandas as pd


def to_1280_format(h, w):
    # Return pixel numbers for crop
    return ((w-1)*1280, (h-1)*1280, w*1280, h*1280)


def convert_pdf(path_pdf, path_convert_pdf):
    pdf_list = list(path_pdf.glob("**/*.pdf"))
    doc = fitz.open(pdf_list[0])
    page = doc.load_page(0)
    pixmap = page.get_pixmap(dpi=300)
    # convert_pdf = path_convert_pdf / "{0}.jpg".format(pdf_list[0].name)
    # pixmap.save(convert_pdf)
    return pixmap.tobytes("jpg")


def crop_image(path_pdf, path_convert_pdf, hight_pixels, width_pixels, bytes_image):
    jpg_list = list(path_pdf.glob("**/*.pdf"))

    img = Image.open(io.BytesIO(data))
    w, h = img.size
    w_crop_iterations = int(w/1280)
    h_crop_iterations = int(h/1280)
    for h_multiplication, h_iteration in enumerate(range(h_crop_iterations), 1):
        for w_multiplication, w_iteration in enumerate(range(w_crop_iterations), 1):
            crop_area = to_1280_format(
                h_multiplication, w_multiplication)

            # Print multiplication and crop area to check results
            print("h mult {} w mult {}".format(
                h_multiplication, w_multiplication))
            print(crop_area)

            # Crop image
            img_crop = img.crop(crop_area)

            # Resize to 1280x1280 format
            img_crop.thumbnail((1280, 1280))
            crop_save = path_convert_pdf / \
                "{}_{}_{}.jpg".format(
                    jpg_list[0].stem, h_multiplication, w_multiplication)
            img_crop.save(crop_save)


# Upload pdf and change to jpg
path_pdf = Path("wall_detection_export/upload_pdf")
path_convert_pdf = Path("wall_detection_export/convert_pdf")
path_export_txt = Path("wall_detection_export/export_txt")
path_model = Path("train_results/model_12classes/weights/best.pt")

data = convert_pdf(path_pdf=path_pdf, path_convert_pdf=path_convert_pdf)
# Chop pdf to 1280x1280
jpg_list = list(path_pdf.glob("**/*.pdf"))
# img = Image.open(jpg_list[0])
# img = Image.fromqpixmap(pixm)
img = Image.open(io.BytesIO(data))
w, h = img.size
w_crop_iterations = int(w/1280)
h_crop_iterations = int(h/1280)
for h_multiplication, h_iteration in enumerate(range(h_crop_iterations), 1):
    for w_multiplication, w_iteration in enumerate(range(w_crop_iterations), 1):
        crop_area = to_1280_format(
            h_multiplication, w_multiplication)

        # Print multiplication and crop area to check results
        print("h mult {} w mult {}".format(
            h_multiplication, w_multiplication))
        print(crop_area)

        # Crop image
        img_crop = img.crop(crop_area)

        # Resize to 1280x1280 format
        img_crop.thumbnail((1280, 1280))
        crop_save = path_convert_pdf / \
            "{}_{}_{}.jpg".format(
                jpg_list[0].stem, h_multiplication, w_multiplication)
        img_crop.save(crop_save)
# Detection walls and export txt labels
model = torch.hub.load(
    "yolov5", 'custom', path=path_model, source='local')
model.conf = 0.6  # Define model confidence

df_predictions = pd.DataFrame()
# df = pd.DataFrame({},
#                   index=["xmin", "ymin", "xmax", "ymax", "confidence", "class", "name"])
for file in path_convert_pdf.glob("**/*.jpg"):
    file_name = file.stem.split("_")
    print(file_name)
    img = Image.open(file)
    results = model(img, size=1280)
    predictions = results.pandas().xyxy[0]
    df = pd.DataFrame(predictions)
    df = df[df["name"] == "wall"]
    df['ymin'] = df['ymin'] + float(file_name[1]) * -1280
    df["ymax"] = df["ymax"] + float(file_name[1]) * -1280
    df["xmin"] = df["xmin"] + float(file_name[2]) * -1280
    df["xmax"] = df["xmax"] + float(file_name[2]) * -1280
    print(df)
    df_predictions = pd.concat([df_predictions, df])

df_predictions.to_csv(path_export_txt / "prediction.csv")
# Combine labels into one txt file with x/y coordination and thickness of wall

# Import this txt file into revit by pyrevit
