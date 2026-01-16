
# ElroiKit
**ELROILAB Labeling/Training GUI Tool**

## Setup Instructions

### 1. Create Anaconda Environment
```sh
conda env create -f conda_environment.yml
```

### 2. Install PyTorch 2.6.0
```sh
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu126
```

### 3. Install PyQt5-commercial
NAS path: `\\192.168.119.6\기업부설연구소2\공유폴더\02. License\01.연구소\01.PYQT\1.latest releases\PyQt5_commercial-5.15.9-cp37-abi3-win_amd64.whl`
```sh
pip install PyQt5_commercial-5.15.9-cp37-abi3-win_amd64.whl
```

### 4. Register PyArmor License
NAS path: `\\192.168.119.6\기업부설연구소2\공유폴더\02. License\01.연구소\03.Pyarmor\pyarmor-regfile-2740.zip`
```sh
pyarmor register pyarmor-regfile-2740.zip
```

### Additional Tools
- **pyarmor 7.7.4** - Requires Purchase

## Creating Installer Instructions

### 1. Obfuscation & Packaging with PyArmor and PyInstaller
Run the build.bat script to obfuscate and package your application.
```sh
build.bat
```
The packaged and obfuscated application will be located in the `.\dist\ElroiKit` directory.

### 2. Creating an Installer with NSIS
To create an installer for the ELROI Kit using NSIS, follow these steps:

1. Download and install NSIS from the official website: [NSIS](https://sourceforge.net/projects/nsisbi/).

2. Open the Inno Setup Compiler, load `ElroiKit.nsi` script, and compile it. This will generate the executable installer. `.\deploy\{version}\ElroiKit_V{version}.exe`.

3. Run the generated installer to ensure that it correctly installs your application and that all necessary files are included.

---

This README provides all necessary setup instructions and package information for the ElroiKit. Ensure you follow each step carefully to configure your environment correctly.
