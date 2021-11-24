# Notes from:
# Python Tutorials for Digital Humanities
# https://www.youtube.com/watch?v=ADV-AjAXHdc&t=1337
import cv2

filename = "tmpimage.jpg"
img = cv2.imread(filename)

# invert image
inverted_image = cv2.bitwise_not(img)
cv2.imwrite("inverted.jpg", inverted_image)

def grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

gray_image = grayscale(img)
cv2.imwrite("gray.jpg", gray_image)

# What's thresh here?
thresh, im_bw = cv2.threshold(gray_image, 150, 200, cv2.THRESH_BINARY)
cv2.imwrite("b2_image.jpg", im_bw)
