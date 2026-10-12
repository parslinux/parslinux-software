# Pars Linux Software Center - Claude Instructions

For full instructions, architecture details, and coding rules, please see:
[docs/CLAUDE.md](docs/CLAUDE.md)

### Quick Commands:
- **Compile Check:** `python3 -m py_compile setup.py src/*.py src/controllers/*.py`
- **Run Application:** `./parslinux-software`
- **Verify Mixin Controllers:** `python3 scratch/verify_mixins.py`
- **FlowBox Stability Test:** `python3 scratch/test_flowbox_stability.py`
- **Headless Application Test:** `python3 scratch/test_mainwindow_headless.py`
- **Backend API Test:** `python3 -c "import sys; sys.path.insert(0, 'src'); from FlathubClient import FlathubClient; print('Flathub:', FlathubClient().check_connection())"`
