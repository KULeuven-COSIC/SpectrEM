# OpenSSH Case Study

This folder contains the modifications we applied to OpenSSH for our verification.
As mentioned in the paper, we add the following modifications to the code:  
 * We add the same simplifications as we considered in Section 5 (i.e., we flush the length of the array and add a trigger).  
 * We ensure the variable containing the length of the array is not placed in the same cache line by aligning it with the cache line size (64 bytes).
 * We add a way to verify our prediction by adding a way to retrieve the out-of-bounds value. For the SSH server gadget, we log this value, whereas for the SFTP server gadget, we implement an additional function to retrieve this value.

The code can be compiled as follows. Note that you can only compile with one of the modified files at once. To compile the SFTP gadget, replace `channels` with `sftp-server`.

```
git clone --depth 1 --branch V_9_3_P1 https://github.com/openssh/openssh-portable.git
cd openssh-portable
patch channels.c ../channels.diff
autoreconf
./configure
make
```

This will produce the `sshd` binary that can then be instantiated to evaluate the gadgets described in our paper.
