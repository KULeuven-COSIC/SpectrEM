import h5py
import numpy as np
import os
import scipy as sp
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'   # Disable tensorflow logs
import tensorflow as tf

from scipy.fft import fft
from scipy.signal import find_peaks
from sklearn.mixture import GaussianMixture

from utils import evaluate_batch, print_results, get_bit_sp, get_outliers, is_cf, IND_CF, IND_INS, get_optimal_window, PRERECORDED_TRACES_DIR



##############################################################################
#####                         Frequency scaling                          #####
##############################################################################

## Frequency scaling
# When DVFS is enabled, the processor will adapt its frequency to the operating
# conditions. The evaluation of the traces can be adapted by splitting the
# based on operating frequency, and evaluating all frequency bins seperately.

def get_cpu_freq(trace):
    """Get the operating frequency from the given trace.

    @param trace The trace for which to get the operating frequency
    """

    # Find the peaks within the frequency spectrum of the trace
    peaks = find_peaks(np.abs(fft(trace)), prominence=50000)[0]

    # Remove lower peaks that do not correspond to a clock frequency, since the
    # minimal clock frequency on the Cortex-A72 is 600 MHz.
    peaks = peaks[peaks > 590]   

    # Round to nearest multiple of 100, since all valid operating frequencies are
    # multiples of 100.
    peaks = np.round(peaks, -2) 

    # We want to assume the lowest frequency as, e.g., harmonics, may interfere
    # otherwise (e.g., when the clock frequency is 600 MHz, there will be a
    # strong harmonic at 1.2 GHz). As a result we iterate over the available
    # frequencies.
    # Note that in any trace there is, for some reason, a peak at 1 GHz. As a
    # result, we only choose 1 GHz if we don't find a peak at any other valid
    # frequency.
    for i in range(600, 1600, 100):
        if i == 1000:
            continue
            
        if i in peaks:
            return i
        
    return 1000

def get_segments(clk_comps):
    """Get the segments for which the POC is running on the core of interest.

    This implementation is based on the observation that the harmonic of the
    clock frequency is much stronger when running on the core under the probe
    than when running on another core.

    @param clk_comps The harmonic of the clock frequency components for which 
                     to compute the segments.
    """

    # We determined the threshold for this component at 5000
    l = np.where(clk_comps > 5000)[0]
  
    # Compute the segments, but tolerate a gap of 1
    # https://stackoverflow.com/questions/21142231/group-consecutive-integers-and-tolerate-gaps-of-1
    segments_all = np.split(l, np.where(np.diff(l)>2)[0]+1)
    segments = []

    for s in segments_all:
        # We throw away any segment smaller than 100 traces.
        if len(s) < 100:
            continue

        segments.append((s[0], s[-1], s[-1] - s[0]))

    return segments

