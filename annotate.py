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

# Helper functions
def coords_to_id(coords):
    """Turn coordinates of a highlight into a unique identifier for use as a filename"""
    return "\\" + str(coords[0]) + "." + str(coords[1]) + "." + str(coords[2]) + "." + str(coords[3]) + ".md"

def highlight_to_coords(highlight, doc):
    # NOTE: This is used to identify a highlight in memory, so changing how this works
    # will lose the existing notes in all docs
    try:
        top_left = highlight.get_begin_document_pos()
        bottom_right = highlight.get_end_document_pos()
        top_left_abs = doc_to_abs(top_left.page, top_left.offset_x, top_left.offset_y, doc)
        bottom_right_abs = doc_to_abs(bottom_right.page, bottom_right.offset_x, bottom_right.offset_y, doc)
        return (top_left_abs[0], top_left_abs[1], bottom_right_abs[0], bottom_right_abs[1])
    except Exception as e:
        with open(r"C:\python\sioyek_extensions\test.txt", "w") as file:
            file.write(f"{e}")
            raise e
    # return (highlight.get_begin_abs_pos().offset_x, highlight.get_begin_abs_pos().offset_y, highlight.get_end_abs_pos().offset_x, highlight.get_end_abs_pos().offset_y)

def highlight_to_rect(h, doc):
    return fitz.Rect(*highlight_to_coords(h, doc))

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

def doc_to_abs(page, x_offset, y_offset, doc):
    # see documentation, this is cursed
    # https://sioyek-documentation.readthedocs.io/en/latest/scripting.html
    page_width = doc.page_widths[page]
    return (x_offset - page_width / 2, y_offset + sum(doc.page_heights[:page]))

# Main body
if __name__ == '__main__':
    # will be called with:
    # python annotate.py "%{sioyek_path}" "%{local_database}" "%{shared_database}" "%{file_path}" "%{file_name}" "%{mouse_pos_document}"
    with open(r"C:\python\sioyek_extensions\test.txt", "w") as file:
        file.write("Started!")
    # raise EOFError  # stop there just to see

    if len(sys.argv) > 1:
        SIOYEK_PATH = clean_path(sys.argv[1])
        LOCAL_DATABASE_FILE = clean_path(sys.argv[2])
        SHARED_DATABASE_FILE = clean_path(sys.argv[3])
        doc_path = clean_path(sys.argv[4])
        doc_name = sys.argv[5]
        mouse_pos = sys.argv[6].split(" ")
        mouse_pos = [float(n) for n in mouse_pos]
        page, mouse_x, mouse_y = int(mouse_pos[0]), mouse_pos[1], mouse_pos[2]

    with open(r"C:\python\sioyek_extensions\test.txt", "w") as file:
        file.write("Working!")
    # with open(r"C:\python\sioyek_extensions\test.txt", "w") as file:
    #     file.write(f"Input received: {SIOYEK_PATH}, {LOCAL_DATABASE_FILE}, {SHARED_DATABASE_FILE}, {doc_name}, {(mouse_x, mouse_y)}")

    # Get highlights from Sioyek and find the nearest one to where we clicked
    sioyek = Sioyek(SIOYEK_PATH, LOCAL_DATABASE_FILE, SHARED_DATABASE_FILE)
    doc = sioyek.get_document(doc_path)
    page_width = doc.page_widths[page]
    document_highlights = doc.get_highlights()

    # See documentation; this is cursed
    mouse_abs_pos = (mouse_x - page_width / 2, mouse_y + sum(doc.page_heights[:page]))

    # find closest highlight to location of click
    if len(document_highlights) == 0:
        raise IndexError("No highlights to search!")  # errors just fail silently
    highlight = document_highlights[0]
    min_distance = float("inf")

    test_str = f"Are all the pages the same height? {all([doc.page_heights[0] == height for height in doc.page_heights])}. We are on page {page}. The offset so far is {sum(doc.page_heights[:page])}."

    for h in document_highlights:
        if rect_distance(highlight_to_rect(h, doc), mouse_abs_pos) < min_distance:
            highlight = h
            min_distance = rect_distance(highlight_to_rect(h, doc), mouse_abs_pos)
        # test_str += f"\n Looking at highlight {h}, distance {rect_distance(highlight_to_rect(h, doc), mouse_abs_pos)} away at location {highlight_to_coords(h, doc)} on page {h.get_begin_document_pos().page}."
    highlight_coords = highlight_to_coords(highlight, doc)

    # Import existing annotations data and check if this doc has an entry
    try:
        document_annotations = load_dict(ANNOTATIONS_MEMORY)
    except EOFError:
        document_annotations = {}

    if doc_name not in document_annotations:
        document_annotations[doc_name] = {}
    curr_annotations = document_annotations[doc_name]  # holds a dict of existing annotations within this doc
    # should have highlight_rectangle : markdown_filename pairs

    # Create new annotation for this highlight if needed
    if highlight_coords not in curr_annotations:
        filepath = ANNOTATIONS_FOLDER_PATH + coords_to_id(highlight_coords)
        try:
            with open(filepath, "x") as _:
                pass
            # x is create mode; create file if it does not exist or error
            with open(filepath, "w") as file:
                file.write("# " + highlight.text)
        except:
            pass

        curr_annotations[highlight_coords] = filepath

    # Store updated annotations data and open the relevant file
    save_dict(document_annotations, ANNOTATIONS_MEMORY)

    os.startfile(curr_annotations[highlight_coords])
