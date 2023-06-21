from utils import evaluate_batch, print_results, PRERECORDED_TRACES_DIR

print("Performing base experiment. Estimated runtime: 20 minutes")

results_gmm_cfa, results_mlp_cfa = evaluate_batch(
    f"{PRERECORDED_TRACES_DIR}/0-base-experiments/spectrem/cf/setup-a/",  # Directory containing the traces
    f"{PRERECORDED_TRACES_DIR}/0-base-experiments/pretrained-mlp-models/spectrem/cf/setup-a/spectrem_cf_a_pretrained_model.hdf5", # Path to pretrained model
    "SpectrEM - cf - setup A")
results_gmm_cfb, results_mlp_cfb = evaluate_batch(
    f"{PRERECORDED_TRACES_DIR}/0-base-experiments/spectrem/cf/setup-b/", 
    f"{PRERECORDED_TRACES_DIR}/0-base-experiments/pretrained-mlp-models/spectrem/cf/setup-b/spectrem_cf_b_pretrained_model.hdf5", 
    "SpectrEM - cf - setup B")

results_gmm_insa, results_mlp_insa = evaluate_batch(
    f"{PRERECORDED_TRACES_DIR}/0-base-experiments/spectrem/ins/setup-a/",  
    f"{PRERECORDED_TRACES_DIR}/0-base-experiments/pretrained-mlp-models/spectrem/ins/setup-a/spectrem_ins_a_pretrained_model.hdf5",
    "SpectrEM - ins - setup B")
results_gmm_insb, results_mlp_insb = evaluate_batch(
    f"{PRERECORDED_TRACES_DIR}/0-base-experiments/spectrem/ins/setup-b/",  
    f"{PRERECORDED_TRACES_DIR}/0-base-experiments/pretrained-mlp-models/spectrem/ins/setup-b/spectrem_ins_b_pretrained_model.hdf5",
    "SpectrEM - ins - setup B")

results_gmm_md, results_mlp_md = evaluate_batch(
    f"{PRERECORDED_TRACES_DIR}/0-base-experiments/meltemdown/ins/setup-b/", 
    f"{PRERECORDED_TRACES_DIR}/0-base-experiments/pretrained-mlp-models/meltemdown/ins/setup-b/meltemdown_ins_b_pretrained_model.hdf5", 
    "MeltEMdown - ins - setup B", 
    spectrem=False)


print(f"SpectrEM")
print(f" -> Control flow gadget")
print_results(results_gmm_cfa, " --> Setup A: GMM:")
print_results(results_mlp_cfa, " --> Setup A: MLP:")

print_results(results_gmm_cfb, " --> Setup B: GMM:")
print_results(results_mlp_cfb, " --> Setup B: MLP:")

print()
print(f" -> Instruction gadget")
print_results(results_gmm_insa, " --> Setup A: GMM:")
print_results(results_mlp_insa, " --> Setup A: MLP:")

print_results(results_gmm_insb, " --> Setup B: GMM:")
print_results(results_mlp_insb, " --> Setup B: MLP:")

print()
print(f"MeltEmdown")
print(f" -> Instruction gadget")
print_results(results_gmm_md, " --> Setup B: GMM:")
print_results(results_mlp_md, " --> Setup B: MLP:")
