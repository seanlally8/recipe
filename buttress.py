from functools import wraps

from flask import redirect, render_template, session
import cv2
import numpy as np
import pytesseract


def check_extension(image):
    '''
    This function checks to make sure the file format is acceptable
    '''

    # Extract extension. Found this method in Flask docs:
    # https://flask.palletsprojects.com/en/2.0.x/patterns/fileuploads/
    ext = image.filename.rsplit(".", )[1].lower()
    if ext != "jpg" or ext != "png":
        return report_error("not a valid file type - only jpg and png accepted")
    else:
        return ext

def image_preprocessing(image):
    '''
    This function prepares the image for OCR by doing the following:

    1. grayscaling
    2. binarizing (renders black/white)
    3. rotating
    4. cropping
    3. removing noise
    4. dilating (thickens font)

    and returns the final dilated image

    this code is largely based on, "Python Tutorials for Digital Humanities," 
    https://www.youtube.com/watch?v=ADV-AjAXHdc&t=1337
    https://www.youtube.com/watch?v=9FCw1xo_s0I&list=PL2VXyKi-KpYuTAZz__9KVl1jQz74bDG7i&index=8

    with help from PyImageSearch
    https://www.pyimagesearch.com/2017/02/20/text-skew-correction-opencv-python/
    https://www.pyimagesearch.com/2020/05/25/tesseract-ocr-text-localization-and-detection/ 

    and Murtaza's Workshop - Robotics and AI 
    https://youtu.be/6DjFscX4I_c
            
    '''
            
    # Grayscale the image in preparation for binarization (the process of turning the
    # image black and white).The code leading up to the pytesseract function
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
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if h > 700:
            rotated = rotate_image(im_bw, c)

    # Crop the image
    contours, hierarchy = cv2.findContours(rotated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if h > 700:
            cropped = rotated[y: y + h, x: x + w]

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
    '''
    This function takes as input the preprocessed image and returns as output a list of 
    images containing large blocks of text from the original image

    Code sources are similar to those mentioned in image_preprocessing()
    '''

    # Prepare image for structural analysis, so we
    # can separate out chunks of text
    # Based on Python Tutorials for Digital Humanities: 
    # https://www.youtube.com/watch?v=9FCw1xo_s0I&t=995s
    blur = cv2.GaussianBlur(image, (7, 7), 0)
    invert = cv2.bitwise_not(blur)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 50))
    over_dilate = cv2.dilate(invert, kernel, iterations=3)

    # Identify the larger blocks of text (this is the structural analysis part), 
    # crop out those blocks, and save them to disk -- each with their own file 
    image_files = []
    contours, hierarchy = cv2.findContours(over_dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for i, c in enumerate(contours):
        x, y, w, h = cv2.boundingRect(c)
        if h > 200:
            roi_image = image[y: y + h, x: x + w]
            filename = f"roi{i}.jpg"
            cv2.imwrite(filename, roi_image) 
            image_files.append(cv2.imread(filename))

    return image_files


def extract_strings(newfiles):
    '''
    This function takes a list of image arrays, then converts those images to strings. The
    function then returns a list of those strings.
    '''

    # Convert each image to a string, and extract strings containing the word(s): 
    # "ingredients", "directions" and/or "instructions"
    string_list = []
    for j in range(len(newfiles)):
        conf = r"--psm 6 --oem 1"
        text = pytesseract.image_to_string(newfiles[j], config=conf)
        if "ingredients" in text.lower() or "directions" in text.lower():
            string_list.append(text)
    
    return string_list


def login_required(f):
    """
    this decorator function is provided by flask. it checks to see if the user is signed in.
    if not, the user is sent to the login page.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def report_error(message):
    """
    Sends an error message (passed from app.py) to the user
    """

    # TODO create a modal using bootstrap to update error.html (or maybe layout.html?) to be a bit more UX friendly
    return render_template("error.html", message=message)