import numpy
import time
import matplotlib
import matplotlib.pyplot as plt
import tqdm
import sim_base
import joblib
import cupy
import statsmodels.tsa.stattools as stats_tools


class RunSequences:
    def __init__(self, function, path='cache/'):
        self.memory = joblib.Memory(path + function.__name__)
        self.function = self.memory.cache(function)

    def __call__(self, N_particles, N_runs, *args, **kwargs):
        run_seqs = numpy.array(
            [self.function(N_particle, N_runs, *args, **kwargs) for N_particle in N_particles]
        )

        return run_seqs

    def clear(self, *args):
        self.function.call_and_shelve(args).clear()

    @staticmethod
    def decorate(function):
        return RunSequences(function)


def prediction_run_seqs(N_part, N_runs, gpu):
    memory = joblib.Memory('cache/predict')
    # memory.clear()

    # noinspection PyShadowingNames
    @memory.cache
    def predict(N_particle, N_runs, gpu):
        times = []

        _, _, _, p = sim_base.get_parts(
            N_particles=N_particle,
            gpu=gpu
        )

        for _ in tqdm.tqdm(range(N_runs)):
            u, _ = sim_base.get_random_io()
            time.sleep(0.1)
            t = time.time()
            p.predict(u, 1.)
            times.append(time.time() - t)

        return numpy.array(times)

    N_particles = 2**numpy.arange(1, N_part, 0.5)
    run_seqs = numpy.array(
        [predict(int(N_particle), N_runs, gpu) for N_particle in tqdm.tqdm(N_particles)]
    )

    return N_particles, run_seqs


def update_run_seqs(N_part, N_runs, gpu):
    memory = joblib.Memory('cache/update')
    # memory.clear()

    # noinspection PyShadowingNames
    @memory.cache
    def update(N_particle, N_runs, gpu):
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

    N_particles = 2**numpy.arange(1, N_part, 0.5)
    run_seqs = numpy.array(
        [update(int(N_particle), N_runs, gpu) for N_particle in tqdm.tqdm(N_particles)]
    )

    return N_particles, run_seqs


def resample_run_seqs(N_part, N_runs, gpu):
    memory = joblib.Memory('cache/resample')
    # memory.clear()

    # noinspection PyShadowingNames
    @memory.cache
    def resample(N_particle, N_runs, gpu):
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

    N_particles = 2**numpy.arange(1, N_part, 0.5)
    run_seqs = numpy.array(
        [resample(int(N_particle), N_runs, gpu) for N_particle in tqdm.tqdm(N_particles)]
    )

    return N_particles, run_seqs


def f_vectorize_run_seqs(N_part, N_runs, gpu):
    memory = joblib.Memory('cache/f_vectorize')

    # noinspection PyShadowingNames
    @memory.cache
    def f_vectorize_run(N_particle, N_runs, mem_gpu):
        times = []

        _, _, _, p = sim_base.get_parts(
            N_particles=N_particle,
            gpu=True
        )

        for _ in tqdm.tqdm(range(N_runs)):
            u, _ = sim_base.get_random_io()
            if mem_gpu:
                u = cupy.asarray(u)
            t = time.time()
            p.f_vectorize(p.particles_device, u, 1.)
            times.append(time.time() - t)

        return numpy.array(times)

    N_particles = 2**numpy.arange(1, N_part, 0.5)
    run_seqs = numpy.array(
        [f_vectorize_run(int(N_particle), N_runs, gpu) for N_particle in tqdm.tqdm(N_particles)]
    )

    return N_particles, run_seqs


