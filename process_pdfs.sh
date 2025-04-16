#!/bin/zsh

# Source the .zshrc file to ensure the environment variables are loaded
source ~/.zshrc

# Get the input paths from Automator
input_paths=("$@")

# Update the PATH environment variable to include the path to any necessary binaries
export PATH="/usr/local/bin:/opt/homebrew/bin:$PATH"

# Add pdf_splitr directory to PATH
export PATH="$HOME/code/pdf_splitr:$PATH"

# Activate the conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate pdf_splitr

# Change to the pdf_splitr directory
cd "$HOME/code/pdf_splitr"

# Check if the first input path is a directory or a file
if [ -d "${input_paths[1]}" ]; then
    # If it's a directory, process all PDFs in it
    for pdf in "${input_paths[1]}"/*.pdf; do
        if [ -f "$pdf" ]; then
            output_file="$(dirname "$pdf")/split_$(basename "$pdf")"
            python pdf_splitr.py "$pdf" "$output_file"
        fi
    done
elif [ -f "${input_paths[1]}" ]; then
    # If it's a file, process the single PDF file
    output_file="$(dirname "${input_paths[1]}")/split_$(basename "${input_paths[1]}")"
    python pdf_splitr.py "${input_paths[1]}" "$output_file"
else
    echo "The path provided does not exist or is not valid."
    exit 1
fi

# Deactivate the conda environment
conda deactivate 