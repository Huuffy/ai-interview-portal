@echo off
call venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt --force-reinstall
pip install -r requirements-torch.txt --index-url https://download.pytorch.org/whl/cu118
pip install openmim
mim install -r requirements-mim.txt
pause