def g_vectorize_run_seqs(N_part, N_runs, gpu):
    memory = joblib.Memory('cache/g_vectorize')

    # noinspection PyShadowingNames
    @memory.cache
    def g_vectorize_run(N_particle, N_runs, mem_gpu):
        times = []

        _, _, _, p = sim_base.get_parts(
            N_particles=N_particle,
            gpu=True
        )

        for _ in tqdm.tqdm(range(N_runs)):
            u, _ = sim_base.get_random_io()
            if mem_gpu:
                u = cupy.asarray(u)
            t = time.time()
            # noinspection PyProtectedMember
            p.g_vectorize(p.particles_device, u, p._y_dummy)
            times.append(time.time() - t)

        return numpy.array(times)

    N_particles = 2**numpy.arange(1, N_part, 0.5)
    run_seqs = numpy.array(
        [g_vectorize_run(int(N_particle), N_runs, gpu) for N_particle in tqdm.tqdm(N_particles)]
    )

    return N_particles, run_seqs


def state_pdf_draw_run_seqs(N_part, N_runs, gpu):
    memory = joblib.Memory('cache/state_pdf_draw')

    # noinspection PyShadowingNames
    @memory.cache
    def state_pdf_draw(N_particle, N_runs):
        times = []

        _, _, _, p = sim_base.get_parts(
            N_particles=N_particle,
            gpu=True
        )

        for _ in tqdm.tqdm(range(N_runs)):
            t = time.time()
            p.state_pdf.draw(p.N_particles)
            times.append(time.time() - t)

        return numpy.array(times)

    N_particles = 2**numpy.arange(1, N_part, 0.5)
    run_seqs = numpy.array(
        [state_pdf_draw(int(N_particle), N_runs, gpu) for N_particle in tqdm.tqdm(N_particles)]
    )

    return N_particles, run_seqs


def measurement_pdf_pdf_run_seqs(N_part, N_runs, gpu):
    memory = joblib.Memory('cache/measurement_pdf_pdf')

    # noinspection PyShadowingNames
    @memory.cache
    def measurement_pdf_pdf(N_particle, N_runs):
        times = []

        _, _, _, p = sim_base.get_parts(
            N_particles=N_particle,
            gpu=True
        )

        for _ in tqdm.tqdm(range(N_runs)):
            es = p.measurement_pdf.draw(p.N_particles)
            t = time.time()
            p.measurement_pdf.pdf(es)
            times.append(time.time() - t)

        return numpy.array(times)

    N_particles = 2**numpy.arange(1, N_part, 0.5)
    run_seqs = numpy.array(
        [measurement_pdf_pdf(int(N_particle), N_runs, gpu) for N_particle in tqdm.tqdm(N_particles)]
    )

    return N_particles, run_seqs


def get_run_seqs():
    """Returns the run sequences for all the runs

    Returns
    -------
    run_seqss : List
        [CPU; GPU] x [predict; update; resample] x [N_particles; run_seq]
    """
    run_seqss = [
        [
            prediction_run_seqs(20, 20, False),
            update_run_seqs(20, 100, False),
            resample_run_seqs(20, 100, False)
        ],
        [
            prediction_run_seqs(24, 100, True),
            update_run_seqs(24, 100, True),
            resample_run_seqs(24, 100, True)
        ]
    ]
    return run_seqss


def plot_example_benchmark():
    run_seqss = get_run_seqs()
    N_particles, run_seqs = run_seqss[0][1]
    run_seq = run_seqs[-1]

    print(numpy.log2(N_particles[-1]))

    plt.figure(figsize=(15, 5))
    plt.subplot(1, 3, 1)
    plt.semilogy(run_seq, 'kx')
    plt.title('Run sequence')
    plt.xlabel('Iterations')
    plt.ylabel('Time (s)')

    plt.subplot(1, 3, 2)
    plt.plot(run_seq[:-1], run_seq[1:], 'kx')
    plt.title('Lag chart')
    plt.xlabel(r'$X_{i-1}$')
    plt.ylabel(r'$X_{i}$')

    plt.subplot(1, 3, 3)
    plt.acorr(run_seq - numpy.average(run_seq))
    plt.title('Autocorrelation graph')
    plt.xlabel('Lag')
    plt.ylabel('Autocorrelation')

    plt.suptitle(r'Benchmarking for CPU update with $N_p = 2^{19.5}$')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('benchmark.pdf')
    plt.show()


