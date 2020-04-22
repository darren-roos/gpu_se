import numpy
import time
import noise
import model
import controller

# Noise
state_noise_cov = numpy.array([[1e-1, 0], [0, 7e-2]])
meas_noise_cov = numpy.array([[6e-2, 0], [0, 1e-2]])

nx = noise.WhiteGaussianNoise(state_noise_cov)
ny = noise.WhiteGaussianNoise(meas_noise_cov)

# Model
A = 2*numpy.eye(2)
B = numpy.array([[2, 0.1], [-0.2, 3]])
C = numpy.array([[1, 0], [1, -1]])
D = numpy.array([[0, 0.2], [0, 0]])
dt = 0.5

m = model.LinearModel(A, B, C, D, dt, nx, ny)

# Controller
P = 5
M = 2
Q = numpy.eye(2)
R = numpy.eye(2)
d = numpy.array([1, 1])
e = numpy.array([0])
p = 0.9

K = controller.SMPC(P, M, Q, R, d, e, m, p)

# Step controller
mu0 = numpy.array([1.2, 3])
u0 = numpy.array([10, 0.1])
sigma0 = numpy.array([[2e-1, 1e-3], [4.5e-3, 7e-2]])
r = numpy.array([0, 0])

u = 0
for i in range(5):
    start = time.time()
    u = K.step(mu0, sigma0)
    if __name__ == "__main__":
        print(time.time() - start)

if __name__ == "__main__":
    print(u)
