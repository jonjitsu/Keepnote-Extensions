
from import_nixnote.nnex import *
import xmltodict
import os


"""
n=NnexNote(data)
"<?xml version='1.0' encoding='UTF-8'?>\n<!DOCTYPE en-note SYSTEM 'http://xml.evernote.com/pub/enml2.dtd'>\n<en-note>test content \n<div>\n  <br></br>\n </div>\n <div>asdf</div>\n <div>adsf</div>\n <div>\n  <br></br>\n </div>\n</en-note>"

"""
class TestNnex:
    
    def load_file(self, filename):
        with open(self.full_path(filename), 'r') as f:
            return xmltodict.parse(f)
        
        raise Exception('Unable to open: ' + os.getcwd() + '/' + f)
    
    def full_path(self, filename):
        return os.path.realpath(os.path.dirname(os.path.realpath(__file__)) + '/' + filename)
            
    def test_dump(self):
        dump = NnexDump(self.full_path('data/test.nnex'))
        tags = dump.get_tags()
        assert [ '1' , '1385618404354' ] == sorted ([ tag.get('Guid') for tag in tags ])
        notes = dump.get_notes()
        assert notes[0].get('Title') == 'Test Note1'
        assert notes[0].get('Guid') == '1385618385151'
        #note_content =xmltodict.parse(notes[0].get('Content'))
        #assert xmltodict.unparse({ u'body' : note_content['en-note'] }) == True
        assert notes[0].get('Content') == 'test content <div style="color: blue; text-align: start;">  <br></br> </div> <div>asdf</div> <div>adsf</div> <div>  <br></br> </div>'
        assert notes[0].clean_html() == 'test content <div style="color: blue; text-align: left;">  <br></br> </div> <div>asdf</div> <div>adsf</div> <div>  <br></br> </div>'
        nbs = dump.get_notebooks()
        nb = find_item(nbs, 'Guid','1385618372050')
        assert nb.get('Stack') == 'TestStack'
        nb = find_item(nbs, 'Guid','1')
        assert nb.get('Stack') == None
        
    def test_big_dumps(self):
        dump = NnexDump(self.full_path('data/t.nnex'))
    
        
    
    
