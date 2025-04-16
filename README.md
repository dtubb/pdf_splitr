# PDF Splitter (pdf_splitr)

A Python tool for splitting PDF pages into left and right halves while preserving annotations. This is useful for scanned books, where each page contains two real pages. It includes a Mac OS X Service and a App, made with automator.

## Features

- Splits each PDF page into left and right halves
- Preserves and correctly positions annotations on each half
- Handles PDFs with different page dimensions and crop boxes

## Installation

1. Clone this repository to `~/code/pdf_splitr` (required for Automator integration):
   ```bash
   mkdir -p ~/code
   cd ~/code
   git clone https://github.com/dtubb/pdf_splitr.git
   cd pdf_splitr
   ```

2. Choose your installation method:

   ### Option A: Using Conda (recommended)
   ```bash
   # Create and activate conda environment
   conda create -n pdf_splitr python=3.8
   conda activate pdf_splitr
   
   # Install dependencies
   pip install -r requirements.txt
   ```

   ### Option B: Using pip only
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Command Line

If using conda, activate the environment first:
```bash
conda activate pdf_splitr
```

Run the script with input and output PDF file paths:
```bash
python pdf_splitr.py <input_pdf> <output_pdf>
```

Example:
```bash
python pdf_splitr.py "my_book.pdf" "split_book.pdf"
```

Options:
```bash
python pdf_splitr.py --help
```

### macOS Automator Integration

The repository includes:
- An Automator Quick Action for processing selected PDFs
- An Automator Application for drag-and-drop PDF processing

Both Automator workflows require the code to be located at `~/code/pdf_splitr`. They will:
- Process single PDF files or entire folders of PDFs
- Create split versions with "split_" prefix in the same location
- Show progress in the macOS notification center

To use the Automator workflows:
1. Ensure the code is installed at `~/code/pdf_splitr`
2. Double-click the Automator workflows to install them
3. For Quick Actions: Right-click PDFs in Finder and select the action
4. For the Application: Drag PDFs or folders onto the app icon

## How It Works

The script:
1. Reads each page of the input PDF
2. Determines the correct page dimensions using CropBox (if available) or MediaBox
3. Creates two new pages for each input page:
   - Left half: from left edge to middle
   - Right half: from middle to right edge
4. Preserves annotations that overlap with each half
5. Adjusts annotation positions to match the new page boundaries
6. Combines all processed pages into a new PDF

## Limitations

- Assumes pages should be split exactly in half
- Does not handle rotated pages or complex page layouts
- May not preserve all types of interactive PDF elements

## Contributing

Feel free to open issues or submit pull requests with improvements.

## Acknowledgments

Written with Cursor.Ai, using Claude.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation


Daniel Tubb. 2025. "PDF Splitter Tool". Available at: https://github.com/your-repo/pdf_splitr

