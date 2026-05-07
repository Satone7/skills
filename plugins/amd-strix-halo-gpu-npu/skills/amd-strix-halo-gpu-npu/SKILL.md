---
name: amd-strix-halo-gpu-npu
version: 2.0.0
description: "AMD Strix Halo GPU (ROCm) and NPU (XDNA/XRT) driver setup and usage guide. Use this skill whenever working with GPU computing, NPU inference, PyTorch on ROCm, deploying AI/ML models, running LLMs locally, or any task that needs AMD GPU/NPU acceleration on this machine. Also load this when installing ML frameworks (PyTorch, ONNX Runtime, llama.cpp with ROCm, IREE, etc.), benchmarking GPU/NPU performance, or diagnosing ROCm/XRT issues. If the task touches deep learning, model inference, or GPU-accelerated computing on this AMD hardware, load this skill first."
---

# AMD Strix Halo GPU/NPU Setup & Usage

## Hardware Profile

- **APU**: AMD RYZEN AI MAX+ 395 w/ Radeon 8060S
- **GPU Architecture**: gfx1151 (RDNA 4.5)
- **NPU**: AMD XDNA (AIE-ML), PCI 1022:17f0 rev 0x11
- **Memory**: Shared system memory (~109 GB available)
- **OS**: Ubuntu 26.04, kernel 7.0.0-15

---

## State Detection (Read This First)

Before performing any installation or configuration, verify the current state:

### GPU State Detection

```bash
# Quick GPU state check
python3 -c "import torch; print('GPU_OK' if torch.cuda.is_available() and torch.randn(2,2,device='cuda').mean().isfinite() else 'GPU_FAIL')" 2>/dev/null
```

**Expected outputs:**
- `GPU_OK` → ROCm and PyTorch working correctly, no action needed
- `GPU_FAIL` → Check error message, likely needs comgr workaround
- `torch not found` → Install PyTorch first

### NPU State Detection

```bash
# Check NPU device node
ls -la /dev/accel/accel0 2>/dev/null && echo "NPU_DEVICE_OK" || echo "NPU_DEVICE_MISSING"

# Check memlock limit (must be unlimited for NPU)
ulimit -l 2>/dev/null | grep -q "unlimited" && echo "MEMLOCK_OK" || echo "MEMLOCK_NEEDS_FIX"

# Check XRT packages
dpkg -l libxrt-npu2 2>/dev/null | grep -q "^ii" && echo "XRT_INSTALLED" || echo "XRT_NOT_INSTALLED"
```

### comgr Workaround Detection

```bash
# Check if comgr workaround is active
readlink -f /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3 2>/dev/null | grep -q "rocm-backup" && echo "COMGR_WORKAROUND_ACTIVE" || echo "COMGR_NEEDS_WORKAROUND"
```

---

## GPU Installation

### Step 1: Install ROCm Packages

```bash
sudo apt update
sudo apt install -y rocminfo rocm-smi rocm-device-libs-21 libamdhip64-7 libamdhip64-dev \
    hipcc-rocm librocblas5 libmiopen1 librccl1
```

**Verify:**
```bash
rocm-smi                    # Should show GPU info
rocminfo | grep -A5 "CPU"   # Should show HSA agents
rocm_agent_enumerator       # Should print: gfx1151 aie2
```

### Step 2: Install PyTorch (ROCm)

```bash
sudo apt install -y python3-torch-rocm libtorch-rocm-2.9 libtorch-rocm-dev
```

### Step 3: Apply comgr Workaround (CRITICAL)

**Problem:** Ubuntu packages `libamd-comgr3` (from `rocm-llvm`) which depends on system LLVM 21. This library has a bug where AMDGPU targets are not registered at runtime, causing `hipErrorInvalidValue` on any GPU computation.

**Solution:** Replace with `libamd-comgr3-rocm` (from `llvm-toolchain-rocm`) which bundles ROCm's own LLVM.

```bash
# Install ROCm comgr (provides libamd_comgr.so.3.0.0.rocm-backup)
sudo apt install -y libamd-comgr3-rocm

# Backup the working ROCm comgr library
sudo cp /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3.0.0 /tmp/libamd_comgr.so.3.0.0.rocm-backup

# If libamd-comgr3 was installed by apt as a dependency, swap the library:
sudo cp /tmp/libamd_comgr.so.3.0.0.rocm-backup /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3.0.0

# Update symlink to point to the working library
sudo ln -sf libamd_comgr.so.3.0.0 /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3
```

**Verify:**
```bash
# Check workaround is active
readlink -f /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3 | grep -q "rocm-backup" && echo "OK" || echo "NEEDS_FIX"

# Verify GPU compute works
python3 -c "
import torch
x = torch.randn(100, 100, device='cuda')
y = torch.matmul(x, x)
print('GPU_COMPUTE_OK')
"
```

**After `apt upgrade` that touches `libamd-comgr3`:**
```bash
# Re-apply workaround
sudo cp /tmp/libamd_comgr.so.3.0.0.rocm-backup /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3.0.0
```

---

## NPU Installation

### Step 1: Install XRT Packages

```bash
sudo apt install -y libxrt2 libxrt-npu2 libxrt-dev libxrt-utils-npu python3-xrt
```

