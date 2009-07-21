#!/usr/bin/env python
"""
output of various data for VAMP project
"""

class DataWriter():
    def __init__(self, datadict):
        self.data = datadict
        self.allfields = sorted(datadict.keys())
        self.paramfields= []
        self.datafields = self.allfields
        self._extract_param_fields()
        
    def set_fields(self, fieldslist):
        self.datafields = fieldslist
        self._extract_param_fields()
    
    def _extract_param_fields(self):
        """
        extract one-item values (parameters) from self.fields
        
        side-effect - changes self.datafields and self.paramfields
                    by moving some values from one to another
        """
        for field in self.datafields:
            if len(self.data[field].shape) == 1:
                self.paramfields.append(field)
                self.datafields.remove(field)
                               
    def _make_header(self):
        header = '#Data export file\n'
        if len(self.paramfields) > 0:
            for param in self.paramfields:
                value = self.data[param]
                header += '#%s (+-error): '%param
                header += len(value)*'\t%f'%tuple(value)+'\n'
        header += '#No.'
        for field in self.datafields:
            header +='\t%s\t%s_error'%(field, field)
        header += '\n'
        return header
    
    def write_file(self, filename):
        try:
            outfile = open(filename, 'w')
        except IOError:
            mesg = 'Can not open file %s for writing!'%filename
            return mesg
        outfile.write(self._make_header())
        length = self.data[self.datafields[0]].shape[-1]
        for i in range(0, length):
            line = '%i'%(i+1)
            for field in self.datafields:
                data = self.data[field][:,i]
                line += len(data)*'\t%f'%tuple(data)
            line += '\n'
            outfile.write(line)
        outfile.close()
        return
