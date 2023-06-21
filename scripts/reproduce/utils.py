import h5py
import numpy as np
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'   # Disable tensorflow logs
import tensorflow as tf


from scipy.fft import fft
from sklearn.mixture import GaussianMixture
from tqdm import tqdm

##############################################################################
#####                   Path to the prerecorded traces                   #####
##############################################################################
PRERECORDED_TRACES_DIR = "./traces"

# Parameters:
F_SAMPLE = 25e9  # 25 GS/s
WINDOW_LENGTH = 0.2e-6  # 200 ns

WINDOW_SIZE = int(F_SAMPLE * WINDOW_LENGTH)

IND_CF = np.array([119, 120, 121])
IND_INS = np.array([19, 20, 27, 28, 29, 30, 31, 32, 33, 89, 90, 91, 100, 140, 150, 210, 260, 270])

# The random string used in the POC SpectrEM implementations
data = b"data|\x01\x36\x9b\x78\xc9\x2c\x3d\x32\xfa\x83\x50\xaf\x39\xaf\x69\x2d\x58\xd7\x38\x6a\xc1\x63\x15\xc7\x3c\x4d\x96\x61\xe1\x88\xbd\xed"
data = np.frombuffer(data, dtype=np.uint8)

def get_bit_sp(index):
    """Get the bit corresponding to the given inputs
    
    @param index The index for which to get the corresponding bit"""
    return (data[index // 8] & (1 << (index % 8))).astype(bool)

def get_bit_md(inputs):
    """Get the bit corresponding to the given inputs for MeltEMdown
    
    @param inputs The inputs for which to retrieve the secret bit"""
    return inputs[:,2]

data_ssh = np.array([False, True, False, True, True, False, True, False, True, True, False, False, False, True, True, True,
 False, True, True, False, True, True, False, False, True, True, False, True, True, False, True, False, True, False,
 False, False, False, True, True, True, False, True, True, False, True, True, False, False, True, True, True, True,
 True, True, True, False, False, False, False, False, False, False, False, True])

def get_bit_ssh(inputs):
    return data_ssh[inputs - 10]

def get_bit_sftp(inputs):
    return inputs==15


def print_results(results, prefix=""):
    print(f"{prefix} {results[0]/results[1]:%} BER ({results[0]} errors in {results[1]} traces)")

def get_optimal_window(f_eval):
    window_start = f_eval.attrs["optimal_window_start"]
    return slice(window_start, window_start + WINDOW_SIZE)

def is_cf(f_eval):
    return f_eval.attrs["gadget"] == "cf"

def get_outliers(components, outlier_threshold: float=1.7):
    return np.where(abs(components - np.mean(components)) <= outlier_threshold * np.std(components))[0]



##############################################################################
#####                           Evaluate file                            #####
##############################################################################

def evaluate_file(filename: str, mlp: str, get_bit, mlp_threshold: float=0.95, gmm_proba=False):
    """Evaluate the BER for the given batch of traces using both GMM and MLP evaluation.

    @param filename The filename of the batch containing the traces.
    @param mlp The filename of the pre-trained MLP model.
    @param get_bit A function that maps the inputs of the batches to their expected values.
    @param mlp_threshold The probability threshold to use when filtering traces based on confidence.
    @param gmm_proba A bool indicating whether to filter the GMM evaluation based on prediction confidence.
    """
    with h5py.File(filename, "r", libver="latest") as f_eval:
        traces = f_eval["data"]["traces"]
        inputs = f_eval["data"]["inputs"]

        window = get_optimal_window(f_eval)

        f = np.abs(fft(traces[:, window]))[:,:1000]

        b = get_bit(inputs[:])

        ind = IND_CF if is_cf(f_eval) else IND_INS

    ############################## MLP Evaluation ##############################

    # We first load in the saved model and predict the encoded bits.
    model = tf.keras.models.load_model(mlp, compile=False)
    mlp_labels = np.squeeze(model.predict(f, verbose=0))

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
    
    ############################## GMM Evaluation ##############################

    # Filter traces for which the clock component is an outlier
    # This is needed for the clustering algorithm as otherwise, the GMM
    # algorithm may decide to consider the outliers as one of the two groups. 
    ind_nol = get_outliers(f[:,120])

    # Filter only the frequency components that we will consider for the traces
    # that we will consider. We do not supply all frequency components to the
    # clustering algorithm as only few components exhibit leakage.
    f = f[ind_nol[:,None],ind]

    # Perform the actual clustering. 
    gmm = GaussianMixture(n_components=2, covariance_type="full")
    gmm_labels = gmm.fit_predict(f)
    b_gmm = b[ind_nol]

    if gmm_proba:
        # Similar to when the MLP classification, the MLP method can output
        # the probabilities of belonging to a specific group. This then gives
        # an estimate of the confidence of the prediction.
        # From our experience, this is only useful when the method would
        # otherwise have a high BER (for instance, when using cache thrashing).
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



def evaluate_batch(directory, mlp, get_bit, desc=None, gmm_proba: bool=False, eval_file=evaluate_file):
    """Evaluate all files within the given directory
    """
    files = [f for f in os.listdir(directory) if f.endswith(".hdf5")]

    errors_gmm, totals_gmm = 0, 0
    errors_mlp, totals_mlp = 0, 0

    for file in tqdm(files, desc=desc, leave=False):
        resutls_gmm, results_mlp = eval_file(f"{directory}/{file}", mlp, get_bit, gmm_proba=gmm_proba)

        errors_gmm += resutls_gmm[0]
        totals_gmm += resutls_gmm[1]

        errors_mlp += results_mlp[0]
        totals_mlp += results_mlp[1]

    return (errors_gmm, totals_gmm), (errors_mlp, totals_mlp)
