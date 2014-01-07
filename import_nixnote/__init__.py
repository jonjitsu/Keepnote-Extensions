"""

    KeepNote
    Import .nnex Extension

"""
#
# Best to do it in an empty notebook.

#xml parsing

import xml.etree.ElementTree as ET

# keepnote imports
import keepnote
import keepnote.gui.extension
from keepnote import notebook as notebooklib
import os,sys,gtk
import pygtk
pygtk.require('2.0')

import xmltodict

sys.path.append(os.path.dirname(__file__))
#import nnex
#from import_nixnote.nnex import *
from nnex import *

class Extension (keepnote.gui.extension.Extension):

    def __init__(self, app):
        """Initialize extension"""
        
        keepnote.gui.extension.Extension.__init__(self, app)
        self.app = app

    def get_depends(self):
        return [("keepnote", ">=", (0, 7, 1))]


    def on_add_ui(self, window):
        """Initialize extension for a particular window"""
            
        self.add_action(
           window, "Import Nixnotes", "Import from .nnex file",
           lambda w: self.on_import_nnex(window,
                                        window.get_notebook()))
        
        self.add_ui(window,
            """
            <ui>
            <menubar name="main_menu_bar">
               <menu action="File">
                  <menu action="Import">
                     <menuitem action="Import Nixnotes"/>
                  </menu>
               </menu>
            </menubar>
            </ui>
            """)


    def on_import_nnex(self, window, notebook):
        """Callback from gui for importing an ncd file"""
        
        if notebook is None:
            self.app.error("Must have notebook open to import.")
            return None

        """Imports NoteCase free version ncd file"""
        
        dialog = gtk.FileChooserDialog(
            "import nnex file", None, 
            action=gtk.FILE_CHOOSER_ACTION_OPEN, 
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                     gtk.STOCK_OPEN, gtk.RESPONSE_OK))
        
        file_filter = gtk.FileFilter()
        file_filter.add_pattern("*.nnex")
        file_filter.set_name("Nixnote (*.ncd)")
        dialog.add_filter(file_filter)
        
        file_filter = gtk.FileFilter()
        file_filter.add_pattern("*")
        file_filter.set_name("All files (*.*)")
        dialog.add_filter(file_filter)
        
        response = dialog.run()
        
        if response == gtk.RESPONSE_OK:
            if dialog.get_filename():
                nnex_file = dialog.get_filename()
                nnex_importer = NnexImporter(nnex_file, window)
                nnex_importer.import_nixnotes()
                
            # self.close_notebook()
        dialog.destroy()


def unset(d, key):
    d.pop(key, None)
