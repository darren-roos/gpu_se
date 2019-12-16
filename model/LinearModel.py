import noise


class LinearModel:
    """Structured data for a discrete state space linear model with noise

    .. math:
        x_{k+1} &= A x_k + B u_k + w_k\\
        y_k &= C x_k + D u_k + v_k

    where :math:`w_k` and :math:`v_k` are additive noise sampled from some distribution

    Parameters
    ----------
    A, B, C, D : ndarray
        2D array containing the relevant state space matrices

    dt : float
        The sampling interval

    state_noise, measurement_noise : noise.Noise, optional
        Objects containing state and measurement noise information

    Attributes
    -----------
    A, B, C, D : ndarray
        2D array containing the relevant state space matrices

    dt : float
        The sampling interval

    state_noise, measurement_noise : noise.Noise
        Objects containing state and measurement noise information

    Nx, Ni, No : int
        Number of states, inputs and outputs

    """
    def __init__(self, A, B, C, D, dt,
                 state_noise: noise.Noise = None,
                 measurement_noise: noise.Noise = None):
        self.A = A
        self.B = B
        self.C = C
        self.D = D

        self.T = dt
        self.w = self.state_noise = state_noise
        self.v = self.measurement_noise = measurement_noise

        self.Nx = self.A.shape[0]
        self.Ni = self.B.shape[1]
        self.No = self.C.shape[0]