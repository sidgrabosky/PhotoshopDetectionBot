#!/usr/bin/env python

import praw
import re
import urllib2
from imageErrorBot import analyze

# Subreddits to monitor
subreddits = 'all'

# Phrase that should trigger investigation
keyPhrases = [
	re.compile("'?Shopped", re.IGNORECASE),
	re.compile("I can tell (from|by) the pixels", re.IGNORECASE),
	re.compile("^Fake.?$", re.IGNORECASE),
	re.compile("doctored", re.IGNORECASE),
	re.compile("photomanipulated", re.IGNORECASE),
	re.compile("ShopDetectionBot|PhotoshopBot", re.IGNORECASE) # Come when called. Good boy!
]

# Regex to extract links to jpgs from comments
imageSearchRegex = re.compile("((https?://)?((?:[a-z\-]+\.)+[a-z]{2,6}(?:/[^/#?]+)+\.(?:jpe?g)))")

# Prepare bot user agent
r = praw.Reddit(user_agent='User-Agent: ShopDetectionBot/0.1 by Sid G.')

# Temp until database stuff is activated
commentsParsed = 0


def runBot():
	for comment in praw.helpers.comment_stream(r, subreddits):
		
		# Check comment for keyphrases
		if any(phrase.search(comment.body) for phrase in keyPhrases):
			print 'A regex was matched for comment id {} (parent: {})!'.format(comment.id, comment.parent_id)
			print 'Matching comment body: {}'.format(comment.body)
			
			# Get images from parent comments (or the thread link/comment)
			if comment.parent_id[:3] == 't3_':
				images = getImagesFromThread(comment.parent_id)
			else:
				images = findImagesInParentTree(comment.parent_id)

			if images is not None:
				for image in images:
					generatedImages = analyze(downloadImage(image[0]))


# Goes up the comment hierarchy tree attempting to find images.
# For now, we'll settle for the first comment that has any images in it
# (we'll get fancier in the future)
def findImagesInParentTree(parent_id, distance=1):

	# Sadly, I think we need to go one at a time. The Reddit API doesn't have a good way to get the parents
	# of a comment, only its children. Getting all the comments for a post doesn't guarantee our comment
	# will even be present (if it's a thread with many comments, only some get returned).

	# Stop searching after 3 parents higher
	if distance > 3:
		print "Could not find parent with valid images. Skipping."
		return None

	print "Trying to get parent:"
	parentComment = r.get_info(thing_id=parent_id)

	if parentComment:
		images = extractImages(parentComment.body)
		if images is not None:
			return images
		else:
			# Higher! Higher! Search this comment's parent instead
			print "No valid image found. Try higher"
			findImagesInParentTree(parentComment.id, distance+1)
	else:
		print "No valid images found in tree"
		return None;

# Extract images from a thread, from either URL or self text as appropriate
def getImagesFromThread(thread_id):
	print "Get images from thread for thread {}".format(thread_id)
	thread = r.get_info(thing_id=thread_id)
	if thread:
		if thread.is_self:
			contentToParse = thread.selftext
		else:
			contentToParse = thread.url
		return extractImages(contentToParse)
	return None

# Extract all jp[e]g urls from a comment. Returns list of url matches.
# Items in each group result: 0 = whole match, including protocol and address,
# 1 = Protocal (HTTP or HTTPS), 2 = Just address, sans-protocol
def extractImages(comment_body):
	images = imageSearchRegex.findall(comment_body)
	if not images:
		return None
	print 'images found: {}'.format(images)
	return images

# download and save a specific image
def downloadImage(imageUrl):
	global commentsParsed
	print 'Downloading image {}'.format(imageUrl)
	fileName = str(commentsParsed) + ".jpg"
	path = "./downloadedImages/" + fileName

	## Prepend http if it's not included, otherwise urllib2 gets antsy
	if imageUrl[:4] != "http":
		imageUrl = "http://" + imageUrl

	try:
		# Download and save image. Adapted from example here: http://stackoverflow.com/a/22776
		u = urllib2.urlopen(imageUrl)
		f = open(path, 'wb')
		meta = u.info()
		file_size = int(meta.getheaders("Content-Length")[0])
		print "Downloading: %s Bytes: %s" % (path, file_size)
		file_size_dl = 0
		block_sz = 8192
		while True:
		    buffer = u.read(block_sz)
		    if not buffer:
		        break
		    file_size_dl += len(buffer)
		    f.write(buffer)
		    status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
		    status = status + chr(8)*(len(status)+1)
		    print status,
		f.close()
		# //
	except urllib2.HTTPError as e:
		print "HTTPError({0}): {1}. Oh well, who cares? Moving on...".format(e.errno, e.strerror)
	except:
		print "Something mysterious went wrong. Not a big deal. There will be more images"

	commentsParsed += 1
	return fileName

# Upload an image to Imgur
def uploadToImgur(image_file):
	print 'whatever'

# Respond to Reddit comment with image links
def respondToComment(comment, imageLinks):
	print 'whatever'

if __name__ == '__main__':
	commentsParsed = 0
	runBot()