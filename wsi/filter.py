# -------------------------------------------------------------
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
# -------------------------------------------------------------

import matplotlib.pyplot as plt
import numpy as np
import PIL
import skimage.exposure as sk_exposure
import skimage.feature as sk_feature
import skimage.filters as sk_filters
import skimage.morphology as sk_morphology
import wsi.slide as slide
from wsi.slide import Time


def pil_to_np_rgb(pil_img):
  """
  Convert a PIL Image to a NumPy array.

  Note that RGB PIL (w, h) -> NumPy (h, w, 3).

  Args:
    pil_img: The PIL Image.

  Returns:
    The PIL image converted to a NumPy array.
  """
  t = Time()
  rgb = np.asarray(pil_img)
  np_info(rgb, "RGB", t.elapsed())
  return rgb


def np_to_pil(np_img):
  """
  Convert a NumPy array to a PIL Image.

  Args:
    np_img: The image represented as a NumPy array.

  Returns:
     The NumPy array converted to a PIL Image.
  """
  return PIL.Image.fromarray(np_img)


def filter_rgb_to_grayscale(np_img, output_type="uint8"):
  """
  Convert an RGB NumPy array to a grayscale NumPy array.

  Shape (h, w, c) to (h, w).

  Args:
    np_img: RGB Image as a NumPy array.
    output_type: Type of array to return (float or uint8)

  Returns:
    Grayscale image as NumPy array with shape (h, w).
  """
  t = Time()
  # Another common RGB ratio possibility: [0.299, 0.587, 0.114]
  grayscale = np.dot(np_img[..., :3], [0.2125, 0.7154, 0.0721])
  if output_type != "float":
    grayscale = grayscale.astype("uint8")
  np_info(grayscale, "Gray", t.elapsed())
  return grayscale


def filter_complement(np_img, output_type="uint8"):
  """
  Obtain the complement of an image as a NumPy array.

  Args:
    np_img: Image as a NumPy array.
    type: Type of array to return (float or uint8).

  Returns:
    Complement image as Numpy array.
  """
  t = Time()
  if output_type == "float":
    complement = 1.0 - np_img
  else:
    complement = 255 - np_img
  np_info(complement, "Complement", t.elapsed())
  return complement


def np_info(np_arr, name=None, elapsed=None):
  """
  Display information (shape, type, max, min, etc) about a NumPy array.

  Args:
    np_arr: The NumPy array.
    name: The (optional) name of the array.
    elapsed: The (optional) time elapsed to perform a filtering operation.
  """
  np_arr = np.asarray(np_arr)
  max = np_arr.max()
  min = np_arr.min()
  mean = np_arr.mean()
  std = np_arr.std()
  if name is None:
    name = "NumPy Array"
  if elapsed is None:
    elapsed = "---"
  print("%-20s | Time: %-14s Max: %6.2f  Min: %6.2f  Mean: %6.2f  Std: %6.2f Type: %-6s Shape: %s" % (
    name, str(elapsed), max, min, mean, std, np_arr.dtype, np_arr.shape))


def filter_hysteresis_threshold(np_img, low=50, high=100, output_type="uint8"):
  """
  Apply two-level (hysteresis) threshold to an image as a NumPy array, returning a binary image.

  Args:
    np_img: Image as a NumPy array.
    low: Low threshold.
    high: High threshold.
    output_type: Type of array to return (bool, float, or uint8).

  Returns:
    NumPy array (bool, float, or uint8) where True, 1.0, and 255 represent a pixel above hysteresis threshold.
  """
  t = Time()
  hyst = sk_filters.apply_hysteresis_threshold(np_img, low, high)
  if output_type == "bool":
    pass
  elif output_type == "float":
    hyst = hyst.astype(float)
  else:
    hyst = (255 * hyst).astype("uint8")
  np_info(hyst, "Hysteresis Threshold", t.elapsed())
  return hyst


def filter_otsu_threshold(np_img, output_type="uint8"):
  """
  Compute Otsu threshold on image as a NumPy array and return binary image based on pixels above threshold.

  Args:
    np_img: Image as a NumPy array.
    output_type: Type of array to return (bool, float, or uint8).

  Returns:
    NumPy array (bool, float, or uint8) where True, 1.0, and 255 represent a pixel above Otsu threshold.
  """
  t = Time()
  otsu_thresh_value = sk_filters.threshold_otsu(np_img)
  otsu = (np_img > otsu_thresh_value)
  if output_type == "bool":
    pass
  elif output_type == "float":
    otsu = otsu.astype(float)
  else:
    otsu = otsu.astype("uint8") * 255
  np_info(otsu, "Otsu Threshold", t.elapsed())
  return otsu


