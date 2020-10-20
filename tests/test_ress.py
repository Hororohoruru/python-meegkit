"""Test RESS."""
import matplotlib.pyplot as plt
import numpy as np
import pytest
import scipy.signal as ss
from meegkit import ress
from meegkit.utils import fold, rms, unfold, snr_spectrum


def create_data(n_times, n_chans=10, n_trials=50, freq=12, sfreq=250,
                noise_dim=8, SNR=1, t0=100, show=False):
    """Create synthetic data.

    Returns
    -------
    noisy_data: array, shape=(n_times, n_channels, n_trials)
        Simulated data with oscillatory component strting at t0.

    """
    # source
    source = np.sin(2 * np.pi * freq * np.arange(n_times - t0) / sfreq)[None].T
    s = source * np.random.randn(1, n_chans)
    s = s[:, :, np.newaxis]
    s = np.tile(s, (1, 1, n_trials))
    signal = np.zeros((n_times, n_chans, n_trials))
    signal[t0:, :, :] = s

    # noise
    noise = np.dot(
        unfold(np.random.randn(n_times, noise_dim, n_trials)),
        np.random.randn(noise_dim, n_chans))
    noise = fold(noise, n_times)

    # mix signal and noise
    signal = SNR * signal / rms(signal.flatten())
    noise = noise / rms(noise.flatten())
    noisy_data = signal + noise

    if show:
        f, ax = plt.subplots(3)
        ax[0].plot(signal[:, 0, 0], label='source')
        ax[1].plot(noise[:, 1, 0], label='noise')
        ax[2].plot(noisy_data[:, 1, 0], label='mixture')
        ax[0].legend()
        ax[1].legend()
        ax[2].legend()
        plt.show()

    return noisy_data, signal


@pytest.mark.parametrize('target', [12, 15, 20])
@pytest.mark.parametrize('n_trials', [10, 20])
def test_ress(target, n_trials, show=False):
    """Test RESS."""
    sfreq = 250
    data, source = create_data(n_times=1000, n_trials=n_trials, freq=target,
                               sfreq=sfreq, show=False)

    out = ress.RESS(data, sfreq=sfreq, peak_freq=target)

    nfft = 250
    bins, psd = ss.welch(out, sfreq, window="hamming", nperseg=nfft,
                         noverlap=125, axis=0)

    print(psd.shape)
    psd = psd.mean(axis=1, keepdims=True)  # average over trials
    snr = snr_spectrum(psd, bins, skipbins=2, n_avg=2)

    if show:
        f, ax = plt.subplots(1)
        ax.plot(bins, snr, 'o')
        ax.axhline(1, ls=':', c='grey', zorder=0)
        ax.axvline(target, ls=':', c='grey', zorder=0)
        ax.set_ylabel('SNR (a.u.)')
        ax.set_xlabel('Frequency (Hz)')
        ax.set_xlim([0, 40])
        plt.show()

    assert snr[bins == target] > 10
    assert (snr[(bins < target - 1) | (bins > target + 1)] < 2).all()


if __name__ == '__main__':
    import pytest
    # pytest.main([__file__])
    test_ress(12, 10, show=True)
