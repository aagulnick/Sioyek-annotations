import os
import sys
import pathlib
import sqlite3
from copy import copy
import hashlib
import subprocess

from sioyek.sioyek import Sioyek, clean_path, get_closest_rect_to_point
from PyPDF2 import PdfWriter, PdfReader
import pickle
import fitz
import math

ANNOTATIONS_FOLDER_PATH = "C:\\python\\sioyek_extensions\\Annotations"
ANNOTATIONS_MEMORY = "C:\\python\\sioyek_extensions\\memory.pkl"
# create a file for ANNOTATIONS_MEMORY if no such file exists
try:
    with open(ANNOTATIONS_MEMORY, "x") as _:
        pass
except:
    # if this errors, file already exists
    pass

def coords_to_id(highlight):
    """Turn highlight into a unique identifier for use as a filename"""
    return "\\" + str(highlight[0]) + "." + str(highlight[1]) + "." + str(highlight[2]) + "." + str(highlight[3]) + ".md"

def highlight_to_coords(highlight):
    return (highlight.get_begin_abs_pos().offset_x, highlight.get_begin_abs_pos().offset_y, highlight.get_end_abs_pos().offset_x, highlight.get_end_abs_pos().offset_y)

def highlight_to_rect(h):
    return fitz.Rect(*highlight_to_coords(h))

def save_dict(to_save, memory_path):
    with open(memory_path, "wb") as memory:
        pickle.dump(to_save, memory)

def load_dict(memory_path):
    with open(memory_path, "rb") as memory:
        d = pickle.load(memory)
    return d

def point_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

def rect_distance(rect, point):
    if rect.contains(point):
        return 0
    else:
        center = rect.x0 + rect.width / 2, rect.y0 + rect.height / 2
        return point_distance(center, point)

if __name__ == '__main__':
    # will be called with:
    # python annotate.py "%{sioyek_path}" "%{local_database}" "%{shared_database}" "%{file_name}" "%{mouse_pos_document}"
    if len(sys.argv) > 1:
        SIOYEK_PATH = clean_path(sys.argv[1])
        LOCAL_DATABASE_FILE = clean_path(sys.argv[2])
        SHARED_DATABASE_FILE = clean_path(sys.argv[3])
        doc_path = clean_path(sys.argv[4])
        doc_name = sys.argv[5]
        mouse_pos = sys.argv[6].split(" ")
        mouse_pos = [float(n) for n in mouse_pos]
        page, mouse_x, mouse_y = int(mouse_pos[0]), mouse_pos[1], mouse_pos[2]

    # Get highlights from Sioyek and find the nearest one to where we clicked
    sioyek = Sioyek(SIOYEK_PATH, LOCAL_DATABASE_FILE, SHARED_DATABASE_FILE)
    doc = sioyek.get_document(doc_path)
    page_width = doc.page_widths[page]
    document_highlights = doc.get_highlights()

    # See documentation; this is cursed
    mouse_abs_pos = (mouse_x - page_width / 2, mouse_y + sum(doc.page_heights[:page]))

    with open(r"C:\python\sioyek_extensions\test.txt", "w") as file:
        file.write(f"Trying to delete an annotation associated with highlight at {page, mouse_x, mouse_y}")

    # find closest highlight to location of click
    if len(document_highlights) == 0:
        raise IndexError("No highlights to search!")  # errors just fail silently
    highlight = document_highlights[0]
    min_distance = float("inf")

    for h in document_highlights:
        if rect_distance(highlight_to_rect(h), mouse_abs_pos) < min_distance:
            highlight = h
            min_distance = rect_distance(highlight_to_rect(h), mouse_abs_pos)
    highlight_coords = highlight_to_coords(highlight)

    # Delete annotation corresponding to the closest highlight
    # If we want to change it so user needs to be hovering over the annotation precisely, add the following line and indent the rest of the file:
    # if highlight_to_rect(highlight).contains(mouse_abs_pos):
    # Currently, this doesn't work; probably shenanigans with computing and comparing locations on the screen
    try:
        document_annotations = load_dict(ANNOTATIONS_MEMORY)
    except EOFError:
        document_annotations = {}

    if doc_name in document_annotations:
        curr_annotations = document_annotations[doc_name]
        if highlight_coords in curr_annotations:
            filepath = curr_annotations[highlight_coords]
            del curr_annotations[highlight_coords]
            with open(r"C:\python\sioyek_extensions\test.txt", "w") as file:
                file.write(f"Deleted an annotation associated with highlight {highlight}")
                file.write(f"\n {curr_annotations=}")

    # Store updated annotations data and open the relevant file
    save_dict(document_annotations, ANNOTATIONS_MEMORY)
    os.startfile(filepath)
