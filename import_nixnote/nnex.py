import xmltodict
import re
import types
import sys
import codecs
import htmlentitydefs
from BeautifulSoup import BeautifulSoup
from keepnote import notebooklib

class KeepnoteImporter:
    
    def __init__(self, window):
        self.window=window
        
    def unescape(self, text):
        """Removes HTML or XML character references 
           and entities from a text string.
           keep &amp;, &gt;, &lt; in the source code.
        from Fredrik Lundh
        http://effbot.org/zone/re-sub.htm#unescape-html
        """
        def fixup(m):
           text = m.group(0)
           if text[:2] == "&#":
              # character reference
              try:
                 if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                 else:
                    return unichr(int(text[2:-1]))
              except ValueError:
                 print "erreur de valeur"
                 pass
           else:
              # named entity
              try:
                 if text[1:-1] == "amp":
                    text = "&amp;amp;"
                 elif text[1:-1] == "gt":
                    text = "&amp;gt;"
                 elif text[1:-1] == "lt":
                    text = "&amp;lt;"
                 else:
                    # print text[1:-1]
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
              except KeyError:
                 print "keyerror"
                 pass
           return text # leave as is
        return re.sub("&#?\w+;", fixup, text)
        
    HTML_HEAD="""
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <title>Appunti</title>
    </head><body> <br/>
    """
    HTML_TAIL='</body></html>'
    def write_node(self, node, html_content):
        """
            Write the note file associated to the node
        """
        fname = node.get_data_file()
        print "Writing to filename: " + fname
        out = codecs.open(fname, "w", "utf8")
        html_cleaner = BeautifulSoup(self.HTML_HEAD + self.unescape(html_content) + self.HTML_TAIL)
        out.write(html_cleaner.prettify())
        out.close() 
    
    def get_root_node(self):
        if hasattr(self,'window'):
            nodes = self.window.get_selected_nodes()
            if len(nodes) == 1:
               parent = nodes[0]    
            else:
               parent = self.window.get_notebook()
            
            return parent
        
        raise Exception('No window set!')



class NnexImporter(KeepnoteImporter):
    def __init__(self, nnex_file, window):
        self.nnex_file = nnex_file
        self.window = window
        
    def import_nixnotes(self):
        root_node = self.get_root_node()
        nnex_dump = NnexDump(self.nnex_file)
        stack_list = {} # stack name => node list
        for notebook in nnex_dump.get_notebooks():
            nb_node = root_node
            stack_name = notebook.get('Stack')
            if stack_name is not None:
                if stack_list.has_key(stack_name):
                    nb_node = stack_list[stack_name]
                else:
                    nb_node = root_node.new_child(notebooklib.CONTENT_TYPE_DIR, stack_name)
                    stack_list[stack_name] = nb_node
                
            nb_node = nb_node.new_child(notebooklib.CONTENT_TYPE_PAGE, notebook.get('Name'))
            self.set_attrs(nb_node, notebook)
            self.write_node(nb_node,'')
            
            for note in notebook.get_notes():
                n_node = nb_node.new_child(notebooklib.CONTENT_TYPE_PAGE, note.get('Title'))
                self.set_attrs(n_node, note)
                self.write_node(n_node, note.clean_html())

    def set_attrs(self, node, nnex_item):
        self.set_timestamps(node, nnex_item)
        node.set_attr('title', nnex_item.get_name())

    def set_timestamps(self, node, nnex_item):
        created, updated = nnex_item.get_timestamps()
        node.set_attr('created_time', created/1000)
        node.set_attr('modified_time', updated/1000)



class NnexContainer:
    """
    Base class for all the NoteBooks, Notes, Tags in a NnexDump    
    """
    field_types = {} # Uses types so any type within that module is valid (ie: Int, String, Float, Boolean)
    required_fields = []
    defaults = {}
    
    def __init__(self, data):
        self.fields = {} 
        self._parse(data)
        
        
    def get(self, field_name):
        return self.fields[field_name]
    
    def has(self, field_name):
        return self.fields.has_key(field_name)
    
    def _parse(self, data):
        self._parse_required(data)
        self._parse_optional(data)
        self._parse_other(data)
        
    def _parse_other(self, data):
        pass
            
    def _parse_required(self, data):
        for field in self.required_fields:
            field_type = self.field_types[field] if self.field_types.has_key(field) else 'String'
            value = self._find_value(field, data)
            if value == None:
                raise Exception('Required Value Missing: ' + field)
            self.fields[field] = self._convert_type(value, field_type)
    
    def _parse_optional(self, data):
        for field in self.defaults: 
            field_type = self.field_types[field] if self.field_types.has_key(field) else 'String'
            value = self._find_value(field, data)
            if value is None:
                value = self.defaults[field]
            self.fields[field] = self._convert_type(value, field_type)
    
    def _find_value(self, field_name, fields):
        if fields.has_key(field_name):
            return fields[field_name]
        else:
            for field in fields:
                if type(field) is dict:
                    return self._find_value(field_name, field)
                
            return None
        
    def _convert_type(self, value, field_type):
        """
        Converts value to field_type
        """
        try:
            type_name = field_type.capitalize() + 'Type'
            python_type = getattr(types, type_name)
            return python_type(value)
        except KeyError:
            return value
    
    
