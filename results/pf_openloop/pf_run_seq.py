import numpy
import time
import matplotlib
import matplotlib.pyplot as plt
import tqdm
import sim_base
import cupy
import statsmodels.tsa.stattools as stats_tools
import torch
import torch.utils.dlpack as torch_dlpack
import filter.particle
from decorators import RunSequences, PickleJar


@RunSequences.vectorize
@PickleJar.pickle(path='pf/raw')
def predict_run_seq(N_particle, N_runs, gpu):
    """Performs a run sequence on the prediction function with the given number
    of particle and number of runs on the CPU or GPU

    Parameters
    ----------
    N_particle : int
        Number of particles

    N_runs : int
        Number of runs in the sequence

    gpu : bool
        If `True` then the GPU implementation is used.
        Otherwise, the CPU implementation is used

    Returns
    -------
    times : numpy.array
        The times of the run sequence
    """
    times = []

    _, _, _, p = sim_base.get_parts(
        N_particles=N_particle,
        gpu=gpu
    )

    for _ in range(N_runs):
        u, _ = sim_base.get_random_io()
        t = time.time()
        p.predict(u, 1.)
        times.append(time.time() - t)

    return numpy.array(times)


@RunSequences.vectorize
@PickleJar.pickle(path='pf/raw')
def update_run_seq(N_particle, N_runs, gpu):
    """Performs a run sequence on the update function with the given number
    of particle and number of runs on the CPU or GPU

    Parameters
    ----------
    N_particle : int
        Number of particles

    N_runs : int
        Number of runs in the sequence

    gpu : bool
        If `True` then the GPU implementation is used.
        Otherwise, the CPU implementation is used

    Returns
    -------
    times : numpy.array
        The times of the run sequence
    """
    times = []

    _, _, _, p = sim_base.get_parts(
        N_particles=N_particle,
        gpu=gpu
    )

    for j in range(N_runs):
        u, y = sim_base.get_random_io()
        t = time.time()
        p.update(u, y)
        times.append(time.time() - t)

    return numpy.array(times)


@RunSequences.vectorize
@PickleJar.pickle(path='pf/raw')
def resample_run_seq(N_particle, N_runs, gpu):
    """Performs a run sequence on the resample function with the given number
    of particle and number of runs on the CPU or GPU

    Parameters
    ----------
    N_particle : int
        Number of particles

    N_runs : int
        Number of runs in the sequence

    gpu : bool
        If `True` then the GPU implementation is used.
        Otherwise, the CPU implementation is used

    Returns
    -------
    times : numpy.array
        The times of the run sequence
    """
    times = []

    _, _, _, p = sim_base.get_parts(
        N_particles=N_particle,
        gpu=gpu
    )

    for j in range(N_runs):
        p.weights = numpy.random.random(size=p.N_particles)
        p.weights /= numpy.sum(p.weights)
        t = time.time()
        p.resample()
        times.append(time.time() - t)

    return numpy.array(times)


# noinspection PyProtectedMember
@RunSequences.vectorize
@PickleJar.pickle(path='pf/raw')
def predict_subs_run_seq(N_particle, N_runs):
    """Performs a run sequence on the prediction function's subroutines
     with the given number of particles and number of runs

    Parameters
    ----------
    N_particle : int
        Number of particles

    N_runs : int
        Number of runs in the sequence

    Returns
    -------
    times : numpy.array
        The times of the run sequence
    """
    timess = []

    _, _, _, pf = sim_base.get_parts(
        N_particles=N_particle,
        gpu=True,
        pf=True
    )

    dt = 1.
    for _ in tqdm.tqdm(range(N_runs)):
        u, _ = sim_base.get_random_io()
        pf.predict(u, 1.)

        times = []
        t = time.time()
        u = cupy.asarray(u)
        times.append(time.time() - t)

        t = time.time()
        pf.particles += pf.f_vectorize(pf.particles, u, dt)
        times.append(time.time() - t)

        t = time.time()
        pf.particles += pf.state_pdf.draw(pf.N_particles)
        times.append(time.time() - t)

        timess.append(times)

    return numpy.array(timess)