**Verify:**
```bash
dpkg -l | grep libxrt-npu2    # Should show "ii  libxrt-npu2"
ls -la /dev/accel/accel0      # Should exist (after reboot or module load)
lsmod | grep amdxdna           # Should show loaded kernel module
```

### Step 2: Configure memlock Limits (REQUIRED)

The NPU DMA engine needs unlimited memlock. Without this, `xrt-smi` fails with `mmap failed (err=-11)`.

```bash
# Create limits configuration
echo '* soft memlock unlimited' | sudo tee /etc/security/limits.d/99-amdxdna.conf
echo '* hard memlock unlimited' | sudo tee -a /etc/security/limits.d/99-amdxdna.conf
```

**IMPORTANT:** Requires logout and re-login (or full reboot) to take effect.

**Verify:**
```bash
ulimit -l    # Should show "unlimited"
# If it shows a number like 8192, you need to re-login
```

### Step 3: Verify NPU

```bash
# Check NPU device
ls -la /dev/accel/accel0

# Verify memlock
ulimit -l | grep -q "unlimited" && echo "MEMLOCK_OK" || echo "NEEDS_RELOGIN"

# If memlock OK, test xrt-smi
xrt-smi examine    # Should show NPU device info
```

**Known Issue:** Ubuntu packages do not include the XRT amdxdna SHIM plugin. If `xrt-smi examine` shows "No devices found" even with correct permissions, the plugin may need to be built from source: https://github.com/amd/xdna-driver (build only the SHIM plugin, not the kernel driver).

---

## PyTorch Usage

```python
import torch

# Verify
torch.cuda.is_available()              # True
torch.cuda.get_device_name(0)          # "Radeon 8060S Graphics"
torch.cuda.get_arch_list()             # ['gfx908', 'gfx90a', 'gfx942', 'gfx1030', 'gfx1151', 'gfx1200', 'gfx1201']

# Compute
x = torch.randn(3, 3).cuda()           # GPU tensor
y = torch.matmul(x, x.T)               # GPU matmul

# Device properties
props = torch.cuda.get_device_properties(0)
print(f"GPU: {props.name}")
print(f"VRAM: {props.total_memory / 1024**3:.1f} GB")
```

### Important Notes

- **Do NOT use pip PyTorch ROCm wheels** (rocm7.0) — they bundle incompatible ROCm 7.0 libraries that segfault on this ROCm 7.1.1 system.
- The Debian package works correctly once the comgr workaround is applied.
- `HIP_CLANG_PATH` and `ROCM_PATH` are not needed — system packages handle paths.

---

## NPU Frameworks

- **IREE / AMD AIE** — for compiling and running models on the NPU
- **FastFlowLM** — lightweight Ollama-compatible NPU runtime
- **ONNX Runtime** with Vitis AI EP — for ONNX model inference on NPU

---

## Quick Reference

| What | Command |
|------|---------|
| GPU status | `rocm-smi` |
| GPU architecture | `rocminfo \| grep gfx` |
| GPU compute test | `python3 -c "import torch; x=torch.randn(2,2,device='cuda'); print('OK' if x.mean().isfinite() else 'FAIL')"` |
| NPU device | `ls -la /dev/accel/accel0` |
| NPU status | `xrt-smi examine` (requires unlimited memlock) |
| Check memlock | `ulimit -l` |
| Fix comgr | `sudo cp /tmp/libamd_comgr.so.3.0.0.rocm-backup /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3.0.0` |
| HIP compile | `hipcc -L/usr/lib/x86_64-linux-gnu -lamdhip64 code.cpp -o code` |

---

## Troubleshooting

### GPU: "hipErrorInvalidValue" / "no targets are registered"

The comgr workaround is not applied or was overwritten.

**Fix:**
```bash
# Re-apply workaround
sudo cp /tmp/libamd_comgr.so.3.0.0.rocm-backup /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3.0.0
```

### GPU: Segfault with pip PyTorch ROCm wheel

pip wheels bundle incompatible ROCm 7.0. Use system packages instead.

**Fix:**
```bash
pip uninstall torch
sudo apt install python3-torch-rocm
# Then apply comgr workaround
```

### NPU: "mmap failed (err=-11)" from xrt-smi

memlock limit is too low.

**Fix:**
```bash
# Check config exists
cat /etc/security/limits.d/99-amdxdna.conf

# If missing, create it
echo '* soft memlock unlimited' | sudo tee /etc/security/limits.d/99-amdxdna.conf
echo '* hard memlock unlimited' | sudo tee -a /etc/security/limits.d/99-amdxdna.conf

# Logout and login again, then verify
ulimit -l    # Should show "unlimited"
```

### NPU: "No devices found" from xrt-smi

The XRT amdxdna SHIM plugin may be missing.

**Fix:** Build from source at https://github.com/amd/xdna-driver (SHIM plugin only).

### NPU: /dev/accel/accel0 not found

Kernel module not loaded or firmware missing.

**Fix:**
```bash
# Check kernel module
lsmod | grep amdxdna

# If not loaded, try loading
sudo modprobe amdxdna

# Check firmware
ls /lib/firmware/amdxdna/
```