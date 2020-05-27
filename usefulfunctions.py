"""Functions that I find useful but don't want to write out each time."""

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline


class MinorSymLogLocator(mticker.Locator):
    """
    Dynamically find minor tick positions based on the positions of major ticks for a symlog scaling.
    
    Attributes
    ----------
    linthresh : float
        The same linthresh value used when setting the symlog scale.
        
    """
    
    def __init__(self, linthresh):
        #super().__init__()
        self.linthresh = linthresh

    def __call__(self):
        majorlocs = self.axis.get_majorticklocs()
        # iterate through minor locs
        minorlocs = []
        # handle the lowest part
        for i in range(1, len(majorlocs)):
            majorstep = majorlocs[i] - majorlocs[i-1]
            if abs(majorlocs[i-1] + majorstep/2) < self.linthresh:
                ndivs = 10
            else:
                ndivs = 9
            minorstep = majorstep / ndivs
            locs = np.arange(majorlocs[i-1], majorlocs[i], minorstep)[1:]
            minorlocs.extend(locs)
        return self.raise_if_exceeds(np.array(minorlocs))

    def tick_values(self, vmin, vmax):
        raise NotImplementedError('Cannot get tick locations for a {0} type.'.format(type(self)))


def csv2ana(filepath, name, datatype, timescale, time_on_columns=True, dropna='time'):
    """
    Convert csv files to the .ana format required by OPTIMUS.

    Parameters
    ----------
    filepath : str
        Full path to the csv file.
    name : str
        Name of the dataset.
    datatype : str
        One of the OPTIMUS datatypes, e.g. 'TAVIS'.
    timescale : str
        One of the OPTIMUS timescales, e.g. 'ps'.
    time_on_columns : bool, optional
        True if the columns of the csv file are times. The default is True.
    dropna : str, optional
        Whether to remove NaN dy deleting timepoints ('time') or wavelengths ('wavelength'). The default is 'time'.

    Returns
    -------
    None.

    """
    data = pd.read_csv(filepath, header=0, index_col=0)
    if time_on_columns:
        data = data.T
    dropna_axis = 1 if dropna == 'wavelength' else 0
    data.dropna(how='any', inplace=True, axis=dropna_axis)
    wavelengths = data.columns.values
    times = np.array([float(x) for x in data.index.values])
    matrix = data.values
    data = pd.DataFrame(index=times, columns=wavelengths, data=matrix)
    data.to_csv(filepath.replace('data', 'data_pyldm'), header=True, index=True)
    savefilepath = filepath.replace('.csv', '.ana')
    with open(savefilepath, 'w') as f:
        f.write('%FILENAME={0}\r'.format(name))
        f.write('%DATATYPE={0}\r'.format(datatype))
        f.write('%TIMESCALE={0}\r'.format(timescale))
        f.write('%TIMELIST=')
        for time in times:
            if time == times[-1]:
                f.write('{0}\r'.format(time))
            else:
                f.write('{0} '.format(time))      
        f.write('%WAVELENGTHLIST=')
        for wave in wavelengths:
            if wave == wavelengths[-1]:
                f.write('{0}\r'.format(wave))
            else:
                f.write('{0} '.format(wave))
        f.write('%INTENSITYMATRIX=\r')
        np.savetxt(f, matrix, delimiter=' ', newline='\r')
    return


def fsci(x):
    """
    Render numbers in proper scientific notation.

    Parameters
    ----------
    x : float
        Number to render in scientific notation.

    Returns
    -------
    fsci_x : str
        Rendered version of x.

    """
    f = mticker.ScalarFormatter(useOffset=False, useMathText=True)
    g = lambda x, pos: '${}$'.format(f._formatSciNotation('%.1e' % x))
    func = mticker.FuncFormatter(g)
    fsci_x = func(x)
    return fsci_x


def format_axes(ax, labelsize=20, linewidth=1.4, length=6, lengthratio=0.5):
    """
    Adjust axes lines and ticks for optimum visibility.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        An Axes object on which to apply the formatting.
    labelsize : float, optional
        Fontsize of the tick labels. The default is 20.
    linewidth : float, optional
        Width in pt of the axes lines and ticks. The default is 1.4.
    length : float, optional
        Length in pt of the major ticks. The default is 6.
    lengthratio : float, optional
        Ratio of minor to major tick lengths. The default is 0.5.

    Returns
    -------
    ax : matplotlib.axes.Axes
        The modified Axes object.

    """
    ax.tick_params(axis='both', which='major', labelsize=labelsize, width=linewidth, length=length)
    ax.tick_params(axis='both', which='minor', labelsize=labelsize, width=linewidth, length=length*lengthratio)
    for axis in ['top','bottom','left','right']:
      ax.spines[axis].set_linewidth(linewidth)
    return ax


def logticks(ax, which='both'):
    """
    Force 10 logarithmic ticks per decade.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        An Axes object on which to apply the formatting.
    which : str, optional
        Which axes to apply the logarithmic ticks to. Can be 'x', 'y' or 'both'. The default is 'both'.

    Returns
    -------
    ax : matplotlib.axes.Axes
        The modified Axes object.

    """
    if which in ['x', 'both']:
        ax.xaxis.set_major_locator(mticker.LogLocator(numticks=12))
        ax.xaxis.set_minor_locator(mticker.LogLocator(subs=np.linspace(0.1, 0.9, 9), numticks=12))
    if which in ['y', 'both']:
        ax.yaxis.set_major_locator(mticker.LogLocator(numticks=12))
        ax.yaxis.set_minor_locator(mticker.LogLocator(subs=np.linspace(0.1, 0.9, 9), numticks=12))
    return ax


def linearticks(ax, xmajorsep=None, xminorsep=None, ymajorsep=None, yminorsep=None):
    """
    Set linear tick spacings.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        An Axes object on which to apply the formatting.
    xmajorsep : float, optional
        Spacing betwen major xticks. The default is None.
    xminorsep : float, optional
        Spacing betwen minor xticks. The default is None.
    ymajorsep : float, optional
        Spacing betwen major yticks. The default is None.
    yminorsep : float, optional
        Spacing betwen minor yticks. The default is None.

    Returns
    -------
    ax : matplotlib.axes.Axes
        The modified Axes object.

    """
    if xmajorsep is not None:
        ax.xaxis.set_major_locator(mticker.MultipleLocator(xmajorsep))
    if xminorsep is not None:
        ax.xaxis.set_minor_locator(mticker.MultipleLocator(xminorsep))
    if ymajorsep is not None:
        ax.yaxis.set_major_locator(mticker.MultipleLocator(ymajorsep))
    if yminorsep is not None:
        ax.yaxis.set_minor_locator(mticker.MultipleLocator(yminorsep))
    return ax


def resample(x, y, new_x, smoothing=0):
    """
    Interpolate a dataset (x, y) onto a new set of points x with optional smoothing.

    Parameters
    ----------
    x : numpy.ndarray
        1D array of original x points.
    y : numpy.ndarray
        1D array of original y points.
    new_x : numpy.ndarray
        1D array of new x points.
    smoothing : float, optional
        Amount of smoothing to do. The default is 0.

    Returns
    -------
    new_y : numpy.ndarray
        The resampled y values.

    """
    y_spl = UnivariateSpline(x, y, s=smoothing)
    new_y = y_spl(new_x)
    return new_y