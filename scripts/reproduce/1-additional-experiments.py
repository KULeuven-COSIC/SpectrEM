from utils import evaluate_batch, print_results, get_bit_sp, PRERECORDED_TRACES_DIR
from itertools import product
import numpy as np
from matplotlib import pyplot as plt


print("Evaluating additional experiments. Estimated run time: 20 minutes")

print()
print("Number of training packets")

gadgets = ["cf", "ins"]
setups = ["a", "b"]

results_nb_train = np.zeros((2, 2, 6, 4), dtype=int)

for gadget_i, setup_i in product(range(2), range(2)):
    gadget = gadgets[gadget_i]
    setup = setups[setup_i]

    print(" -> Control flow gadget" if gadget=="cf" else " -> Instruction gadget")
    print(" --> Setup A" if setup=="a" else " --> Setup B")

    for nb_train in range(6):
        results_gmm, results_mlp = evaluate_batch(
            f"{PRERECORDED_TRACES_DIR}/1-additional-experiments/0-training-packets/{gadget}/setup-{setup}/{nb_train}/", 
            f"{PRERECORDED_TRACES_DIR}/0-base-experiments/pretrained-mlp-models/spectrem/{gadget}/setup-{setup}/spectrem_{gadget}_{setup}_pretrained_model.hdf5", 
            get_bit_sp,
            f"SpectrEM - {gadget} - setup {setup} - {nb_train} training packets")

        results_nb_train[gadget_i, setup_i, nb_train, 0] = results_gmm[0]
        results_nb_train[gadget_i, setup_i, nb_train, 1] = results_gmm[1]
        results_nb_train[gadget_i, setup_i, nb_train, 2] = results_mlp[0]
        results_nb_train[gadget_i, setup_i, nb_train, 3] = results_mlp[1]

        print_results(results_gmm, f" ---> {nb_train} training packets: GMM:")
        print_results(results_mlp, f" ---> {nb_train} training packets: MLP:")

    print()


plt.figure(figsize=(15, 5), dpi=80)

ax = plt.subplot(1, 2, 1)
plt.semilogy(np.arange(6), results_nb_train[0, 0, :, 0] / results_nb_train[0, 0, :, 1], "b--", label="Setup A -- GMM")
plt.semilogy(np.arange(6), results_nb_train[0, 0, :, 2] / results_nb_train[0, 0, :, 3], "b-", label="Setup A -- MLP")

plt.semilogy(np.arange(6), results_nb_train[0, 1, :, 0] / results_nb_train[0, 1, :, 1], "y--", label="Setup B -- GMM")
plt.semilogy(np.arange(6), results_nb_train[0, 1, :, 2] / results_nb_train[0, 1, :, 3], "y-", label="Setup B -- MLP")

plt.xlim(0, 5)
plt.ylim(5e-5, 1)

plt.title("Control flow gadget")
plt.ylabel("BER")
plt.xlabel("Number of training packets")
plt.legend()

ax = plt.subplot(1, 2, 2)
plt.semilogy(np.arange(6), results_nb_train[1, 0, :, 0] / results_nb_train[1, 0, :, 1], "b--", label="Setup A -- GMM")
plt.semilogy(np.arange(6), results_nb_train[1, 0, :, 2] / results_nb_train[1, 0, :, 3], "b-", label="Setup A -- MLP")

plt.semilogy(np.arange(6), results_nb_train[1, 1, :, 0] / results_nb_train[1, 1, :, 1], "y--", label="Setup B -- GMM")
plt.semilogy(np.arange(6), results_nb_train[1, 1, :, 2] / results_nb_train[1, 1, :, 3], "y-", label="Setup B -- MLP")



plt.xlim(0, 5)
plt.ylim(5e-5, 1)

plt.title("Instruction gadget")
plt.ylabel("BER")
plt.xlabel("Number of training packets")
plt.legend()
plt.savefig('figure5.png', bbox_inches='tight')




print("Number of udiv instructions")
print(" -> Instruction gadget")
print(" --> Setup B")

results_nb_ins = np.zeros((13, 4), dtype=int)

nb_inss = [1, 2, 4, 8, 12, 16, 24, 32, 40, 48, 56, 64, 72]

for i, nb_ins in enumerate(nb_inss):
    results_gmm, results_mlp = evaluate_batch(
        f"{PRERECORDED_TRACES_DIR}/1-additional-experiments/1-udiv-instructions/{nb_ins:02d}/", 
        f"{PRERECORDED_TRACES_DIR}/1-additional-experiments/pretrained-mlp-models/1-udiv-instructions/spectrem_ins_b_pretrained_model_64.hdf5", 
        get_bit_sp,
        f"SpectrEM - {gadget} - setup {setup} - {nb_ins} udiv instructions")

    results_nb_ins[i, 0] = results_gmm[0]
    results_nb_ins[i, 1] = results_gmm[1]
    results_nb_ins[i, 2] = results_mlp[0]
    results_nb_ins[i, 3] = results_mlp[1]

    print_results(results_gmm, f" ---> {nb_ins} udiv instructions: GMM:")
    print_results(results_mlp, f" ---> {nb_ins} udiv instructions: MLP:")


plt.figure(figsize=(15, 5), dpi=80)

plt.semilogy(nb_inss, results_nb_ins[:, 0] / results_nb_ins[:, 1], "y--", label="Setup B -- GMM")
plt.semilogy(nb_inss, results_nb_ins[:, 2] / results_nb_ins[:, 3], "y-", label="Setup B -- MLP")

plt.xlim(0, 72)
plt.ylim(1e-5, 1)

plt.title("Control flow gadget")
plt.ylabel("BER")
plt.xlabel("Number of training packets")
plt.legend()
plt.savefig('figure7.png', bbox_inches='tight')