def plot_max_auto():
    run_seqss = get_run_seqs()

    for row in range(2):
        for col in range(3):
            plt.subplot(2, 3, 3*row + col + 1)
            N_parts, run_seqs = run_seqss[row][col]
            N_logs = numpy.log2(N_parts)

            for N_log, run_seq in zip(N_logs, run_seqs):
                abs_cors = numpy.abs(stats_tools.pacf(run_seq, nlags=10)[1:])
                plt.plot(N_log, numpy.median(abs_cors), 'kx')
            plt.ylim(0, 1)
            plt.xlim(0, 20)
            plt.axhline(0.3, color='r')
    plt.show()


# noinspection PyUnresolvedReferences
def plot_run_seqs():
    run_seqss = get_run_seqs()

    cmap = matplotlib.cm.get_cmap('Spectral')
    norm = matplotlib.colors.Normalize(vmin=1, vmax=24)

    for row in range(2):
        for col in range(3):
            plt.subplot(2, 3, row + 2*col + 1)
            N_parts, run_seqs = run_seqss[row][col]
            N_logs = numpy.log2(N_parts)

            for N_log, run_seq in zip(N_logs, run_seqs):
                normailised_value = (N_log - N_logs[0]) / N_logs[-1]
                plt.semilogy(run_seq, '.', color=cmap(normailised_value))

    plt.colorbar(
        matplotlib.cm.ScalarMappable(
            norm=norm,
            cmap=cmap
        ),
        ax=plt.gcf().get_axes()
    )

    plt.savefig('run_seqs.pdf')
    plt.show()


def plot_speed_up():
    run_seqss = get_run_seqs()

    for method in range(3):
        cpu_time = numpy.min(run_seqss[0][method][1], axis=1)
        gpu_time = numpy.min(run_seqss[1][method][1], axis=1)

        speed_up = cpu_time / gpu_time[:cpu_time.shape[0]]
        logN_part = numpy.log2(run_seqss[0][method][0])
        plt.semilogy(logN_part, speed_up, '.')

    plt.legend(['Predict', 'Update', 'Resample'])
    plt.show()


def plot_times():
    run_seqss = get_run_seqs()

    for device in range(2):
        plt.subplot(1, 2, device+1)
        for method in range(3):
            times = numpy.min(run_seqss[device][method][1], axis=1)
            logN_part = numpy.log2(run_seqss[device][method][0])
            plt.semilogy(logN_part, times, '.')

        plt.legend(['Predict', 'Update', 'Resample'])
    plt.show()


def predict(N_particle, N_runs, gpu):
    times = []

    _, _, _, p = sim_base.get_parts(
        N_particles=N_particle,
        gpu=gpu
    )

    for _ in tqdm.tqdm(range(N_runs)):
        u, _ = sim_base.get_random_io()
        # time.sleep(0.1)
        t = time.time()
        p.predict(u, 1.)
        times.append((time.time() - t))

    return numpy.array(times)


if __name__ == '__main__':
    # run_seq = predict(2**20, 100, True)
    # plt.plot(run_seq, 'kx')
    # plt.show()
    # pandas.plotting.autocorrelation_plot(run_seq)
    # plt.show()
    #
    # x = run_seq - numpy.average(run_seq)
    # Nx = len(x)
    # maxlags = 50
    # cors = numpy.correlate(x, x, mode="full")
    # cors /= numpy.dot(x, x)
    # cors = cors[Nx:Nx + maxlags]
    # lags = numpy.arange(1, maxlags + 1)
    # plt.vlines(lags, [0], cors)
    # plt.show()
    # smod.plot_pacf(run_seq)
    # plt.show()
    # plt.stem(stool.pacf(run_seq, nlags=10)[1:], linefmt='k-', markerfmt='ko', use_line_collection=True)
    # plt.show()
    plot_max_auto()
    # plot_example_benchmark()
    # plot_run_seqs()
    # plot_speed_up()
    # plot_times()
