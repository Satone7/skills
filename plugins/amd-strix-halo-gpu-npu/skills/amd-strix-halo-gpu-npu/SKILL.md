---
name: amd-strix-halo-gpu-npu
version: 3.0.0
description: "AMD Strix Halo GPU (ROCm) and NPU (XDNA/XRT) driver setup and usage guide. Use this skill whenever working with GPU computing, NPU inference, PyTorch on ROCm, deploying AI/ML models, running LLMs locally, or any task that needs AMD GPU/NPU acceleration on this machine. Also load this when installing ML frameworks (PyTorch, ONNX Runtime, llama.cpp with ROCm, IREE, etc.), benchmarking GPU/NPU performance, or diagnosing ROCm/XRT issues. If the task touches deep learning, model inference, or GPU-accelerated computing on this AMD hardware, load this skill first."
---

# AMD Strix Halo GPU/NPU Setup & Usage

## Hardware Profile

- **APU**: AMD RYZEN AI MAX+ 395 w/ Radeon 8060S (STRXLGEN, DID 0x1586)
- **GPU Architecture**: gfx1151 (RDNA 4.5)
- **NPU**: AMD XDNA (AIE-ML), PCI 1022:17f0 rev 0x11
- **Memory**: 107 GB system memory, shared GPU VRAM
- **OS**: Ubuntu 26.04, kernel 7.0.0-15 (OEM, >= 6.14-1018 required)
- **ROCm**: Installed via `amdgpu-install 30.30.1` with `--no-dkms` (inbox drivers)
- **HIP**: 7.1.52801
- **PyTorch**: 2.9.1 (Ubuntu `python3-torch-rocm`)

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
# Check if comgr symlink points to the working library (>= 100MB, not the broken ~58MB one)
COMGR_SIZE=$(stat -c%s "$(readlink -f /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3)" 2>/dev/null || echo 0)
[ "$COMGR_SIZE" -gt 100000000 ] 2>/dev/null && echo "COMGR_OK" || echo "COMGR_NEEDS_FIX"
```

---

## GPU Installation

### Step 1: User Groups (REQUIRED)

Add current user to `render` and `video` groups for GPU resource access. Reboot required.

```bash
sudo usermod -a -G render,video $LOGNAME
# Reboot after this
```

**Verify:**
```bash
groups | grep -E "render|video"
```

### Step 2: Install ROCm via amdgpu-install (Official Method)

Follow the official AMD Ryzen ROCm installation guide. The `--no-dkms` flag is required because inbox drivers are used.

```bash
# Download and install the installer script (Ubuntu 24.04/26.04)
wget https://repo.radeon.com/amdgpu-install/7.2.1/ubuntu/noble/amdgpu-install_7.2.1.70201-1_all.deb
sudo apt install ./amdgpu-install_7.2.1.70201-1_all.deb

# Install ROCm (no DKMS — inbox drivers only)
amdgpu-install -y --usecase=rocm --no-dkms
```

**Verify:**
```bash
rocm-smi                    # Should show GPU info (Radeon 8060S)
rocminfo | grep -A5 "Agent 2"  # Should show gfx1151
rocm_agent_enumerator       # Should print: gfx1151
hipcc --version             # Should show HIP 7.1
```

### Step 3: Install PyTorch (ROCm)

```bash
sudo apt install -y python3-torch-rocm libtorch-rocm-2.9 libtorch-rocm-dev
```

**IMPORTANT:** Do NOT use pip PyTorch ROCm wheels — they bundle incompatible ROCm libraries that segfault.

### Step 4: Apply comgr Workaround (CRITICAL)

**Problem:** Ubuntu packages `libamd-comgr3` (~58MB, from `rocm-llvm`) which depends on system LLVM 21. This library has a bug where AMDGPU targets are not registered at runtime, causing `hipErrorInvalidValue` or segfault on any GPU computation.

`amdgpu-install` may set the comgr symlink to point to this broken library after installation.

**Solution:** Point the symlink to the correct library file (>= 100MB).

```bash
# Install ROCm comgr (provides the working library)
sudo apt install -y libamd-comgr3-rocm

# Verify the base library file is the large (working) one
ls -lh /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3.0.0
# Should be ~132MB, NOT ~58MB

# Fix symlink to point to the base file (not any backup)
sudo ln -sf libamd_comgr.so.3.0.0 /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3
```

**Verify:**
```bash
# Check symlink points to large library
stat -c%s "$(readlink -f /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3)" | grep -qE "^[1-9][0-9]{8,}" && echo "COMGR_OK" || echo "COMGR_NEEDS_FIX"

# Verify GPU compute works
python3 -c "
import torch
x = torch.randn(100, 100, device='cuda')
y = torch.matmul(x, x)
print('GPU_COMPUTE_OK')
"
```

**After `apt upgrade` or `amdgpu-install` that touches comgr:**
```bash
# Check and re-apply if needed
COMGR_SIZE=$(stat -c%s "$(readlink -f /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3)" 2>/dev/null || echo 0)
[ "$COMGR_SIZE" -lt 100000000 ] && sudo ln -sf libamd_comgr.so.3.0.0 /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3
```

### Step 5: Configure Shared Memory (TTM)

ROCm uses shared system memory. Default is ~50% of system RAM. Use `amd-ttm` to adjust.

```bash
# Install amd-ttm tool
pipx install amd-debug-tools

# Query current setting
amd-ttm

# Set to desired GB (e.g., 80 GB)
amd-ttm --set 80
# Reboot required
```

**BIOS recommendation:** Set minimum dedicated VRAM to 0.5GB in BIOS, then set TTM to a larger amount.

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

- **Do NOT use pip PyTorch ROCm wheels** — they bundle incompatible ROCm libraries that segfault. Use Ubuntu `python3-torch-rocm` instead.
- **amdgpu-install sets broken comgr symlink** — After running `amdgpu-install`, the `libamd_comgr.so.3` symlink may point to the broken Ubuntu comgr (~58MB). Always verify and fix after installation.
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
| Fix comgr | `sudo ln -sf libamd_comgr.so.3.0.0 /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3` |
| TTM memory | `amd-ttm` / `amd-ttm --set <GB>` |
| HIP compile | `hipcc -L/usr/lib/x86_64-linux-gnu -lamdhip64 code.cpp -o code` |

---

## Troubleshooting

### GPU: Segfault or "hipErrorInvalidValue" / "no targets are registered"

The comgr workaround is not applied or was overwritten by `apt upgrade` / `amdgpu-install`.

**Fix:**
```bash
# Check current library size (must be > 100MB)
COMGR_SIZE=$(stat -c%s "$(readlink -f /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3)" 2>/dev/null || echo 0)
echo "Current comgr size: $COMGR_SIZE bytes"

# Fix symlink to point to the working base library
sudo ln -sf libamd_comgr.so.3.0.0 /usr/lib/x86_64-linux-gnu/libamd_comgr.so.3
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