# noinspection PyProtectedMember
@RunSequences.vectorize
@PickleJar.pickle(path='pf/raw')
def update_subs_run_seq(N_particle, N_runs):
    """Performs a run sequence on the update function's subroutines
     with the given number of particles and number of runs

    Parameters
    ----------
    N_particle : int
        Number of particles

    N_runs : int
        Number of runs in the sequence

    Returns
    -------
    times : numpy.array
        The times of the run sequence
    """
    timess = []

    _, _, _, pf = sim_base.get_parts(
        N_particles=N_particle,
        gpu=True,
        pf=True
    )

    for _ in tqdm.tqdm(range(N_runs)):
        u, z = sim_base.get_random_io()
        pf.predict(u, 1.)

        times = []
        t = time.time()
        u = cupy.asarray(u)
        z = cupy.asarray(z, dtype=cupy.float32)
        times.append(time.time() - t)

        t = time.time()
        ys = cupy.asarray(pf.g_vectorize(pf.particles, u, pf._y_dummy))
        times.append(time.time() - t)

        t = time.time()
        es = z - ys
        ws = cupy.asarray(pf.measurement_pdf.pdf(es))
        pf.weights *= ws
        times.append(time.time() - t)

        timess.append(times)

    return numpy.array(timess)


# noinspection PyProtectedMember
@RunSequences.vectorize
@PickleJar.pickle(path='pf/raw')
def resample_subs_run_seq(N_particle, N_runs):
    """Performs a run sequence on the resample function's subroutines
     with the given number of particles and number of runs

    Parameters
    ----------
    N_particle : int
        Number of particles

    N_runs : int
        Number of runs in the sequence

    Returns
    -------
    times : numpy.array
        The times of the run sequence
    """
    timess = []

    _, _, _, pf = sim_base.get_parts(
        N_particles=N_particle,
        gpu=True,
        pf=True
    )

    for _ in tqdm.tqdm(range(N_runs)):
        u, _ = sim_base.get_random_io()
        pf.predict(u, 1.)

        times = []

        t = time.time()
        t_weights = torch_dlpack.from_dlpack(cupy.asarray(pf.weights).toDlpack())
        t_cumsum = torch.cumsum(t_weights, 0)
        cumsum = cupy.fromDlpack(torch_dlpack.to_dlpack(t_cumsum))
        cumsum /= cumsum[-1]
        times.append(time.time() - t)

        t = time.time()
        sample_index = cupy.zeros(pf.N_particles, dtype=cupy.int64)
        random_number = cupy.float64(cupy.random.rand())

        filter.particle.ParallelParticleFilter._parallel_resample[pf._bpg, pf._tpb](
            cumsum, sample_index,
            random_number,
            pf.N_particles
        )
        times.append(time.time() - t)

        t = time.time()
        pf.particles = cupy.asarray(pf.particles)[sample_index]
        pf.weights = cupy.full(pf.N_particles, 1 / pf.N_particles)
        times.append(time.time() - t)

        timess.append(times)

    return numpy.array(timess)


@RunSequences.vectorize
@PickleJar.pickle(path='pf/raw')
def no_op_run_seq(N_time, N_runs):
    """Performs a run sequence on a no-op routine with the given sleep time
     and number of runs

    Parameters
    ----------
    N_time : float
        Sleep time

    N_runs : int
        Number of runs in the sequence

    Returns
    -------
    times : numpy.array
        The times of the run sequence
    """
    times = []

    for _ in tqdm.tqdm(range(N_runs)):
        t = time.time()
        time.sleep(N_time)
        times.append(time.time() - t)

    return numpy.array(times)


