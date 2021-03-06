import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image
import matplotlib.colors

def read_sar_file(path, dtype, header):
    "Load a single SAR file"
    # Load data and reshape
    array = np.fromfile(path, dtype=dtype)
    if header:
        array = array[1024:]
    # Swap byte order
    return array.newbyteorder('S')

def sar_sum(sar_list):
    "Sum of a list of SARData covariance matrices objects"
    s = SARData()
    s.hhhh = sum([X.hhhh for X in sar_list])
    s.hhhv = sum([X.hhhv for X in sar_list])
    s.hvhv = sum([X.hvhv for X in sar_list])
    s.hhvv = sum([X.hhvv for X in sar_list])
    s.hvvv = sum([X.hvvv for X in sar_list])
    s.vvvv = sum([X.vvvv for X in sar_list])
    return s

class Region(object):
    "Defines a rectangular area in an image"
    def __init__(self, range_i, range_j):
        self.range_i = range_i
        self.range_j = range_j

class SARData(object):
    """
    Object representing a polarimetric SAR image
    using covariance matrix representation
    """

    def load(self, path, code, shape, header):
        "Load SARData object for a given month code"
        self.shape = shape
        self.size = shape[0]*shape[1]
        extension = ".emi" if header else ""
        self.hhhh = read_sar_file(path + '/{}/{}hhhh{}'.format(code, code, extension), np.float32, header)
        self.hhhv = read_sar_file(path + '/{}/{}hhhv{}'.format(code, code, extension), np.complex64, header)
        self.hvhv = read_sar_file(path + '/{}/{}hvhv{}'.format(code, code, extension), np.float32, header)
        self.hhvv = read_sar_file(path + '/{}/{}hhvv{}'.format(code, code, extension), np.complex64, header)
        self.hvvv = read_sar_file(path + '/{}/{}hvvv{}'.format(code, code, extension), np.complex64, header)
        self.vvvv = read_sar_file(path + '/{}/{}vvvv{}'.format(code, code, extension), np.float32, header)
        return self

    def region(self, region):
        "Extract a subset of the SARData image defined by a Region object"
        s = SARData()
        s.hhhh = self.hhhh.reshape(self.shape)[np.ix_(region.range_i, region.range_j)].flatten()
        s.hhhv = self.hhhv.reshape(self.shape)[np.ix_(region.range_i, region.range_j)].flatten()
        s.hvhv = self.hvhv.reshape(self.shape)[np.ix_(region.range_i, region.range_j)].flatten()
        s.hhvv = self.hhvv.reshape(self.shape)[np.ix_(region.range_i, region.range_j)].flatten()
        s.hvvv = self.hvvv.reshape(self.shape)[np.ix_(region.range_i, region.range_j)].flatten()
        s.vvvv = self.vvvv.reshape(self.shape)[np.ix_(region.range_i, region.range_j)].flatten()
        s.shape = (len(region.range_i), len(region.range_j))
        s.size = len(region.range_i) * len(region.range_j)
        return s

    def masked_region(self, mask):
        "Extract a subset of the SARData image defined by a mask"
        assert(mask.shape == self.hhhh.shape)

        s = SARData()
        for c in ["hhhh", "hhhv", "hvhv", "hhvv", "hvvv", "vvvv"]:
            s.__dict__[c] = self.__dict__[c][mask]
        s.shape = None
        s.size = mask.sum()
        return s

    def determinant(self):
        "Determinants of the covariance matrices in a SARData object"
        return np.real((self.hhhh*self.hvhv*self.vvvv
            + self.hhhv*self.hvvv*np.conj(self.hhvv)
            + self.hhvv*np.conj(self.hhhv)*np.conj(self.hvvv)
            - self.hhvv*self.hvhv*np.conj(self.hhvv)
            - self.hhhv*np.conj(self.hhhv)*self.vvvv
            - self.hhhh*self.hvvv*np.conj(self.hvvv)))

    def color_composite(self):
        "Color composite of a EMISAR image"

        # Take logarithm
        green = 10*np.log(self.hhhh.reshape(self.shape)) / np.log(10)
        blue = 10*np.log(self.vvvv.reshape(self.shape)) / np.log(10)
        red = 10*np.log(self.hvhv.reshape(self.shape)) / np.log(10)

        # Normalize
        green = matplotlib.colors.normalize(-30, 0, clip=True)(green)
        blue = matplotlib.colors.normalize(-30, 0, clip=True)(blue)
        red = matplotlib.colors.normalize(-36, -6, clip=True)(red)

        # Return as a RGB image
        return np.concatenate((red[:,:,None], green[:,:,None], blue[:,:,None]), axis=2)

print("Loading SAR data...")

# Define notable rectangular regions in the SAR data set
region_complete = Region(range(0, 1024), range(0, 1024))
region_nochange = Region(range(307, 455), range(52, 120))
region_rye = Region(range(116, 146), range(328, 411))
region_grass = Region(range(268, 330), range(128, 234))

mask_forest = plt.imread("../SAR_Data/forestidx.tif")[:, :, 0].astype(bool, copy=True).flatten()
mask_rye = plt.imread("../SAR_Data/ryeidx.tif")[:, :, 0].astype(bool, copy=True).flatten()
mask_grass = plt.imread("../SAR_Data/grassidx.tif")[:, :, 0].astype(bool, copy=True).flatten()

# Load data
march  = SARData().load("../SAR_Data", "fl062_l", (1024, 1024), header=True)
april  = SARData().load("../SAR_Data", "fl063_l", (1024, 1024), header=False)
may    = SARData().load("../SAR_Data", "fl064_l", (1024, 1024), header=False)
june   = SARData().load("../SAR_Data", "fl065_l", (1024, 1024), header=False)
july   = SARData().load("../SAR_Data", "fl068_l", (1024, 1024), header=False)
august = SARData().load("../SAR_Data", "fl074_l", (1024, 1024), header=True)

# The complete time series
sar_list = [march, april, may, june, july, august]

# Load the masks defining image regions
mask_forest = plt.imread("../SAR_Data/forestidx.tif")[:, :, 0].astype(bool, copy=True).flatten()
mask_rye = plt.imread("../SAR_Data/ryeidx.tif")[:, :, 0].astype(bool, copy=True).flatten()
mask_grass = plt.imread("../SAR_Data/grassidx.tif")[:, :, 0].astype(bool, copy=True).flatten()
masks_crops = [plt.imread("../SAR_Data/masks/{}.tif".format(x))[:, :, 0].astype(bool, copy=True).flatten() for x in range(1, 38)]

# Time series of image regions
sar_list_nochange = [X.masked_region(mask_forest) for X in sar_list]
sar_list_rye      = [X.masked_region(mask_rye)    for X in sar_list]
sar_list_grass    = [X.masked_region(mask_grass)  for X in sar_list]

# Make color composites
plt.imsave("fig/march.jpg", march.color_composite())
plt.imsave("fig/april.jpg", april.color_composite())
plt.imsave("fig/may.jpg", may.color_composite())
plt.imsave("fig/june.jpg", june.color_composite())
plt.imsave("fig/july.jpg", july.color_composite())
plt.imsave("fig/august.jpg", august.color_composite())

