import pandas as pd
import os
import yaml
from nsds_lab_to_nwb.utils import split_block_folder

class ExpNoteReader():
    def __init__(self, path, block_folder):
        """Class for parsing experiment notes

        Parameters
        ----------
        path : str
            Path or Google Sheets URL to the experiment notes
        block_folder : str
            Name of the block to parse for

        Raises
        ------
        Exception
            Raises exception when trying to parse xlsx or
            Google sheets because those parses are not
            implemented
        """
        self.path = path
        self.input_format = None
        self.block_folder = block_folder
        _, _, blockstr = split_block_folder(block_folder)
        self.block_id = int(blockstr[1:])
        
        self.file = []
        
        # autodetect input format
        if path.startswith('http'):
            self.input_format = 'gs'            
        else:        
            path_contents = os.listdir(path)
            for file in path_contents:
                if file.endswith('.xlsx'): #priority for xlsx format
                    self.input_format = 'xlsx'
                    self.file.append(file)
            if self.input_format is None:
                for file in path_contents:
                    if file.endswith('.csv'): #secondary are csv files
                        self.input_format = 'csv'
                        self.file.append(file)
        
        if self.input_format is None:
            raise Exception('Unknown input format')
        
        self.meta_df = None
        self.block_df = None
        self.meta_block_df = None
        self.nsds_meta = None
    
    def read_input(self):
        """Read input
        """
        if self.input_format == 'csv':
            self.read_csvs()
        elif self.input_format == 'xlsx':
            self.read_xlsx()
        elif self.input_format == 'gs':
            self.read_gs()        
        
    def read_csvs(self):
        """Read csv files
        """
        #detect which csv is a block and which is meta based on 
        #default name Google Drive assigns when downloading it
        if self.file[0].endswith('BlockData.csv'):
            block_file = self.file[0]
            meta_file = self.file[1]
        else:
            block_file = self.file[1]
            meta_file = self.file[0]
            
        meta_path_file = os.path.join(self.path, meta_file)
        block_path_file = os.path.join(self.path, block_file)
        raw_meta = pd.read_csv(meta_path_file, 
                               delimiter=',',
                               skiprows=1, 
                               names=['a', 'values', 'b', 'c'],
                               index_col=1,
                               dtype=type('hello'))
        raw_meta = raw_meta.iloc[:, 1]
        raw_meta.dropna(inplace=True)
        self.meta_df = raw_meta
        
        block_df = pd.read_csv(block_path_file,
                                     delimiter=',',
                                     header=2,
                                     dtype=type('hello'))   
        
        #clean up block_df
        for idx, row in block_df.iterrows():
            try:
                _ = int(row['block_id'])
            except:
                max_row = idx
                break
            
        for column in block_df.columns:
            if column.startswith('Unnamed'):
                block_df.drop(column, axis=1, inplace=True)
        block_df = block_df[:max_row]
        block_df.dropna(axis=1, how='all', inplace=True)
        self.block_df = block_df
         
    
    def read_xlsx(self):
        """Read xlsx

        Raises
        ------
        NotImplementedError
            ToDo
        """
        raise NotImplementedError('TODO')
    
    def read_gs(self):
        """Read Google Sheet

        Raises
        ------
        NotImplementedError
            ToDo
        """
        raise NotImplementedError('TODO')
    
    def merge_meta_block(self):
        """Merge meta and block dataframes and return as dictionary
        """
        sub_block = self.block_df[self.block_df['block_id'].astype(int)==self.block_id].transpose().to_dict()[0]
        meta = self.meta_df.to_dict()
        meta.update(sub_block)
        self.nsds_meta = meta
    
    def _dump_dict_as_yaml(self, file_name, my_dict):        
        with open(file_name, 'w') as file:
            yaml.dump(my_dict, file)   
    
    def dump_yaml(self):
        """Dump parsed data as yaml 
        """
        nsds_meta = self.get_nsds_meta()
        self._dump_dict_as_yaml(self.block_folder + '.yaml', nsds_meta)
    
    def get_nsds_meta(self):
        """Get parsed data

        Returns
        -------
        nsds_meta : dict
            Parsed meta data
        """
        if self.nsds_meta is None:
            self.read_input()
            self.merge_meta_block()
        return self.nsds_meta
        