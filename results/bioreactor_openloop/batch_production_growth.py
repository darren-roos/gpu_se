import numpy
import tqdm
import matplotlib
import matplotlib.pyplot as plt
import sim_base
import model


def simulate():
    """Performs no noise simulation"""
    # Simulation set-up
    end_time = 800
    ts = numpy.linspace(0, end_time, end_time*10)
    dt = ts[1]

    bioreactor = model.Bioreactor(
        #                Ng,         Nx,      Nfa, Ne, Nh
        X0=numpy.array([3000 / 180, 1 / 24.6, 0 / 116, 0., 0.]),
        high_N=True
    )

    select_inputs = [0, 1]  # Fg_in, Fm_in
    select_outputs = [0, 2]  # Cg, Cfa

    state_pdf, measurement_pdf = sim_base.get_noise()

    # Initial values
    us = [numpy.array([0., 0.])]
    xs = [bioreactor.X.copy()]
    ys = [bioreactor.outputs(us[-1])]
    ys_meas = [bioreactor.outputs(us[-1])]

    not_cleared = True
    for t in tqdm.tqdm(ts[1:]):
        if t < 25:
            us.append(numpy.array([0., 0.]))
        elif t < 200:
            if not_cleared:
                bioreactor.X[[0, 2, 3, 4]] = 0
                not_cleared = False
                bioreactor.high_N = False

            us.append(numpy.array([0.03, 0.]))
        elif t < 500:
            us.append(numpy.array([0.058, 0.]))
        else:
            us.append(numpy.array([0.074, 0.]))

        bioreactor.step(dt, us[-1])
        bioreactor.X += state_pdf.draw().get().squeeze()
        outputs = bioreactor.outputs(us[-1])
        ys.append(outputs.copy())
        outputs[select_outputs] += measurement_pdf.draw().get().squeeze()
        ys_meas.append(outputs)
        xs.append(bioreactor.X.copy())

    ys = numpy.array(ys)
    ys_meas = numpy.array(ys_meas)
    us = numpy.array(us)

    return ts, ys, ys_meas, us, end_time, select_inputs


def plot():
    """Plots outputs, inputs and biases vs time for a simulation
    that shows the various phases of the bioreactor
    """
    ts, ys, ys_meas, us, end_time, select_inputs = simulate()

    def add_time_lines(axis):
        for time in [25, 200, 500]:
            axis.axvline(time, color='black', alpha=0.4)
        axis.set_xlim([0, ts[-1]])

    matplotlib.rcParams.update({'font.size': 15})
    fig, axes = plt.subplots(1, 2,
                             figsize=(6.25*2, 5),
                             gridspec_kw={'wspace': 0.25}
                             )

    ax = axes[0]
    ax.plot(ts, us[:, select_inputs[1]], 'k')
    ax.plot(ts, us[:, select_inputs[0]], 'k--')

    ax.set_ylabel(r'$\frac{L}{min}$')
    ax.set_xlabel(r't ($min$)')
    ax.set_xlim([0, ts[-1]])
    ax.legend([r'$F_{m, in}$', r'$F_{G, in}$'])
    ax.set_title('Inputs')

    add_time_lines(ax)
    ax.axhline(0.4 / 5000 * 640, color='green')
    ax.axhline(0.5 / 5000 * 640, color='green')

    ax = axes[1]
    ax.plot(ts, ys_meas[:, 2], 'k')
    ax.plot(ts, ys_meas[:, 0], 'grey')
    ax.plot(ts, ys_meas[:, 3], 'k--')

    ax.set_title(r'Outputs')
    ax.set_ylabel(r'$\frac{mg}{L}$')
    ax.set_xlabel(r't ($min$)')
    ax.legend([r'$C_{FA}$', r'$C_{G}$', r'$C_{E}$'])

    ax.axhline(280, color='red')
    add_time_lines(ax)

    # plt.subplot(2, 3, 6)
    # plt.plot(ts, ys[:, 1])
    # plt.title(r'$C_{X}$')
    # add_time_lines()

    # plt.suptitle('Openloop transition between steady states')
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('batch_production_growth.pdf')
    plt.show()


def plot_pretty():
    """Plots outputs, inputs and biases vs time for a simulation
    that shows the various phases of the bioreactor.
    For use in a presentation
    """
    ts, ys, ys_meas, us, end_time, select_inputs = simulate()

    black = '#2B2B2D'
    red = '#E90039'
    orange = '#FF1800'
    white = '#FFFFFF'
    yellow = '#FF9900'

    def add_time_lines():
        for time in [25, 200, 500, 700]:
            plt.axvline(time, color=red, alpha=0.4)
        plt.xlim([0, ts[-1]])

    plt.style.use('seaborn-deep')

    plt.figure(figsize=(12.8, 9.6))
    plt.rcParams.update({'font.size': 16, 'text.color': white, 'axes.labelcolor': white,
                         'axes.edgecolor': white, 'xtick.color': white, 'ytick.color': white})

    plt.gcf().set_facecolor(black)

    plt.subplot(2, 3, 1)
    plt.plot(ts, ys_meas[:, 2], color=orange)
    plt.title(r'$C_{FA}$')
    add_time_lines()
    plt.gca().set_facecolor(black)

    plt.subplot(2, 3, 2)
    plt.plot(ts, ys_meas[:, 0], color=orange)
    plt.title(r'$C_{G}$')
    add_time_lines()
    plt.gca().set_facecolor(black)

    plt.subplot(2, 3, 3)
    plt.plot(ts, ys_meas[:, 3], color=orange)
    plt.title(r'$C_{E}$')
    add_time_lines()
    plt.gca().set_facecolor(black)

    plt.subplot(2, 3, 4)
    plt.plot(ts, us[:, select_inputs[1]], color=yellow)
    plt.title(r'$F_{m, in}$')
    add_time_lines()
    plt.gca().set_facecolor(black)

    plt.subplot(2, 3, 5)
    plt.plot(ts, us[:, select_inputs[0]], color=yellow)
    plt.title(r'$F_{G, in}$')
    plt.xlim([0, ts[-1]])
    plt.axhline(0.4 / 5000 * 640, color='green')
    plt.axhline(0.5 / 5000 * 640, color='green')
    plt.gca().set_facecolor(black)

    # plt.subplot(2, 3, 6)
    # plt.plot(ts, ys[:, 1], color=orange)
    # plt.title(r'$C_{X}$')
    # add_time_lines()
    # plt.gca().set_facecolor(black)

    # plt.suptitle('Openloop growth and production run')
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('batch_production_growth.png', transparent=True)
    plt.show()


if __name__ == '__main__':
    plot()
    # plot_pretty()
