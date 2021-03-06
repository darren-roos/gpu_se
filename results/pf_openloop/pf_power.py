import numpy
import matplotlib
import matplotlib.pyplot as plt
import sim_base
import time
from decorators import PowerMeasurement, PickleJar, RunSequences


@RunSequences.vectorize
@PickleJar.pickle(path='pf/raw')
@PowerMeasurement.measure
def predict_power_seq(N_particle, t_run, gpu):
    """Performs a power sequence on the prediction function with the given number
    of particle and number of runs on the CPU or GPU

    Parameters
    ----------
    N_particle : int
        Number of particles

    t_run : float
        Minimum run time of the function. Repeats if the time is too short

    gpu : bool
        If `True` then the GPU implementation is used.
        Otherwise, the CPU implementation is used

    Returns
    -------
    runs : int
        The number of times the function was run
    """
    _, _, _, p = sim_base.get_parts(
        N_particles=N_particle,
        gpu=gpu
    )

    t = time.time()
    runs = 0
    while time.time() - t < t_run:
        runs += 1
        u, _ = sim_base.get_random_io()
        p.predict(u, 1.)

    return runs


@RunSequences.vectorize
@PickleJar.pickle(path='pf/raw')
@PowerMeasurement.measure
def update_power_seq(N_particle, t_run, gpu):
    """Performs a power sequence on the update function with the given number
    of particle and number of runs on the CPU or GPU

    Parameters
    ----------
    N_particle : int
        Number of particles

    t_run : float
        Minimum run time of the function. Repeats if the time is too short

    gpu : bool
        If `True` then the GPU implementation is used.
        Otherwise, the CPU implementation is used

    Returns
    -------
    runs : int
        The number of times the function was run
    """
    _, _, _, p = sim_base.get_parts(
        N_particles=N_particle,
        gpu=gpu
    )

    t = time.time()
    runs = 0
    while time.time() - t < t_run:
        runs += 1
        u, y = sim_base.get_random_io()
        p.update(u, y)

    return runs


@RunSequences.vectorize
@PickleJar.pickle(path='pf/raw')
@PowerMeasurement.measure
def resample_power_seq(N_particle, t_run, gpu):
    """Performs a power sequence on the resample function with the given number
    of particle and number of runs on the CPU or GPU

    Parameters
    ----------
    N_particle : int
        Number of particles

    t_run : float
        Minimum run time of the function. Repeats if the time is too short

    gpu : bool
        If `True` then the GPU implementation is used.
        Otherwise, the CPU implementation is used

    Returns
    -------
    runs : int
        The number of times the function was run
    """
    _, _, _, p = sim_base.get_parts(
        N_particles=N_particle,
        gpu=gpu
    )

    t = time.time()
    runs = 0
    while time.time() - t < t_run:
        runs += 1
        p.resample()

    return runs


@RunSequences.vectorize
@PickleJar.pickle(path='pf/raw')
@PowerMeasurement.measure
def nothing_power_seq(N_particle, t_run):
    """Performs a power sequence on the no-op function with the given number
    of particle and number of runs on the CPU or GPU.
    Used to check default power usage

    Parameters
    ----------
    N_particle : int
        Number of particles

    t_run : float
        Minimum run time of the function. Repeats if the time is too short

    Returns
    -------
    runs : int
        The number of times the function was run
    """
    _ = N_particle
    t = time.time()
    runs = 0
    while time.time() - t < t_run:
        runs += 1
        time.sleep(246)

    return runs


# noinspection PyTypeChecker
@PickleJar.pickle(path='pf/processed')
def cpu_gpu_power_seqs():
    """Returns the power sequences for all the runs

    Returns
    -------
    power_seqss : List
        [CPU; GPU] x [predict; update; resample] x [N_particles; power_seq]
    """
    N_particles_cpu = numpy.array([int(i) for i in 2**numpy.arange(0, 24, 0.5)])
    N_particles_gpu = numpy.array([int(i) for i in 2**numpy.arange(0, 24, 0.5)])
    power_seqss = [
        [
            predict_power_seq(N_particles_cpu, 5, False),
            update_power_seq(N_particles_cpu, 5, False),
            resample_power_seq(N_particles_cpu, 5, False)
        ],
        [
            predict_power_seq(N_particles_gpu, 5, True),
            update_power_seq(N_particles_gpu, 5, True),
            resample_power_seq(N_particles_gpu, 5, True)
        ]
    ]
    
    for cpu_gpu in range(2):
        for method in range(3):
            _, powers = power_seqss[cpu_gpu][method]
            for i, (N_runs, power) in enumerate(powers):
                powers[i] = power / N_runs
        
    return power_seqss


def plot_energy_per_run():
    """Plot the energy per run of CPU and GPU implementations of the
     predict, update and resample functions
    """
    powerss = cpu_gpu_power_seqs()
    matplotlib.rcParams.update({'font.size': 20})
    fig, axes = plt.subplots(1, 3, sharey='all', figsize=(6.25 * 3, 10))

    for cpu_gpu in range(2):
        for method in range(3):
            ax = axes[method]

            N_parts, powers = powerss[cpu_gpu][method]
            N_logs = numpy.log2(N_parts)
            total_power = powers[:, 0]
            if cpu_gpu:
                total_power += powers[:, 1]

            ax.semilogy(
                N_logs,
                total_power,
                ['k.', 'kx'][cpu_gpu],
                label=['CPU', 'GPU'][cpu_gpu],
                markersize=9
            )
            ax.legend()
            ax.set_xlabel(r'$\log_2(N_p)$')
            if method == 0:
                ax.set_ylabel(r'$\frac{\mathrm{J}}{\mathrm{run}}$')
            ax.set_title(['Predict', 'Update', 'Resample'][method])
            ax.set_xlim([0, 19.5])

    # fig.suptitle('Energy per run')
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('energy_per_run.pdf')
    plt.show()


if __name__ == '__main__':
    plot_energy_per_run()
