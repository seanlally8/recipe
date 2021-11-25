from functools import wraps

from flask import redirect, render_template, session
import cv2
import numpy as np


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

def image_preprocessing(image):
            '''
            derives from the youtube channel, "Python Tutorials for Digital Humanities," 
            https://www.youtube.com/watch?v=ADV-AjAXHdc&t=1122
            '''
            
            # Grayscale the image in preparation for binarization (the process of turning the
            # image black and white).The code leading up to the pytesseract function
            def grayscale(image):
                return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            gray_image = grayscale(image)
            cv2.imwrite("gray.jpg", gray_image)

            # Binarize the image            
            thresh, im_bw = cv2.threshold(gray_image, 90, 140, cv2.THRESH_BINARY)
            cv2.imwrite("b2_image.jpg", im_bw)

            # Remove any noise from the image
            def noise_removal(image):
                kernel = np.ones((1, 1), np.uint8)
                image = cv2.dilate(image, kernel, iterations=1)
                kernel = np.ones((1, 1), np.uint8)
                image = cv2.erode(image, kernel, iterations=1)
                image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
                image = cv2.medianBlur(image, 3)
                return (image)

            no_noise = noise_removal(im_bw)
            cv2.imwrite("no_noise.jpg", no_noise)

            # Dilate (or thicken) the image
            def thick_font(image):
                image = cv2.bitwise_not(image)
                kernel = np.ones((2, 2), np.uint8)
                image = cv2.dilate(image, kernel, iterations=1)
                image = cv2.bitwise_not(image)
                return (image) 

            dilated_image = thick_font(no_noise)
            cv2.imwrite("dilated.jpg", dilated_image)