@PickleJar.pickle(path='pf/processed')
def cpu_gpu_run_seqs():
    """Returns the run sequences for the predict, update and resample method

    Returns
    -------
    run_seqss : List
        [CPU; GPU] x [predict; update; resample] x [N_particles; run_seq]
    """
    N_particles_cpu = 2**numpy.arange(1, 20, 0.5)
    N_particles_gpu = 2**numpy.arange(1, 24, 0.5)
    run_seqss = [
        [
            predict_run_seq(N_particles_cpu, 20, False),
            update_run_seq(N_particles_cpu, 100, False),
            resample_run_seq(N_particles_cpu, 100, False)
        ],
        [
            predict_run_seq(N_particles_gpu, 100, True),
            update_run_seq(N_particles_gpu, 100, True),
            resample_run_seq(N_particles_gpu, 100, True)
        ]
    ]
    return run_seqss


# noinspection PyTypeChecker
@PickleJar.pickle(path='pf/processed')
def pf_sub_routine_run_seqs():
    """Returns the run sequences for the predict, update and resample subroutines

    Returns
    -------
    run_seqss : List
        [predict; update; resample] x [N_particles; run_seq]
    """
    N_particles_gpu = numpy.array([int(i) for i in 2**numpy.arange(1, 24, 0.5)])
    run_seqss = [
        predict_subs_run_seq(N_particles_gpu, 100),
        update_subs_run_seq(N_particles_gpu, 100),
        resample_subs_run_seq(N_particles_gpu, 100)
    ]
    return run_seqss


def plot_max_auto():
    """Plot the maximum autocorrelation for the predict, update and resample run sequences
    """
    run_seqss = cpu_gpu_run_seqs()

    matplotlib.rcParams.update({'font.size': 20})
    fig, axes = plt.subplots(
        2, 3,
        sharey='row',
        sharex='col',
        figsize=(6.25 * 3, 5 * 2),
        gridspec_kw={'wspace': 0.14}
    )
    for row in range(2):
        for col in range(3):
            ax = axes[row, col]
            N_parts, run_seqs = run_seqss[row][col]
            N_logs = numpy.log2(N_parts)

            for N_log, run_seq in zip(N_logs, run_seqs):
                abs_cors = numpy.abs(stats_tools.pacf(run_seq, nlags=10)[1:])
                ax.plot(N_log, numpy.max(abs_cors), 'kx')
            ax.set_ylim(0, 1)
            ax.set_xlim(0, 20)
            ax.axhline(0.2, color='r')
            if row:
                ax.set_xlabel(r'$N_p$')
            ax.set_xticklabels('$2^{' + numpy.char.array(ax.get_xticks(), unicode=True) + '}$')

            if row == 0:
                ax.set_title(['Predict', 'Update', 'Resample'][col])

            if row == 0 and col == 0:
                ax.set_ylabel('CPU', rotation=0, labelpad=25)

            if col == 0 and row == 1:
                ax.set_ylabel('GPU', rotation=0, labelpad=25)
    # fig.suptitle('Maximum autocorrelation values')
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('max_autocorrelation.pdf')
    plt.show()


def plot_speed_up():
    """Plot the speed-up between CPU and GPU implementations
     for predict, update and resample functions
    """
    run_seqss = cpu_gpu_run_seqs()

    matplotlib.rcParams.update({'font.size': 9})
    plt.figure(figsize=(6.25, 5))
    for method in range(3):
        plt.yscale('log')
        logN_part = numpy.log2(run_seqss[0][method][0])
        cpu_times = run_seqss[0][method][1]
        gpu_times = run_seqss[1][method][1][:cpu_times.shape[0]]

        speed_up = numpy.median(cpu_times, axis=1) / numpy.median(gpu_times, axis=1)
        plt.plot(
            logN_part,
            speed_up,
            ['k.', 'kx', 'k^'][method],
            label=['Predict', 'Update', 'Resample'][method]
        )

    plt.legend()
    ticks, _ = plt.xticks()
    plt.xticks(
        ticks,
        '$2^{' + numpy.char.array(ticks, unicode=True) + '}$'
    )

    # plt.title('Speed-up of particle filter')
    plt.ylabel('Speed-up')
    plt.xlabel('$ N_p $')
    plt.xlim(xmin=1, xmax=19.5)
    plt.axhline(1, color='black', alpha=0.4)
    plt.tight_layout()
    plt.savefig('PF_speedup.pdf')
    plt.show()