def get_clk_freq_comp(trace, freq):
    """Compute the first harmonic of the clock frequency."""
    # Get the first harmonic of the clk freq component
    # Note: Divide by 5 because we are working with a window size of 5000 at a
    # sample frequency of 25 GHz.
    # TODO: remove hardcoded window
    return np.abs(fft(trace[11000:16000]))[2*freq//5]

ind = { 600: np.array([119, 120, 121]),
        700: np.array([139, 140, 141]),
        800: np.array([159, 160, 161]),
        900: np.array([179, 180, 191]),
        1000: np.array([199, 200, 201]),
        1100: np.array([219, 220, 221]),
        1200: np.array([239, 240, 241]),
        1300: np.array([259, 260, 261]),
        1400: np.array([279, 280, 281]),
        1500: np.array([299, 300, 301])}

pos = { 600: 16000,
    700: 16000,
    800: 16000,
    900: 16500,
    1000: 16500,
    1100: 16500,
    1200: 16500,
    1300: 16500,
    1400: 18000,
    1500: 19500}

def evaluate_file_dvfs(filename, mlp_dir, get_bit, mlp_threshold=0.95, gmm_proba=None):
    # Load in the pre-trained MLP models
    models = {freq//1000:tf.keras.models.load_model(f"{mlp_dir}/model-{freq}.hdf5", compile=False) for freq in range(600000, 1600000, 100000)}

    f_traces = h5py.File(filename, "r", libver="latest")

    traces = f_traces["data"]["traces"]
    inputs = f_traces["data"]["inputs"]

    nbtraces = traces.shape[0]

    # We first compute the operating frequency for each trace. 
    freqs = np.array([get_cpu_freq(traces[i]) for i in range(nbtraces)])

    # While technically not required, as for these POCs we lock the core the
    # POC is running on, we also implement the filtering based on which core
    # the POC is running on. This allows to evaluate traces that have both DVFS
    # enabled and do not specify the core.
    clk_comps = np.array([get_clk_freq_comp(traces[i], freqs[i]) for i in range(nbtraces)])
    segments = get_segments(clk_comps)

    
    # For each frequency bin, we now compute how many traces fall in that bin.
    nb_freqs = dict()
    for s in segments:
        start, stop, length = s
        
        tmp = freqs[start:stop]
        unique, counts = np.unique(tmp, return_counts=True)
        
        for freq, count in zip(unique, counts):
            if freq in nb_freqs:
                nb_freqs[freq] += count
            else:
                nb_freqs[freq] = count
                
    
    # For each frequency bin, we now store the components around the clock
    # frequency (in fs), the ground truths (in expected), and the indices
    # corresponding to the stored components and ground truths (in inds).
    # These are all stored as lists in dictionaries with the corresponding
    # clock frequency as the key.
    fs = {freq: np.zeros((nb_freqs[freq], 3), dtype=float) for freq in nb_freqs}
    expected = {freq: np.zeros((nb_freqs[freq],), dtype=int) for freq in nb_freqs}
    inds = {freq: np.zeros((nb_freqs[freq],), dtype=int) for freq in nb_freqs}
    
    cur_indices = {freq: 0 for freq in nb_freqs}

    for s in segments:
        start, stop, length = s

        for freq in nb_freqs:
            traces_freq = np.where(freqs[start:stop] == freq)[0] + start

            fs[freq][cur_indices[freq]:cur_indices[freq]+len(traces_freq)] = np.abs(fft(traces[traces_freq,pos[freq]:pos[freq]+5000]))[:,ind[freq]]
            expected[freq][cur_indices[freq]:cur_indices[freq]+len(traces_freq)] = get_bit_sp(inputs[traces_freq])
            inds[freq][cur_indices[freq]:cur_indices[freq]+len(traces_freq)] = traces_freq
            cur_indices[freq] += len(traces_freq)


    # We now evaluate the traces within each frequency bin seperately.
    errors_gmm, totals_gmm = 0, 0
    errors_mlp, totals_mlp = 0, 0

    for freq in nb_freqs:

        ## GMM evaluation

        f = fs[freq]

        # Filter traces for which the clock component is an outlier
        # This is needed for the clustering algorithm as otherwise, the GMM
        # algorithm may decide to consider the outliers as one of the two groups. 
        ind_nol = get_outliers(f[:,1], outlier_threshold=2)

        # Filter only the frequency components that we will consider for the traces
        # that we will consider. We do not supply all frequency components to the
        # clustering algorithm as only few components exhibit leakage.
        f = f[ind_nol, :]
                
        # When there are less than two traces in a frequency bin, the clustering
        # will not work. We simply ignore these traces.
        if f.shape[0] < 2:
            continue

        # Perform the actual clustering
        gmm = GaussianMixture(n_components=2, covariance_type="full", n_init=10, random_state=0)
        gmm_labels = gmm.fit_predict(f)

        b = expected[freq][ind_nol]
        total_gmm = len(b)

        error_gmm = np.sum(gmm_labels == b)

        # The GMM algorithm has no way to know which group represents a zero and
        # which a one. As a result, we switch the groups should the GMM predict
        # the bits the other way around.
        if error_gmm > total_gmm//2:
            error_gmm = total_gmm-error_gmm

        errors_gmm += error_gmm
        totals_gmm += total_gmm

        ## MLP evaluation
        window = slice(pos[freq], pos[freq]+5000)
        f = np.abs(fft(traces[inds[freq][ind_nol],window]))[:,:1000]
        mlp_labels = np.squeeze(models[freq].predict(f, verbose=0))

        # To improve the BER, we only consider traces where the MLP network produced
        # confident predictions. Each label for a trace returns two numbers that can
        # be interpreted of the probability of that trace encoding that particular
        # bit. We only consider traces for which the MLP network assigns a
        # probability larger than mlp_threshold (95% by default).
        mlp_predictions = np.argmax(mlp_labels, axis=1)
        mlp_confidence = np.max(mlp_labels, axis=1)
        mlp_considered = np.where(mlp_confidence > mlp_threshold)[0]
        mlp_predictions = mlp_predictions[mlp_considered]

        b = get_bit_sp(inputs[inds[freq][ind_nol][mlp_considered]])
        total_mlp = len(mlp_considered)
        error_mlp = np.sum(mlp_predictions != b)

        errors_mlp += error_mlp
        totals_mlp += total_mlp

    return (errors_gmm, totals_gmm), (errors_mlp, totals_mlp)




##############################################################################
#####                           Core affinity                            #####
##############################################################################

def evaluate_range(traces, inputs, window, ind, start=0, stop=16384, step=None):
    nb = stop - start
    if step is None:
        step = nb
    
    fail_g_tot = 0
    total_tot = 0
    
    for i in range(np.ceil(nb/step).astype(int)):
        sstart = start + i*step
        sstop = min(start + (i+1)*step, stop)
        
        f = np.abs(fft(traces[sstart:sstop,window]))[:,:1000]

        ind_nol = get_outliers(f[:,120])

        ## GMM evaluation

        f = f[ind_nol[:,None],ind]
                
        # Sometimes, there is only a single remaining trace due to considering
        # the traces in batches. This would cause the clustering algorithms to
        # throw an error. We simply ignore this single trace and do not consider
        # it.
        if len(f) < 2:
            continue
                
        gmm = GaussianMixture(n_components=2, covariance_type="full", random_state=0)
        gmm_labels = gmm.fit_predict(f)
        
        b_gmm = get_bit_sp(inputs[np.arange(sstart, sstop)[ind_nol]])
        total_gmm = len(gmm_labels)
        error_gmm = np.sum(gmm_labels == b_gmm)

        # The GMM algorithm has no way to know which group represents a zero and
        # which a one. As a result, we switch the groups should the GMM predict
        # the bits the other way around.
        if error_gmm > total_gmm//2:
            error_gmm = total_gmm-error_gmm
            
        fail_g_tot += error_gmm
        total_tot += total_gmm

    return fail_g_tot, total_tot

def evaluate_file_cores(filename, mlp_detectcore, mlp_predictbit, mlp_threshold: float=0.95, gmm_proba=None):
    f_traces = h5py.File(filename, "r", libver="latest")

    traces = f_traces["data"]["traces"]
    inputs = f_traces["data"]["inputs"]

    nbtraces = traces.shape[0]

    window = get_optimal_window(f_traces)

    ## GMM evaluation

    # We first compute the components at the first harmonic of the operating
    # frequency. These components can tell us whether the POC was running on
    # the core of interest or not. When running on the core for which we optimized
    # our probe position, we noticed that this component was much larger than
    # when running on a different core. We therefore locate segments within the
    # batch for which this component is large thoughout the segment.
    clk_comps = np.array([get_clk_freq_comp(traces[i], 600) for i in range(nbtraces)])
    segments = get_segments(clk_comps)
    
    # We now evaluate the traces for each segment seperately.
    errors_gmm = 0
    totals_gmm = 0

    # We cluster the traces for each segment seperately.
    for s in segments:
        start, stop, length = s
        
        ind = IND_CF if is_cf(f_traces) else IND_INS

        # We are considering traces running on either core 0 or core 1.
        # Traces running on different cores, but in the same clustering batch
        # may result in worse performance. As a result, we split up the segments
        # in batches of 64 traces.
        error_gmm, total_gmm = evaluate_range(traces, inputs, window, ind, start, stop, 64)
        
        errors_gmm += error_gmm
        totals_gmm += total_gmm


    ## MLP evaluation

    # We trained two MLP networks to evaluate the traces in this scenatio. The
    # first network detects whether the POC was running on the correct core,
    # whereas the decond MLP network does the actual classification.
    model_predictcore = tf.keras.models.load_model(mlp_detectcore, compile=False)
    model_predictbit = tf.keras.models.load_model(mlp_predictbit, compile=False)

    # The inputs to the first MLP network are simply the frequency representation
    # of the full traces (up to 200 points to limit the number of parameters).
    f = np.abs(sp.fft.fft(traces))[:,:2000]
    core_labels = np.squeeze(model_predictcore.predict(f, verbose=0))

    # When the label is 1, the trace is running on the correct core.
    core_predictions = np.argmax(core_labels, axis=1)
    correct_core = np.where(core_predictions==1)[0]

    # We now continue the MLP evaluation similarly to the base experiments
    f = np.abs(fft(traces[:, window]))[:,:1000]
    mlp_labels = np.squeeze(model_predictbit.predict(f, verbose=0))

    # To improve the BER, we only consider traces where the MLP network produced
    # confident predictions. Each label for a trace returns two numbers that can
    # be interpreted of the probability of that trace encoding that particular
    # bit. We only consider traces for which the MLP network assigns a
    # probability larger than mlp_threshold (95% by default).
    mlp_predictions = np.argmax(mlp_labels, axis=1)
    mlp_confidence = np.max(mlp_labels, axis=1)
    mlp_considered = np.where(mlp_confidence > mlp_threshold)[0]

    # We now filter out any traces not running on the correct core.
    mlp_considered = np.intersect1d(mlp_considered, correct_core)

    mlp_predictions = mlp_predictions[mlp_considered]

    b = get_bit_sp(inputs[:])
    totals_mlp = len(mlp_considered)
    errors_mlp = np.sum(mlp_predictions != b[mlp_considered])
        
    return (errors_gmm, totals_gmm), (errors_mlp, totals_mlp)






##############################################################################
#####                              Flushing                              #####
##############################################################################

# Since flushing spreads the leakage more in time, the MLP method is revised to
# not consider a single FFT window, but rather a spectrogram. To keep the number
# of parameters under control, each FFT window within this spectrogram only 
# consists of the leaking frequencies. 
# The GMM method is not adapted, and thus shows a much higher BER compared to 
# the MLP method.
def evaluate_file_noflush(filename: str, mlp: str, get_bit, mlp_threshold: float=0.95, gmm_proba=False):
    with h5py.File(filename, "r", libver="latest") as f_eval:
        traces = f_eval["data"]["traces"]
        inputs = f_eval["data"]["inputs"]

        window = get_optimal_window(f_eval)

        f = np.abs(fft(traces[:, window]))[:,:1000]

        nbtr = traces.shape[0]
        f_mlp = np.zeros((nbtr, len(range(10000, 20100, 100)), 3))
        for i, window in enumerate(range(10000, 20100, 100)):
            f_mlp[:, i, :] = np.abs(fft(traces[:,window:window+5000]))[:,[119, 120, 121]]
            
        f_mlp = np.reshape(f_mlp, (nbtr, len(range(10000, 20100, 100)) * 3))

        b = get_bit(inputs[:])

        ind = IND_CF

    ## MLP Evaluation

    # We first load in the saved model and predict the encoded bits.
    model = tf.keras.models.load_model(mlp, compile=False)
    
    mlp_labels = np.squeeze(model.predict(f_mlp, verbose=0))

    # To improve the BER, we only consider traces where the MLP network produced
    # confident predictions. Each label for a trace returns two numbers that can
    # be interpreted of the probability of that trace encoding that particular
    # bit. We only consider traces for which the MLP network assigns a
    # probability larger than mlp_threshold (95% by default).
    mlp_predictions = np.argmax(mlp_labels, axis=1)
    mlp_confidence = np.max(mlp_labels, axis=1)
    mlp_considered = np.where(mlp_confidence > mlp_threshold)[0]
    mlp_predictions = mlp_predictions[mlp_considered]

    total_mlp = len(mlp_considered)
    error_mlp = np.sum(mlp_predictions != b[mlp_considered])
    
    ## GMM Evaluation

    # Filter traces for which the clock component is an outlier
    # This is needed for the clustering algorithm as otherwise, the GMM
    # algorithm may decide to consider the outliers as one of the two groups. 
    ind_nol = get_outliers(f[:,120])

    # Filter only the frequency components that we will consider for the traces
    # that we will consider. We do not supply all frequency components to the
    # clustering algorithm as only few components exhibit leakage.
    f = f[ind_nol[:,None],ind]

    # Perform the actual clustering. 
    gmm = GaussianMixture(n_components=2, covariance_type="full", n_init=10, random_state=0)
    gmm_labels = gmm.fit_predict(f)
    b_gmm = b[ind_nol]

    if gmm_proba:
        gmm_labels_proba = gmm.predict_proba(f)
        gmm_confidence = np.max(gmm_labels_proba, axis=1)
        gmm_considered = np.where(gmm_confidence > mlp_threshold)[0]
        gmm_labels = gmm_labels[gmm_considered]
        b_gmm = b[ind_nol][gmm_considered]
    
    total_gmm = len(gmm_labels)
    error_gmm = np.sum(gmm_labels == b_gmm)

    # The GMM algorithm has no way to know which group represents a zero and
    # which a one. As a result, we switch the groups should the GMM predict
    # the bits the other way around.
    if error_gmm > total_gmm//2:
        error_gmm = total_gmm-error_gmm

    return (error_gmm, total_gmm), (error_mlp, total_mlp)

print("Evaluating experiments in Section 7 (reducing evaluation assumptions).")
print("Estimated run time: 2 hours")

results_gmm_dvfs, results_mlp_dvfs = evaluate_batch(
    f"{PRERECORDED_TRACES_DIR}/2-reducing-assumptions/0-frequency-scaling/", 
    f"{PRERECORDED_TRACES_DIR}/2-reducing-assumptions/pretrained-mlp-models/0-frequency-scaling/", 
    get_bit_sp,
    "Frequency scaling",
    gmm_proba=None,
    eval_file=evaluate_file_dvfs)

print(f"Frequency scaling")
print_results(results_gmm_dvfs, " -> GMM:")
print_results(results_mlp_dvfs, " -> MLP:")

results_gmm_cores, results_mlp_cores = evaluate_batch(
    f"{PRERECORDED_TRACES_DIR}/2-reducing-assumptions/1-core-affinity/",
    f"{PRERECORDED_TRACES_DIR}/2-reducing-assumptions/pretrained-mlp-models/1-core-affinity/spectrem_coreaffinity_predictcore_pretrained_model.hdf5",
    f"{PRERECORDED_TRACES_DIR}/2-reducing-assumptions/pretrained-mlp-models/1-core-affinity/spectrem_coreaffinity_pretrained_model.hdf5",
    "Core affinity",
    eval_file=evaluate_file_cores)

print(f"Core affinity")
print_results(results_gmm_cores, " -> GMM:")
print_results(results_mlp_cores, " -> MLP:")

results_gmm_noflush, results_mlp_noflush = evaluate_batch(
    f"{PRERECORDED_TRACES_DIR}/2-reducing-assumptions/2-flushing", 
    f"{PRERECORDED_TRACES_DIR}/2-reducing-assumptions/pretrained-mlp-models/2-flushing/spectrem_cf_a_pretrained_model.hdf5", 
    get_bit_sp,
    "Flushing",
    gmm_proba=True,
    eval_file=evaluate_file_noflush)

print(f"Flushing")
print_results(results_gmm_noflush, " -> GMM:")
print_results(results_mlp_noflush, " -> MLP:")
