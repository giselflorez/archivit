# Quick Protection Guide
## WEB3GISEL - ARCHIV-IT

## 🚀 Quick Start

### Create Protected Build
```bash
cd /Users/onthego/+NEWPROJ
python scripts/protection/obfuscate_code.py
```

This creates `protected_build/` with **6 layers of protection**:
1. ✅ Anti-AI encryption
2. ✅ Bytecode compilation
3. ✅ JavaScript obfuscation
4. ✅ CSS minification
5. ✅ File structure protection
6. ✅ Hardware-bound licensing

### Distribute to Testers
```bash
# Zip the protected build
zip -r protected_build_v1.0.zip protected_build/

# Send to tester with instructions
```

### Tester Setup (They Do This)
```bash
# 1. Extract
unzip protected_build_v1.0.zip
cd protected_build

# 2. Generate license (on their machine)
python scripts/protection/generate_tester_license.py "Tester Name"

# 3. Run
python start_protected.py
```

---

## 🔒 What's Protected

| Feature | Protection Level |
|---------|-----------------|
| **AI Reconstruction** | ⭐⭐⭐⭐⭐ Impossible |
| **Source Code Theft** | ⭐⭐⭐⭐⭐ No source distributed |
| **License Sharing** | ⭐⭐⭐⭐⭐ Hardware-bound |
| **Reverse Engineering** | ⭐⭐⭐⭐⭐ Encrypted runtime |
| **Partial Copying** | ⭐⭐⭐⭐⭐ Dependency chains |

---

## ⚠️ NEVER Do This

❌ Don't send `protected_build` to git
❌ Don't share your development folder
❌ Don't commit `license.key` files
❌ Don't give source code to testers

---

## ✅ Always Do This

✅ Only distribute `protected_build.zip`
✅ Keep original source private
✅ Generate unique licenses per tester
✅ Track who has access
✅ Revoke by deleting `license.key`

---

## 📋 Tester Checklist

Send this to new testers:

```
# ARCHIV-IT - Beta Testing Setup

1. Extract protected_build.zip
2. Install Python dependencies:
   pip install -r requirements.txt
3. Generate your license:
   python scripts/protection/generate_tester_license.py "Your Name"
4. Start the app:
   python start_protected.py

IMPORTANT:
- Works only on THIS computer
- License expires in 90 days
- DO NOT share or redistribute
- DO NOT attempt to copy code
- DO NOT feed to AI tools

Questions? Email: info@giselx.art
```

---

## 🔧 Advanced

### Custom License Duration
```bash
# 30-day license
python scripts/protection/generate_tester_license.py "Name" 30

# 180-day license
python scripts/protection/generate_tester_license.py "Name" 180
```

### Check License Status
```python
from scripts.protection.license_manager import LicenseManager
lm = LicenseManager()
valid, msg = lm.validate_license()
print(msg)
```

### Verify Protection Integrity
```bash
python scripts/protection/anti_ai_protection.py
```

---

## 📖 Full Documentation

- `PROTECTION_README.md` - Complete guide
- `ANTI_AI_PROTECTION_SUMMARY.md` - Anti-AI technical details
- `LICENSE` - Legal terms

---

**Protected by WEB3GISEL © 2026**