def filter_local_otsu_threshold(np_img, disk_size=3, output_type="uint8"):
  """
  Compute local Otsu threshold for each pixel and return binary image based on pixels being less than the
  local Otsu threshold.

  Args:
    np_img: Image as a NumPy array.
    disk_size: Radius of the disk structuring element used to compute the Otsu threshold for each pixel.
    output_type: Type of array to return (bool, float, or uint8).

  Returns:
    NumPy array (bool, float, or uint8) where local Otsu threshold values have been applied to original image.
  """
  t = Time()
  local_otsu = sk_filters.rank.otsu(np_img, sk_morphology.disk(disk_size))
  local_otsu = (np_img <= local_otsu)
  if output_type == "bool":
    pass
  elif output_type == "float":
    local_otsu = local_otsu.astype(float)
  else:
    local_otsu = local_otsu.astype("uint8") * 255
  np_info(local_otsu, "Otsu Local Threshold", t.elapsed())
  return local_otsu


def filter_entropy(np_img, neighborhood=9, threshold=5, output_type="uint8"):
  """
  Filter image based on entropy (complexity).

  Args:
    np_img: Image as a NumPy array.
    neighborhood: Neighborhood size (defines height and width of 2D array of 1's).
    threshold: Threshold value.
    output_type: Type of array to return (bool, float, or uint8).

  Returns:
    NumPy array (bool, float, or uint8) where True, 1.0, and 255 represent a measure of complexity.
  """
  t = Time()
  entr = sk_filters.rank.entropy(np_img, np.ones((neighborhood, neighborhood))) > threshold
  if output_type == "bool":
    pass
  elif output_type == "float":
    entr = entr.astype(float)
  else:
    entr = entr.astype("uint8") * 255
  np_info(entr, "Entropy", t.elapsed())
  return entr


def filter_canny(np_img, sigma=1, low_threshold=0, high_threshold=25, output_type="uint8"):
  """
  Filter image based on Canny algorithm edges.

  Args:
    np_img: Image as a NumPy array.
    sigma: Width (std dev) of Gaussian.
    low_threshold: Low hysteresis threshold value.
    high_threshold: High hysteresis threshold value.
    output_type: Type of array to return (bool, float, or uint8).

  Returns:
    NumPy array (bool, float, or uint8) representing Canny edge map (binary image).
  """
  t = Time()
  can = sk_feature.canny(np_img, sigma=sigma, low_threshold=low_threshold, high_threshold=high_threshold)
  if output_type == "bool":
    pass
  elif output_type == "float":
    can = can.astype(float)
  else:
    can = can.astype("uint8") * 255
  np_info(can, "Canny Edges", t.elapsed())
  return can


def filter_remove_small_objects(np_img, min_size=3000, output_type="uint8"):
  """
  Filter image to remove small objects (connected components) less than a particular minimum size.

  Args:
    np_img: Image as a NumPy array of type bool.
    min_size: Minimum size of small object to remove.
    output_type: Type of array to return (bool, float, or uint8).

  Returns:
     NumPy array (bool, float, or uint8).
  """
  t = Time()
  rem_sm = np_img.astype(bool)  # make sure mask is boolean
  rem_sm = sk_morphology.remove_small_objects(rem_sm, min_size=min_size)
  if output_type == "bool":
    pass
  elif output_type == "float":
    rem_sm = rem_sm.astype(float)
  else:
    rem_sm = rem_sm.astype("uint8") * 255
  np_info(rem_sm, "Remove Small Objs", t.elapsed())
  return rem_sm


def filter_contrast_stretch(np_img, low=40, high=60):
  """
  Filter image (gray or RGB) using contrast stretching to increase contrast in image based on the intensities in
  a specified range.

  Args:
    np_img: Image as a NumPy array (gray or RGB).
    low: Range percentage low value.
    high: Range percentage high value.

  Returns:
    Image with contrast enhanced.
  """
  t = Time()
  low_p, high_p = np.percentile(np_img, (low, high))
  contrast_stretch = sk_exposure.rescale_intensity(np_img, in_range=(low_p, high_p))
  np_info(contrast_stretch, "Contrast Stretch", t.elapsed())
  return contrast_stretch


def filter_histogram_equalization(np_img, nbins=256, output_type="uint8"):
  """
  Filter image (gray or RGB) using histogram equalization to increase contrast in image.

  Args:
    np_img: Image as a NumPy array (gray or RGB).
    nbins: Number of histogram bins.
    output_type: Type of array to return (float or uint8).

  Returns:
     NumPy array (float or uint8) with contrast enhanced by histogram equalization.
  """
  t = Time()
  # if uint8 type and nbins is specified, convert to float so that nbins can be a value besides 256
  if np_img.dtype == "uint8" and nbins != 256:
    np_img = np_img / 255
  hist_equ = sk_exposure.equalize_hist(np_img, nbins=nbins)
  if output_type == "float":
    pass
  else:
    hist_equ = (hist_equ * 255).astype("uint8")
  np_info(hist_equ, "Hist Equalization", t.elapsed())
  return hist_equ


