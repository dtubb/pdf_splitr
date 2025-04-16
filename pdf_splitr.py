#!/usr/bin/env python3
"""
PDF Splitter - A tool that splits PDF pages into left and right halves, while preserving annotations.
Useful for old scans of books where each page contains two actual pages.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import PyPDF2
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from PyPDF2.generic import ArrayObject, FloatObject, NameObject

app = typer.Typer(help="Split PDF pages into left and right halves while preserving annotations.")
console = Console()

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
        reader = PyPDF2.PdfReader(self.input_path)
        writer = PyPDF2.PdfWriter()
        total_pages = len(reader.pages)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn()
        ) as progress:
            task = progress.add_task("Processing pages", total=total_pages)
            for page_num, page in enumerate(reader.pages, 1):
                width, height, x_offset, y_offset = self.get_page_dimensions(page)
                
                # Create left half
                left_page = PyPDF2.PdfWriter()
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
                                    console.print(f"[yellow]Warning: Could not process annotation on page {page_num}: {e}[/yellow]")
                                continue
                        
                        # Update or remove annotations list
                        if new_annots:
                            left_page.pages[0][NameObject('/Annots')] = ArrayObject(new_annots)
                        elif '/Annots' in left_page.pages[0]:
                            del left_page.pages[0]['/Annots']

                writer.add_page(left_page.pages[0])

                # Create right half
                right_page = PyPDF2.PdfWriter()
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
                                    console.print(f"[yellow]Warning: Could not process annotation on page {page_num}: {e}[/yellow]")
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

def process_pdf(input_path: str, output_path: str) -> None:
    """Process a single PDF file."""
    try:
        processor = PDFProcessor(input_path, output_path)
        processor.process_pdf()
        console.print(f"[green]Successfully processed {input_path} -> {output_path}[/green]")
    except Exception as e:
        console.print(f"[red]Error processing {input_path}: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def main(
    input_pdf: str = typer.Argument(..., help="Input PDF file path"),
    output_pdf: str = typer.Argument(..., help="Output PDF file path"),
) -> None:
    """
    Split PDF pages into left and right halves while preserving annotations.
    
    This is useful for scanned books where each page contains two real pages.
    The script will create a new PDF with twice as many pages, splitting each
    original page into left and right halves.
    """
    # Validate input path
    if not os.path.exists(input_pdf):
        console.print(f"[red]Error: Input file {input_pdf} does not exist[/red]")
        raise typer.Exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_pdf)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    process_pdf(input_pdf, output_pdf)

if __name__ == "__main__":
    app() 