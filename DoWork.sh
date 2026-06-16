#!/bin/bash
set -e

echo "Starting DoWork.sh..."

cd "$(dirname "$0")"


find_python() {
	for py_cmd in python3 python python3.10 python3.9 python3.8 python3.7; do
		if command -v $py_cmd >/dev/null 2>&1; then
			ver=$($py_cmd -c 'import sys; print(sys.version_info.major)')
			if [ "$ver" -eq 3 ]; then
				echo $py_cmd
				return 0
			fi
		fi
	done
	return 1
}


install_venv_package() {
	echo "Attempting to install 'python3-venv' automatically..."

	if [ -f /etc/os-release ]; then
		. /etc/os-release
		DISTRO_ID=$ID
	else
		echo "ERROR: Cannot detect OS type. Please install 'python3-venv' manually."
		return 1
	fi

	case "$DISTRO_ID" in
		ubuntu|debian)
			echo "Detected Debian-based system ($DISTRO_ID)"
			apt update && apt install -y python3-venv && return 0
			command -v sudo >/dev/null && sudo apt update && sudo apt install -y python3-venv && return 0
			;;
		fedora)
			echo "Detected Fedora"
			dnf install -y python3-venv && return 0
			command -v sudo >/dev/null && sudo dnf install -y python3-venv && return 0
			;;
		centos|rhel)
			echo "Detected RHEL/CentOS"
			yum install -y python3-venv && return 0
			command -v sudo >/dev/null && sudo yum install -y python3-venv && return 0
			;;
		opensuse*|suse)
			echo "Detected openSUSE"
			zypper install -y python3-venv && return 0
			command -v sudo >/dev/null && sudo zypper install -y python3-venv && return 0
			;;
		*)
			echo "Unknown or unsupported distribution: $DISTRO_ID"
			;;
	esac

	echo "ERROR: Failed to install 'python3-venv' automatically. Please install it manually."
	return 1
}


PYTHON_BIN=$(find_python)

if [ -z "$PYTHON_BIN" ]; then
	echo "ERROR: No suitable Python3 interpreter found on this server."
	exit 1
else
	echo "Using Python interpreter: $PYTHON_BIN"
fi


if ! "$PYTHON_BIN" -m venv --help >/dev/null 2>&1; then
	echo "'venv' module not available."
	install_venv_package || exit 1


	if ! "$PYTHON_BIN" -m venv --help >/dev/null 2>&1; then
		echo "Still missing 'venv' even after install. Please check manually."
		exit 1
	fi
fi


ENV_DIR="env"

if [ -d "$ENV_DIR" ]; then
	echo "Removing existing virtual environment: $ENV_DIR"
	rm -rf "$ENV_DIR"
fi

echo "Creating virtual environment using $PYTHON_BIN..."
$PYTHON_BIN -m venv "$ENV_DIR"

echo "Activating virtual environment..."
source "$ENV_DIR/bin/activate"

pip install --upgrade pip >/dev/null 2>&1


if [ -f "requirements.txt" ]; then
	echo "Installing dependencies from requirements.txt"
	pip install -r requirements.txt >/dev/null 2>&1
fi


echo "Running Python scripts..."

./env/bin/python code/summary_stats_data.py >/dev/null 2>&1
./env/bin/python code/aro_heatmap_sex_or_race.py >/dev/null 2>&1
./env/bin/python code/aro_heatmap_sex_race_charge.py >/dev/null 2>&1
./env/bin/python code/circle_bar_graph_race.py >/dev/null 2>&1
./env/bin/python code/circle_bar_graph_sex.py >/dev/null 2>&1
./env/bin/python code/circle_bar_graph_sex_race.py >/dev/null 2>&1
./env/bin/python code/edf.py >/dev/null 2>&1
./env/bin/python code/glc.py >/dev/null 2>&1

echo "Compiling LaTeX report..."

cd mypapers

pdflatex mypaper.tex > ../latex.log 2>&1
bibtex mypaper > ../latex.log 2>&1
pdflatex mypaper.tex > ../latex.log 2>&1
pdflatex mypaper.tex > ../latex.log 2>&1

cd ..

tail -n 10 latex.log | grep -i "Output written on" || echo "LaTeX compilation done."

echo "DoWork.sh completed! Check plots/, tables/, and mypapers/ for outputs."

deactivate || true