def filter_adaptive_equalization(np_img, nbins=256, clip_limit=0.01, output_type="uint8"):
  """
  Filter image (gray or RGB) using adaptive equalization to increase contrast in image, where contrast in local regions
  is enhanced.

  Args:
    np_img: Image as a NumPy array (gray or RGB).
    nbins: Number of histogram bins.
    clip_limit: Clipping limit where higher value increases contrast.
    output_type: Type of array to return (float or uint8).

  Returns:
     NumPy array (float or uint8) with contrast enhanced by adaptive equalization.
  """
  t = Time()
  adapt_equ = sk_exposure.equalize_adapthist(np_img, nbins=nbins, clip_limit=clip_limit)
  if output_type == "float":
    pass
  else:
    adapt_equ = (adapt_equ * 255).astype("uint8")
  np_info(adapt_equ, "Adapt Equalization", t.elapsed())
  return adapt_equ


def filter_local_equalization(np_img, disk_size=50):
  """
  Filter image (gray) using local equalization, which uses local histograms based on the disk structuring element.

  Args:
    np_img: Image as a NumPy array.
    disk_size: Radius of the disk structuring element used for the local histograms

  Returns:
    NumPy array with contrast enhanced using local equalization.
  """
  t = Time()
  local_equ = sk_filters.rank.equalize(np_img, selem=sk_morphology.disk(disk_size))
  np_info(local_equ, "Local Equalization", t.elapsed())
  return local_equ


def filter_autolevel(np_img, disk_size=1, output_type="uint8"):
  t = Time()
  autolevel = sk_filters.rank.autolevel(np_img, selem=sk_morphology.disk(disk_size))
  autolevel = np_img > autolevel
  if output_type == "bool":
    pass
  elif output_type == "float":
    autolevel = autolevel.astype(float)
  else:
    autolevel = autolevel.astype("uint8") * 255
  np_info(autolevel, "Auto Level", t.elapsed())
  return autolevel


def filter_subtract_mean(np_img, neigh=50, output_type="uint8"):
  t = Time()
  subtract_mean = sk_filters.rank.subtract_mean(np_img, selem=np.ones((neigh, neigh)))
  subtract_mean = np_img > subtract_mean
  if output_type == "bool":
    pass
  elif output_type == "float":
    subtract_mean = subtract_mean.astype(float)
  else:
    subtract_mean = subtract_mean.astype("uint8") * 255
  np_info(subtract_mean, "Subtract Mean", t.elapsed())
  return subtract_mean


def filter_modal(np_img, neigh=50, output_type="uint8"):
  t = Time()
  modal = sk_filters.rank.modal(np_img, selem=np.ones((neigh, neigh)))
  np_info(modal, "Modal", t.elapsed())
  return modal


# def filter_try(np_img, neigh=50, output_type="uint8"):
#   t = Time()
#   tryit = sk_filters.rank.pop_bilateral(np_img, selem=np.ones((neigh, neigh)))
#   # tryit = np_img < tryit
#   if output_type == "bool":
#     pass
#   elif output_type == "float":
#     tryit = tryit.astype(float)
#   else:
#     tryit = tryit.astype("uint8") * 255
#   np_info(tryit, "Try It", t.elapsed())
#   return tryit

img_path = slide.get_training_thumb_path(2)
img = slide.open_image(img_path)
# img.show()
rgb = pil_to_np_rgb(img)
gray = filter_rgb_to_grayscale(rgb)
np_to_pil(gray).show()
complement = filter_complement(gray)
# np_to_pil(complement).show()
# hyst = filter_hysteresis_threshold(complement)
# np_to_pil(hyst).show()
# entr = filter_entropy(complement)
# np_to_pil(entr).show()
# entr = filter_entropy(complement, neighborhood=6, threshold=4)
# np_to_pil(entr).show()
# rem_small = filter_remove_small_objects(hyst)
# np_to_pil(rem_small).show()
# otsu = filter_otsu_threshold(complement)
# np_to_pil(otsu).show()
# can = filter_canny(gray, sigma=7) # interesting WRT pen ink edges
# np_to_pil(can).show()
# plt.imshow(can)
# plt.show()
# local_otsu = filter_local_otsu_threshold(complement)
# np_to_pil(local_otsu).show()
# contrast_stretch = filter_contrast_stretch(gray, low=40, high=60)
# np_to_pil(contrast_stretch).show()
# complement = filter_complement(gray)
# np_to_pil(complement).show()
# hyst = filter_hysteresis_threshold(complement)
# np_to_pil(hyst).show()
# hist_equ = filter_histogram_equalization(rgb)
# np_to_pil(hist_equ).show()
# hist_equ = filter_histogram_equalization(gray, nbins=2)
# np_to_pil(hist_equ).show()
# hist_equ = filter_histogram_equalization(gray, nbins=64)
# np_to_pil(hist_equ).show()
# hist_equ = filter_histogram_equalization(gray, nbins=32)
# np_to_pil(hist_equ).show()
# adapt_equ = filter_adaptive_equalization(gray)
# np_to_pil(adapt_equ).show()
# local_equ = filter_local_equalization(gray)
# np_to_pil(local_equ).show()
# autolevel = filter_autolevel(complement)
# np_to_pil(autolevel).show()
# sub = filter_subtract_mean(complement)
# np_to_pil(sub).show()
# modal = filter_modal(complement)
# np_to_pil(modal).show()

tryit = filter_try(gray)
# np_to_pil(tryit).show()
