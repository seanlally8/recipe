import glob
import os
from functools import wraps

import cv2
import numpy as np
import pytesseract
from flask import redirect, render_template, session
from pytesseract import Output


def check_extension(extension):
    """
    This function checks to make sure the file format is acceptable
    """
    # https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/
    if extension != "jpg" or extension != "png":
        return report_error("not a valid file type - only jpg and png accepted")
    else:
        return True


def image_preprocessing(image):
    """
    This function prepares the image for OCR with the following steps:

    1. grayscale
    2. binarize (renders black/white)
    3. rotate
    4. crop
    3. remove noise
    4. dilate (thickens font)

    Then returns the final dilated image

    Largely based on, "Python Tutorials for Digital Humanities," 
    https://www.youtube.com/watch?v=ADV-AjAXHdc&t=1337
    https://www.youtube.com/watch?v=9FCw1xo_s0I&list=PL2VXyKi-KpYuTAZz__9KVl1jQz74bDG7i&index=8

    With help from PyImageSearch
    https://www.pyimagesearch.com/2017/02/20/text-skew-correction-opencv-python/
    https://www.pyimagesearch.com/2020/05/25/tesseract-ocr-text-localization-and-detection/ 

    And Murtaza's Workshop - Robotics and AI 
    https://youtu.be/6DjFscX4I_c
            
    """
            
    # Grayscale the image in preparation for binarization 
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Binarize the image            
    thresh, im_bw = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # Rotate the image
    # specifically drawn from https://www.pyimagesearch.com/2017/02/20/text-skew-correction-opencv-python/
    def rotate_image(image, contour):
        rect = cv2.minAreaRect(contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        cv2.drawContours(image,[box],0,(0,0,255),2)

        angle = -(rect[-1])
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        image = cv2.warpAffine(image, M, (w, h),
            flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return image

    contours, hierarchy = cv2.findContours(im_bw, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda x: cv2.contourArea(x))
    rotated = rotate_image(im_bw, contours[-1])

    # Crop the image
    contours, hierarchy = cv2.findContours(rotated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=lambda x: cv2.contourArea(x))
    x, y, w, h = cv2.boundingRect(contours[-1])
    cropped = rotated[y: y + h, x: x + w]
    cv2.imwrite("cropped.jpg", cropped)

    # Remove noise from the image 
    def noise_removal(image):
        kernel = np.ones((1, 1), np.uint8)
        image = cv2.dilate(image, kernel, iterations=1)
        kernel = np.ones((1, 1), np.uint8)
        image = cv2.erode(image, kernel, iterations=1)
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        image = cv2.medianBlur(image, 3)
        return (image)
    
    no_noise = noise_removal(cropped)

    # Dilate image (i.e. thicken text)
    def thick_font(image):
        image = cv2.bitwise_not(image)
        kernel = np.ones((3, 3), np.uint8)
        image = cv2.dilate(image, kernel, iterations=1)
        image = cv2.bitwise_not(image)
        return image 

    dilated_image = thick_font(no_noise)

    return dilated_image


def parse_image(image):
    """
    This function takes as input the preprocessed image and returns as output a list of 
    images containing large blocks of text from the original image

    Code sources are similar to those mentioned in image_preprocessing() docstring
    """

    # Prepare image for structural analysis, so we
    # can separate out chunks of text
    # Based on Python Tutorials for Digital Humanities: 
    # https://www.youtube.com/watch?v=9FCw1xo_s0I&t=995s
    blur = cv2.GaussianBlur(image, (7, 7), 0)
    invert = cv2.bitwise_not(blur)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 50))
    over_dilate = cv2.dilate(invert, kernel, iterations=3)

    # Identify contours on the page, preparing to extract images of the appropriate size
    image_arrays = []
    contours, hierarchy = cv2.findContours(over_dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # To account for images of varying sizes, we can use the ratio, partial_image_width:full_image_width.
    # Thus, we identify the dimensions of the largest box (the full image)
    contours = sorted(contours, key=lambda x: cv2.contourArea(x))
    fullx, fully, fullw, fullh = cv2.boundingRect(contours[-1])


    # Finally, find the larger blocks of text (this is the structural analysis part), 
    # crop out those blocks, and save them to disk -- each with their own file (roi#.jpg)
    for i, c in enumerate(contours):
        x, y, w, h = cv2.boundingRect(c)
        if (w / fullw) > .5:
            roi_image = image[y: y + h, x: x + w]
            filename = f"roi{i}.jpg"
            cv2.imwrite(filename, roi_image) 
            image_arrays.append(cv2.imread(filename))

    return image_arrays


def extract_strings(newfiles):
    """
    This function takes a list of image arrays, then converts those images to strings. The
    function then returns a list of those strings.
    """

    # Declare an empty string list we can fill with the OCRed text
    string_list = []


    # Go through each element in the list of images passed in as an argument
    for j in range(len(newfiles)):

        # Flags passed to tesseract:
        # --psm 11 --> Assume sparse text
        # --psm 6 --> Assume a single uniform block of text.
        # --oem 1 --> Neural nets LSTM engine only.
        # The flag, '-l eng_layer,' refers to finetuned traineddata obtained using Shreeshrii's tess4training
        # scripts (https://github.com/Shreeshrii/tess4training), which are based on Ray Smith's tutorials
        # (https://tesseract-ocr.github.io/tessdoc/tess4/TrainingTesseract-4.00.html).
        # The finetuned data allows 'recipe' to accurately recognize fractions.
        config_init = r"--psm 11 --oem 1"
        config_second = r"--psm 6 --oem 1"

        text = pytesseract.image_to_string(newfiles[j], config=config_init)
        data = pytesseract.image_to_data(newfiles[j], config=config_init, output_type=Output.DICT)

        if "\u00BC" in text.lower() or "\u00BD" in text.lower():
            if check_conf_score(data, 0):
                string_list.append(text)
            
        elif "prepare" in text.lower() or "preheat" in text.lower() or "assemble" in text.lower() or "bowls" in text.lower():

            text = pytesseract.image_to_string(newfiles[j], config=config_second)

            if check_conf_score(data, 1):
                string_list.append(text)

    return string_list


def check_conf_score(data, x):
    """
    This function takes as input the dictionary of data provided by pytesseract.image_to_data()
    and checks to see if the average confidence score meets the pre-established standard.
    """
    if x < 1:
        print("INGREDIENTS")
    else:
        print("INSTRUCTIONS")

    # Declare variable to hold the total sum of confidence scores in 'data' (see below)
    conf_sum = 0

    # Calculate the average confidence score for this OCR output
    for i in range(len(data["conf"])):
        conf_sum += float(data["conf"][i])
    conf_avg = conf_sum / len(data["conf"])

    # Check to make sure the average confidence score meets the minimum requirement
    if conf_avg < 50:
        print(f"FAIL: {conf_avg}")
        return False

    else:
        print(f"SUCCESS: {conf_avg}")
        return True


def html_to_string(recipe_part):
    """
    This function changes the html elements -- in a given list -- to clean strings
    e.g. <li>List Item</li> --> "List Item"
    """

    for i in range(len(recipe_part)):
        recipe_part[i] = recipe_part[i].string.strip()
    return recipe_part


def login_required(f):
    """
    This decorator function is provided by flask. It checks to see if the user is signed in.
    If not, the user is sent to the login page.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def remove_files():
    """
    This function removes the jpeg files generated in by 
    parse_image() (above) and image.save (in app.py)
    """

    filelist = glob.glob("*.jpg")
    for filename in filelist:
        os.remove(filename)
    return True


def report_error(message):
    """
    Sends an error message (passed from app.py) to the user
    """

    # TODO create a modal using bootstrap to update error.html (or maybe layout.html?) to be a bit more UX friendly
    return render_template("error.html", message=message)
