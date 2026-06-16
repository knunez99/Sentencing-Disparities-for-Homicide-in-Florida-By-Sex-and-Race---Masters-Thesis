README
What this zip file contains
---------------------------
This zip file contains the following depositories
- 'code/': This contains all the python scripts involved to clean data and create visualizations.
- 'data/': This contains all the data used for this report, including cleaned csv's and sqlite database.
- 'literature/': This contains all the works done by other researchers that were referenced during the report.
- 'mypapers/': This contains all the Latex files. This is also where the complied pdf of the report will be located.
- 'plots/': This is where all the plots will be sent to and contained.
- 'preliminaries/': This contains the project outline and topic papers.
- 'references/': This contains the Bibtex file and the Chicago.bst that will compile the reference page.
- 'slides/': This contains all the slides as presented on the project throughout the semester.
- 'tables/': This is where all the tables will be sent and contained.
- 'requirmeents.txt': This contains all the packages neccessary to run the scripts
- 'DoWork.sh': This is the shell script you will need to run. Further details listed below.

What the DoWork.sh Shell Script Does
---------------------
- Detects an available Python 3 interpreter on your system.
- Checks if the Python 'venv' module is available for creating virtual environments.
- Attempts to automatically install the 'python3-venv' package if missing, using your system’s package manager
  (supports Debian/Ubuntu, Fedora, CentOS/RHEL, openSUSE).
- Creates and activates a new Python virtual environment in the 'env/' directory.
- Upgrades pip and installs required Python dependencies listed in requirements.txt.
- Runs several Python data processing and visualization scripts located in the 'code/' directory.
- These python code files include creating plots and tables form the 'cases' database located in 'data/'
- Compiles a LaTeX report ('mypaper.pdf') located in the 'mypapers/' directory.
- Prints a summary message when the process completes successfully.

Where to Find Results
---------------------
- The compiled PDF LaTeX report is saved as 'mypaper.pdf' in the 'mypapers/' directory.
- Other output files like plots and tables are saved in their respective directories ('plots/', 'tables/').

Handling 'venv' Package Errors
------------------------------
If you encounter errors related to the missing 'python3-venv' package, the script tries to install it automatically
using your system’s package manager. However:

- You may need sudo privileges to install system packages.
- If automatic installation fails, manually install 'python3-venv' using one of the following commands depending on your system:

  Debian/Ubuntu:
    sudo apt update
    sudo apt install python3-venv

  Fedora:
    sudo dnf install python3-venv

  CentOS/RHEL:
    sudo yum install python3-venv

  openSUSE:
    sudo zypper install python3-venv

- After installing, remove the 'env/' dipository and re-run the script.

