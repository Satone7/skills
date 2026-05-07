---
name: amd-strix-halo-gpu-npu
version: 1.0.0
description: "AMD Strix Halo GPU (ROCm) and NPU (XDNA/XRT) driver setup and usage guide. Use this skill whenever working with GPU computing, NPU inference, PyTorch on ROCm, deploying AI/ML models, running LLMs locally, or any task that needs AMD GPU/NPU acceleration on this machine. Also load this when installing ML frameworks (PyTorch, ONNX Runtime, llama.cpp with ROCm, IREE, etc.), benchmarking GPU/NPU performance, or diagnosing ROCm/XRT issues. If the task touches deep learning, model inference, or GPU-accelerated computing on this AMD hardware, load this skill first."
---

# AMD Strix Halo GPU/NPU Setup & Usage

## Hardware Profile

- **APU**: AMD RYZEN AI MAX+ 395 w/ Radeon 8060S
- **GPU Architecture**: gfx1151 (RDNA 4.5)
- **NPU**: AMD XDNA (AIE-ML), PCI 1022:17f0 rev 0x11
- **Memory**: Shared system memory (~109 GB available)
- **OS**: Ubuntu 26.04, kernel 7.0.0-15

## ROCm GPU Stack

### Installed Packages

```bash
rocminfo rocm-smi rocm-device-libs-21 libamdhip64-7 libamdhip64-dev
hipcc-rocm librocblas5 libmiopen1 librccl1
```

All from Ubuntu universe repos (ROCm 7.1.1).

### Critical: comgr Workaround

Ubuntu packages `libamd-comgr3` (from `rocm-llvm`) which depends on system LLVM 21.
This library has a bug where AMDGPU targets are not registered at runtime, causing
`hipErrorInvalidValue` on any GPU computation (`no targets are registered`).

**Fix**: Replace with `libamd-comgr3-rocm` (from `llvm-toolchain-rocm`), which bundles
ROCm's own LLVM and works correctly. Both provide the same SONAME (`libamd_comgr.so.3`)
and are ABI-compatible.

```bash
# Install ROCm comgr and back up its library
sudo apt install -y libamd-comgr3-rocm
sudo cp /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3.0.0 /tmp/libamd_comgr.so.3.0.0.rocm-backup

# Install packages that depend on libamd-comgr3 (apt will swap it in)
sudo apt install -y python3-torch-rocm  # or any other ROCm-dependent package

# Restore the working ROCm comgr library
sudo cp /tmp/libamd_comgr.so.3.0.0.rocm-backup /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3.0.0
```

After any `apt upgrade` that touches `libamd-comgr3`, repeat the restore step.

### Verify GPU

```bash
rocm-smi                          # GPU status, temperature, power
rocminfo | head -40               # HSA agents and gfx architecture
rocm_agent_enumerator              # prints: gfx1151 aie2
```

## PyTorch (ROCm)

### Installation

```bash
sudo apt install -y python3-torch-rocm libtorch-rocm-2.9 libtorch-rocm-dev
# Then apply the comgr workaround above
```

Version: **2.9.1+debian** (system Python 3.14).

### Usage

```python
import torch

# Verify
torch.cuda.is_available()              # True
torch.cuda.get_device_name(0)          # "Radeon 8060S Graphics"
torch.cuda.get_arch_list()             # ['gfx908', 'gfx90a', 'gfx942', 'gfx1030', 'gfx1151', 'gfx1200', 'gfx1201']

# Compute
x = torch.randn(3, 3).cuda()           # GPU tensor
y = torch.matmul(x, x.T)              # GPU matmul
```

### Important Notes

- Do **not** use pip PyTorch ROCm wheels (rocm7.0) — they bundle incompatible ROCm 7.0
  libraries that segfault on this ROCm 7.1.1 system.
- The Debian package works correctly once the comgr workaround is applied.
- `HIP_CLANG_PATH` and `ROCM_PATH` are not needed — the system packages handle paths.

## NPU (AMD XDNA)

### Installed Packages

```bash
libxrt2 libxrt-npu2 libxrt-dev libxrt-utils-npu   # XRT 2.21.75
```

### Device Node

```
/dev/accel/accel0    (not /dev/npu*)
```

Kernel module: `amdxdna` (in-tree, firmware v1.1.2.65).

### Required Configuration

The NPU DMA engine needs unlimited memlock. Without this, `xrt-smi` fails with
`mmap failed (err=-11)`.

```bash
# One-time setup (requires re-login to take effect)
echo '* soft memlock unlimited' | sudo tee /etc/security/limits.d/99-amdxdna.conf
echo '* hard memlock unlimited' | sudo tee -a /etc/security/limits.d/99-amdxdna.conf
```

After re-login, verify with `ulimit -l` (should show `unlimited`).

### Verify NPU

```bash
source /opt/xilinx/xrt/setup.sh
xrt-smi examine          # Should show "NPU Strix" or "RyzenAI-npu5"
```

If `xrt-smi examine` shows "No devices found", the XRT amdxdna SHIM plugin may be
missing from the Ubuntu packages. Build it from source:
https://github.com/amd/xdna-driver (build only the SHIM plugin, not the kernel driver).

### NPU Frameworks

- **IREE / AMD AIE** — for compiling and running models on the NPU
- **FastFlowLM** — lightweight Ollama-compatible NPU runtime
- **ONNX Runtime** with Vitis AI EP — for ONNX model inference on NPU

## Quick Reference

| What | Command |
|------|---------|
| GPU status | `rocm-smi` |
| GPU architecture | `rocminfo \| grep gfx` |
| PyTorch GPU test | `python3 -c "import torch; print(torch.cuda.is_available(), torch.randn(2,2).cuda())"` |
| NPU device | `ls -la /dev/accel/accel0` |
| NPU status | `source /opt/xilinx/xrt/setup.sh && xrt-smi examine` |
| Fix comgr | `sudo cp /tmp/libamd_comgr.so.3.0.0.rocm-backup /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3.0.0` |
| HIP compile | `hipcc -L/usr/lib/x86_64-linux-gnu -lamdhip64 code.cpp -o code` |
