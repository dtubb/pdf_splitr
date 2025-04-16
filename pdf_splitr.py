#!/usr/bin/env python3
"""
PDF Splitter - A tool that splits PDF pages into left and right halves, while preserving annotations.
Useful for old scans of books where each page contains two actual pages.
"""

import os
from pathlib import Path
import typer
from rich import print
from typing import Optional
from PyPDF2 import PdfReader, PdfWriter
from PyPDF2.generic import ArrayObject, FloatObject, NameObject

app = typer.Typer(
    help="Split PDF pages into left and right halves while preserving annotations.",
    add_completion=False
)

class PDFProcessor:
    """Handles the processing of PDF files, splitting each page into left and right halves."""
    
    def __init__(self, input_path: Path, output_path: Path):
        """Initialize the processor with input and output paths.
        
        Args:
            input_path: Path to the input PDF file
            output_path: Path where the processed PDF will be saved
        """
        self.input_path = input_path
        self.output_path = output_path
        
        # Create output directory if it doesn't exist
        os.makedirs(output_path.parent, exist_ok=True)

    def get_page_dimensions(self, page):
        """Get the effective dimensions of the page, preferring CropBox over MediaBox.
        
        The CropBox defines the visible area of the page, while MediaBox defines the physical page size.
        Some PDFs have larger MediaBoxes with white margins defined by the CropBox.
        
        Args:
            page: A PDF page object from PyPDF2
            
        Returns:
            tuple: (width, height, x_offset, y_offset) of the page's visible area
        """
        if '/CropBox' in page:
            box = page.cropbox
        else:
            box = page.mediabox
        
        width = float(box.width)
        height = float(box.height)
        x_offset = float(box.left)
        y_offset = float(box.bottom)
        
        return width, height, x_offset, y_offset

    def process_pdf(self, quiet: bool = False):
        """Process the PDF file, splitting each page into left and right halves.
        
        Args:
            quiet: If True, suppress progress messages
        
        This method:
        1. Reads the input PDF
        2. For each page:
           - Creates a left half with the left portion of content
           - Creates a right half with the right portion of content
           - Preserves and adjusts annotations for each half
        3. Saves the processed PDF with twice as many pages
        """
        reader = PdfReader(self.input_path)
        writer = PdfWriter()
        total_pages = len(reader.pages)

        with typer.progressbar(
            reader.pages,
            length=total_pages,
            label="Processing pages",
            show_pos=True
        ) as progress:
            for page_num, page in enumerate(progress, 1):
                width, height, x_offset, y_offset = self.get_page_dimensions(page)
                
                # Create left half
                left_page = PdfWriter()
                left_page.add_page(page)
                left_page.pages[0].mediabox.lower_left = (x_offset, y_offset)
                left_page.pages[0].mediabox.upper_right = (x_offset + width/2, y_offset + height)
                
                # Handle annotations for left page
                if '/Annots' in left_page.pages[0]:
                    annots = left_page.pages[0]['/Annots']
                    if annots:
                        new_annots = []
                        for annot in annots:
                            try:
                                # Handle indirect object references
                                if hasattr(annot, 'get_object'):
                                    annot = annot.get_object()
                                
                                # Check if annotation overlaps with left half
                                if '/Rect' in annot:
                                    rect = annot['/Rect']
                                    x_left = float(rect[0])
                                    x_right = float(rect[2])
                                    if x_right > x_offset and x_left < x_offset + width/2:
                                        new_annots.append(annot)
                            except Exception as e:
                                if not quiet:
                                    typer.secho(
                                        f"Warning: Could not process annotation on page {page_num}: {e}",
                                        fg=typer.colors.YELLOW
                                    )
                                continue
                        
                        # Update or remove annotations list
                        if new_annots:
                            left_page.pages[0][NameObject('/Annots')] = ArrayObject(new_annots)
                        elif '/Annots' in left_page.pages[0]:
                            del left_page.pages[0]['/Annots']

                writer.add_page(left_page.pages[0])

                # Create right half
                right_page = PdfWriter()
                right_page.add_page(page)
                right_page.pages[0].mediabox.lower_left = (x_offset + width/2, y_offset)
                right_page.pages[0].mediabox.upper_right = (x_offset + width, y_offset + height)

                # Handle annotations for right page
                if '/Annots' in right_page.pages[0]:
                    annots = right_page.pages[0]['/Annots']
                    if annots:
                        new_annots = []
                        for annot in annots:
                            try:
                                # Handle indirect object references
                                if hasattr(annot, 'get_object'):
                                    annot = annot.get_object()
                                
                                # Check if annotation overlaps with right half
                                if '/Rect' in annot:
                                    rect = annot['/Rect']
                                    x_left = float(rect[0])
                                    x_right = float(rect[2])
                                    if x_right > x_offset + width/2 and x_left < x_offset + width:
                                        new_annots.append(annot)
                            except Exception as e:
                                if not quiet:
                                    typer.secho(
                                        f"Warning: Could not process annotation on page {page_num}: {e}",
                                        fg=typer.colors.YELLOW
                                    )
                                continue
                        
                        # Update or remove annotations list
                        if new_annots:
                            right_page.pages[0][NameObject('/Annots')] = ArrayObject(new_annots)
                        elif '/Annots' in right_page.pages[0]:
                            del right_page.pages[0]['/Annots']

                writer.add_page(right_page.pages[0])

        # Save the processed PDF
        with open(self.output_path, "wb") as output_file:
            writer.write(output_file)

@app.command()
def split_pdf(
    input_pdf: Path = typer.Argument(
        ...,
        help="Path to the input PDF file",
        exists=True,
        dir_okay=False,
        resolve_path=True
    ),
    output_pdf: Path = typer.Argument(
        ...,
        help="Path where the processed PDF will be saved",
        dir_okay=False,
        resolve_path=True
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet", "-q",
        help="Suppress progress messages"
    )
):
    """Split each page of a PDF into left and right halves, preserving annotations."""
    try:
        processor = PDFProcessor(input_pdf, output_pdf)
        processor.process_pdf(quiet=quiet)
        if not quiet:
            typer.secho(
                f"\nSuccessfully created: {output_pdf}",
                fg=typer.colors.GREEN
            )
    except Exception as e:
        typer.secho(f"Error: {str(e)}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 