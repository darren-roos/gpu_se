import numpy
import cupy
from gaussian_sum_dist.MultivariateGaussianSum import MultivariateGaussianSum

m = MultivariateGaussianSum(
    means=numpy.array([[10, 0],
                       [-10, -10]]),
    covariances=numpy.array([[[1, 0],
                              [0, 1]],

                             [[2, 0.5],
                              [0.5, 0.5]]]),
    weights=numpy.array([0.3, 0.7]))

x = cupy.array([-10, -10])
pdf_test = m.pdf(x)

draw_test = m.draw(10)