def plot_times():
    """Plot the run times of CPU and GPU implementations
     for predict, update and resample functions
    """
    run_seqss = cpu_gpu_run_seqs()

    matplotlib.rcParams.update({'font.size': 9})
    fig, axes = plt.subplots(3, 1, sharey='all', figsize=(6.25, 11))
    for device in range(2):
        for method in range(3):
            ax = axes[method]
            ax.set_yscale('log')
            timess = run_seqss[device][method][1]
            logN_part = numpy.log2(run_seqss[device][method][0])

            times = numpy.median(timess, axis=1)

            # plot outliers
            ranges = numpy.ptp(timess, axis=1)
            mins = numpy.min(timess, axis=1)
            for i in range(times.shape[0]):
                truth = numpy.logical_or(
                    (timess[i] - mins[i]) / ranges[i] < 0.1,
                    (timess[i] - mins[i]) / ranges[i] > 0.9,
                )
                n = timess[i][truth].shape[0]
                ax.plot(
                    [logN_part[i]] * n,
                    timess[i][truth],
                    ['.', 'x'][device],
                    color=(0, 0, 1, 0.5),
                    markersize=4
                )

            times_err = numpy.abs(numpy.quantile(timess, [0.1, 0.9], axis=1) - times)
            ax.errorbar(
                logN_part,
                times,
                yerr=times_err,
                fmt=['k.', 'kx'][device],
                capsize=[5, 3][device],
                elinewidth=2,
                markeredgewidth=1,
                ecolor=(1, 0, 0, 1),
                label=['CPU', 'GPU'][device]
            )

            ax.legend()
            ax.set_title(['Predict', 'Update', 'Resample'][method])

            ax.set_ylabel('Time (s)')
            ax.set_xlabel('$ N_p $')
            ax.set_xlim(xmin=1, xmax=19.5)

            if device:
                ax.set_xticklabels('$2^{' + numpy.char.array(ax.get_xticks(), unicode=True) + '}$')
    # fig.suptitle('Run times particle filter methods')
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    fig.savefig('PF_times.pdf')
    plt.show()


def plot_sub_routine_fractions():
    """Plot the run time fractions of GPU implementation subroutines used in
     predict, update and resample functions
    """
    names = [
        [
            'f (memory copy)', 'f', 'State noise - draw'
        ],
        [
            'g (memory copy)', 'g', 'Measurement noise - pdf'
        ],
        [
            'cumsum', 'Nicely algorithm', 'Index copying'
        ]
    ]

    func_seqss = pf_sub_routine_run_seqs()

    matplotlib.rcParams.update({'font.size': 9})
    fig, axes = plt.subplots(3, 1, sharey='all', figsize=(6.25, 11))
    for i in range(3):
        ax = axes[i]
        N_parts, func_seqs = func_seqss[i]
        logN_part = numpy.log2(N_parts)

        total_times = numpy.sum(numpy.nanmin(func_seqs, axis=1), axis=1)
        frac_times = numpy.nanmin(func_seqs, axis=1).T / total_times
        ax.stackplot(logN_part, frac_times, labels=names[i])

        ax.legend()
        ax.set_title(['Predict', 'Update', 'Resample'][i])
        ax.set_ylabel('Fraction of runtime')
        ax.set_xlabel(r'$ N_p $')
        ax.set_xticklabels('$2^{' + numpy.char.array(ax.get_xticks(), unicode=True) + '}$')

    plt.tight_layout()
    plt.savefig('pf_frac_breakdown.pdf')
    plt.show()


if __name__ == '__main__':
    plot_sub_routine_fractions()
    plot_max_auto()
    plot_times()
    plot_speed_up()
