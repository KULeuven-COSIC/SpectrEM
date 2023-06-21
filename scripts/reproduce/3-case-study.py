from utils import evaluate_batch, print_results, get_bit_ssh, get_bit_sftp, PRERECORDED_TRACES_DIR

print("Evaluating case study traces. Estimated runtime: 5 minutes")

results_gmm_ssh, results_mlp_ssh = evaluate_batch(
    f"{PRERECORDED_TRACES_DIR}/3-case-study/ssh-gadget/", 
    f"{PRERECORDED_TRACES_DIR}/3-case-study/pretrained-mlp-models/casestudy-ssh-pretrained-model.hdf5",
    get_bit_ssh,
    "SSH gadget",
    gmm_proba=True)

print(f"SSH gadget")
print_results(results_gmm_ssh, " -> GMM:")
print_results(results_mlp_ssh, " -> MLP:")

results_gmm_sftp, results_mlp_sftp = evaluate_batch(
    f"{PRERECORDED_TRACES_DIR}/3-case-study/sftp-gadget/", 
    f"{PRERECORDED_TRACES_DIR}/3-case-study/pretrained-mlp-models/casestudy-sftp-pretrained-model.hdf5", 
    get_bit_sftp,
    "SFTP gadget",
    gmm_proba=True)

print(f"SFTP gadget")
print_results(results_gmm_sftp, " -> GMM:")
print_results(results_mlp_sftp, " -> MLP:")