class NnexTag(NnexContainer):
    required_fields = { 'Name', 'Guid' }
    defaults = { 'ParentGuid':None }
    
    
# A notebook knows about its notes
class NnexNotebook(NnexContainer):
    field_types = { 'ServiceCreated':'int', 'ServiceUpdated':'int' }
    required_fields = [ 'Name', 'Guid', 'ServiceCreated', 'ServiceUpdated' ]
    defaults = { 'ReadOnly':False, 'Stack':None }
    
    def add_notes(self, notes):
        self.notes = [ note for note in notes if note.get('NotebookGuid') == self.fields['Guid'] ]
        
    def get_notes(self):
        return self.notes
    
    def get_name(self):
        return self.fields['Name']
    
    def get_timestamps(self):
        return ( self.fields['ServiceCreated'], self.fields['ServiceUpdated'] )
    
class NnexNote(NnexContainer):
    field_types = { 'Created':'int', 'Updated':'int' }
    required_fields = [ 'Title', 'Guid', 'Created', 'Updated', 'NotebookGuid', 'Content' ]
    defaults = { 'ReadOnly':False }
    html_header = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>Appunti</title>
</head><body>
"""
    html_footer = '</body></html>'
    
    def _parse_other(self, data):
        self.fields['TagGuids'] = []
        if data.has_key('NoteTags') and data['NoteTags'].has_key('Guid'):
            guids = data['NoteTags']['Guid'] if type(data['NoteTags']['Guid']) is list else [ data['NoteTags']['Guid'] ]
            for guid in guids:
                self.fields['TagGuids'].append(guid)
                
        self.strip_nnex_xml()
                
    def add_tags(self, tags):
        self.tags = [ tag for tag in tags if tag.get('Guid') in self.fields['TagGuids'] ]
    
    def strip_nnex_xml(self):
        self.fields['Content'] = re.sub("</en-note>.*","",re.sub('.*<en-note>','', self.fields['Content'].replace("\n","")))
        
    def clean_html(self):
        replacements = { 'text-align\s*:\s*start' : 'text-align: left' }
        html = self.fields['Content']
        for search, replace in replacements.iteritems():
            html = re.sub(search, replace, html, 0, re.MULTILINE)
        return html

    def wrapped_content(self):
        return self.html_header + self.fields['Content'] + self.html_footer
    
    def get_name(self):
        return self.fields['Title']
    
    def get_timestamps(self):
        return ( self.fields['Created'], self.fields['Updated'] )
    
    
class ProgressObservable:
    pass
    
class NnexDump:
    class_map = {
        'tags'      : NnexTag,
        'notes'     : NnexNote,
        'notebooks' : NnexNotebook }
    
    def __init__(self, filename):
        self.filename = filename
        self.loadFile(filename)
        self._parse()
        
    def loadFile(self, filename):
        with open(filename, 'r') as f:
            self.dump = xmltodict.parse(f)
            
        self.dump = self.dump['nevernote-export']
                
    def _parse_items(self, item_type):
        attribute = item_type.lower() + 's'
        setattr(self, attribute, [])
        if self.dump.has_key(item_type):
            items = self.dump[item_type] if type(self.dump[item_type]) is list else [ self.dump[item_type] ]
          
            nnex_class = self.class_map[attribute]
            store = getattr(self, attribute)
            for item in items:
                store.append(nnex_class(item))
            
    def _parse (self):
        for item_type in [ 'Tag', 'Note', 'Notebook']:
            self._parse_items(item_type)
        
        for note in self.notes:
            note.add_tags(self.tags)
            
        for notebook in self.notebooks:
            notebook.add_notes(self.notes)
            
            
    def get_tags(self):
        return self.tags
    
    def get_notebooks(self):
        return self.notebooks
    
    def get_notebooks_for(self, stack):
        return ( nb for nb in self.notebooks if nb.get('Stack') == stack )
    
    def get_notes(self):
        return self.notes
    
    def get_stacks(self):
        seen = set()
        for nb in self.notebooks:
            stackname = nb.get('Stack')
            if stackname not in seen:
                seen.add(stackname)
                yield seen
    
    
def filter_items(items, key, value):
    """ Filters list of items based on key == value """
    return [ item for item in items if item.get(key) == value ]


def find_item(items, key, value):
    """ Returns the first item found or None """
    items = filter_items(items, key, value)
    return items[0] if len(items) > 0 else None