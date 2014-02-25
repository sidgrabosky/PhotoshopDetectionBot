#!/usr/bin/env python

from PIL import Image, ImageChops, ImageFilter
from datetime import datetime
from os import listdir


MAX_WIDTH = 1500.00     # These are floats to make division easier elsewhere
MAX_HEIGHT = 1000.00
SOURCE_IMAGE_DIRECTORY = './sample_sourceImages/'
DIFF_IMAGE_DIRECTORY = './sample_diffImages/'
TEMP = './temp/temp.jpg'   # Temp file used for holding compressed images pre-diff
CONTRAST = 200      # How much to exaggerate the diff features. Higher makes differences more obvious, but adds noise
BLUR_AMOUNT = 3     # How much to blur the blurred diffs. Higher suppresses more noise, but loses detail


# Perform Image Error Analysis on a single image and saves resulting diff images
def analyze(fileName):

    startTime = datetime.now()
    fileNameNoExtension = fileName.rsplit( ".", 1 )[ 0 ];

    try:
        original = Image.open('./' + SOURCE_IMAGE_DIRECTORY + fileName)
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)
        return 0

    # Compress the file. We will use the differences to locate anomalies
    original.save(TEMP, quality=95)
    temporary = Image.open(TEMP)

    # Resize image to a sane size (but do not embiggen). This saves gobs of time when doing diff
    # However, it does seem to drastically reduce the quality of the diffs, due to resize interpolation
    # original = resizeImageToFit(original, Image.NEAREST)
    # temporary = resizeImageToFit(temporary, Image.NEAREST)

    # Do the diff calculation to expose the compression anomalies
    diff = ImageChops.difference(original, temporary)
    d = diff.load()
    width, height = diff.size
    for x in range(width):
        for y in range(height):
            d[x, y] = tuple(k * CONTRAST for k in d[x, y])

    # Do median blur on resulting diff image. Makes areas of note easier to resolve
    # Otherwise the good parts just sorta got lost in the noise a lot of the time
    medianBlur = ImageFilter.MedianFilter(BLUR_AMOUNT)
    diffBlur = diff.filter(medianBlur)

    # Resize final images to a sane size (but do not embiggen).
    # Doesn't save time like doing it before diff'ing, but results in much nicer image quality
    diff = resizeImageToFit(diff)
    diffBlur = resizeImageToFit(diffBlur)

    diffFileName = fileNameNoExtension + "_diff.jpg"
    diff.save(DIFF_IMAGE_DIRECTORY + diffFileName, quality=90)

    diffFileName = fileNameNoExtension + "_diff_blur.jpg"
    diffBlur.save(DIFF_IMAGE_DIRECTORY + diffFileName, quality=90)

    print(datetime.now()-startTime)
    print 'Done. Saved diff as {}'.format(diffFileName)


# Resize an image to fit MAX_SIZE while maintaining aspect ratio; do not enlarge
def resizeImageToFit(image, interpolation = Image.ANTIALIAS):
    width, height = image.size
    if width >= height:
        if width <= MAX_WIDTH and height <= MAX_HEIGHT:
            # No resize needed
            print 'No resize needed.'
            return image
        widthRatio = MAX_WIDTH / width
        heightRatio = MAX_HEIGHT / height
    else:
        if height <= MAX_WIDTH and width <= MAX_HEIGHT:
            # No resize needed
            print 'No resize needed.'
            return image
        widthRatio = MAX_HEIGHT / width
        heightRatio = MAX_WIDTH / height

    # Use the smaller of the two ratios, to prevent stretching or enlargement,
    # or exceeding the MAX_SIZE
    resizeRatio = min(widthRatio, heightRatio)

    # Convert pixel values to ints, then use those for new dimensions
    newWidth = int(round(width * resizeRatio))
    newHeight = int(round(height * resizeRatio))
    newSize = (newWidth, newHeight)

    print 'Resize ratio is {}. New dimension are {} x {}'.format(resizeRatio, newWidth, newHeight)
   
    return image.resize(newSize, interpolation)


# Reads all jpg images in sourceImages directory and converts them for analysis
def convertImages():
    totalStart = datetime.now()

    for file in listdir(SOURCE_IMAGE_DIRECTORY):
        if file.endswith(".jpg"):
            print 'Starting to process file {}'.format(file)
            analyze(file)

    print('Finished processing all. Total time passed: {}').format(datetime.now()-totalStart)


if __name__ == '__main__':
    convertImages()